"""
设置媒体上传 API
为管理后台设置页面提供专用的媒体上传接口，支持图片和视频类型
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db
from src.unified_logger import default_logger as logger
from src.utils.upload.public_upload import FileProcessor, process_single_file

router = APIRouter(tags=["media-settings"])

# 允许的 MIME 类型：图片 + 视频
ALLOWED_MIMES = {
    # 图片格式
    'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp',
    'image/svg+xml', 'image/tiff',
    # 视频格式
    'video/mp4', 'video/mpeg', 'video/quicktime', 'video/x-msvideo',
    'video/webm', 'video/x-matroska',
}

# 最大文件大小：50MB（视频文件通常较大）
MAX_FILE_SIZE = 50 * 1024 * 1024


@router.post('/settings/upload')
async def upload_settings_media(
    request: Request,
    current_user_obj=Depends(jwt_required),
    db: AsyncSession = Depends(get_async_db)
):
    """
    设置页面专用媒体上传接口

    支持图片和视频类型文件上传，用于管理后台设置页面的媒体资源管理。

    支持的图片格式：JPEG, PNG, GIF, BMP, WebP, SVG, TIFF
    支持的视频格式：MP4, MPEG, QuickTime, AVI, WebM, MKV

    最大文件大小：50MB

    Returns:
        上传成功返回文件 URL 和媒体信息
    """
    try:
        form = await request.form()
        file = form.get('file')

        if not file or not hasattr(file, 'filename') or not file.filename:
            return JSONResponse(
                {'success': False, 'message': '未上传文件或文件名为空'},
                status_code=400
            )

        file_data = await file.read()

        # 使用 FileProcessor 处理文件
        processor = FileProcessor(
            current_user_obj.id,
            allowed_mimes=ALLOWED_MIMES,
            allowed_size=MAX_FILE_SIZE
        )

        # 验证文件
        is_valid, validation_result = processor.validate_file(file_data, file.filename)
        if not is_valid:
            return JSONResponse(
                {'success': False, 'message': validation_result},
                status_code=400
            )

        # 处理文件并创建数据库记录
        try:
            result = await process_single_file(processor, file_data, file.filename, db)
        except Exception as e:
            await db.rollback()
            logger.error(f"设置媒体文件处理失败: {file.filename} - {str(e)}", exc_info=True)
            return JSONResponse(
                {'success': False, 'message': '文件处理失败', 'error': str(e)},
                status_code=500
            )

        if not result.get('success'):
            await db.rollback()
            return JSONResponse(
                {'success': False, 'message': '文件处理失败',
                 'error': result.get('error', '未知错误')},
                status_code=500
            )

        # 构建响应
        storage_path = result.get('storage_path', '')
        if storage_path:
            url = f"/api/v2/assets/storage/{storage_path}"
        else:
            url = f"/api/v2/media/{result.get('media_id', '')}"

        return JSONResponse({
            'success': True,
            'message': '上传成功',
            'data': {
                'url': url,
                'media_id': result.get('media_id'),
                'filename': file.filename,
                'mime_type': result.get('mime_type', ''),
                'size': len(file_data),
            }
        })

    except Exception as e:
        logger.error(f"设置媒体上传错误: {str(e)}", exc_info=True)
        return JSONResponse(
            {'success': False, 'message': '上传失败', 'error': str(e)},
            status_code=500
        )
