"""
SQLAlchemy 模型定义 - MonitoringAlert
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Numeric, Index

from . import Base  # 使用统一的 Base



class MonitoringAlert(Base):
    """监控告警模型模型"""
    __tablename__ = 'monitoring_alerts'


    __table_args__ = (
        Index('idx_alert_type', 'alert_type'),
        Index('idx_alert_severity', 'severity'),
        Index('idx_alert_resolved', 'is_resolved'),
        Index('idx_alert_created', 'created_at'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='告警 ID')

    alert_type = Column(String(50), nullable=True, doc='告警类型')

    severity = Column(String(20), default='warning', doc='严重程度')

    title = Column(String(255), nullable=True, doc='告警标题')

    message = Column(Text, nullable=False, doc='告警消息')


    source = Column(String(255), nullable=True, doc='告警来源')

    metric_name = Column(String(100), nullable=True, doc='指标名称')

    metric_value = Column(Numeric(10, 2), nullable=True, doc='指标值')

    threshold = Column(Numeric(10, 2), nullable=True, doc='阈值')

    is_resolved = Column(Boolean, default=False, doc='是否已解决')

    resolved_at = Column(DateTime, nullable=True, doc='解决时间')

    notified_users = Column(Text, nullable=True, doc='已通知用户列表（JSON格式）')

    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')

    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'title': self.title,
            'message': self.message,
            'source': self.source,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'threshold': self.threshold,
            'is_resolved': self.is_resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'notified_users': self.notified_users,
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
        return f'<MonitoringAlert id={self.id}>'
