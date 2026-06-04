"""
封面图片API路由
提供封面图片的生成和管理功能
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.file_hash import FileHash
from shared.models.media import Media
from shared.services.articles.cover_image_service import cover_image_service
from shared.utils.logger import get_logger
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

logger = get_logger(__name__)
router = APIRouter()


@router.post("/generate-cover/{media_id}")
async def generate_cover_url(
        media_id: int,
        current_user_obj=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    为媒体文件生成封面URL
    
    该接口会：
    1. 验证用户是否有权限访问该媒体文件
    2. 读取原始图片数据
    3. 优化图片（调整大小、压缩）
    4. 保存到公开缓存目录
    5. 返回公开访问的URL
    
    Args:
        media_id: 媒体ID
    
    Returns:
        封面图片的公开URL
    """
    try:
        # 查询媒体文件，验证权限
        media_query = select(Media).where(
            Media.id == media_id,
            Media.user == current_user_obj.id
        )
        media_result = await db.execute(media_query)
        media = media_result.scalar_one_or_none()

        if not media:
            raise HTTPException(status_code=404, detail="媒体文件不存在或无权限访问")

        # 查询文件哈希信息
        file_hash_query = select(FileHash).where(FileHash.hash == media.hash)
        file_hash_result = await db.execute(file_hash_query)
        file_hash = file_hash_result.scalar_one_or_none()

        if not file_hash:
            raise HTTPException(status_code=404, detail="文件信息不存在")

        # 检查是否为图片类型
        if not file_hash.mime_type or not file_hash.mime_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="只有图片文件可以生成封面")

        # 读取原始图片数据
        from pathlib import Path

        # 尝试从多个路径读取文件
        image_data = None
        possible_paths = [
            Path(f"storage/objects/{media.hash[:2]}/{media.hash}"),
            Path(f"storage/objects/{media.hash[:2]}/{media.hash}.png"),
        ]

        # 如果 storage_path 中有扩展名信息
        if file_hash.storage_path and '.' in Path(file_hash.storage_path).name:
            ext = Path(file_hash.storage_path).suffix
            possible_paths.append(Path(f"storage/objects/{media.hash[:2]}/{media.hash}{ext}"))

        # 尝试读取文件
        for file_path in possible_paths:
            if file_path.exists():
                with open(file_path, 'rb') as f:
                    image_data = f.read()
                break

        # 如果标准路径不存在，尝试从 storage_path 构建
        if not image_data and file_hash.storage_path:
            if not file_hash.storage_path.startswith(("s3://",)):
                relative_path = Path(file_hash.storage_path)
                full_path = Path("storage") / relative_path
                if full_path.exists():
                    with open(full_path, 'rb') as f:
                        image_data = f.read()

        if not image_data:
            raise HTTPException(status_code=404, detail="无法读取原始图片文件")

        # 优化并保存封面
        cover_url = cover_image_service.optimize_and_save_cover(
            media_id=media_id,
            image_data=image_data,
            file_hash=media.hash,
            mime_type=file_hash.mime_type,
            max_width=1920,
            max_height=1080,
            quality=85
        )

        if not cover_url:
            raise HTTPException(status_code=500, detail="生成封面失败")

        return ApiResponse(
            success=True,
            data={
                "cover_url": cover_url,
                "media_id": media_id,
                "message": "封面生成成功"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成封面URL失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


@router.delete("/remove-cover/{media_id}")
async def remove_cover(
        media_id: int,
        current_user_obj=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    删除封面图片
    
    Args:
        media_id: 媒体ID
    
    Returns:
        删除结果
    """
    try:
        # 查询媒体文件，验证权限
        media_query = select(Media).where(
            Media.id == media_id,
            Media.user == current_user_obj.id
        )
        media_result = await db.execute(media_query)
        media = media_result.scalar_one_or_none()

        if not media:
            raise HTTPException(status_code=404, detail="媒体文件不存在或无权限访问")

        # 删除封面
        success = cover_image_service.delete_cover(media_id, media.hash)

        return ApiResponse(
            success=success,
            data={"message": "封面已删除" if success else "封面不存在"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除封面失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")
