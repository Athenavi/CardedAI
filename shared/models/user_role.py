"""
SQLAlchemy 模型定义 - UserRole
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base


class UserRole(Base):
    """用户角色关联模型模型"""
    __tablename__ = 'user_role_assignments'


    __table_args__ = (
        Index('idx_user_roles_user_id', 'user_id'),
        Index('idx_user_roles_role_id', 'role_id'),
        Index('idx_user_roles_unique', 'user_id', 'role_id', unique=True),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='关联 ID')

    user_id = Column(BigInteger, ForeignKey('users.id'), doc='用户 ID')


    role_id = Column(BigInteger, ForeignKey('roles.id'), doc='角色 ID')


    assigned_by = Column(BigInteger, ForeignKey('users.id'), nullable=True, doc='分配者用户 ID')


    created_at = Column(DateTime, doc='分配时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'role_id': self.role_id,
            'assigned_by': self.assigned_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<UserRole id={self.id}>'


