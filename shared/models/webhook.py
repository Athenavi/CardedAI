"""
SQLAlchemy 模型定义 - Webhook
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Index

from . import Base  # 使用统一的 Base



class Webhook(Base):
    """Webhook配置模型模型"""
    __tablename__ = 'webhooks'


    __table_args__ = (
        Index('idx_webhooks_is_active', 'is_active'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='Webhook ID')

    name = Column(String(255), nullable=True, doc='Webhook名称')

    url = Column(String(2048), nullable=True, doc='Webhook URL')

    secret = Column(String(255), nullable=True, doc='签名密钥（用于HMAC验证）')

    events = Column(Text, nullable=False, doc='订阅的事件列表（JSON数组）')


    is_active = Column(Boolean, default=True, doc='是否激活')


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
            'url': self.url,
            'secret': self.secret,
            'events': self.events,
            'is_active': self.is_active,
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
        return f'<Webhook id={self.id}>'
