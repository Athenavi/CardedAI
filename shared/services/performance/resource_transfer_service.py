"""
外部资源转存服务

负责将外部 URL 指向的资源下载到本地存储，并登记 FileHash 与 Media 记录。
同时提供下载任务的创建、查询、取消与执行（供 API 与后台队列处理器复用）。
"""

import asyncio
import hashlib
import ipaddress
import mimetypes
import os
import socket
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import unquote, urlparse

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import DownloadTask, Media
from shared.models.file_hash import FileHash
from src.unified_logger import default_logger as logger

# 下载限制
_MAX_DOWNLOAD_BYTES = 200 * 1024 * 1024  # 单文件上限 200MB
_DOWNLOAD_TIMEOUT = 60.0  # 秒
_ALLOWED_SCHEMES = ("http", "https")


class ResourceTransferService:
    """外部资源转存服务

    用法::

        service = ResourceTransferService(db)
        task = await service.create_download_task(user_id, url, "image")
        media = await service.execute_download(task.id)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # 任务管理
    # ------------------------------------------------------------------
    async def create_download_task(
        self,
        user_id: int,
        source_url: str,
        resource_type: str = "image",
        priority: int = 0,
    ) -> DownloadTask:
        """创建下载任务（仅登记，实际下载由 execute_download 完成）"""
        url = self._validate_url(source_url)
        now = datetime.now()
        task = DownloadTask(
            user_id=user_id,
            source_url=url,
            resource_type=resource_type or "image",
            priority=priority,
            status="pending",
            progress=0,
            downloaded_size=0,
            created_at=now,
            updated_at=now,
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def get_task_status(self, task_id: int) -> Optional[Dict[str, Any]]:
        """获取任务详情（不存在返回 None）"""
        task = await self._get_task(task_id)
        if not task:
            return None
        return {
            "id": task.id,
            "user_id": task.user_id,
            "source_url": task.source_url,
            "resource_type": task.resource_type,
            "filename": task.filename,
            "status": task.status,
            "progress": task.progress or 0,
            "total_size": task.total_size,
            "downloaded_size": task.downloaded_size or 0,
            "error_message": task.error_message,
            "media_id": task.media_id,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        }

    async def cancel_task(self, task_id: int, user_id: int) -> bool:
        """取消任务（仅 pending/failed/downloading 可取消，且须属主本人）"""
        task = await self._get_task(task_id)
        if not task or task.user_id != user_id:
            return False
        if task.status in ("completed", "cancelled"):
            return False
        task.status = "cancelled"
        task.updated_at = datetime.now()
        await self.db.commit()
        return True

    # ------------------------------------------------------------------
    # 执行下载
    # ------------------------------------------------------------------
    async def execute_download(self, task_id: int) -> Optional[Media]:
        """执行下载任务：抓取资源 -> 落盘 -> 登记 FileHash/Media -> 回写任务状态

        Returns:
            成功时返回创建的 Media 记录；失败时返回 None（任务状态置为 failed）
        """
        task = await self._get_task(task_id)
        if not task:
            logger.warning(f"下载任务不存在: {task_id}")
            return None
        if task.status not in ("pending", "failed"):
            logger.info(f"下载任务 {task_id} 状态为 {task.status}，跳过执行")
            return None

        task.status = "downloading"
        task.progress = 0
        task.error_message = None
        task.updated_at = datetime.now()
        await self.db.commit()

        try:
            content, content_type, filename = await self._download(task.source_url)

            file_hash = hashlib.sha256(content).hexdigest()

            from src.utils.storage.s3_storage import s3_storage
            storage_path = s3_storage.save_file(file_hash, content, filename)

            await self._upsert_file_hash(
                file_hash, filename, len(content), content_type, storage_path
            )

            file_type = self._file_type_from_mime(content_type, task.resource_type)
            now = datetime.now()
            media = Media(
                user=task.user_id,
                hash=file_hash,
                filename=filename,
                original_filename=filename,
                file_path=storage_path,
                file_url="",
                file_size=len(content),
                file_type=file_type,
                mime_type=content_type,
                is_public=True,
                download_count=0,
                description=f"转存自 {task.source_url}",
                created_at=now,
                updated_at=now,
            )
            self.db.add(media)
            await self.db.flush()
            media.file_url = f"/api/v2/media/{media.id}"
            await self.db.flush()

            task.status = "completed"
            task.progress = 100
            task.filename = filename
            task.total_size = len(content)
            task.downloaded_size = len(content)
            task.media_id = media.id
            task.updated_at = datetime.now()
            await self.db.commit()

            logger.info(f"下载任务 {task_id} 完成: media_id={media.id}, size={len(content)}")
            return media

        except Exception as e:
            logger.error(f"下载任务 {task_id} 失败: {e}", exc_info=True)
            task.status = "failed"
            task.error_message = str(e)[:1000]
            task.updated_at = datetime.now()
            await self.db.commit()
            return None

    async def transfer(self, source_url: str, destination_path: str) -> bool:
        """将外部资源下载并保存到指定相对路径（通用工具方法）"""
        try:
            content, _content_type, _filename = await self._download(source_url)
        except Exception as e:
            logger.error(f"资源转存失败 {source_url}: {e}")
            return False
        try:
            from src.utils.storage.s3_storage import s3_storage
            s3_storage.save_raw_file(destination_path, content)
            return True
        except Exception as e:
            logger.error(f"资源写入失败 {destination_path}: {e}")
            return False

    # ------------------------------------------------------------------
    # 内部辅助
    # ------------------------------------------------------------------
    async def _get_task(self, task_id: int) -> Optional[DownloadTask]:
        result = await self.db.execute(
            select(DownloadTask).where(DownloadTask.id == task_id)
        )
        return result.scalar_one_or_none()

    async def _upsert_file_hash(
        self,
        file_hash: str,
        filename: str,
        file_size: int,
        mime_type: str,
        storage_path: str,
    ) -> FileHash:
        """登记文件哈希（已存在则增加引用计数）"""
        result = await self.db.execute(select(FileHash).where(FileHash.hash == file_hash))
        existing = result.scalar_one_or_none()
        if existing:
            existing.reference_count = (existing.reference_count or 0) + 1
            return existing

        now = datetime.now()
        record = FileHash(
            hash=file_hash,
            filename=filename,
            file_size=file_size,
            mime_type=mime_type,
            storage_path=storage_path,
            reference_count=1,
            created_at=now,
            updated_at=now,
        )
        self.db.add(record)
        await self.db.flush()
        return record

    @staticmethod
    def _validate_url(url: str) -> str:
        """校验 URL 协议与格式"""
        url = (url or "").strip()
        if not url:
            raise ValueError("URL 不能为空")
        parsed = urlparse(url)
        if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
            raise ValueError("仅支持 http/https 协议")
        if not parsed.hostname:
            raise ValueError("无效的 URL 主机")
        return url

    @staticmethod
    async def _assert_public_host(url: str) -> None:
        """SSRF 防护：拒绝解析到内网/回环/保留地址的主机"""
        host = urlparse(url).hostname
        if not host:
            raise ValueError("无效的 URL 主机")

        loop = asyncio.get_event_loop()
        try:
            infos = await loop.getaddrinfo(host, None)
        except socket.gaierror:
            raise ValueError(f"无法解析主机: {host}")

        for info in infos:
            ip = ipaddress.ip_address(info[4][0])
            if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
                raise ValueError(f"不允许访问内网地址: {host}")

    async def _download(self, url: str) -> Tuple[bytes, str, str]:
        """下载资源，返回 (内容, MIME, 文件名)"""
        self._validate_url(url)
        await self._assert_public_host(url)

        parsed = urlparse(url)
        raw_name = unquote(os.path.basename(parsed.path)) or ""
        filename = raw_name or "download"

        chunks: List[bytes] = []
        total = 0
        content_type = "application/octet-stream"

        async with httpx.AsyncClient(
            timeout=_DOWNLOAD_TIMEOUT, follow_redirects=True
        ) as client:
            async with client.stream("GET", url) as resp:
                resp.raise_for_status()
                header_type = resp.headers.get("content-type", "")
                if header_type:
                    content_type = header_type.split(";")[0].strip() or content_type
                async for chunk in resp.aiter_bytes():
                    total += len(chunk)
                    if total > _MAX_DOWNLOAD_BYTES:
                        raise ValueError(
                            f"文件超过大小限制 ({_MAX_DOWNLOAD_BYTES // 1024 // 1024}MB)"
                        )
                    chunks.append(chunk)

        content = b"".join(chunks)
        if not content:
            raise ValueError("下载内容为空")

        # 补全扩展名
        if "." not in filename:
            ext = mimetypes.guess_extension(content_type)
            if ext:
                filename += ext

        return content, content_type, filename

    @staticmethod
    def _file_type_from_mime(mime_type: Optional[str], fallback: str = "other") -> str:
        """根据 MIME 归类文件类型"""
        if not mime_type:
            return fallback if fallback in ("image", "video", "audio", "document") else "other"
        if mime_type.startswith("image/"):
            return "image"
        if mime_type.startswith("video/"):
            return "video"
        if mime_type.startswith("audio/"):
            return "audio"
        if mime_type.startswith("text/") or mime_type in ("application/pdf",):
            return "document"
        return fallback if fallback in ("image", "video", "audio", "document") else "other"
