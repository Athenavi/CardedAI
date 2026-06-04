import asyncio
import hashlib

import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional, Union

try:
    import magic

    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
    magic = None
from fastapi import Depends, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import FileHash, Media, UploadChunk, UploadTask
from src.extensions import get_async_db_session as get_async_db
from src.utils.storage import s3_storage
from src.utils.image.video_processor import video_processor

from src.unified_logger import default_logger as logger


class FileProcessor:
    """文件处理器，统一处理文件上传逻辑"""

    def __init__(self, user_id: int, allowed_mimes: Optional[set] = None,
                 allowed_size: int = 10 * 1024 * 1024):
        self.user_id = user_id
        self.allowed_mimes = allowed_mimes or {'image/jpeg', 'image/png'}
        self.allowed_size = allowed_size

    def validate_file(self, file_data: bytes, filename: str) -> tuple[bool, Union[str, dict]]:
        """验证文件基本属性"""
        if not filename:
            return False, "文件名为空"

        # 获取MIME类型
        mime_type = self._get_mime_type(file_data, filename)

        logger.info(f"[INFO] 验证文件: {filename}")
        logger.info(f"   - 检测到的 MIME 类型: {mime_type}")
        logger.info(f"   - 允许的 MIME 类型数量: {len(self.allowed_mimes)}")
        logger.info(f"   - 文件大小: {len(file_data)} bytes")

        if mime_type not in self.allowed_mimes:
            error_msg = f"不支持的文件类型: {mime_type}"
            logger.error(f"[ERROR] {error_msg}")
            logger.error(f"   - 允许的 MIME 类型列表: {list(self.allowed_mimes)[:10]}...")  # 只显示前10个
            return False, error_msg

        file_size = len(file_data)
        if file_size > self.allowed_size:
            error_msg = f"文件大小超过限制: {self.allowed_size / 1024 / 1024}MB"
            logger.error(f"[ERROR] {error_msg}")
            return False, error_msg

        logger.info(f"[OK] 文件验证通过: {filename}")
        return True, {"mime_type": mime_type, "file_size": file_size}

    def _get_mime_type(self, file_data: bytes, filename: str) -> str:
        """获取文件的MIME类型"""
        try:
            if HAS_MAGIC and magic:
                mime_type = magic.from_buffer(file_data, mime=True)
                logger.debug(f"[DEBUG] Magic 检测到 MIME 类型: {mime_type} (文件: {filename})")
                return mime_type
            else:
                logger.warning(f"[WARN] Magic 库不可用，使用扩展名推断")
                raise Exception("Magic library not available")
        except Exception as e:
            logger.warning(f"[WARN] Magic 库失败，使用扩展名推断: {e}")
            # 如果magic库失败，使用扩展名推断
            import mimetypes
            _, ext = os.path.splitext(filename)
            mime_type, _ = mimetypes.guess_type(f"dummy{ext}")

            # 常见类型映射
            if mime_type is None:
                mime_type = self._guess_mime_from_extension(filename)
                logger.debug(f"[DEBUG] 根据扩展名猜测 MIME 类型: {mime_type} (文件: {filename})")

            result = mime_type or 'application/octet-stream'
            logger.info(f"[OK] 最终 MIME 类型: {result} (文件: {filename})")
            return result

    @staticmethod
    def _guess_mime_from_extension(filename: str) -> str:
        """根据扩展名猜测MIME类型"""
        lower_name = filename.lower()
        _, ext = os.path.splitext(lower_name)

        # 图片格式
        image_exts = {
            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
            '.gif': 'image/gif', '.bmp': 'image/bmp', '.webp': 'image/webp',
            '.svg': 'image/svg+xml', '.tiff': 'image/tiff', '.tif': 'image/tiff'
        }
        if ext in image_exts:
            return image_exts[ext]

        # 视频格式
        video_exts = {
            '.mp4': 'video/mp4', '.mov': 'video/quicktime', '.avi': 'video/x-msvideo',
            '.mkv': 'video/x-matroska', '.flv': 'video/x-flv', '.wmv': 'video/x-ms-wmv',
            '.webm': 'video/webm', '.m4v': 'video/x-m4v'
        }
        if ext in video_exts:
            return video_exts[ext]

        # 音频格式
        audio_exts = {
            '.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.flac': 'audio/flac',
            '.aac': 'audio/aac', '.ogg': 'audio/ogg', '.m4a': 'audio/mp4',
            '.wma': 'audio/x-ms-wma'
        }
        if ext in audio_exts:
            return audio_exts[ext]

        # 文档格式
        document_exts = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.csv': 'text/csv',
            '.html': 'text/html', '.htm': 'text/html'
        }
        if ext in document_exts:
            return document_exts[ext]

        # 压缩格式
        archive_exts = {
            '.zip': 'application/zip',
            '.rar': 'application/x-rar-compressed',
            '.7z': 'application/x-7z-compressed',
            '.gz': 'application/gzip',
            '.tar': 'application/x-tar',
            '.bz2': 'application/x-bzip2'
        }
        if ext in archive_exts:
            return archive_exts[ext]

        # 其他常见格式
        other_exts = {
            '.json': 'application/json',
            '.xml': 'application/xml'
        }
        if ext in other_exts:
            return other_exts[ext]

        # 未知类型，返回通用二进制
        return 'application/octet-stream'

    @staticmethod
    def calculate_hash(file_data: bytes) -> str:
        """计算文件哈希"""
        return hashlib.sha256(file_data).hexdigest()

    @staticmethod
    def save_file(file_hash: str, file_data: bytes, original_filename: str) -> str:
        """保存文件到存储系统"""
        return s3_storage.save_file(file_hash, file_data, original_filename)

    @staticmethod
    async def create_file_hash_record(db: AsyncSession, file_hash: str, filename: str,
                                      file_size: int, mime_type: str, storage_path: str,
                                      reference_count: int = 1) -> FileHash:
        """创建文件哈希记录"""
        # 检查是否已存在
        stmt = select(FileHash).where(FileHash.hash == file_hash)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.reference_count += reference_count
            return existing

        from datetime import datetime
        now = datetime.now()
        new_file_hash = FileHash(
            hash=file_hash,
            filename=filename,
            file_size=file_size,
            mime_type=mime_type,
            storage_path=storage_path,
            reference_count=reference_count,
            created_at=now,
            updated_at=now
        )
        db.add(new_file_hash)
        await db.flush()
        return new_file_hash

    async def create_media_record(self, db: AsyncSession, file_hash: str,
                                  filename: str, check_existing: bool = False) -> Media:
        """创建媒体记录"""
        if check_existing:
            stmt = select(Media).where(
                Media.user == self.user_id,
                Media.hash == file_hash
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                return existing

        # 获取 FileHash 记录以获取存储路径
        stmt = select(FileHash).where(FileHash.hash == file_hash)
        result = await db.execute(stmt)
        file_hash_record = result.scalar_one_or_none()

        if not file_hash_record:
            raise ValueError(f"FileHash record not found for hash: {file_hash}")

        from datetime import datetime
        now = datetime.now()

        # 检测文件类型
        mime_type = file_hash_record.mime_type or ''
        file_type = 'other'
        if mime_type.startswith('image/'):
            file_type = 'image'
        elif mime_type.startswith('video/'):
            file_type = 'video'
        elif mime_type.startswith('audio/'):
            file_type = 'audio'

        new_media = Media(
            user=self.user_id,
            hash=file_hash,
            filename=filename,  # 存储文件名（用于内部引用）
            original_filename=filename,  # 存储原始文件名（用户看到的名称）
            file_path=file_hash_record.storage_path,  # 存储路径
            file_url='',  # 临时空字符串，稍后更新为实际URL
            file_size=file_hash_record.file_size,
            file_type=file_type,
            mime_type=mime_type,
            is_public=True,
            download_count=0,
            created_at=now,
            updated_at=now
        )
        db.add(new_media)
        await db.flush()  # 刷新以获取生成的 ID

        # 构建文件URL（使用 media_id）
        new_media.file_url = f"/api/v2/media/{new_media.id}"
        await db.flush()  # 再次刷新以保存 file_url

        # 如果是视频文件，异步处理视频（转码、生成缩略图等）
        if file_type == 'video':
            asyncio.create_task(
                self._process_video_after_upload(new_media, file_hash_record)
            )

        return new_media

    async def _process_video_after_upload(self, media: Media, file_hash: FileHash):
        """
        视频上传后处理：生成缩略图、转码等

        Args:
            media: 媒体记录
            file_hash: 文件哈希记录
        """
        try:
            from datetime import datetime
            import tempfile

            logger.info(f"开始处理视频文件: {media.filename}")

            # 获取文件路径
            file_path = file_hash.storage_path

            # 创建临时目录用于处理
            with tempfile.TemporaryDirectory() as temp_dir:
                # 下载文件到临时目录
                local_video_path = os.path.join(temp_dir, media.filename)
                file_data = s3_storage.read_file(file_path)

                if not file_data:
                    logger.error(f"无法读取视频文件: {file_path}")
                    return

                # 保存到本地临时文件
                with open(local_video_path, 'wb') as f:
                    f.write(file_data)

                # 1. 获取视频信息
                video_info = video_processor.get_video_info(local_video_path)
                if video_info:
                    logger.info(f"视频信息: {video_info}")

                    # 更新媒体记录的宽度和高度
                    from sqlalchemy import update
                    from src.extensions import get_async_db_session

                    async with get_async_db_session()() as db:
                        stmt = update(Media).where(
                            Media.id == media.id
                        ).values(
                            width=video_info['width'],
                            height=video_info['height'],
                            duration=int(video_info['duration']),
                            updated_at=datetime.now()
                        )
                        await db.execute(stmt)
                        await db.commit()

                # 2. 生成缩略图
                thumbnail_filename = f"{Path(media.filename).stem}_thumb.jpg"
                thumbnail_local_path = os.path.join(temp_dir, thumbnail_filename)

                thumbnail_success = video_processor.create_thumbnail(
                    video_path=local_video_path,
                    thumbnail_path=thumbnail_local_path,
                    time=1.0,  # 从第1秒提取
                    width=320,
                    quality=85
                )

                if thumbnail_success and os.path.exists(thumbnail_local_path):
                    # 上传缩略图到存储
                    with open(thumbnail_local_path, 'rb') as f:
                        thumbnail_data = f.read()

                    thumbnail_hash = hashlib.sha256(thumbnail_data).hexdigest()
                    thumbnail_storage_path = s3_storage.save_file(
                        thumbnail_hash,
                        thumbnail_data,
                        thumbnail_filename
                    )

                    # 更新媒体记录的缩略图信息
                    async with get_async_db_session()() as db:
                        stmt = update(Media).where(
                            Media.id == media.id
                        ).values(
                            thumbnail_path=thumbnail_storage_path,
                            thumbnail_url=f"/api/v1/media/thumbnail/{media.id}",
                            updated_at=datetime.now()
                        )
                        await db.execute(stmt)
                        await db.commit()

                    logger.info(f"视频缩略图生成成功: {thumbnail_storage_path}")

                # 3. 生成多种分辨率版本（可选，根据配置）
                # 这里可以根据系统配置决定是否启用多分辨率转码
                # 暂时注释掉，避免大量占用存储空间
                # resolutions_dir = os.path.join(temp_dir, "resolutions")
                # os.makedirs(resolutions_dir, exist_ok=True)
                #
                # resolution_results = video_processor.generate_multiple_resolutions(
                #     input_path=local_video_path,
                #     output_dir=resolutions_dir
                # )
                #
                # for res_result in resolution_results:
                #     if res_result.get('success'):
                #         # 上传每个分辨率版本
                #         pass

            logger.info(f"视频处理完成: {media.filename}")

        except Exception as e:
            logger.error(f"视频后处理失败: {str(e)}", exc_info=True)


class ChunkedUploadProcessor:
    """分块上传处理器"""

    def __init__(self, user_id: int, chunk_size: int = 5 * 1024 * 1024):
        self.user_id = user_id
        self.chunk_size = chunk_size
        self.temp_dir = "upload_chunks"
        os.makedirs(self.temp_dir, exist_ok=True)

    async def init_upload(self, filename: str, total_size: int, total_chunks: int,
                          file_hash: Optional[str] = None, existing_upload_id: Optional[str] = None,
                          db: AsyncSession = Depends(get_async_db)) -> dict:
        """初始化上传任务，支持断点续传"""
        try:
            # 断点续传检查
            if existing_upload_id:
                resume_result = await self._check_resume_upload(
                    existing_upload_id, filename, total_size, total_chunks, db
                )
                if resume_result:
                    return resume_result

            # 文件已存在检查
            if file_hash:
                exist_result = await self._check_file_exists(file_hash, filename, db)
                if exist_result:
                    return exist_result

            # 检查现有任务
            resume_task = await self._find_resumable_task(filename, db)
            if resume_task:
                return resume_task

            # 创建新任务
            upload_id = str(uuid.uuid4())
            task = UploadTask(
                id=upload_id,
                user_id=self.user_id,
                filename=filename,
                total_size=total_size,
                total_chunks=total_chunks,
                uploaded_chunks=0,
                file_hash=file_hash,
                status='initialized'
            )
            db.add(task)
            await db.commit()

            return {
                'success': True,
                'upload_id': upload_id,
                'file_exists': False,
                'resume_upload': False
            }
        except Exception as e:
            await db.rollback()
            return {'success': False, 'error': str(e)}

    async def _check_resume_upload(self, upload_id: str, filename: str,
                                   total_size: int, total_chunks: int,
                                   db: AsyncSession) -> Optional[dict]:
        """检查是否可以断点续传"""
        stmt = select(UploadTask).where(
            UploadTask.id == upload_id,
            UploadTask.user_id == self.user_id,
            UploadTask.filename == filename,
            UploadTask.total_size == total_size,
            UploadTask.total_chunks == total_chunks
        )
        result = await db.execute(stmt)
        existing_task = result.scalar_one_or_none()

        if existing_task:
            # 获取已上传分块
            chunk_stmt = select(UploadChunk.chunk_index).where(
                UploadChunk.upload_id == upload_id
            )
            chunk_result = await db.execute(chunk_stmt)
            uploaded_indices = [chunk[0] for chunk in chunk_result.all()]

            return {
                'success': True,
                'upload_id': upload_id,
                'file_exists': False,
                'resume_upload': True,
                'uploaded_chunks': uploaded_indices,
                'uploaded_count': len(uploaded_indices),
                'total_chunks': total_chunks
            }
        return None

    async def _check_file_exists(self, file_hash: str, filename: str,
                                 db: AsyncSession) -> Optional[dict]:
        """检查文件是否已存在"""
        stmt = select(FileHash).where(FileHash.hash == file_hash)
        result = await db.execute(stmt)
        existing_file = result.scalar_one_or_none()

        if existing_file:
            # 创建媒体记录
            processor = FileProcessor(self.user_id)
            media_record = await processor.create_media_record(
                db, file_hash, filename, check_existing=True
            )
            existing_file.reference_count += 1
            await db.commit()

            return {
                'success': True,
                'upload_id': str(uuid.uuid4()),
                'file_exists': True,
                'file_hash': file_hash,
                'media_id': media_record.id,
                'instant': True
            }
        return None

    async def _find_resumable_task(self, filename: str,
                                   db: AsyncSession) -> Optional[dict]:
        """查找可恢复的上传任务"""
        stmt = select(UploadTask).where(
            UploadTask.user_id == self.user_id,
            UploadTask.filename == filename,
            UploadTask.status.in_(['initialized', 'uploading'])
        )
        result = await db.execute(stmt)
        existing_task = result.scalar_one_or_none()

        if existing_task:
            # 获取已上传分块
            chunk_stmt = select(UploadChunk.chunk_index).where(
                UploadChunk.upload_id == existing_task.id
            )
            chunk_result = await db.execute(chunk_stmt)
            uploaded_indices = [chunk[0] for chunk in chunk_result.all()]

            existing_task.status = 'uploading'
            await db.commit()

            return {
                'success': True,
                'upload_id': existing_task.id,
                'file_exists': False,
                'resume_upload': True,
                'uploaded_chunks': uploaded_indices,
                'uploaded_count': len(uploaded_indices),
                'total_chunks': existing_task.total_chunks
            }
        return None

    async def upload_chunk(self, upload_id: str, chunk_index: int,
                           chunk_data: bytes, chunk_hash: str,
                           db: AsyncSession = Depends(get_async_db)) -> dict:
        """上传单个分块"""
        try:
            # 验证任务存在
            task = await self._get_upload_task(upload_id, db)
            if not task:
                return {'success': False, 'error': '上传任务不存在'}

            # 检查分块是否已上传
            if await self._chunk_exists(upload_id, chunk_index, chunk_hash, db):
                return {'success': True, 'message': '分块已存在'}

            # 保存分块文件
            chunk_path = await self._save_chunk_file(upload_id, chunk_index, chunk_data)

            # 记录分块信息
            chunk_record = UploadChunk(
                upload_id=upload_id,
                chunk_index=chunk_index,
                chunk_hash=chunk_hash,
                chunk_size=len(chunk_data),
                chunk_path=chunk_path
            )
            db.add(chunk_record)

            # 更新任务进度
            task.uploaded_chunks += 1
            task.status = 'uploading'
            await db.commit()

            return {'success': True, 'message': '分块上传成功'}

        except Exception as e:
            await db.rollback()

            logger.error(f"分块上传失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def _get_upload_task(self, upload_id: str,
                               db: AsyncSession) -> Optional[UploadTask]:
        """获取上传任务"""
        stmt = select(UploadTask).where(
            UploadTask.id == upload_id,
            UploadTask.user_id == self.user_id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def _chunk_exists(self, upload_id: str, chunk_index: int,
                            chunk_hash: str, db: AsyncSession) -> bool:
        """检查分块是否已存在"""
        stmt = select(UploadChunk).where(
            UploadChunk.upload_id == upload_id,
            UploadChunk.chunk_index == chunk_index
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        return existing is not None and existing.chunk_hash == chunk_hash

    async def _save_chunk_file(self, upload_id: str, chunk_index: int,
                               chunk_data: bytes) -> str:
        """保存分块文件到磁盘"""
        chunk_filename = f"{upload_id}_{chunk_index}.chunk"
        chunk_path = os.path.join(self.temp_dir, chunk_filename)

        # 使用异步写入
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, self._write_chunk_file, chunk_path, chunk_data
        )
        return chunk_path

    @staticmethod
    def _write_chunk_file(path: str, data: bytes):
        """同步写入分块文件"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(data)

    async def get_upload_progress(self, upload_id: str,
                                  db: AsyncSession = Depends(get_async_db)) -> dict:
        """获取上传进度"""
        task = await self._get_upload_task(upload_id, db)
        if not task:
            return {'success': False, 'error': '上传任务不存在'}

        # 获取已上传分块数量
        stmt = select(UploadChunk).where(UploadChunk.upload_id == upload_id)
        result = await db.execute(stmt)
        uploaded_chunks = len(result.all())

        progress = 0
        if task.total_chunks > 0:
            progress = round((uploaded_chunks / task.total_chunks) * 100, 2)

        return {
            'success': True,
            'upload_id': upload_id,
            'total_chunks': task.total_chunks,
            'uploaded_chunks': uploaded_chunks,
            'progress': progress,
            'status': task.status
        }

    async def complete_upload(self, upload_id: str, file_hash: str, mime_type: str,
                              db: AsyncSession = Depends(get_async_db)) -> dict:
        """完成上传，合并所有分块"""
        try:
            # 验证任务
            task = await self._get_upload_task(upload_id, db)
            if not task:
                return {'success': False, 'error': '上传任务不存在'}

            # 获取分块
            chunks = await self._get_chunks(upload_id, db)
            if len(chunks) != task.total_chunks:
                return {
                    'success': False,
                    'error': f'分块不完整: {len(chunks)}/{task.total_chunks}'
                }

            # 合并分块并验证
            merged_data, actual_hash = await self._merge_and_validate_chunks(chunks, file_hash)
            if actual_hash != file_hash:
                return {'success': False, 'error': '文件哈希验证失败'}

            # 保存文件
            processor = FileProcessor(self.user_id)
            storage_path = processor.save_file(actual_hash, merged_data, task.filename)

            # 创建记录
            await processor.create_file_hash_record(
                db, actual_hash, task.filename, task.total_size, mime_type, storage_path
            )
            await processor.create_media_record(db, actual_hash, task.filename)

            # 更新任务
            task.status = 'completed'
            task.file_hash = actual_hash

            # 清理
            await self._cleanup_chunks(chunks, db)

            await db.commit()
            return {
                'success': True,
                'file_hash': actual_hash,
                'message': '文件上传完成'
            }

        except Exception as e:
            await db.rollback()

            logger.error(f"完成上传失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def _get_chunks(self, upload_id: str, db: AsyncSession) -> List[UploadChunk]:
        """获取所有分块"""
        stmt = select(UploadChunk).where(
            UploadChunk.upload_id == upload_id
        ).order_by(UploadChunk.chunk_index)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def _merge_and_validate_chunks(self, chunks: List[UploadChunk],
                                         expected_hash: str) -> tuple[bytes, str]:
        """合并分块并验证哈希"""
        merged_path = os.path.join(self.temp_dir, f"{chunks[0].upload_id}_merged")

        # 异步合并
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, self._merge_chunks_sync, chunks, merged_path
        )

        # 读取合并后的文件
        with open(merged_path, 'rb') as f:
            file_data = f.read()

        # 计算哈希
        actual_hash = hashlib.sha256(file_data).hexdigest()

        # 清理临时文件
        if os.path.exists(merged_path):
            os.remove(merged_path)

        return file_data, actual_hash

    def _merge_chunks_sync(self, chunks: List[UploadChunk], output_path: str):
        """同步合并分块"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'wb') as out_file:
            for chunk in chunks:
                chunk_path = self._resolve_chunk_path(chunk)
                if os.path.exists(chunk_path):
                    with open(chunk_path, 'rb') as chunk_file:
                        shutil.copyfileobj(chunk_file, out_file)

    def _resolve_chunk_path(self, chunk: UploadChunk) -> str:
        """解析分块文件路径"""
        # 尝试多种可能的路径
        possible_paths = [
            os.path.abspath(chunk.chunk_path),
            os.path.abspath(os.path.join(self.temp_dir, os.path.basename(chunk.chunk_path))),
            chunk.chunk_path,
            os.path.join(self.temp_dir, f"{chunk.upload_id}_{chunk.chunk_index}.chunk")
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path
        raise FileNotFoundError(f"分块文件不存在: {chunk.chunk_path}")

    async def _cleanup_chunks(self, chunks: List[UploadChunk], db: AsyncSession):
        """清理分块文件和记录"""
        for chunk in chunks:
            chunk_path = self._resolve_chunk_path(chunk)
            if os.path.exists(chunk_path):
                os.remove(chunk_path)
            await db.delete(chunk)

    async def get_uploaded_chunks(self, upload_id: str,
                                  db: AsyncSession = Depends(get_async_db)) -> dict:
        """获取已上传的分块列表"""
        task = await self._get_upload_task(upload_id, db)
        if not task:
            return {'success': False, 'error': '上传任务不存在'}

        stmt = select(UploadChunk).where(UploadChunk.upload_id == upload_id)
        result = await db.execute(stmt)
        chunks = result.scalars().all()

        uploaded_list = [
            {
                'chunk_index': chunk.chunk_index,
                'chunk_hash': chunk.chunk_hash,
                'chunk_size': chunk.chunk_size
            }
            for chunk in chunks
        ]

        progress = 0
        if task.total_chunks > 0:
            progress = round((len(uploaded_list) / task.total_chunks) * 100, 2)

        return {
            'success': True,
            'upload_id': upload_id,
            'uploaded_chunks': uploaded_list,
            'uploaded_count': len(uploaded_list),
            'total_chunks': task.total_chunks,
            'progress': progress
        }

    async def cancel_upload(self, upload_id: str,
                            db: AsyncSession = Depends(get_async_db)) -> dict:
        """取消上传任务"""
        task = await self._get_upload_task(upload_id, db)
        if not task:
            return {'success': False, 'error': '上传任务不存在'}

        # 获取并删除分块
        chunks = await self._get_chunks(upload_id, db)
        await self._cleanup_chunks(chunks, db)

        # 删除任务
        await db.delete(task)
        await db.commit()

        return {'success': True, 'message': '上传任务已取消'}


async def process_single_file(processor: FileProcessor, file_data: bytes,
                              filename: str, db: AsyncSession = Depends(get_async_db)) -> dict:
    """处理单个文件上传"""
    try:
        # 验证文件
        is_valid, validation_result = processor.validate_file(file_data, filename)
        if not is_valid:
            return {'success': False, 'error': validation_result}

        # 计算哈希
        file_hash = processor.calculate_hash(file_data)
        mime_type = validation_result['mime_type']
        file_size = validation_result['file_size']

        # 检查文件是否已存在
        stmt = select(FileHash).where(FileHash.hash == file_hash)
        result = await db.execute(stmt)
        existing_file = result.scalar_one_or_none()

        if not existing_file:
            # 保存新文件
            storage_path = processor.save_file(file_hash, file_data, filename)
            await processor.create_file_hash_record(
                db, file_hash, filename, file_size, mime_type, storage_path, 1
            )
        else:
            # 增加引用计数
            existing_file.reference_count += 1
            storage_path = existing_file.storage_path

        # 创建媒体记录
        media = await processor.create_media_record(db, file_hash, filename, check_existing=True)
        await db.commit()

        return {
            'success': True,
            'hash': file_hash,
            'media_id': media.id,
            'storage_path': storage_path
        }

    except Exception as e:
        await db.rollback()

        logger.error(f"文件处理失败: {str(e)}")
        return {'success': False, 'error': str(e)}


async def process_multiple_files(files: List[UploadFile], user_id: int,
                                 allowed_size: int, allowed_mimes: set,
                                 check_existing: bool = True,
                                 db: AsyncSession = Depends(get_async_db)) -> tuple[dict, int]:
    """处理多个文件上传"""
    processor = FileProcessor(user_id, allowed_mimes, allowed_size)
    uploaded_files = []
    reused_count = 0
    errors = []

    # 收集文件信息
    file_info_list = []
    for file in files:
        try:
            file_data = await file.read()
            is_valid, validation_result = processor.validate_file(file_data, file.filename)

            if not is_valid:
                errors.append(f'File {file.filename}: {validation_result}')
                continue

            file_info = {
                'filename': file.filename,
                'file_data': file_data,
                'file_hash': processor.calculate_hash(file_data),
                **validation_result
            }
            file_info_list.append(file_info)

        except Exception as e:
            errors.append(f'Error processing file {file.filename}: {str(e)}')

    # 按哈希分组处理
    hash_groups = {}
    for file_info in file_info_list:
        hash_groups.setdefault(file_info['file_hash'], []).append(file_info)

    # 处理每个哈希组
    for file_hash, file_group in hash_groups.items():
        try:
            first_file = file_group[0]

            # 检查文件是否已存在
            stmt = select(FileHash).where(FileHash.hash == file_hash)
            result = await db.execute(stmt)
            existing_file = result.scalar_one_or_none()

            if existing_file:
                existing_file.reference_count += len(file_group)
                reused_count += len(file_group)
            else:
                # 保存新文件
                storage_path = processor.save_file(
                    file_hash, first_file['file_data'], first_file['filename']
                )
                await processor.create_file_hash_record(
                    db, file_hash, first_file['filename'],
                    first_file['file_size'], first_file['mime_type'],
                    storage_path, len(file_group)
                )

            # 为每个文件创建媒体记录
            for file_info in file_group:
                await processor.create_media_record(
                    db, file_hash, file_info['filename'], check_existing
                )
                uploaded_files.append(file_info['filename'])

            await db.commit()

        except Exception as e:
            await db.rollback()
            errors.append(f'Error processing files with hash {file_hash}: {str(e)}')

    # 构建响应
    response = {
        'message': 'success' if not errors else 'partial success',
        'uploaded': uploaded_files,
        'reused': reused_count
    }

    if errors:
        response['errors'] = errors

    status_code = 200 if not errors else 207
    return response, status_code
