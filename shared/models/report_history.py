"""
SQLAlchemy 模型定义 - ReportHistory
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base



class ReportHistory(Base):
    """报表历史记录模型模型"""
    __tablename__ = 'report_history'


    __table_args__ = (
        Index('idx_report_history_scheduled', 'scheduled_report_id'),
        Index('idx_report_history_generated', 'generated_at'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='记录 ID')

    scheduled_report_id = Column(BigInteger, ForeignKey('scheduled_reports.id'), nullable=True, doc='关联的定时报表 ID')


    report_name = Column(String(255), nullable=True, doc='报表名称')

    report_type = Column(String(50), nullable=True, doc='报表类型')

    content = Column(Text, nullable=False, doc='报表内容（JSON或CSV）')


    format = Column(String(10), nullable=True, doc='导出格式')

    generated_at = Column(DateTime, doc='生成时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'scheduled_report_id': self.scheduled_report_id,
            'report_name': self.report_name,
            'report_type': self.report_type,
            'content': self.content,
            'format': self.format,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<ReportHistory id={self.id}>'
