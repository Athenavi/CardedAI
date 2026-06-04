"""
SQLAlchemy 模型定义 - FieldPermission
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey

from . import Base  # 使用统一的 Base



class FieldPermission(Base):
    """字段级权限控制模型模型"""
    __tablename__ = 'field_permissions'

    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='权限 ID')

    role_id = Column(BigInteger, ForeignKey('roles.id'), doc='角色 ID')

    model_name = Column(String(100), nullable=True, doc='模型名称')

    field_name = Column(String(100), nullable=True, doc='字段名称')

    can_read = Column(Boolean, default=True, doc='是否可读')

    can_write = Column(Boolean, default=False, doc='是否可写')

    created_at = Column(DateTime, doc='创建时间')

    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'role_id': self.role_id,
            'model_name': self.model_name,
            'field_name': self.field_name,
            'can_read': self.can_read,
            'can_write': self.can_write,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<FieldPermission id={self.id}>'
