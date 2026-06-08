"""
情报采集调度器（APScheduler）

在应用启动时注册定时任务：
- 数据源采集：根据每个数据源的 schedule_cron 字段
- 每日简报：每天 8:00 生成
- 每周简报：每周一 8:00 生成
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def init_intel_scheduler(scheduler) -> None:
    """注册情报相关的定时任务到 APScheduler"""
    try:
        # 1. 每日简报（每天早上 8:00）
        scheduler.add_job(
            _generate_daily_briefing_job,
            trigger="cron",
            id="intel_daily_briefing",
            hour=8,
            minute=0,
            replace_existing=True,
        )
        logger.info("[IntelScheduler] 已注册每日简报任务 (08:00)")

        # 2. 每周简报（每周一 8:00）
        scheduler.add_job(
            _generate_weekly_briefing_job,
            trigger="cron",
            id="intel_weekly_briefing",
            day_of_week="mon",
            hour=8,
            minute=0,
            replace_existing=True,
        )
        logger.info("[IntelScheduler] 已注册每周简报任务 (周一 08:00)")

    except Exception as e:
        logger.warning(f"[IntelScheduler] 注册定时任务失败: {e}")


def _generate_daily_briefing_job():
    """定时任务：生成每日简报"""
    try:
        import asyncio
        from shared.services.intel.briefing_generator import briefing_generator
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(briefing_generator.generate_daily_briefing())
        loop.close()
        logger.info(f"[IntelScheduler] 每日简报生成完成: success={result.get('success')}, count={result.get('intelligence_count')}")
    except Exception as e:
        logger.error(f"[IntelScheduler] 每日简报生成失败: {e}")


def _generate_weekly_briefing_job():
    """定时任务：生成每周简报"""
    try:
        import asyncio
        from shared.services.intel.briefing_generator import briefing_generator
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(briefing_generator.generate_weekly_briefing())
        loop.close()
        logger.info(f"[IntelScheduler] 每周简报生成完成: success={result.get('success')}, count={result.get('intelligence_count')}")
    except Exception as e:
        logger.error(f"[IntelScheduler] 每周简报生成失败: {e}")
