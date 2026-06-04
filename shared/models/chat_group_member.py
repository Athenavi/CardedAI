"""
SQLAlchemy 模型定义 - ChatGroupMember
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base


class ChatGroupMember(Base):
    """群聊成员关系模型模型"""
    __tablename__ = 'chat_group_members'


    __table_args__ = (
        Index('idx_chat_group_members_group', 'group'),
        Index('idx_chat_group_members_user', 'user'),
        Index('idx_chat_group_members_unique', 'group', 'user', unique=True),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='成员关系 ID')

    group = Column(BigInteger, ForeignKey('chat_groups.id'), doc='群聊 ID')


    user = Column(BigInteger, ForeignKey('users.id'), doc='用户 ID')


    role = Column(String(50), default='member', doc='角色 (owner/admin/member)')

    joined_at = Column(DateTime, doc='加入时间')

    last_read_at = Column(DateTime, nullable=True, doc='最后阅读时间')

    is_muted = Column(Boolean, default=False, doc='是否静音')



    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'group': self.group,
            'user': self.user,
            'role': self.role,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'last_read_at': self.last_read_at.isoformat() if self.last_read_at else None,
            'is_muted': self.is_muted,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<ChatGroupMember id={self.id}>'


