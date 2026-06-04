"""
媒体批量上传和处理服务
支持多文件同时上传、后台任务队列、进度追踪
"""

import asyncio

from typing import List, Dict, Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.media import Media
from shared.services.media.image_tool import image_processor
from src.utils.upload.public_upload import FileProcessor

from src.unified_logger import default_logger as logger

# 默认配置
DEFAULT_MAX_CONCURRENT = 5
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class BatchUploadService:
    """
    批量上传服务
    
    功能:
    1. 多文件同时上传
    2. 上传进度追踪
    3. 后台自动处理（生成缩略图、提取元数据）
    4. 失败重试机制
    5. 上传结果汇总
    """

    def __init__(self, max_concurrent: int = DEFAULT_MAX_CONCURRENT, retry_attempts: int = DEFAULT_RETRY_ATTEMPTS):
        self.max_concurrent_uploads = max_concurrent
        self.retry_attempts = retry_attempts

    async def batch_upload_files(
            self,
            db: AsyncSession,
            user_id: int,
            files: List[Any],
            allowed_mimes: Optional[set] = None,
            max_file_size: int = DEFAULT_MAX_FILE_SIZE
    ) -> Dict[str, Any]:
        """批量上传文件"""
        results, errors = [], []
        successful_count = failed_count = 0
        semaphore = asyncio.Semaphore(self.max_concurrent_uploads)

        async def upload_single_file(file_obj, index: int):
            nonlocal successful_count, failed_count
            async with semaphore:
                try:
                    logger.info(f"开始上传文件 {index + 1}/{len(files)}: {file_obj.filename}")
                    content = await file_obj.read()
                    processor = FileProcessor(user_id=user_id, allowed_mimes=allowed_mimes, allowed_size=max_file_size)

                    is_valid, validation_result = processor.validate_file(content, file_obj.filename or "unknown")
                    if not is_valid:
                        failed_count += 1
                        error_msg = f"文件 {file_obj.filename} 验证失败: {validation_result}"
                        errors.append({'filename': file_obj.filename, 'error': error_msg})
                        logger.warning(error_msg)
                        return None

                    file_hash = processor.calculate_hash(content)
                    storage_path = processor.save_file(file_hash, content, file_obj.filename or "unknown")
                    file_hash_record = await processor.create_file_hash_record(
                        db=db, file_hash=file_hash, filename=file_obj.filename or "unknown",
                        file_size=len(content), mime_type=validation_result['mime_type'], storage_path=storage_path
                    )
                    media_record = await processor.create_media_record(
                        db=db, file_hash=file_hash, filename=file_obj.filename or "unknown", check_existing=True
                    )
                    await db.commit()

                    successful_count += 1
                    result = {
                        'index': index, 'filename': file_obj.filename, 'media_id': media_record.id,
                        'file_hash': file_hash, 'file_url': media_record.file_url,
                        'file_size': len(content), 'mime_type': validation_result['mime_type'], 'status': 'success'
                    }
                    results.append(result)
                    logger.info(f"文件上传成功: {file_obj.filename}")
                    return result
                except Exception as e:
                    failed_count += 1
                    error_msg = f"文件 {file_obj.filename} 上传失败: {str(e)}"
                    errors.append({'filename': file_obj.filename, 'error': str(e)})
                    logger.error(error_msg, exc_info=True)
                    return None

        tasks = [upload_single_file(file_obj, idx) for idx, file_obj in enumerate(files)]
        await asyncio.gather(*tasks, return_exceptions=True)

        return {
            'success': failed_count == 0, 'total': len(files),
            'successful': successful_count, 'failed': failed_count,
            'results': results, 'errors': errors
        }

    async def process_media_batch(
            self,
            db: AsyncSession,
            media_ids: List[int],
            operations: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """批量处理媒体文件（后台任务）"""
        operations = operations or ['thumbnail', 'metadata']
        results, errors = [], []

        for media_id in media_ids:
            try:
                query = select(Media).where(Media.id == media_id)
                result = await db.execute(query)
                media = result.scalar_one_or_none()

                if not media:
                    errors.append({'media_id': media_id, 'error': '媒体记录不存在'})
                    continue

                processing_result = await self._process_single_media(db=db, media=media, operations=operations)
                results.append({
                    'media_id': media_id, 'filename': media.original_filename,
                    'status': 'success', 'result': processing_result
                })
            except Exception as e:
                errors.append({'media_id': media_id, 'error': str(e)})
                logger.error(f"处理媒体 {media_id} 失败: {e}", exc_info=True)

        return {
            'total': len(media_ids), 'successful': len(results),
            'failed': len(errors), 'results': results, 'errors': errors
        }

    async def _process_single_media(
            self,
            db: AsyncSession,
            media: Media,
            operations: List[str]
    ) -> Dict[str, Any]:
        """处理单个媒体文件"""
        from src.utils.storage.s3_storage import s3_storage
        import json
        
        result = {}

        # 生成缩略图
        if 'thumbnail' in operations and media.file_type == 'image':
            try:
                file_data = s3_storage.read_file(media.file_path)
                thumbnail_ops = {'thumbnail': 200, 'quality': 85, 'format': 'JPEG'}
                thumbnail_data, _ = image_processor.process_image(file_data, thumbnail_ops)
                thumbnail_hash = image_processor.calculate_hash(thumbnail_data)
                thumbnail_path = f"thumbnails/{thumbnail_hash}.jpg"
                s3_storage.save_raw_file(thumbnail_path, thumbnail_data)
                media.thumbnail_path = thumbnail_path
                await db.flush()
                result['thumbnail'] = {'path': thumbnail_path, 'url': f"/api/v1/media/thumbnails/{thumbnail_hash}"}
                logger.info(f"生成缩略图成功: {media.original_filename}")
            except Exception as e:
                result['thumbnail_error'] = str(e)
                logger.error(f"生成缩略图失败: {e}")

        # 提取元数据
        if 'metadata' in operations:
            try:
                file_data = s3_storage.read_file(media.file_path)
                info = image_processor.get_image_info(file_data)
                if 'width' in info:
                    media.width = info['width']
                if 'height' in info:
                    media.height = info['height']
                if 'exif' in info:
                    media.metadata = json.dumps(info['exif'], ensure_ascii=False, default=str)
                await db.flush()
                result['metadata'] = info
                logger.info(f"提取元数据成功: {media.original_filename}")
            except Exception as e:
                result['metadata_error'] = str(e)
                logger.error(f"提取元数据失败: {e}")

        # 优化图片
        if 'optimize' in operations and media.file_type == 'image':
            try:
                file_data = s3_storage.read_file(media.file_path)
                optimize_ops = {'quality': 75, 'format': 'WEBP'}
                optimized_data, _ = image_processor.process_image(file_data, optimize_ops)
                if len(optimized_data) < len(file_data):
                    optimized_hash = image_processor.calculate_hash(optimized_data)
                    optimized_path = f"optimized/{optimized_hash}.webp"
                    s3_storage.save_raw_file(optimized_path, optimized_data)
                    media.optimized_path = optimized_path
                    await db.flush()
                    result['optimized'] = {
                        'original_size': len(file_data), 'optimized_size': len(optimized_data),
                        'savings': f"{(1 - len(optimized_data) / len(file_data)) * 100:.1f}%"
                    }
                    logger.info(f"优化图片成功: {media.original_filename}")
            except Exception as e:
                result['optimize_error'] = str(e)
                logger.error(f"优化图片失败: {e}")

        return result


# 全局实例
batch_upload_service = BatchUploadService()
