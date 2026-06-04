"""
文件获取、流式传输、范围请求
"""
import urllib.parse
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.file_hash import FileHash
from shared.models.media import Media
from shared.utils.logger import get_logger
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db
from .utils import PREVIEWABLE_TYPES, handle_local_file, handle_s3_streaming

logger = get_logger(__name__)
router = APIRouter()


# 公开访问的封面缓存路由（无需认证）
@router.get("/cover/{filename}")
async def get_cover_image(filename: str):
    """
    获取封面图片（公开访问，无需认证）
    
    Args:
        filename: 封面文件名，格式为 {media_id}_{hash}.{ext}
    
    Returns:
        封面图片文件
    """
    try:
        # 构建封面文件路径
        cover_dir = Path("storage/cache/cover")
        cover_path = cover_dir / filename

        # 安全检查：防止目录遍历攻击
        if not cover_path.exists():
            raise HTTPException(status_code=404, detail="封面图片不存在")

        # 确保文件在允许的目录内
        try:
            cover_path.resolve().relative_to(cover_dir.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="非法的文件路径")

        # 确定 MIME 类型
        ext = cover_path.suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.gif': 'image/gif',
        }
        content_type = mime_types.get(ext, 'image/jpeg')

        # 返回文件，设置缓存头
        return FileResponse(
            path=cover_path,
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=604800, immutable",  # 7天缓存
                "X-Content-Type-Options": "nosniff",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取封面图片失败: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/{media_id}")
async def get_media_file_by_id(
        media_id: int,
        request: Request,
        range_header: Optional[str] = None,
        current_user_obj=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    try:
        logger.info(f"[DEBUG] 请求媒体文件 - ID: {media_id}, User: {current_user_obj.id}")

        # 查询媒体文件（支持访问自己的文件或公开文件）
        media_query = select(Media).where(Media.id == media_id)
        media_result = await db.execute(media_query)
        media = media_result.scalar_one_or_none()

        if not media:
            logger.error(f"[ERROR] 媒体文件不存在 - ID: {media_id}")
            raise HTTPException(status_code=404, detail="文件不存在")

        logger.info(
            f"[DEBUG] 找到媒体文件 - ID: {media.id}, Hash: {media.hash}, User: {media.user}, IsPublic: {media.is_public}")

        # 检查用户权限（只能访问自己的文件或公开文件）
        if media.user != current_user_obj.id and not media.is_public:
            logger.warning(f"[WARN] 无权访问 - Media User: {media.user}, Current User: {current_user_obj.id}")
            raise HTTPException(status_code=403, detail="无权访问该媒体文件")

        # 查询文件哈希信息
        file_hash_query = select(FileHash).where(FileHash.hash == media.hash)
        file_hash_result = await db.execute(file_hash_query)
        file_hash = file_hash_result.scalar_one_or_none()
        if not file_hash:
            raise HTTPException(status_code=404, detail="文件不存在")

        # 确定文件路径（用于生成 ETag）
        # 注意：文件可能带扩展名或不带扩展名，需要尝试两种情况
        file_path_without_ext = Path(f"storage/objects/{media.hash[:2]}/{media.hash}")
        file_path_with_ext = Path(f"storage/objects/{media.hash[:2]}/{media.hash}.png")  # 默认尝试 .png

        # 如果 storage_path 中有扩展名信息，使用它
        if file_hash.storage_path and '.' in Path(file_hash.storage_path).name:
            ext = Path(file_hash.storage_path).suffix
            file_path_with_ext = Path(f"storage/objects/{media.hash[:2]}/{media.hash}{ext}")

        # 优先使用带扩展名的路径，如果不存在则使用不带扩展名的路径
        if file_path_with_ext.exists():
            file_path = file_path_with_ext
        elif file_path_without_ext.exists():
            file_path = file_path_without_ext
        else:
            file_path = file_path_without_ext  # 默认使用不带扩展名的路径

        # 生成 ETag：直接使用文件修改时间
        try:
            file_stat = file_path.stat() if file_path.exists() else None
            if not file_stat and file_hash.storage_path.startswith("local://"):
                local_path = Path(file_hash.storage_path.replace("local://", "", 1))
                if local_path.exists():
                    file_stat = local_path.stat()

            if file_stat:
                etag = f'"{int(file_stat.st_mtime)}"'
            else:
                # 如果文件不存在，使用 hash 作为 ETag
                etag = f'"{media.hash}"'
        except Exception as e:
            logger.error(f"生成 ETag 失败: {e}")
            etag = f'"{media.hash}"'

        # 检查客户端是否有缓存（If-None-Match）
        if_none_match = request.headers.get("if-none-match")

        # 调试日志
        # logger.info(f"媒体文件请求 - ID: {media_id}")
        # logger.info(f"  Media Hash: {media.hash}")
        # logger.info(f"  FileHash Storage Path: {file_hash.storage_path}")
        # logger.info(f"  Expected file_path: {file_path}")
        # logger.info(f"  File exists at expected path: {file_path.exists()}")
        # logger.info(f"  ETag: {etag}")
        # logger.info(f"  If-None-Match (from client): {if_none_match}")
        # logger.info(f"  Match result: {if_none_match == etag if if_none_match else 'N/A'}")

        if if_none_match and if_none_match == etag:
            # 文件未修改，返回 304 Not Modified
            logger.info(f"[OK] 命中 ETag 缓存，返回 304 - ID: {media_id}")
            return Response(status_code=304, headers={"ETag": etag})

        # 设置响应头
        encoded_filename = urllib.parse.quote(file_hash.filename.encode('utf-8'))
        headers = {
            "Accept-Ranges": "bytes",
            "Content-Type": file_hash.mime_type,
            "X-Content-Type-Options": "nosniff",
            "ETag": etag,
            # 设置缓存控制：公共缓存，最大缓存时间 7 天
            "Cache-Control": "public, max-age=604800, immutable"
        }
        if file_hash.mime_type in PREVIEWABLE_TYPES:
            headers["Content-Disposition"] = f'inline; filename*=UTF-8\'\'{encoded_filename}'
        else:
            headers["Content-Disposition"] = f'attachment; filename*=UTF-8\'\'{encoded_filename}'

        # 处理本地文件（优先检查标准路径，支持带扩展名和不带扩展名）
        if file_path.exists():
            logger.info(f"  [OK] 文件存在于标准路径: {file_path}")
            return await handle_local_file(file_path, file_hash.mime_type, file_hash.filename, range_header, headers)

        # 如果标准路径不存在，尝试从 storage_path 构建完整路径
        if file_hash.storage_path:
            # 处理相对路径格式：objects/xx/xxx.ext
            if not file_hash.storage_path.startswith(("s3://",)):
                relative_path = Path(file_hash.storage_path)  #
                full_path = Path("storage") / relative_path
                logger.info(f"  尝试从 storage_path 构建路径: {full_path}")
                if full_path.exists():
                    logger.info(f"  [OK] 文件存在于 storage_path 对应的路径: {full_path}")
                    return await handle_local_file(full_path, file_hash.mime_type, file_hash.filename, range_header,
                                                   headers)

        # 处理 S3 存储
        elif file_hash.storage_path and file_hash.storage_path.startswith("s3://"):
            logger.info(f"  [OK] 使用 S3 路径: {file_hash.storage_path}")
            return await handle_s3_streaming(
                s3_path=file_hash.storage_path,
                mime_type=file_hash.mime_type,
                filename=file_hash.filename,
                range_header=range_header,
                headers=headers,
                media_hash=media.hash
            )
        else:
            # 如果 storage_path 为空或无效，但文件也不存在于标准路径
            logger.error(f"  [ERROR] 不支持的存储类型: '{file_hash.storage_path}'")
            logger.error(f"  文件是否存在于标准路径: {file_path.exists()}")
            logger.error(
                f"  FileHash 完整信息: id={file_hash.id}, hash={file_hash.hash}, filename={file_hash.filename}")

            # 如果文件实际上存在于标准路径但没有被检测到（可能是权限问题）
            if file_path.exists():
                logger.warning(f"  [WARN] 文件存在但之前的检查失败，重试...")
                return await handle_local_file(file_path, file_hash.mime_type, file_hash.filename, range_header,
                                               headers)

            raise HTTPException(status_code=400,
                                detail=f"不支持的存储类型: '{file_hash.storage_path}'，文件也不存在于标准路径")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")
