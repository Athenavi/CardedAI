"""
SQLAlchemy 模型定义 - PrivateMessage
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base


class PrivateMessage(Base):
    """站内私信模型模型"""
    __tablename__ = 'private_messages'


    __table_args__ = (
        Index('idx_private_messages_sender', 'sender'),
        Index('idx_private_messages_recipient', 'recipient'),
        Index('idx_private_messages_created', 'created_at'),
        Index('idx_private_messages_conversation', 'sender', 'recipient'),
        Index('idx_private_messages_is_read', 'is_read'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='消息ID')

    sender = Column(BigInteger, ForeignKey('users.id'), doc='发送者')


    recipient = Column(BigInteger, ForeignKey('users.id'), doc='接收者')


    content = Column(Text, nullable=False, doc='消息内容')


    message_type = Column(String(50), default='text', doc='消息类型')

    attachment_url = Column(String(500), nullable=True, doc='附件URL(图片/文件)')

    is_read = Column(Boolean, default=False, doc='是否已读')


    read_at = Column(DateTime, nullable=True, doc='阅读时间')

    is_deleted_by_sender = Column(Boolean, default=False, doc='发送者是否删除')


    is_deleted_by_recipient = Column(Boolean, default=False, doc='接收者是否删除')


    parent_message = Column(BigInteger, ForeignKey('private_messages.id'), nullable=True, doc='父消息ID(用于回复)')


    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'sender': self.sender,
            'recipient': self.recipient,
            'content': self.content,
            'message_type': self.message_type,
            'attachment_url': self.attachment_url,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'is_deleted_by_sender': self.is_deleted_by_sender,
            'is_deleted_by_recipient': self.is_deleted_by_recipient,
            'parent_message': self.parent_message,
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
        return f'<PrivateMessage id={self.id}>'


