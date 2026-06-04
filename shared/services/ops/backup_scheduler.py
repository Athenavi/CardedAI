"""
P8-3: 定时备份任务调度器
使用 APScheduler 实现自动化备份调度
"""
import asyncio
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from shared.services.ops.backup_manager import backup_manager
from shared.services.ops.health_checker import health_checker
from src.unified_logger import default_logger as logger


class BackupScheduler:
    """
    P8-3: 备份任务调度器
    
    功能：
    1. 每日凌晨 2 点自动备份数据库
    2. 每周日凌晨 3 点执行完整备份
    3. 每月 1 号凌晨 4 点执行月度备份
    4. 每小时健康检查
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    async def daily_backup_job(self):
        """每日备份任务"""
        logger.info("Starting daily database backup...")
        result = await backup_manager.create_database_backup('daily')

        if result['success']:
            logger.info(f"Daily backup completed: {result['filename']}")
        else:
            logger.error(f"Daily backup failed: {result.get('error')}")

    async def weekly_backup_job(self):
        """每周备份任务"""
        logger.info("Starting weekly full backup...")

        # 数据库备份
        db_result = await backup_manager.create_database_backup('weekly')

        # 文件备份
        files_result = await backup_manager.create_files_backup()

        if db_result['success'] and files_result['success']:
            logger.info("Weekly full backup completed")
        else:
            logger.error("Weekly backup partially failed")

    async def monthly_backup_job(self):
        """每月备份任务"""
        logger.info("Starting monthly archive backup...")
        result = await backup_manager.create_database_backup('monthly')

        if result['success']:
            logger.info(f"Monthly backup completed: {result['filename']}")
        else:
            logger.error(f"Monthly backup failed: {result.get('error')}")

    async def hourly_health_check(self):
        """每小时健康检查"""
        logger.debug("Running hourly health check...")
        health = await health_checker.check_application_health()

        if health['status'] != 'healthy':
            logger.warning(f"Health check failed: {health}")

    def start(self):
        """启动调度器"""
        # 每日备份：凌晨 2 点
        self.scheduler.add_job(
            self.daily_backup_job,
            trigger=CronTrigger(hour=2, minute=0),
            id='daily_backup',
            name='Daily Database Backup',
            replace_existing=True
        )

        # 每周备份：周日凌晨 3 点
        self.scheduler.add_job(
            self.weekly_backup_job,
            trigger=CronTrigger(day_of_week='sun', hour=3, minute=0),
            id='weekly_backup',
            name='Weekly Full Backup',
            replace_existing=True
        )

        # 每月备份：每月 1 号凌晨 4 点
        self.scheduler.add_job(
            self.monthly_backup_job,
            trigger=CronTrigger(day=1, hour=4, minute=0),
            id='monthly_backup',
            name='Monthly Archive Backup',
            replace_existing=True
        )

        # 每小时健康检查
        self.scheduler.add_job(
            self.hourly_health_check,
            trigger=CronTrigger(minute=0),
            id='hourly_health_check',
            name='Hourly Health Check',
            replace_existing=True
        )

        self.scheduler.start()
        logger.info("Backup scheduler started")
        logger.info("Scheduled jobs:")
        for job in self.scheduler.get_jobs():
            logger.info(f"  - {job.name}: {job.trigger}")

    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()
        logger.info("Backup scheduler stopped")


# 全局实例
backup_scheduler = BackupScheduler()
