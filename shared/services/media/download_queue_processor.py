"""
外部资源下载后台任务处理器
定期检查并处理待处理的下载任务
"""
import asyncio

from typing import Optional

from sqlalchemy import select

from shared.models import DownloadTask
from shared.services.performance.resource_transfer_service import ResourceTransferService
from src.utils.database.unified_manager import db_manager

from src.unified_logger import default_logger as logger


class DownloadQueueProcessor:
    """下载队列处理器"""

    def __init__(self, max_concurrent: int = 3, check_interval: int = 30):
        """
        初始化处理器
        
        Args:
            max_concurrent: 最大并发下载数
            check_interval: 检查间隔（秒）
        """
        self.max_concurrent = max_concurrent
        self.check_interval = check_interval
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def start(self):
        """启动队列处理器"""
        if self.is_running:
            logger.warning("Download queue processor is already running")
            return

        self.is_running = True
        self.task = asyncio.create_task(self._run_processor())
        logger.info(
            f"Download queue processor started (max_concurrent={self.max_concurrent}, interval={self.check_interval}s)")

    async def stop(self):
        """停止队列处理器"""
        if not self.is_running:
            logger.warning("Download queue processor is not running")
            return

        self.is_running = False

        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        logger.info("Download queue processor stopped")

    async def _run_processor(self):
        """运行处理器主循环"""
        while self.is_running:
            try:
                await self._process_queue()
            except Exception as e:
                logger.error(f"Error in download queue processor: {e}", exc_info=True)

            # 等待下一个检查周期
            await asyncio.sleep(self.check_interval)

    async def _process_queue(self):
        """处理下载队列"""
        try:
            # 检查系统是否已安装
            from shared.services.install.install_manager.installation_wizard import installation_wizard_service
            if not installation_wizard_service.is_installed():
                logger.debug("System not installed, skipping download queue processing")
                return
            
            # 获取待处理的任务
            async with db_manager.get_session() as db:
                result = await db.execute(
                    select(DownloadTask)
                    .where(DownloadTask.status == "pending")
                    .order_by(DownloadTask.priority, DownloadTask.created_at)
                    .limit(self.max_concurrent)
                )
                pending_tasks = result.scalars().all()

                if not pending_tasks:
                    return

                logger.info(f"Found {len(pending_tasks)} pending download tasks")

                # 并发处理任务
                tasks = []
                for task in pending_tasks:
                    # 使用信号量限制并发
                    coro = self._process_single_task(task.id)
                    tasks.append(asyncio.create_task(coro))

                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    # 检查结果
                    success_count = sum(1 for r in results if isinstance(r, bool) and r)
                    logger.info(f"Processed {len(tasks)} tasks, {success_count} succeeded")

        except Exception as e:
            logger.error(f"Failed to process queue: {e}", exc_info=True)

    async def _process_single_task(self, task_id: int) -> bool:
        """处理单个任务"""
        async with self.semaphore:
            try:
                async with db_manager.get_session() as db:
                    service = ResourceTransferService(db)
                    media = await service.execute_download(task_id)

                    if media:
                        logger.info(f"Task {task_id} completed successfully, media_id={media.id}")
                        return True
                    else:
                        logger.warning(f"Task {task_id} failed")
                        return False

            except Exception as e:
                logger.error(f"Task {task_id} processing error: {e}", exc_info=True)
                return False


# 全局实例
download_queue_processor = DownloadQueueProcessor(
    max_concurrent=3,
    check_interval=30
)


async def init_download_processor():
    """初始化下载处理器（在应用启动时调用）"""
    await download_queue_processor.start()


async def shutdown_download_processor():
    """关闭下载处理器（在应用关闭时调用）"""
    await download_queue_processor.stop()
