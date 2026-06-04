"""
媒体缩略图路由 - 提供基于 media_id 的缩略图访问
"""

import urllib.parse
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.file_hash import FileHash
from shared.models.media import Media
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db
from src.utils.image.processing import generate_thumbnail as sync_generate_thumbnail
from .utils import PREVIEWABLE_TYPES, handle_local_file, handle_s3_streaming

router = APIRouter()
from src.unified_logger import default_logger as logger


@router.get("/{media_id}")
async def get_user_media_file(
        media_id: int,
        request: Request,
        range_header: Optional[str] = None,
        current_user_obj=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):
    """
    获取用户媒体文件（支持流式传输和范围请求）
    
    Args:
        media_id: 媒体文件ID
        request: FastAPI请求对象
        range_header: HTTP Range头，用于断点续传
        current_user_obj: 当前用户对象
        db: 数据库会话
        
    Returns:
        流式响应或FileResponse
    """
    try:
        user_id = current_user_obj.id

        # 查询媒体记录
        query = select(Media).where(Media.id == media_id)
        result = await db.execute(query)
        media = result.scalar_one_or_none()

        if not media:
            raise HTTPException(status_code=404, detail="媒体文件不存在")

        # 检查用户权限（只能访问自己的文件或公开文件）
        if media.user != user_id and not media.is_public:
            raise HTTPException(status_code=403, detail="无权访问该媒体文件")

        # 查询文件哈希信息
        file_hash_query = select(FileHash).where(FileHash.hash == media.hash)
        file_hash_result = await db.execute(file_hash_query)
        file_hash = file_hash_result.scalar_one_or_none()

        if not file_hash:
            raise HTTPException(status_code=404, detail="文件哈希信息不存在")

        # 确定文件路径
        file_path_without_ext = Path(f"storage/objects/{media.hash[:2]}/{media.hash}")
        file_path_with_ext = None

        # 如果 storage_path 中有扩展名信息，使用它
        if file_hash.storage_path and '.' in Path(file_hash.storage_path).name:
            ext = Path(file_hash.storage_path).suffix
            file_path_with_ext = Path(f"storage/objects/{media.hash[:2]}/{media.hash}{ext}")

        # 优先使用带扩展名的路径，如果不存在则使用不带扩展名的路径
        if file_path_with_ext and file_path_with_ext.exists():
            file_path = file_path_with_ext
        elif file_path_without_ext.exists():
            file_path = file_path_without_ext
        else:
            file_path = file_path_without_ext

        # 生成 ETag
        try:
            file_stat = file_path.stat() if file_path.exists() else None
            if not file_stat and file_hash.storage_path.startswith("local://"):
                local_path = Path(file_hash.storage_path.replace("local://", "", 1))
                if local_path.exists():
                    file_stat = local_path.stat()

            if file_stat:
                etag = f'"{int(file_stat.st_mtime)}"'
            else:
                etag = f'"{media.hash}"'
        except Exception as e:
            logger.error(f"生成 ETag 失败: {e}")
            etag = f'"{media.hash}"'

        # 检查客户端是否有缓存（If-None-Match）
        if_none_match = request.headers.get("if-none-match")
        if if_none_match and if_none_match == etag:
            logger.info(f"[OK] 命中 ETag 缓存，返回 304 - ID: {media_id}")
            return Response(status_code=304, headers={"ETag": etag})

        # 设置响应头
        encoded_filename = urllib.parse.quote(file_hash.filename.encode('utf-8'))
        headers = {
            "Accept-Ranges": "bytes",
            "Content-Type": file_hash.mime_type or 'application/octet-stream',
            "X-Content-Type-Options": "nosniff",
            "ETag": etag,
            "Cache-Control": "public, max-age=604800, immutable"
        }

        # 根据 MIME 类型设置 Content-Disposition
        if file_hash.mime_type in PREVIEWABLE_TYPES:
            headers["Content-Disposition"] = f'inline; filename*=UTF-8\'\'{encoded_filename}'
        else:
            headers["Content-Disposition"] = f'attachment; filename*=UTF-8\'\'{encoded_filename}'

        # 处理本地文件
        if file_path.exists():
            logger.info(f"[OK] 文件存在于本地路径: {file_path}")
            return await handle_local_file(
                file_path=file_path,
                mime_type=file_hash.mime_type or 'application/octet-stream',
                filename=file_hash.filename,
                range_header=range_header,
                headers=headers
            )

        # 如果标准路径不存在，尝试从 storage_path 构建完整路径
        if file_hash.storage_path and not file_hash.storage_path.startswith(("s3://",)):
            relative_path = Path(file_hash.storage_path)
            full_path = Path("storage") / relative_path
            logger.info(f"尝试从 storage_path 构建路径: {full_path}")
            if full_path.exists():
                logger.info(f"[OK] 文件存在于 storage_path 对应的路径: {full_path}")
                return await handle_local_file(
                    file_path=full_path,
                    mime_type=file_hash.mime_type or 'application/octet-stream',
                    filename=file_hash.filename,
                    range_header=range_header,
                    headers=headers
                )

        # 处理 S3 存储
        if file_hash.storage_path and file_hash.storage_path.startswith("s3://"):
            logger.info(f"[OK] 使用 S3 路径: {file_hash.storage_path}")
            return await handle_s3_streaming(
                s3_path=file_hash.storage_path,
                mime_type=file_hash.mime_type or 'application/octet-stream',
                filename=file_hash.filename,
                range_header=range_header,
                headers=headers,
                media_hash=media.hash
            )

        # 文件不存在
        logger.error(f"文件不存在 - media_id: {media_id}, hash: {media.hash}")
        raise HTTPException(status_code=404, detail="文件不存在")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取媒体文件时发生未预期错误 - media_id: {media_id}, error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取媒体文件失败: {str(e)}")



@router.get("/{media_id}/thumbnail")
async def get_media_thumbnail(
        media_id: int,
        request: Request,
        db: AsyncSession = Depends(get_async_db),
        current_user=Depends(jwt_required)
):
    """
    获取媒体文件的缩略图
    
    Args:
        media_id: 媒体文件ID
        
    Returns:
        缩略图文件或404
    """
    try:
        logger.info(f"收到缩略图请求 - media_id: {media_id}")

        # 查询媒体记录
        query = select(Media).where(Media.id == media_id)
        result = await db.execute(query)
        media = result.scalar_one_or_none()

        if not media:
            logger.warning(f"媒体文件不存在 - media_id: {media_id}")
            raise HTTPException(status_code=404, detail="媒体文件不存在")

        # 检查用户权限（只能访问自己的文件或公开文件）
        if media.user != current_user.id and not media.is_public:
            logger.warning(f"无权访问该媒体文件 - media_id: {media_id}, user: {current_user.id}")
            raise HTTPException(status_code=403, detail="无权访问该媒体文件")

        # 如果已有缩略图路径，直接返回
        if media.thumbnail_path:
            from src.utils.storage.s3_storage import s3_storage
            thumbnail_data = s3_storage.read_file(media.thumbnail_path)

            if thumbnail_data:
                logger.info(f"返回已存在的缩略图 - media_id: {media_id}")
                return Response(
                    content=thumbnail_data,
                    media_type='image/jpeg',
                    headers={
                        'Cache-Control': 'public, max-age=2592000',  # 缓存30天
                        'Content-Disposition': f'inline; filename="thumbnail_{media_id}.jpg"'
                    }
                )

        # 如果没有缩略图，尝试生成
        logger.info(f"缩略图不存在，开始生成 - media_id: {media_id}")

        # 查找原始文件
        original_dir = Path(f"storage/objects/{media.hash[:2]}")
        original_path = None

        # 尝试查找带扩展名或不带扩展名的文件
        path_without_ext = original_dir / media.hash
        if path_without_ext.exists():
            original_path = path_without_ext
        else:
            # 尝试查找带扩展名的文件
            if original_dir.exists():
                for file in original_dir.iterdir():
                    if file.name.startswith(media.hash + '.'):
                        original_path = file
                        break

        if not original_path or not original_path.exists():
            logger.error(f"原始文件不存在 - media_id: {media_id}, hash: {media.hash}")
            raise HTTPException(status_code=404, detail="原始文件不存在")

        # 生成缩略图
        thumb_dir = Path(f"storage/thumbnails/{media.hash[:2]}")
        thumb_dir.mkdir(parents=True, exist_ok=True)
        thumb_path = thumb_dir / f"{media.hash}.jpg"

        logger.info(f"开始生成缩略图 - media_id: {media_id}, path: {thumb_path}")

        try:
            # 同步生成缩略图（因为 generate_thumbnail 是同步函数）
            success = sync_generate_thumbnail(str(original_path), str(thumb_path), size=(200, 200))

            if success and thumb_path.exists():
                logger.info(f"缩略图生成成功 - media_id: {media_id}")

                # 更新数据库中的缩略图路径
                media.thumbnail_path = f"thumbnails/{media.hash[:2]}/{media.hash}.jpg"
                media.thumbnail_url = f"/api/v2/media/{media_id}/thumbnail"
                await db.commit()

                # 读取并返回缩略图
                with open(thumb_path, 'rb') as f:
                    thumbnail_data = f.read()

                return Response(
                    content=thumbnail_data,
                    media_type='image/jpeg',
                    headers={
                        'Cache-Control': 'public, max-age=2592000',
                        'Content-Disposition': f'inline; filename="thumbnail_{media_id}.jpg"'
                    }
                )
            else:
                logger.warning(f"缩略图生成失败 - media_id: {media_id}")
                raise HTTPException(status_code=404, detail="该文件类型不支持缩略图")
        except Exception as e:
            logger.error(f"生成缩略图时出错 - media_id: {media_id}, error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"生成缩略图失败: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取缩略图时发生未预期错误 - media_id: {media_id}, error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取缩略图失败: {str(e)}")
