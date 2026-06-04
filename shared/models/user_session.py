"""
SQLAlchemy 模型定义 - UserSession
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base


class UserSession(Base):
    """用户会话模型模型"""
    __tablename__ = 'user_sessions'


    __table_args__ = (
        Index('idx_user_sessions_user_id', 'user_id'),
        Index('idx_user_access_token', 'access_token', unique=True),
        Index('idx_user_sessions_is_active', 'is_active'),
        Index('idx_user_sessions_expires', 'expires_at'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='会话 ID')

    user_id = Column(BigInteger, ForeignKey('users.id'), doc='用户ID')


    access_token = Column(String(255), unique=True, nullable=True, doc='会话令牌')

    refresh_token = Column(String(255), index=True, nullable=True, doc='会话刷新令牌（不唯一 扫码的登录依赖）')

    device_info = Column(String(500), nullable=True, doc='设备信息（User-Agent）')

    ip_address = Column(String(45), nullable=True, doc='IP地址')

    location = Column(String(100), nullable=True, doc='地理位置')

    is_active = Column(Boolean, default=True, doc='是否活跃')


    last_activity = Column(DateTime, doc='最后活动时间')

    expires_at = Column(DateTime, doc='过期时间')

    created_at = Column(DateTime, doc='创建时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'device_info': self.device_info,
            'ip_address': self.ip_address,
            'location': self.location,
            'is_active': self.is_active,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<UserSession id={self.id}>'


