"""
SQLAlchemy 模型定义 - AlertEvent
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-06-04 16:28:03
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from shared.models import Base  # 使用统一的 Base（跨子包引用）



class AlertEvent(Base):
    """预警事件记录模型"""
    __tablename__ = 'intel_alert_events'


    __table_args__ = (
        Index('idx_intel_ae_rule', 'rule_id'),
        Index('idx_intel_ae_status', 'status'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='事件 ID')

    rule_id = Column(BigInteger, ForeignKey('intel_alert_rules.id'), nullable=True, doc='触发的规则 ID')


    intelligence_id = Column(BigInteger, ForeignKey('intel_intelligence.id'), nullable=True, doc='关联的情报 ID')


    severity = Column(String(20), nullable=True, doc='事件严重程度')

    message = Column(Text, nullable=True, doc='告警消息')


    status = Column(String(20), default='pending', doc='状态 (pending/acknowledged/resolved)')

    created_at = Column(DateTime, doc='创建时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'rule_id': self.rule_id,
            'intelligence_id': self.intelligence_id,
            'severity': self.severity,
            'message': self.message,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<AlertEvent id={self.id}>'


