"""
SQLAlchemy 模型定义 - ChatGroupInvite
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base


class ChatGroupInvite(Base):
    """群聊邀请链接模型模型"""
    __tablename__ = 'chat_group_invites'


    __table_args__ = (
        Index('idx_chat_group_invites_code', 'invite_code', unique=True),
        Index('idx_chat_group_invites_group', 'group'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='邀请 ID')

    group = Column(BigInteger, ForeignKey('chat_groups.id'), doc='群聊 ID')


    invite_code = Column(String(100), unique=True, nullable=True, doc='邀请码（UUID）')

    created_by = Column(BigInteger, ForeignKey('users.id'), doc='创建者')


    expires_at = Column(DateTime, nullable=True, doc='过期时间（null表示永久有效）')

    max_uses = Column(BigInteger, nullable=True, doc='最大使用次数（null表示无限制）')


    use_count = Column(BigInteger, default=0, doc='已使用次数')


    is_active = Column(Boolean, default=True, doc='是否激活')


    created_at = Column(DateTime, doc='创建时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'group': self.group,
            'invite_code': self.invite_code,
            'created_by': self.created_by,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'max_uses': self.max_uses,
            'use_count': self.use_count,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<ChatGroupInvite id={self.id}>'


