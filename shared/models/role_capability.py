"""
SQLAlchemy 模型定义 - RoleCapability
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base



class RoleCapability(Base):
    """角色-权限能力关联模型模型"""
    __tablename__ = 'role_capabilities'


    __table_args__ = (
        Index('idx_role_capabilities_role', 'role_id'),
        Index('idx_role_capabilities_capability', 'capability_id'),
        Index('idx_role_capabilities_unique', 'role_id', 'capability_id', unique=True),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='关联 ID')

    role_id = Column(BigInteger, ForeignKey('roles.id'), doc='角色 ID')


    capability_id = Column(BigInteger, ForeignKey('capabilities.id'), doc='权限能力 ID')


    created_at = Column(DateTime, doc='创建时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'role_id': self.role_id,
            'capability_id': self.capability_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<RoleCapability id={self.id}>'
