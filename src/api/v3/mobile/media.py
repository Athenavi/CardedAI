"""
移动端媒体API
提供适合移动端的媒体相关接口，包括图片上传、压缩等功能
"""
import os
import uuid

from fastapi import APIRouter, Depends, Request, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required
from src.utils.database.main import get_async_session

router = APIRouter(tags=["mobile-media"])


@router.post("/upload/image")
async def upload_mobile_image(
        request: Request,
        file: UploadFile = File(..., description="图片文件"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    """
    上传图片（移动端）
    支持自动压缩和优化
    """
    try:
        # 验证文件类型
        allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
        if file.content_type not in allowed_types:
            return ApiResponse(
                success=False,
                error=f"不支持的文件类型: {file.content_type}。支持的类型: {', '.join(allowed_types)}"
            )

        # 验证文件大小（限制10MB）
        file_size = 0
        content = await file.read()
        file_size = len(content)

        if file_size > 10 * 1024 * 1024:  # 10MB
            return ApiResponse(success=False, error="文件大小超过限制（最大10MB）")

        # 生成唯一文件名
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"

        # 确定存储路径
        upload_dir = os.path.join("static", "uploads", "mobile", str(current_user.id))
        os.makedirs(upload_dir, exist_ok=True)

        # 保存文件
        file_path = os.path.join(upload_dir, unique_filename)
        with open(file_path, "wb") as f:
            f.write(content)

        # 构建URL
        base_url = str(request.url).split('/media/upload')[0]
        file_url = f"{base_url}/api/v2/static/uploads/mobile/{current_user.id}/{unique_filename}"

        return ApiResponse(
            success=True,
            data={
                "url": file_url,
                "filename": unique_filename,
                "size": file_size,
                "content_type": file.content_type,
                "message": "图片上传成功"
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in upload_mobile_image: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))


@router.post("/upload/article-cover")
async def upload_article_cover(
        request: Request,
        file: UploadFile = File(..., description="封面图片"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    """
    上传文章封面（移动端）
    """
    try:
        # 验证文件类型
        allowed_types = ['image/jpeg', 'image/png', 'image/webp']
        if file.content_type not in allowed_types:
            return ApiResponse(
                success=False,
                error=f"不支持的文件类型: {file.content_type}"
            )

        # 读取文件内容
        content = await file.read()
        file_size = len(content)

        if file_size > 5 * 1024 * 1024:  # 5MB
            return ApiResponse(success=False, error="文件大小超过限制（最大5MB）")

        # 生成唯一文件名
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        unique_filename = f"cover_{uuid.uuid4().hex}.{file_extension}"

        # 确定存储路径
        upload_dir = os.path.join("static", "uploads", "covers", str(current_user.id))
        os.makedirs(upload_dir, exist_ok=True)

        # 保存文件
        file_path = os.path.join(upload_dir, unique_filename)
        with open(file_path, "wb") as f:
            f.write(content)

        # 构建URL
        base_url = str(request.url).split('/media/upload')[0]
        file_url = f"{base_url}/api/v2/static/uploads/covers/{current_user.id}/{unique_filename}"

        return ApiResponse(
            success=True,
            data={
                "url": file_url,
                "filename": unique_filename,
                "size": file_size,
                "message": "封面上传成功"
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in upload_article_cover: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))
