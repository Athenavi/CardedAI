"""
媒体增强 API（单个优化、WebP转换等，无冲突端点）
"""

from pathlib import Path

from fastapi import APIRouter, Depends, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.file_hash import FileHash
from shared.models.media import Media
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["media-enhancement"])
from src.unified_logger import default_logger as logger


@router.post("/optimize/{file_id}")
async def optimize_media_file(
        file_id: int,
        quality: int = Form(85),
        max_width: int = Form(1920),
        max_height: int = Form(1080),
        db: AsyncSession = Depends(get_async_db),
        current_user=Depends(jwt_required)
):
    """优化指定媒体文件"""
    query = (
        select(Media)
        .join(FileHash, Media.hash == FileHash.hash)
        .where(Media.id == file_id, Media.user == current_user.id)
    )
    result = await db.execute(query)
    media = result.scalar_one_or_none()
    if not media:
        return ApiResponse(success=False, error="文件不存在或无权访问")
    
    try:
        from PIL import Image
        import io
        
        # 获取文件路径
        file_path = Path(media.file_path)
        if not file_path.exists():
            return ApiResponse(success=False, error="文件不存在")
        
        # 只处理图片
        if not media.mime_type or not media.mime_type.startswith('image/'):
            return ApiResponse(success=False, error="只能优化图片文件")
        
        # 打开图片
        img = Image.open(file_path)
        
        # 调整大小
        original_size = img.size
        if img.width > max_width or img.height > max_height:
            img.thumbnail((max_width, max_height), Image.LANCZOS)
        
        # 保存优化后的图片
        output = io.BytesIO()
        save_kwargs = {'quality': quality, 'optimize': True}
        
        if media.mime_type == 'image/jpeg':
            img.save(output, format='JPEG', **save_kwargs)
        elif media.mime_type == 'image/png':
            img.save(output, format='PNG', optimize=True)
        else:
            img.save(output, format=img.format, **save_kwargs)
        
        # 写回文件
        with open(file_path, 'wb') as f:
            f.write(output.getvalue())
        
        # 更新文件大小
        new_size = file_path.stat().st_size
        file_hash_obj = await db.execute(
            select(FileHash).where(FileHash.hash == media.hash)
        )
        file_hash = file_hash_obj.scalar_one_or_none()
        if file_hash:
            file_hash.file_size = new_size
            await db.commit()
        
        logger.info(f"图片优化完成: {media.original_filename}, 原始: {original_size}, 新大小: {new_size} bytes")
        
        return ApiResponse(
            success=True, 
            message=f"图片优化成功，大小: {_format_file_size(new_size)}",
            data={'original_size': original_size, 'new_size': new_size}
        )
        
    except Exception as e:
        logger.error(f"图片优化失败: {e}")
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=f"优化失败: {str(e)}")


@router.post("/convert-webp/{file_id}")
async def convert_to_webp_endpoint(
        file_id: int,
        quality: int = Form(80),
        keep_original: bool = Form(True),
        db: AsyncSession = Depends(get_async_db),
        current_user=Depends(jwt_required)
):
    """将图片转换为WebP格式"""
    query = (
        select(Media)
        .join(FileHash, Media.hash == FileHash.hash)
        .where(Media.id == file_id, Media.user == current_user.id)
    )
    result = await db.execute(query)
    media = result.scalar_one_or_none()
    if not media:
        return ApiResponse(success=False, error="文件不存在或无权访问")
    if not media.mime_type or not media.mime_type.startswith('image/'):
        return ApiResponse(success=False, error="只能转换图片文件")
    
    try:
        from PIL import Image
        import io
        
        # 获取文件路径
        original_path = Path(media.file_path)
        if not original_path.exists():
            return ApiResponse(success=False, error="文件不存在")
        
        # 打开图片
        img = Image.open(original_path)
        
        # 生成WebP文件路径
        webp_path = original_path.with_suffix('.webp')
        
        # 转换为WebP
        output = io.BytesIO()
        img.save(output, format='WEBP', quality=quality, method=6)
        
        # 保存WebP文件
        with open(webp_path, 'wb') as f:
            f.write(output.getvalue())
        
        webp_size = webp_path.stat().st_size
        original_size = original_path.stat().st_size
        
        logger.info(f"WebP转换完成: {media.original_filename}, 原始: {_format_file_size(original_size)}, WebP: {_format_file_size(webp_size)}")
        
        # 如果不保留原图，删除原图并更新数据库
        if not keep_original:
            original_path.unlink()
            media.file_path = str(webp_path)
            media.mime_type = 'image/webp'
            
            # 更新文件大小
            file_hash_obj = await db.execute(
                select(FileHash).where(FileHash.hash == media.hash)
            )
            file_hash = file_hash_obj.scalar_one_or_none()
            if file_hash:
                file_hash.file_size = webp_size
                file_hash.mime_type = 'image/webp'
                await db.commit()
        
        return ApiResponse(
            success=True,
            message=f"WebP转换成功，大小: {_format_file_size(webp_size)}",
            data={
                'original_size': original_size,
                'webp_size': webp_size,
                'webp_path': str(webp_path),
                'compression_ratio': f"{(1 - webp_size/original_size)*100:.1f}%"
            }
        )
        
    except Exception as e:
        logger.error(f"WebP转换失败: {e}")
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=f"转换失败: {str(e)}")


@router.get("/stats/{file_id}")
async def get_media_stats(
        file_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user=Depends(jwt_required)
):
    """获取媒体文件统计信息"""
    query = (
        select(Media, FileHash)
        .join(FileHash, Media.hash == FileHash.hash)
        .where(Media.id == file_id, Media.user == current_user.id)
    )
    result = await db.execute(query)
    row = result.first()
    if not row:
        return ApiResponse(success=False, error="文件不存在或无权访问")
    media, fh = row
    stats = {
        'id': media.id,
        'filename': media.original_filename,
        'mime_type': fh.mime_type,
        'file_size': fh.file_size,
        'file_size_human': _format_file_size(fh.file_size),
        'created_at': media.created_at.isoformat() if media.created_at else None,
    }
    if fh.mime_type and fh.mime_type.startswith('image/'):
        stats['is_image'] = True
    return ApiResponse(success=True, data=stats)


def _format_file_size(size_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"
