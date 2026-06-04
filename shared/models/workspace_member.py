"""
SQLAlchemy 模型定义 - WorkspaceMember
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base



class WorkspaceMember(Base):
    """工作区成员模型模型"""
    __tablename__ = 'workspace_members'


    __table_args__ = (
        Index('idx_workspace_members_workspace', 'workspace_id'),
        Index('idx_workspace_members_user', 'user_id'),
        Index('idx_workspace_members_unique', 'workspace_id', 'user_id', unique=True),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='成员 ID')

    workspace_id = Column(BigInteger, ForeignKey('workspaces.id'), doc='工作区 ID')


    user_id = Column(BigInteger, ForeignKey('users.id'), doc='用户 ID')


    role = Column(String(20), default='viewer', doc='角色（owner/admin/editor/viewer）')

    joined_at = Column(DateTime, doc='加入时间')

    is_active = Column(Boolean, default=True, doc='是否激活')

    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'user_id': self.user_id,
            'role': self.role,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'is_active': self.is_active,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<WorkspaceMember id={self.id}>'
