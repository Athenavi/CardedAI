"""
SQLAlchemy 模型定义 - Notification
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey

from . import Base  # 使用统一的 Base


class Notification(Base):
    """通知模型模型"""
    __tablename__ = 'notifications'




    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='通知 ID')

    recipient = Column(BigInteger, ForeignKey('users.id'), doc='接收者')


    type = Column(String(100), nullable=True, doc='通知类型')

    title = Column(String(200), nullable=True, doc='标题')

    message = Column(String(255), nullable=True, doc='消息内容')

    is_read = Column(Boolean, default=False, doc='是否已读')


    read_at = Column(DateTime, nullable=True, doc='阅读时间')

    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'recipient': self.recipient,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
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
        return f'<Notification id={self.id}>'


