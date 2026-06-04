"""
外部资源下载服务
支持断点续传、进度跟踪、队列管理
"""
import asyncio
import hashlib

import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import aiohttp
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.download_task import DownloadTask
from shared.models.media import Media
from shared.models.file_hash import FileHash

from src.unified_logger import default_logger as logger


class ResourceTransferService:
    """外部资源转存服务"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.chunk_size = 1024 * 1024  # 1MB chunks for progress tracking
        self.download_dir = Path("storage/objects")
        self.download_dir.mkdir(parents=True, exist_ok=True)

    async def create_download_task(
            self,
            user_id: int,
            source_url: str,
            resource_type: str = "image",
            priority: int = 0
    ) -> DownloadTask:
        """创建下载任务"""
        try:
            # 验证URL
            if not source_url.startswith(('http://', 'https://')):
                raise ValueError("URL必须以http://或https://开头")

            # 创建任务记录
            task = DownloadTask(
                user_id=user_id,
                source_url=source_url,
                resource_type=resource_type,
                status="pending",
                priority=priority,
                retry_count=0,
                max_retries=3
            )

            self.db.add(task)
            await self.db.flush()
            await self.db.refresh(task)

            logger.info(f"创建下载任务: {task.id}, URL: {source_url}")
            return task

        except Exception as e:
            logger.error(f"创建下载任务失败: {e}")
            raise

    async def execute_download(self, task_id: int) -> Optional[Media]:
        """执行下载任务（支持断点续传）"""
        task = None
        temp_path = None

        try:
            # 获取任务
            result = await self.db.execute(
                select(DownloadTask).where(DownloadTask.id == task_id)
            )
            task = result.scalar_one_or_none()

            if not task:
                logger.error(f"任务不存在: {task_id}")
                return None

            if task.status in ["completed", "downloading"]:
                logger.warning(f"任务状态不允许下载: {task.status}")
                return None

            # 更新任务状态为下载中
            await self._update_task_status(task, "downloading")

            # 创建临时文件路径
            file_hash = hashlib.md5(task.source_url.encode()).hexdigest()
            temp_filename = f"{file_hash}.tmp"
            temp_path = self.download_dir / temp_filename

            # 检查是否有未完成的下载（断点续传）
            resume_position = 0
            if temp_path.exists():
                resume_position = temp_path.stat().st_size
                logger.info(f"检测到未完成下载，从 {resume_position} 字节继续")

            # 开始下载
            media = await self._download_with_resume(task, temp_path, resume_position)

            if media:
                # 下载成功，清理临时文件
                if temp_path.exists():
                    temp_path.unlink()
                logger.info(f"下载完成: {media.original_filename}")
                return media
            else:
                # 下载失败
                return None

        except Exception as e:
            logger.error(f"执行下载任务失败 (task_id={task_id}): {e}", exc_info=True)
            if task:
                await self._update_task_status(
                    task, "failed", error_message=str(e)
                )
            return None

        finally:
            # 清理临时文件（如果存在且下载失败）
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                except:
                    pass

    async def _download_with_resume(
            self,
            task: DownloadTask,
            temp_path: Path,
            resume_position: int = 0
    ) -> Optional[Media]:
        """带断点续传的下载"""
        headers = {}
        if resume_position > 0:
            headers['Range'] = f'bytes={resume_position}-'

        timeout = aiohttp.ClientTimeout(total=300)  # 5分钟超时

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(task.source_url, headers=headers) as response:
                    # 检查响应状态
                    if response.status not in [200, 206]:
                        raise Exception(f"HTTP错误: {response.status}")

                    # 获取文件大小
                    content_length = response.headers.get('Content-Length')
                    total_size = int(content_length) if content_length else None

                    if total_size:
                        # 计算总大小（考虑断点续传）
                        actual_total = resume_position + total_size
                        await self._update_task_progress(task, actual_total, resume_position)

                    # 打开文件准备写入
                    mode = 'ab' if resume_position > 0 else 'wb'
                    downloaded_size = resume_position

                    with open(temp_path, mode) as f:
                        chunk_count = 0
                        async for chunk in response.content.iter_chunked(self.chunk_size):
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            chunk_count += 1

                            # 每下载几个chunk更新一次进度
                            if chunk_count % 5 == 0:
                                await self._update_task_progress(
                                    task, actual_total if total_size else None, downloaded_size
                                )

                    # 下载完成，处理文件
                    return await self._finalize_download(task, temp_path, downloaded_size)

        except asyncio.CancelledError:
            logger.info(f"任务被取消: {task.id}")
            await self._update_task_status(task, "cancelled")
            return None

        except Exception as e:
            logger.error(f"下载失败: {e}")
            await self._handle_download_error(task, e)
            return None

    async def _finalize_download(
            self,
            task: DownloadTask,
            temp_path: Path,
            file_size: int
    ) -> Optional[Media]:
        """完成下载，创建媒体记录"""
        try:
            # 读取文件数据
            with open(temp_path, 'rb') as f:
                file_data = f.read()

            # 计算文件哈希
            file_hash = hashlib.sha256(file_data).hexdigest()

            # 检测MIME类型
            mime_type = await self._detect_mime_type(file_data, task.source_url)

            # 生成文件名
            ext = self._get_extension_from_mime(mime_type)
            filename = f"{file_hash}{ext}"

            # 移动到最终位置
            final_path = self.download_dir / filename[:2] / filename
            final_path.parent.mkdir(parents=True, exist_ok=True)

            # 如果文件已存在，跳过
            if final_path.exists():
                logger.info(f"文件已存在: {filename}")
            else:
                with open(final_path, 'wb') as f:
                    f.write(file_data)

            # 创建或获取FileHash记录
            file_hash_record = await self._get_or_create_file_hash(
                file_hash, file_size, mime_type, str(final_path.relative_to(Path(".")))
            )

            # 创建Media记录
            media = Media(
                user_id=task.user_id,
                hash=file_hash,
                original_filename=task.filename or f"downloaded_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}",
                file_path=str(final_path),
                file_size=file_size,
                file_type=self._get_media_type(mime_type),
                mime_type=mime_type,
                description=f"从 {task.source_url} 下载"
            )

            self.db.add(media)
            await self.db.flush()
            await self.db.refresh(media)

            # 更新任务状态
            task.media_id = media.id
            await self._update_task_status(task, "completed")

            logger.info(f"媒体创建成功: {media.id}, 文件: {filename}")
            return media

        except Exception as e:
            logger.error(f"完成下载失败: {e}", exc_info=True)
            await self._update_task_status(task, "failed", error_message=str(e))
            return None

    async def _update_task_status(
            self,
            task: DownloadTask,
            status: str,
            error_message: Optional[str] = None
    ):
        """更新任务状态"""
        now = datetime.now()

        updates = {
            "status": status,
            "updated_at": now
        }

        if status == "downloading":
            updates["started_at"] = now
        elif status == "completed":
            updates["completed_at"] = now
        elif status == "failed" and error_message:
            updates["error_message"] = error_message

        await self.db.execute(
            update(DownloadTask)
            .where(DownloadTask.id == task.id)
            .values(**updates)
        )
        await self.db.commit()

        # 刷新本地对象
        await self.db.refresh(task)

    async def _update_task_progress(
            self,
            task: DownloadTask,
            total_size: Optional[int],
            downloaded_size: int
    ):
        """更新下载进度"""
        progress = 0
        if total_size and total_size > 0:
            progress = min(int((downloaded_size / total_size) * 100), 100)

        await self.db.execute(
            update(DownloadTask)
            .where(DownloadTask.id == task.id)
            .values(
                total_size=total_size,
                downloaded_size=downloaded_size,
                progress=progress,
                updated_at=datetime.now()
            )
        )
        await self.db.commit()

    async def _handle_download_error(self, task: DownloadTask, error: Exception):
        """处理下载错误（支持重试）"""
        task.retry_count += 1

        if task.retry_count < task.max_retries:
            # 可以重试
            logger.info(f"任务 {task.id} 将重试 ({task.retry_count}/{task.max_retries})")
            await self._update_task_status(
                task, "pending",
                error_message=f"重试 {task.retry_count}: {str(error)}"
            )
        else:
            # 达到最大重试次数
            logger.error(f"任务 {task.id} 达到最大重试次数")
            await self._update_task_status(
                task, "failed",
                error_message=f"失败: {str(error)}"
            )

    async def _detect_mime_type(self, file_data: bytes, url: str) -> str:
        """检测MIME类型"""
        # 简单的魔数检测
        if file_data[:8] == b'\x89PNG\r\n\x1a\n':
            return 'image/png'
        elif file_data[:3] == b'\xff\xd8\xff':
            return 'image/jpeg'
        elif file_data[:4] == b'RIFF' and file_data[8:12] == b'WEBP':
            return 'image/webp'
        elif file_data[:4] == b'GIF8':
            return 'image/gif'
        elif file_data[:4] == b'\x00\x00\x00\x1c' or file_data[4:8] == b'ftyp':
            return 'video/mp4'

        # 从URL扩展名推断
        url_lower = url.lower()
        if any(url_lower.endswith(ext) for ext in ['.jpg', '.jpeg']):
            return 'image/jpeg'
        elif url_lower.endswith('.png'):
            return 'image/png'
        elif url_lower.endswith('.gif'):
            return 'image/gif'
        elif url_lower.endswith('.webp'):
            return 'image/webp'
        elif url_lower.endswith('.mp4'):
            return 'video/mp4'
        elif url_lower.endswith('.webm'):
            return 'video/webm'

        # 默认
        return 'application/octet-stream'

    def _get_extension_from_mime(self, mime_type: str) -> str:
        """根据MIME类型获取扩展名"""
        ext_map = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'video/mp4': '.mp4',
            'video/webm': '.webm',
            'audio/mpeg': '.mp3',
            'application/pdf': '.pdf',
        }
        return ext_map.get(mime_type, '.bin')

    def _get_media_type(self, mime_type: str) -> str:
        """获取媒体类型分类"""
        if mime_type.startswith('image/'):
            return 'image'
        elif mime_type.startswith('video/'):
            return 'video'
        elif mime_type.startswith('audio/'):
            return 'audio'
        else:
            return 'document'

    async def _get_or_create_file_hash(
            self,
            file_hash: str,
            file_size: int,
            mime_type: str,
            storage_path: str
    ) -> FileHash:
        """获取或创建FileHash记录"""
        result = await self.db.execute(
            select(FileHash).where(FileHash.hash == file_hash)
        )
        file_hash_record = result.scalar_one_or_none()

        if not file_hash_record:
            file_hash_record = FileHash(
                hash=file_hash,
                file_size=file_size,
                mime_type=mime_type,
                storage_path=storage_path
            )
            self.db.add(file_hash_record)
            await self.db.flush()

        return file_hash_record

    async def get_task_status(self, task_id: int) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        result = await self.db.execute(
            select(DownloadTask).where(DownloadTask.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            return None

        return {
            "id": task.id,
            "status": task.status,
            "progress": task.progress,
            "total_size": task.total_size,
            "downloaded_size": task.downloaded_size,
            "error_message": task.error_message,
            "media_id": task.media_id,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        }

    async def cancel_task(self, task_id: int, user_id: int) -> bool:
        """取消任务"""
        result = await self.db.execute(
            select(DownloadTask).where(
                DownloadTask.id == task_id,
                DownloadTask.user_id == user_id
            )
        )
        task = result.scalar_one_or_none()

        if not task:
            return False

        if task.status in ["completed", "cancelled"]:
            return False

        await self._update_task_status(task, "cancelled")
        return True
