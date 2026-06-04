"""
SQLAlchemy 模型定义 - MonitoringMetric
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Numeric, ForeignKey, Index

from . import Base  # 使用统一的 Base



class MonitoringMetric(Base):
    """监控指标模型模型"""
    __tablename__ = 'monitoring_metrics'


    __table_args__ = (
        Index('idx_metric_name_timestamp', 'metric_name', 'timestamp'),
        Index('idx_metric_timestamp', 'timestamp'),
        Index('idx_metric_site', 'site_id'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='指标 ID')

    metric_name = Column(String(100), index=True, nullable=True, doc='指标名称')

    metric_value = Column(Numeric(10, 2), doc='指标值')


    metric_type = Column(String(50), nullable=True, doc='指标类型（cpu/memory/disk/request等）')

    labels = Column(Text, nullable=True, doc='标签（JSON格式）')


    timestamp = Column(DateTime, doc='时间戳')

    site_id = Column(BigInteger, ForeignKey('sites.id'), nullable=True, doc='关联站点 ID')

    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'metric_type': self.metric_type,
            'labels': self.labels,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'site_id': self.site_id,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<MonitoringMetric id={self.id}>'
