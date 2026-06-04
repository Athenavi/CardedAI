"""
SQLAlchemy 模型定义 - SSOProvider
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base



class SSOProvider(Base):
    """SSO 提供商配置模型模型"""
    __tablename__ = 'sso_providers'


    __table_args__ = (
        Index('idx_sso_provider_type', 'provider_type'),
        Index('idx_sso_provider_site', 'site_id'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='配置 ID')

    site_id = Column(BigInteger, ForeignKey('sites.id'), nullable=True, doc='关联的站点 ID（为空表示全局配置）')


    provider_type = Column(String(50), nullable=True, doc='提供商类型（oauth2/saml/custom）')

    name = Column(String(100), nullable=True, doc='提供商名称')

    client_id = Column(String(255), nullable=True, doc='Client ID')

    client_secret = Column(String(255), nullable=True, doc='Client Secret')

    authorization_url = Column(String(500), nullable=True, doc='Authorization URL')

    token_url = Column(String(500), nullable=True, doc='Token URL')

    userinfo_url = Column(String(500), nullable=True, doc='User Info URL')

    scope = Column(String(255), default='openid profile email', doc='OAuth Scope')

    redirect_uri = Column(String(500), nullable=True, doc='Redirect URI')

    attribute_mapping = Column(Text, nullable=True, doc='属性映射（JSON格式）')


    auto_provision_users = Column(Boolean, default=True, doc='是否自动创建用户')


    default_role = Column(String(50), default='subscriber', doc='新用户默认角色')

    is_active = Column(Boolean, default=False, doc='是否激活')

    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')

    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'site_id': self.site_id,
            'provider_type': self.provider_type,
            'name': self.name,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'authorization_url': self.authorization_url,
            'token_url': self.token_url,
            'userinfo_url': self.userinfo_url,
            'scope': self.scope,
            'redirect_uri': self.redirect_uri,
            'attribute_mapping': self.attribute_mapping,
            'auto_provision_users': self.auto_provision_users,
            'default_role': self.default_role,
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
        return f'<SSOProvider id={self.id}>'
