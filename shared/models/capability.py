"""
SQLAlchemy 模型定义 - Capability
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Index
from sqlalchemy.orm import relationship

from . import Base  # 使用统一的 Base


class Capability(Base):
    """权限能力模型模型"""
    __tablename__ = 'capabilities'


    __table_args__ = (
        Index('idx_capabilities_code', 'code', unique=True),
        Index('idx_capabilities_resource', 'resource_type', 'action'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='权限 ID')

    code = Column(String(100), unique=True, nullable=True, doc='权限代码（唯一标识）')

    name = Column(String(255), nullable=True, doc='权限名称')

    description = Column(String(255), nullable=True, doc='权限描述')

    resource_type = Column(String(100), nullable=True, doc='资源类型（article, user, category等）')

    action = Column(String(50), nullable=True, doc='操作类型（create, read, update, delete）')

    is_active = Column(Boolean, default=True, doc='是否激活')


    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')

    # 关系定义
    roles = relationship('Role', secondary='role_capabilities', back_populates='capabilities')

    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'resource_type': self.resource_type,
            'action': self.action,
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
        return f'<Capability id={self.id}>'


