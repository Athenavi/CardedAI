"""
SQLAlchemy 模型定义 - ScheduledReport
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Index

from . import Base  # 使用统一的 Base



class ScheduledReport(Base):
    """定时报表任务模型模型"""
    __tablename__ = 'scheduled_reports'


    __table_args__ = (
        Index('idx_scheduled_reports_active', 'is_active'),
        Index('idx_scheduled_reports_next_run', 'next_run_at'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='报表 ID')

    name = Column(String(255), nullable=True, doc='报表名称')

    report_type = Column(String(50), nullable=True, doc='报表类型 (content/user-activity/traffic/custom)')

    frequency = Column(String(20), nullable=True, doc='执行频率 (daily/weekly/monthly)')

    metrics = Column(Text, nullable=True, doc='指标列表（JSON格式，custom类型需要）')


    days = Column(Integer, default=30, doc='统计天数')


    export_format = Column(String(10), default='json', doc='导出格式 (json/csv)')

    is_active = Column(Boolean, default=True, doc='是否激活')


    last_run_at = Column(DateTime, nullable=True, doc='上次执行时间')

    next_run_at = Column(DateTime, nullable=True, doc='下次执行时间')

    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'name': self.name,
            'report_type': self.report_type,
            'frequency': self.frequency,
            'metrics': self.metrics,
            'days': self.days,
            'export_format': self.export_format,
            'is_active': self.is_active,
            'last_run_at': self.last_run_at.isoformat() if self.last_run_at else None,
            'next_run_at': self.next_run_at.isoformat() if self.next_run_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<ScheduledReport id={self.id}>'
