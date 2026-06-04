"""
定时发布后台任务调度器

功能：
1. 定期检查并发布到期文章
2. 后台任务管理
3. 任务日志记录
"""
import asyncio

from typing import Optional

from src.unified_logger import default_logger as logger


class ScheduledPublishScheduler:
    """
    定时发布调度器
    """

    def __init__(self, db_session_factory, check_interval: int = 60):
        """
        初始化调度器
        
        Args:
            db_session_factory: 数据库会话工厂
            check_interval: 检查间隔（秒），默认60秒
        """
        self.db_session_factory = db_session_factory
        self.check_interval = check_interval
        self.is_running = False
        self.task: Optional[asyncio.Task] = None

    async def start(self):
        """启动调度器"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return

        self.is_running = True
        self.task = asyncio.create_task(self._run_scheduler())
        logger.info(f"Scheduled publish scheduler started (interval: {self.check_interval}s)")

    async def stop(self):
        """停止调度器"""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return

        self.is_running = False

        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        logger.info("Scheduled publish scheduler stopped")

    async def _run_scheduler(self):
        """运行调度器主循环"""
        while self.is_running:
            try:
                # 检查系统是否已安装
                from shared.services.install.install_manager.installation_wizard import installation_wizard_service
                if not installation_wizard_service.is_installed():
                    logger.debug("System not installed, skipping scheduled publish check")
                    await asyncio.sleep(self.check_interval)
                    continue
                
                await self._check_and_publish()
            except Exception as e:
                logger.error(f"Error in scheduled publish scheduler: {e}")

            # 等待下一个检查周期
            await asyncio.sleep(self.check_interval)

    async def _check_and_publish(self):
        """检查并发布到期文章"""
        from shared.services.articles.scheduled_publish import create_scheduled_publish_service

        # 创建数据库会话
        async with self.db_session_factory() as db:
            try:
                service = create_scheduled_publish_service(db)
                result = await service.publish_due_articles()

                if result['published_count'] > 0:
                    logger.info(
                        f"Published {result['published_count']} scheduled articles "
                        f"(failed: {result['failed_count']})"
                    )

                    if result['failed_articles']:
                        for failed in result['failed_articles']:
                            logger.error(
                                f"Failed to publish article {failed['article_id']}: "
                                f"{failed['error']}"
                            )

                await db.commit()
            except Exception as e:
                logger.error(f"Error checking scheduled publishes: {e}")
                await db.rollback()


# 全局调度器实例
scheduler: Optional[ScheduledPublishScheduler] = None


def init_scheduler(db_session_factory, check_interval: int = 60) -> ScheduledPublishScheduler:
    """
    初始化全局调度器
    
    Args:
        db_session_factory: 数据库会话工厂
        check_interval: 检查间隔（秒）
        
    Returns:
        调度器实例
    """
    global scheduler
    scheduler = ScheduledPublishScheduler(db_session_factory, check_interval)
    return scheduler


def get_scheduler() -> Optional[ScheduledPublishScheduler]:
    """获取全局调度器实例"""
    return scheduler


async def start_scheduler():
    """启动全局调度器"""
    if scheduler:
        await scheduler.start()


async def stop_scheduler():
    """停止全局调度器"""
    if scheduler:
        await scheduler.stop()
