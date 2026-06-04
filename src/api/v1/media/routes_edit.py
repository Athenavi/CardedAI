"""
媒体编辑：删除、更新、批量优化等
"""

import os
from threading import Thread

from fastapi import APIRouter, Depends, Body, Request, Query, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.file_hash import FileHash
from shared.models.media import Media
from shared.services.media.image_tool import image_editor, image_processor
from shared.services.media.media_manager import media_library_service
from src.api.v1.core.responses import ApiResponse
from src.api.v1.utils.storage_utils import async_file_cleanup
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter()
from src.unified_logger import default_logger as logger


# ---------- 批量删除（查询参数） ----------
@router.delete("/")
async def delete_user_media_api(
        current_user_obj=Depends(jwt_required),
        file_id_list: str = Query(..., alias="file-id-list"),
        db: AsyncSession = Depends(get_async_db)
):
    try:
        if not file_id_list:
            return JSONResponse({'success': False, 'message': '缺少文件ID列表'}, status_code=400)
        try:
            id_list = [int(mid) for mid in file_id_list.split(',')]
        except ValueError:
            return JSONResponse({'success': False, 'message': '文件ID包含非法字符'}, status_code=400)

        target_query = select(Media).where(Media.id.in_(id_list), Media.user == current_user_obj.id)
        target_result = await db.execute(target_query)
        target_files = target_result.scalars().all()
        if len(target_files) != len(id_list):
            return JSONResponse({'success': False, 'message': '部分文件不存在或无权访问'}, status_code=403)

        cleanup_data = []
        media_hashes = [mf.hash for mf in target_files if mf.hash]
        if not media_hashes:
            return JSONResponse({'success': False, 'message': '没有有效的媒体记录'}, status_code=400)

        fh_query = select(FileHash).where(FileHash.hash.in_(media_hashes))
        fh_result = await db.execute(fh_query)
        file_hashes = fh_result.scalars().all()
        fh_map = {fh.hash: fh for fh in file_hashes}

        for media in target_files:
            if not media.hash:
                continue
            await db.delete(media)
            fh = fh_map.get(media.hash)
            if fh:
                fh.reference_count -= 1
                if fh.reference_count == 0:
                    cleanup_data.append({'hash': fh.hash, 'storage_path': fh.storage_path})
                    await db.delete(fh)

        await db.commit()
        if cleanup_data:
            Thread(target=async_file_cleanup, args=(db, cleanup_data)).start()
        return JSONResponse({'success': True, 'data': {'deleted_count': len(target_files)}, 'message': "删除成功"})
    except Exception as e:
        await db.rollback()
        return JSONResponse({'success': False, 'message': '数据库操作失败'}, status_code=500)


# ---------- 批量删除（JSON） ----------
@router.post("/batch-delete")
async def batch_delete_media(
        media_ids: list = Body(...),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    try:
        result = await media_library_service.batch_delete_media(db, media_ids)
        if result["success"]:
            return ApiResponse(success=True, message=f"成功删除 {result['deleted_count']} 个文件", data=result)
        return ApiResponse(success=False, error=result.get("error"))
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# ---------- 批量分类 ----------
@router.post("/batch-categorize")
async def batch_categorize_media(
        media_ids: list = Body(...),
        category: str = Body(...),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """批量为媒体设置分类"""
    try:
        from sqlalchemy import update as sql_update

        # 批量更新分类
        stmt = (
            sql_update(Media)
            .where(Media.id.in_(media_ids))
            .values(category=category)
        )
        result = await db.execute(stmt)
        await db.commit()

        return ApiResponse(
            success=True,
            message=f"成功为 {result.rowcount} 个文件设置分类",
            data={"updated_count": result.rowcount}
        )
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


# ---------- 批量标签 ----------
@router.post("/batch-tags")
async def batch_update_tags(
        media_ids: list = Body(...),
        tags: list = Body(...),
        mode: str = Body('add'),  # 'add' 或 'replace'
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """批量为媒体设置标签

    注意：每个媒体最多支持5个标签
    """
    try:
        from sqlalchemy import select

        # 检查标签数量限制
        if len(tags) > 5:
            return ApiResponse(success=False, error="最多只能设置5个标签")

        # 查询所有媒体
        query = select(Media).where(Media.id.in_(media_ids))
        result = await db.execute(query)
        media_list = result.scalars().all()

        updated_count = 0
        for media in media_list:
            if mode == 'replace':
                # 完全替换
                media.tags = ','.join(tags) if tags else None
            else:
                # 追加标签 - 检查总数不超过5个
                existing_tags = set()
                if media.tags:
                    existing_tags = set(t.strip() for t in media.tags.split(',') if t.strip())
                existing_tags.update(tags)

                if len(existing_tags) > 5:
                    continue  # 跳过超过限制的媒体

                media.tags = ','.join(existing_tags) if existing_tags else None
            updated_count += 1

        await db.commit()

        return ApiResponse(
            success=True,
            message=f"成功为 {updated_count} 个文件更新标签",
            data={"updated_count": updated_count}
        )
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


# ---------- 详情更新 ----------
@router.get("/detail/{media_id}")
async def get_media_detail(
        media_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user=Depends(jwt_required)
):
    query = select(Media).where(Media.id == media_id)
    result = await db.execute(query)
    media = result.scalar_one_or_none()
    if not media:
        return ApiResponse(success=False, error="媒体文件不存在")
    return ApiResponse(success=True, data=media.to_dict())


@router.put("/detail/{media_id}")
async def update_media(
        media_id: int,
        request: Request,
        db: AsyncSession = Depends(get_async_db),
        current_user=Depends(jwt_required)
):
    query = select(Media).where(Media.id == media_id)
    result = await db.execute(query)
    media = result.scalar_one_or_none()
    if not media:
        return ApiResponse(success=False, error="媒体文件不存在")
    body = await request.json()
    if 'description' in body:
        media.description = body['description']
    if 'alt_text' in body:
        media.alt_text = body['alt_text']
    if 'tags' in body:
        # 处理 tags 字段 - 支持字符串和数组两种格式
        tags_value = body['tags']

        # 如果是字符串，解析为数组进行检查
        if isinstance(tags_value, str):
            tags_list = [t.strip() for t in tags_value.split(',') if t.strip()] if tags_value else []
        elif isinstance(tags_value, list):
            tags_list = tags_value
        else:
            tags_list = []

        # 检查标签数量限制（最多5个）
        if len(tags_list) > 5:
            return ApiResponse(success=False, error="最多只能设置5个标签")

        # 保存为逗号分隔的字符串
        media.tags = ','.join(tags_list) if tags_list else None
    if 'category' in body:
        media.category = body['category']
    await db.commit()
    await db.refresh(media)
    return ApiResponse(success=True, data={"message": "更新成功", "media": media.to_dict()})


@router.delete("/detail/{media_id}")
async def delete_media(
        media_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user=Depends(jwt_required)
):
    query = select(Media).where(Media.id == media_id)
    result = await db.execute(query)
    media = result.scalar_one_or_none()
    if not media:
        return ApiResponse(success=False, error="媒体文件不存在")
    try:
        if media.file_path and os.path.exists(media.file_path):
            os.remove(media.file_path)
        if media.thumbnail_path and os.path.exists(media.thumbnail_path):
            os.remove(media.thumbnail_path)
    except Exception as e:
        logger.warning(f"删除物理文件失败: {e}")
    await db.delete(media)
    await db.commit()
    return ApiResponse(success=True, data={"message": "删除成功"})


# ---------- 批量优化 ----------
@router.post("/batch/optimize")
async def batch_optimize_images(
        media_ids: list = Body(...),
        quality: int = Body(75),
        convert_to_webp: bool = Body(True),
        max_width: int = Body(1920),
        max_height: int = Body(1080),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    try:
        from src.utils.storage.s3_storage import s3_storage

        stmt = select(Media).where(Media.id.in_(media_ids))
        result = await db.execute(stmt)
        media_files = result.scalars().all()
        if not media_files:
            return JSONResponse(content={"success": False, "error": "未找到指定的媒体文件"}, status_code=404)

        optimized_count = 0
        results = []
        for media in media_files:
            try:
                if not media.mime_type.startswith('image/'):
                    results.append({'id': media.id, 'filename': media.filename, 'status': 'skipped'})
                    continue
                file_data = s3_storage.read_file(media.file_path)
                if not file_data:
                    results.append({'id': media.id, 'filename': media.filename, 'status': 'failed'})
                    continue
                original_size = len(file_data)
                ops = {'quality': quality, 'max_width': max_width, 'max_height': max_height}
                if convert_to_webp:
                    ops['format'] = 'WEBP'
                optimized_data, info = image_processor.process_image(file_data, ops)
                optimized_size = len(optimized_data)
                if optimized_size < original_size:
                    new_filename = f"{media.filename.rsplit('.', 1)[0]}.webp" if convert_to_webp else media.filename
                    new_path = f"optimized/{new_filename}"
                    s3_storage.save_raw_file(new_path, optimized_data)
                    media.optimized_path = new_path
                    media.file_size = optimized_size
                    optimized_count += 1
                    results.append({'id': media.id, 'status': 'success',
                                    'compression': round((1 - optimized_size / original_size) * 100, 2)})
                else:
                    results.append({'id': media.id, 'status': 'skipped'})
            except Exception as e:
                results.append({'id': media.id, 'status': 'failed', 'error': str(e)})
        await db.commit()
        return JSONResponse(content={"success": True, "data": {"total": len(media_files), "optimized": optimized_count,
                                                               "results": results}})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


# ---------- 批量更新元数据 ----------
@router.post("/batch-update")
async def batch_update_metadata(
        updates: list = Body(...),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    try:
        result = await media_library_service.batch_update_metadata(db, updates)
        if result["success"]:
            return ApiResponse(success=True, message=f"成功更新 {result['updated_count']} 个文件", data=result)
        return ApiResponse(success=False, error=result.get("error"))
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# ---------- 存储统计 ----------
@router.get("/storage/stats")
async def get_storage_stats(
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    import humanize
    from sqlalchemy import func
    from .dependencies import get_user_storage_limit, get_user_storage_used
    try:
        total_count_stmt = select(func.count(Media.id))
        total_count_result = await db.execute(total_count_stmt)
        total_count = total_count_result.scalar() or 0
        total_size_stmt = select(func.sum(Media.file_size))
        total_size_result = await db.execute(total_size_stmt)
        total_size = total_size_result.scalar() or 0
        type_stats_stmt = select(
            Media.file_type, func.count(Media.id).label('count'), func.sum(Media.file_size).label('total_size')
        ).group_by(Media.file_type)
        type_stats_result = await db.execute(type_stats_stmt)
        type_stats = [{'type': row[0], 'count': row[1], 'total_size': row[2] or 0} for row in type_stats_result.all()]
        storage_limit = await get_user_storage_limit(current_user.id, db)
        storage_used = await get_user_storage_used(current_user.id, db)
        usage_percentage = (storage_used / storage_limit * 100) if storage_limit > 0 else 0
        return JSONResponse(content={
            "success": True,
            "data": {
                "total_count": total_count,
                "total_size": total_size,
                "total_size_formatted": humanize.naturalsize(total_size),
                "type_stats": type_stats,
                "user_storage": {
                    "used": storage_used,
                    "limit": storage_limit,
                    "used_formatted": humanize.naturalsize(storage_used),
                    "limit_formatted": humanize.naturalsize(storage_limit),
                    "usage_percentage": round(usage_percentage, 2)
                }
            }
        })
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


# ---------- 图片编辑 ----------
@router.post("/edit")
async def edit_image(
        request: Request,
        current_user=Depends(jwt_required)
):
    body = await request.json()
    image_path = body.get('image_path')
    operations = body.get('operations', [])
    if not image_path:
        return ApiResponse(success=False, error="请指定图片路径")
    success, message, data = image_editor.process_image(image_path, operations)
    if not success:
        return ApiResponse(success=False, error=message)
    return ApiResponse(success=True, data={"message": message})


# ---------- 上传图片编辑结果 ----------
@router.post("/{media_id}/edit")
async def upload_edited_image(
        media_id: int,
        file: UploadFile = File(...),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    上传编辑后的图片并更新媒体记录

    Args:
        media_id: 媒体文件ID
        file: 编辑后的图片文件
    """
    try:
        from src.utils.storage.s3_storage import s3_storage
        import hashlib
        from datetime import datetime

        # 验证媒体文件是否存在且属于当前用户
        query = select(Media).where(Media.id == media_id, Media.user == current_user.id)
        result = await db.execute(query)
        media = result.scalar_one_or_none()

        if not media:
            return JSONResponse(
                content={"success": False, "error": "媒体文件不存在或无权访问"},
                status_code=404
            )

        # 读取上传的文件
        file_data = await file.read()

        # 验证是否为有效图片
        validation = image_processor.validate_image(file_data)
        if not validation['valid']:
            return JSONResponse(
                content={"success": False, "error": f"无效的图片: {', '.join(validation['errors'])}"},
                status_code=400
            )

        # 计算新文件的 hash
        file_hash = hashlib.sha256(file_data).hexdigest()

        # 获取文件信息
        image_info = image_processor.get_image_info(file_data)

        # 保存文件到存储
        ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        filename = f"{file_hash}.{ext}"
        storage_path = f"objects/{file_hash[:2]}/{filename}"

        # 使用 S3 存储或本地存储
        try:
            s3_storage.save_raw_file(storage_path, file_data)
            file_url = f"/storage/{storage_path}"
        except Exception as e:
            logger.warning(f"S3 存储失败，使用本地存储: {e}")
            # 回退到本地存储
            import os
            local_path = f"storage/{storage_path}"
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(file_data)
            file_url = f"/api/v2/assets/storage/{storage_path}"

        # 生成缩略图
        thumbnail_path = None
        thumbnail_url = None
        try:
            thumb_dir = f"storage/thumbnails/{file_hash[:2]}"
            os.makedirs(thumb_dir, exist_ok=True)
            thumb_file = f"{thumb_dir}/{file_hash}.jpg"

            from src.utils.image.processing import generate_thumbnail
            generate_thumbnail(local_path if os.path.exists(local_path) else f"storage/{storage_path}", thumb_file)

            if os.path.exists(thumb_file):
                thumbnail_path = f"thumbnails/{file_hash[:2]}/{file_hash}.jpg"
                thumbnail_url = f"/api/v2/assets/storage/{thumbnail_path}"
        except Exception as e:
            logger.warning(f"生成缩略图失败: {e}")

        # 更新媒体记录
        media.hash = file_hash
        media.filename = filename
        media.file_path = storage_path
        media.file_url = file_url
        media.file_size = len(file_data)
        media.mime_type = validation['info']['format'].lower() if 'format' in validation['info'] else file.content_type
        media.width = image_info['width']
        media.height = image_info['height']
        media.thumbnail_path = thumbnail_path
        media.thumbnail_url = thumbnail_url
        media.updated_at = datetime.now()

        await db.commit()

        return JSONResponse(
            content={
                "success": True,
                "message": "图片保存成功",
                "data": media.to_dict()
            }
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"保存图片失败: {e}")
        import traceback
        return JSONResponse(
            content={"success": False, "error": str(e), "traceback": traceback.format_exc()},
            status_code=500
        )
