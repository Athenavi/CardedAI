"""
SQLAlchemy 模型定义 - AuditLog
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base



class AuditLog(Base):
    """操作审计日志模型模型"""
    __tablename__ = 'audit_logs'


    __table_args__ = (
        Index('idx_audit_logs_user_id', 'user_id'),
        Index('idx_audit_logs_action', 'action'),
        Index('idx_audit_logs_created_at', 'created_at'),
        Index('idx_audit_logs_resource', 'resource_type', 'resource_id'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='日志 ID')

    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=True, doc='操作用户 ID')


    action = Column(String(100), nullable=True, doc='操作动作 (如: create_article, update_settings)')

    resource_type = Column(String(50), nullable=True, doc='资源类型 (如: Article, User)')

    resource_id = Column(BigInteger, nullable=True, doc='资源 ID')


    ip_address = Column(String(45), nullable=True, doc='操作 IP 地址')

    user_agent = Column(Text, nullable=True, doc='用户代理字符串')

    request_data = Column(Text, nullable=True, doc='请求数据快照 (JSON)')

    status = Column(String(20), default='success', doc='操作状态 (success, failure)')

    error_message = Column(Text, nullable=True, doc='错误信息')


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
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'request_data': self.request_data,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<AuditLog id={self.id}>'
