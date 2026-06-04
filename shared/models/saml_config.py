"""
SQLAlchemy 模型定义 - SAMLConfig
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base



class SAMLConfig(Base):
    """SAML 2.0 配置模型模型"""
    __tablename__ = 'saml_configs'


    __table_args__ = (
        Index('idx_saml_config_site', 'site_id'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='配置 ID')

    site_id = Column(BigInteger, ForeignKey('sites.id'), nullable=True, doc='关联的站点 ID（为空表示全局配置）')


    entity_id = Column(String(255), nullable=True, doc='SAML Entity ID (SP Identifier)')

    acs_url = Column(String(500), nullable=True, doc='Assertion Consumer Service URL')

    slo_url = Column(String(500), nullable=True, doc='Single Logout Service URL')

    idp_entity_id = Column(String(255), nullable=True, doc='Identity Provider Entity ID')

    idp_sso_url = Column(String(500), nullable=True, doc='IdP SSO URL')

    idp_slo_url = Column(String(500), nullable=True, doc='IdP SLO URL')

    idp_certificate = Column(Text, nullable=False, doc='IdP X.509 Certificate (PEM格式)')


    sp_private_key = Column(Text, nullable=True, doc='SP Private Key (PEM格式)')


    sp_certificate = Column(Text, nullable=True, doc='SP Certificate (PEM格式)')

    attribute_mapping = Column(Text, nullable=True, doc='属性映射配置（JSON格式）')

    enable_slo = Column(Boolean, default=False, doc='是否启用单点登出')

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
            'entity_id': self.entity_id,
            'acs_url': self.acs_url,
            'slo_url': self.slo_url,
            'idp_entity_id': self.idp_entity_id,
            'idp_sso_url': self.idp_sso_url,
            'idp_slo_url': self.idp_slo_url,
            'idp_certificate': self.idp_certificate,
            'sp_private_key': self.sp_private_key,
            'sp_certificate': self.sp_certificate,
            'attribute_mapping': self.attribute_mapping,
            'enable_slo': self.enable_slo,
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
        return f'<SAMLConfig id={self.id}>'
