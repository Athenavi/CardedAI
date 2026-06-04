"""
SQLAlchemy 模型定义 - ChatGroup
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base


class ChatGroup(Base):
    """群聊会话模型模型"""
    __tablename__ = 'chat_groups'


    __table_args__ = (
        Index('idx_chat_groups_creator', 'creator'),
        Index('idx_chat_groups_created_at', 'created_at'),
        Index('idx_chat_groups_is_active', 'is_active'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='群聊 ID')

    name = Column(String(255), nullable=True, doc='群聊名称')

    description = Column(String(255), nullable=True, doc='群聊描述')

    avatar = Column(String(255), nullable=True, doc='群聊头像 URL')

    creator = Column(BigInteger, ForeignKey('users.id'), doc='创建者')


    member_count = Column(BigInteger, default=0, doc='成员数量')


    last_message_at = Column(DateTime, nullable=True, doc='最后消息时间')

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
            'description': self.description,
            'avatar': self.avatar,
            'creator': self.creator,
            'member_count': self.member_count,
            'last_message_at': self.last_message_at.isoformat() if self.last_message_at else None,
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
        return f'<ChatGroup id={self.id}>'


