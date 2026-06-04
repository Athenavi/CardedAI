"""
SQLAlchemy 模型定义 - OAuthAccount
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base


class OAuthAccount(Base):
    """OAuth 第三方登录账号关联模型模型"""
    __tablename__ = 'oauth_accounts'


    __table_args__ = (
        Index('idx_oauth_accounts_provider_user', 'provider', 'provider_user_id', unique=True),
        Index('idx_oauth_accounts_user_provider', 'user_id', 'provider', unique=True),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='主键ID')

    user_id = Column(BigInteger, ForeignKey('users.id'), doc='关联的用户ID')


    provider = Column(String(50), index=True, nullable=True, doc='OAuth提供商(github/google/wechat/qq/weibo)')

    provider_user_id = Column(String(255), index=True, nullable=True, doc='第三方平台的用户ID')

    access_token = Column(String(255), nullable=True, doc='访问令牌（加密存储）')

    refresh_token = Column(String(255), nullable=True, doc='刷新令牌（加密存储）')

    token_expires_at = Column(DateTime, nullable=True, doc='Token过期时间')

    extra_data = Column(String(255), nullable=True, doc='额外数据（JSON格式，存储头像、昵称等）')

    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'provider': self.provider,
            'provider_user_id': self.provider_user_id,
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'token_expires_at': self.token_expires_at.isoformat() if self.token_expires_at else None,
            'extra_data': self.extra_data,
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
        return f'<OAuthAccount id={self.id}>'


