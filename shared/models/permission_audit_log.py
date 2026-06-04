"""
SQLAlchemy 模型定义 - PermissionAuditLog
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base



class PermissionAuditLog(Base):
    """权限审计日志模型模型"""
    __tablename__ = 'permission_audit_logs'


    __table_args__ = (
        Index('idx_permission_audit_user', 'user_id'),
        Index('idx_permission_audit_action', 'action'),
        Index('idx_permission_audit_time', 'created_at'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='审计日志 ID')

    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=True, doc='用户 ID')


    action = Column(String(50), index=True, nullable=True, doc='操作类型')

    resource_type = Column(String(50), nullable=True, doc='资源类型')

    resource_id = Column(BigInteger, nullable=True, doc='资源 ID')


    details = Column(Text, nullable=True, doc='详细信息（JSON格式）')


    ip_address = Column(String(45), nullable=True, doc='IP 地址')

    created_at = Column(DateTime, doc='创建时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<PermissionAuditLog id={self.id}>'
