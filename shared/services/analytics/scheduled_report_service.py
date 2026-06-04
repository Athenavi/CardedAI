"""
定时报表生成服务
支持定期自动生成报表并保存
"""


import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.unified_logger import default_logger as logger


class ScheduledReportService:
    """定时报表服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_scheduled_report(self, config: Dict) -> Dict:
        """
        创建定时报表任务
        
        Args:
            config: 配置信息
                - name: 报表名称
                - type: 报表类型 (content/user-activity/traffic/custom)
                - frequency: 频率 (daily/weekly/monthly)
                - metrics: 指标列表（custom类型需要）
                - days: 统计天数
                - export_format: 导出格式 (json/csv)
                
        Returns:
            创建的定时报表配置
        """
        from shared.models.scheduled_report import ScheduledReport

        now = datetime.now()

        # 计算下次执行时间
        frequency = config.get('frequency', 'daily')
        if frequency == 'daily':
            next_run = now + timedelta(days=1)
            next_run = next_run.replace(hour=0, minute=0, second=0, microsecond=0)
        elif frequency == 'weekly':
            next_run = now + timedelta(weeks=1)
            next_run = next_run.replace(hour=0, minute=0, second=0, microsecond=0)
        elif frequency == 'monthly':
            # 下个月的第一天
            if now.month == 12:
                next_run = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                next_run = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            raise ValueError(f"Invalid frequency: {frequency}")

        scheduled_report = ScheduledReport(
            name=config['name'],
            report_type=config['type'],
            frequency=frequency,
            metrics=json.dumps(config.get('metrics', [])),
            days=config.get('days', 30),
            export_format=config.get('export_format', 'json'),
            is_active=True,
            next_run_at=next_run,
            created_at=now,
            updated_at=now,
        )

        self.db.add(scheduled_report)
        await self.db.commit()
        await self.db.refresh(scheduled_report)

        return {
            'id': scheduled_report.id,
            'name': scheduled_report.name,
            'type': scheduled_report.report_type,
            'frequency': scheduled_report.frequency,
            'next_run_at': scheduled_report.next_run_at.isoformat(),
            'is_active': scheduled_report.is_active,
        }

    async def get_scheduled_reports(self) -> List[Dict]:
        """获取所有定时报表任务"""
        from shared.models.scheduled_report import ScheduledReport

        result = await self.db.execute(
            select(ScheduledReport).order_by(ScheduledReport.created_at.desc())
        )
        reports = result.scalars().all()

        return [
            {
                'id': r.id,
                'name': r.name,
                'type': r.report_type,
                'frequency': r.frequency,
                'metrics': json.loads(r.metrics) if r.metrics else [],
                'days': r.days,
                'export_format': r.export_format,
                'is_active': r.is_active,
                'last_run_at': r.last_run_at.isoformat() if r.last_run_at else None,
                'next_run_at': r.next_run_at.isoformat() if r.next_run_at else None,
                'created_at': r.created_at.isoformat(),
            }
            for r in reports
        ]

    async def toggle_report(self, report_id: int) -> Dict:
        """启用/禁用定时报表"""
        from shared.models.scheduled_report import ScheduledReport

        result = await self.db.execute(
            select(ScheduledReport).where(ScheduledReport.id == report_id)
        )
        report = result.scalar_one_or_none()

        if not report:
            raise ValueError(f"Report not found: {report_id}")

        report.is_active = not report.is_active
        report.updated_at = datetime.now()

        await self.db.commit()

        return {
            'id': report.id,
            'is_active': report.is_active,
        }

    async def run_scheduled_reports(self):
        """
        执行到期的定时报表任务
        这个方法应该被定时任务调度器调用（如APScheduler）
        """
        from shared.models.scheduled_report import ScheduledReport
        from shared.services.system.report_generator import ReportGenerator

        now = datetime.now()

        # 查找所有到期且激活的报表
        result = await self.db.execute(
            select(ScheduledReport).where(
                ScheduledReport.is_active == True,
                ScheduledReport.next_run_at <= now
            )
        )
        reports = result.scalars().all()

        logger.info(f"Found {len(reports)} scheduled reports to run")

        for report in reports:
            try:
                logger.info(f"Running scheduled report: {report.name}")

                # 生成报表
                generator = ReportGenerator(self.db)

                if report.report_type == 'content':
                    data = await generator.generate_content_report(report.days)
                elif report.report_type == 'user-activity':
                    data = await generator.generate_user_activity_report(report.days)
                elif report.report_type == 'traffic':
                    data = await generator.generate_traffic_report(report.days)
                else:
                    metrics = json.loads(report.metrics) if report.metrics else []
                    data = await generator.generate_custom_report(metrics, report.days)

                # 导出报表
                exported = generator.export_report(data, report.export_format)

                # 保存报表历史
                from shared.models.report_history import ReportHistory
                history = ReportHistory(
                    scheduled_report_id=report.id,
                    report_name=report.name,
                    report_type=report.report_type,
                    content=exported,
                    format=report.export_format,
                    generated_at=now,
                )
                self.db.add(history)

                # 更新下次执行时间
                frequency = report.frequency
                if frequency == 'daily':
                    next_run = now + timedelta(days=1)
                    next_run = next_run.replace(hour=0, minute=0, second=0, microsecond=0)
                elif frequency == 'weekly':
                    next_run = now + timedelta(weeks=1)
                    next_run = next_run.replace(hour=0, minute=0, second=0, microsecond=0)
                elif frequency == 'monthly':
                    if now.month == 12:
                        next_run = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0,
                                               microsecond=0)
                    else:
                        next_run = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)

                report.last_run_at = now
                report.next_run_at = next_run
                report.updated_at = now

                await self.db.commit()
                logger.info(f"Successfully ran report: {report.name}")

            except Exception as e:
                logger.error(f"Failed to run scheduled report {report.name}: {e}")
                await self.db.rollback()


# 工厂函数
def create_scheduled_report_service(db: AsyncSession) -> ScheduledReportService:
    return ScheduledReportService(db)
