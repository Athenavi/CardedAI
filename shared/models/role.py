"""
SQLAlchemy 模型定义 - Role
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from . import Base  # 使用统一的 Base


class Role(Base):
    """角色模型模型"""
    __tablename__ = 'roles'


    __table_args__ = (
        Index('idx_roles_slug', 'slug', unique=True),
        Index('idx_roles_is_system', 'is_system'),
        Index('idx_roles_parent', 'parent_id'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='角色 ID')

    name = Column(String(100), nullable=True, doc='角色名称')

    slug = Column(String(100), unique=True, nullable=True, doc='角色标识（唯一）')

    description = Column(String(255), nullable=True, doc='角色描述')

    is_system = Column(Boolean, default=False, doc='是否为系统角色（系统角色不可删除）')

    parent_id = Column(BigInteger, ForeignKey('roles.id'), nullable=True, doc='父角色 ID（用于权限继承）')


    is_active = Column(Boolean, default=True, doc='是否激活')


    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')

    # 关系定义
    capabilities = relationship('Capability', secondary='role_capabilities', back_populates='roles')

    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'is_system': self.is_system,
            'parent_id': self.parent_id,
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
        return f'<Role id={self.id}>'


