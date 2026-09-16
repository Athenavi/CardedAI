"""
图片编辑工具 API（不操作数据库，直接处理上传文件）
"""

from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, UploadFile, File, Body, HTTPException
from fastapi.responses import Response

from shared.services.media.image_tool import image_processor
from src.auth import jwt_required_dependency as jwt_required

router = APIRouter(tags=["media-edit-tools"])
from src.unified_logger import default_logger as logger


@router.post("/process")
async def process_image(
        file: UploadFile = File(...),
        operations: Dict[str, Any] = Body(...),
        current_user=Depends(jwt_required)
):
    """处理图片（支持多个操作）"""
    try:
        content = await file.read()
        validation = image_processor.validate_image(content)
        if not validation['valid']:
            raise HTTPException(status_code=400, detail=f"无效的图片: {'; '.join(validation['errors'])}")
        processed_data, mime_type = image_processor.process_image(content, operations)
        return Response(
            content=processed_data,
            media_type=mime_type,
            headers={'Content-Disposition': f'attachment; filename="processed_{file.filename}"'}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"图片处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"图片处理失败: {str(e)}")


@router.post("/info")
async def get_image_info(
        file: UploadFile = File(...),
        current_user=Depends(jwt_required)
):
    """获取图片信息"""
    try:
        content = await file.read()
        validation = image_processor.validate_image(content)
        if not validation['valid']:
            raise HTTPException(status_code=400, detail=f"无效的图片: {'; '.join(validation['errors'])}")
        info = image_processor.get_image_info(content)
        return {'success': True, 'data': info}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取图片信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取图片信息失败: {str(e)}")


@router.post("/validate")
async def validate_image(
        file: UploadFile = File(...),
        max_size_mb: float = Body(10, embed=True),
        current_user=Depends(jwt_required)
):
    """验证图片"""
    try:
        content = await file.read()
        result = image_processor.validate_image(content, max_size_mb)
        return {'success': True, 'data': result}
    except Exception as e:
        logger.error(f"图片验证失败: {e}")
        raise HTTPException(status_code=500, detail=f"图片验证失败: {str(e)}")


# 便捷端点（内部调用 process）
@router.post("/crop")
async def crop_image(
        file: UploadFile = File(...),
        x: int = Body(...),
        y: int = Body(...),
        width: int = Body(...),
        height: int = Body(...),
        quality: int = Body(85),
        output_format: str = Body('JPEG'),
        current_user=Depends(jwt_required)
):
    content = await file.read()
    operations = {
        'crop': {'x': x, 'y': y, 'width': width, 'height': height},
        'quality': quality,
        'format': output_format
    }
    processed_data, mime_type = image_processor.process_image(content, operations)
    return Response(content=processed_data, media_type=mime_type,
                    headers={'Content-Disposition': f'attachment; filename="cropped_{file.filename}"'})


@router.post("/rotate")
async def rotate_image(
        file: UploadFile = File(...),
        angle: float = Body(...),
        quality: int = Body(85),
        output_format: str = Body('JPEG'),
        current_user=Depends(jwt_required)
):
    content = await file.read()
    operations = {'rotate': angle, 'quality': quality, 'format': output_format}
    processed_data, mime_type = image_processor.process_image(content, operations)
    return Response(content=processed_data, media_type=mime_type,
                    headers={'Content-Disposition': f'attachment; filename="rotated_{file.filename}"'})


@router.post("/resize")
async def resize_image(
        file: UploadFile = File(...),
        width: Optional[int] = Body(None),
        height: Optional[int] = Body(None),
        maintain_aspect: bool = Body(True),
        quality: int = Body(85),
        output_format: str = Body('JPEG'),
        current_user=Depends(jwt_required)
):
    content = await file.read()
    operations = {
        'resize': {'width': width, 'height': height, 'maintain_aspect': maintain_aspect},
        'quality': quality,
        'format': output_format
    }
    processed_data, mime_type = image_processor.process_image(content, operations)
    return Response(content=processed_data, media_type=mime_type,
                    headers={'Content-Disposition': f'attachment; filename="resized_{file.filename}"'})


@router.post("/thumbnail")
async def create_thumbnail(
        file: UploadFile = File(...),
        size: int = Body(200),
        quality: int = Body(85),
        output_format: str = Body('JPEG'),
        current_user=Depends(jwt_required)
):
    content = await file.read()
    operations = {'thumbnail': size, 'quality': quality, 'format': output_format}
    processed_data, mime_type = image_processor.process_image(content, operations)
    return Response(content=processed_data, media_type=mime_type,
                    headers={'Content-Disposition': f'attachment; filename="thumb_{file.filename}"'})
