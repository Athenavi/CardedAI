"""
SQLAlchemy 模型定义 - WebhookDelivery
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base



class WebhookDelivery(Base):
    """Webhook投递记录模型模型"""
    __tablename__ = 'webhook_deliveries'


    __table_args__ = (
        Index('idx_webhook_deliveries_webhook', 'webhook'),
        Index('idx_webhook_deliveries_event', 'event'),
        Index('idx_webhook_deliveries_success', 'success'),
        Index('idx_webhook_deliveries_created', 'created_at'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='投递记录ID')

    webhook = Column(BigInteger, ForeignKey('webhooks.id'), doc='Webhook ID')


    event = Column(String(100), nullable=True, doc='事件类型')

    payload = Column(Text, nullable=False, doc='请求payload（JSON）')


    response_status = Column(Integer, nullable=True, doc='响应状态码')


    response_body = Column(Text, nullable=True, doc='响应内容')


    success = Column(Boolean, default=False, doc='是否成功')


    retry_count = Column(Integer, default=0, doc='重试次数')


    next_retry_at = Column(DateTime, nullable=True, doc='下次重试时间')

    created_at = Column(DateTime, doc='创建时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'webhook': self.webhook,
            'event': self.event,
            'payload': self.payload,
            'response_status': self.response_status,
            'response_body': self.response_body,
            'success': self.success,
            'retry_count': self.retry_count,
            'next_retry_at': self.next_retry_at.isoformat() if self.next_retry_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<WebhookDelivery id={self.id}>'
