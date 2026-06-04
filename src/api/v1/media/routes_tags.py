"""
单个媒体的标签、缩略图、EXIF操作
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.media import Media
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter()


@router.get("/{media_id}/exif")
async def get_exif_data(media_id: int, current_user=Depends(jwt_required)):
    return ApiResponse(success=True, data={"exif": {}})


@router.post("/{media_id}/remove-exif")
async def remove_exif(
        media_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user=Depends(jwt_required)
):
    """移除图片的EXIF元数据"""
    try:
        from PIL import Image
        from pathlib import Path
        import io

        # 查询媒体文件
        query = select(Media).where(Media.id == media_id)
        result = await db.execute(query)
        media = result.scalar_one_or_none()

        if not media:
            return ApiResponse(success=False, error="媒体文件不存在")

        # 只处理图片
        if not media.mime_type or not media.mime_type.startswith('image/'):
            return ApiResponse(success=False, error="只能处理图片文件")

        # 获取文件路径
        file_path = Path(media.file_path)
        if not file_path.exists():
            return ApiResponse(success=False, error="文件不存在")

        # 打开图片
        img = Image.open(file_path)

        # 提取图片数据(不包含EXIF)
        data = list(img.getdata())
        image_without_exif = Image.new(img.mode, img.size)
        image_without_exif.putdata(data)

        # 保存不含EXIF的图片
        output = io.BytesIO()

        if media.mime_type == 'image/jpeg':
            image_without_exif.save(output, format='JPEG', quality=95)
        elif media.mime_type == 'image/png':
            image_without_exif.save(output, format='PNG')
        else:
            image_without_exif.save(output, format=img.format)

        # 写回文件
        with open(file_path, 'wb') as f:
            f.write(output.getvalue())

        logger = __import__('logging').getLogger(__name__)
        logger.info(f"EXIF已移除: {media.original_filename}")

        return ApiResponse(
            success=True,
            message="EXIF元数据已移除",
            data={'filename': media.original_filename}
        )

    except Exception as e:
        logger = __import__('logging').getLogger(__name__)
        logger.error(f"移除EXIF失败: {e}")
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=f"移除EXIF失败: {str(e)}")


@router.post("/{media_id}/tags")
async def update_media_tags(
        media_id: int,
        request: Request,
        db: AsyncSession = Depends(get_async_db),
        current_user=Depends(jwt_required)
):
    """
    更新媒体的标签
    支持 mode 参数：
    - add: 追加标签（默认）
    - replace: 替换全部标签
    
    注意：每个媒体最多支持5个标签
    """
    body = await request.json()
    tags = body.get('tags', [])
    mode = body.get('mode', 'add')  # 'add' 或 'replace'

    query = select(Media).where(Media.id == media_id)
    result = await db.execute(query)
    media = result.scalar_one_or_none()
    if not media:
        return ApiResponse(success=False, error="媒体文件不存在")

    if mode == 'replace':
        # 完全替换 - 检查标签数量限制
        if len(tags) > 5:
            return ApiResponse(success=False, error="最多只能设置5个标签")
        media.tags = ','.join(tags) if tags else None
    else:
        # 追加（默认行为）- 检查标签数量限制
        existing_tags = set()
        if media.tags:
            existing_tags = set(t.strip() for t in media.tags.split(',') if t.strip())
        existing_tags.update(tags)

        if len(existing_tags) > 5:
            return ApiResponse(success=False,
                               error=f"最多只能设置5个标签，当前已有{len(existing_tags) - len(tags)}个，尝试添加{len(tags)}个")

        media.tags = ','.join(existing_tags) if existing_tags else None

    await db.commit()
    return ApiResponse(success=True,
                       data={"message": "标签更新成功", "tags": media.tags.split(',') if media.tags else []})


@router.delete("/{media_id}/tags")
async def remove_tags(
        media_id: int,
        request: Request,
        db: AsyncSession = Depends(get_async_db),
        current_user=Depends(jwt_required)
):
    body = await request.json()
    tags_to_remove = body.get('tags', [])
    query = select(Media).where(Media.id == media_id)
    result = await db.execute(query)
    media = result.scalar_one_or_none()
    if not media:
        return ApiResponse(success=False, error="媒体文件不存在")
    if media.tags:
        existing_tags = [t.strip() for t in media.tags.split(',')]
        new_tags = [t for t in existing_tags if t not in tags_to_remove]
        media.tags = ','.join(new_tags) if new_tags else None
        await db.commit()
    return ApiResponse(success=True, data={"message": "标签移除成功"})
