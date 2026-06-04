"""
SQLAlchemy 模型定义 - LoginAttempt
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Index

from . import Base  # 使用统一的 Base


class LoginAttempt(Base):
    """登录尝试记录模型模型"""
    __tablename__ = 'login_attempts'


    __table_args__ = (
        Index('idx_login_attempts_username', 'username'),
        Index('idx_login_attempts_ip', 'ip_address'),
        Index('idx_login_attempts_created', 'created_at'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='记录 ID')

    username = Column(String(255), index=True, nullable=True, doc='尝试登录的用户名')

    ip_address = Column(String(45), index=True, nullable=True, doc='IP地址')

    user_agent = Column(String(500), nullable=True, doc='User-Agent')

    is_success = Column(Boolean, default=False, doc='是否成功')


    failure_reason = Column(String(255), nullable=True, doc='失败原因')

    created_at = Column(DateTime, doc='尝试时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'username': self.username,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'is_success': self.is_success,
            'failure_reason': self.failure_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<LoginAttempt id={self.id}>'


