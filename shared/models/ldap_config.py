"""
SQLAlchemy 模型定义 - LDAPConfig
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base



class LDAPConfig(Base):
    """LDAP 配置模型模型"""
    __tablename__ = 'ldap_configs'


    __table_args__ = (
        Index('idx_ldap_config_site', 'site_id'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='配置 ID')

    site_id = Column(BigInteger, ForeignKey('sites.id'), nullable=True, doc='关联的站点 ID（为空表示全局配置）')


    server_url = Column(String(500), nullable=True, doc='LDAP 服务器 URL (ldap://或ldaps://)')

    bind_dn = Column(String(255), nullable=True, doc='Bind DN (用于查询的用户)')

    bind_password = Column(String(255), nullable=True, doc='Bind Password')

    base_dn = Column(String(255), nullable=True, doc='Base DN (搜索起点)')

    user_filter = Column(String(255), default='(objectClass=inetOrgPerson)', doc='用户过滤器')

    username_attribute = Column(String(100), default='uid', doc='用户名属性')

    email_attribute = Column(String(100), default='mail', doc='邮箱属性')

    first_name_attribute = Column(String(100), default='givenName', doc='名字属性')

    last_name_attribute = Column(String(100), default='sn', doc='姓氏属性')

    use_ssl = Column(Boolean, default=False, doc='是否使用 SSL/TLS')


    verify_certificates = Column(Boolean, default=True, doc='是否验证证书')


    auto_sync_users = Column(Boolean, default=False, doc='是否自动同步用户')

    sync_interval = Column(Integer, default=3600, doc='同步间隔（秒）')

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
            'server_url': self.server_url,
            'bind_dn': self.bind_dn,
            'bind_password': self.bind_password,
            'base_dn': self.base_dn,
            'user_filter': self.user_filter,
            'username_attribute': self.username_attribute,
            'email_attribute': self.email_attribute,
            'first_name_attribute': self.first_name_attribute,
            'last_name_attribute': self.last_name_attribute,
            'use_ssl': self.use_ssl,
            'verify_certificates': self.verify_certificates,
            'auto_sync_users': self.auto_sync_users,
            'sync_interval': self.sync_interval,
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
        return f'<LDAPConfig id={self.id}>'
