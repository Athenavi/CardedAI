"""
SQLAlchemy 模型定义 - Site
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Index

from . import Base  # 使用统一的 Base


class Site(Base):
    """站点模型模型"""
    __tablename__ = 'sites'


    __table_args__ = (
        Index('idx_sites_slug', 'slug'),
        Index('idx_sites_domain', 'domain'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='站点 ID')

    name = Column(String(255), nullable=True, doc='站点名称')

    slug = Column(String(100), unique=True, nullable=True, doc='站点标识')

    domain = Column(String(255), unique=True, nullable=True, doc='主域名')

    additional_domains = Column(Text, nullable=True, doc='附加域名列表（JSON格式）')

    description = Column(Text, nullable=True, doc='站点描述')

    logo_url = Column(String(500), nullable=True, doc='Logo URL')

    favicon_url = Column(String(500), nullable=True, doc='Favicon URL')

    theme = Column(String(100), default='default', doc='主题')

    language = Column(String(10), default='en', doc='语言')

    timezone = Column(String(50), default='UTC', doc='时区')

    settings = Column(Text, nullable=True, doc='站点设置（JSON格式）')


    is_active = Column(Boolean, default=True, doc='是否激活')


    is_default = Column(Boolean, default=False, doc='是否为默认站点')


    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'domain': self.domain,
            'additional_domains': self.additional_domains,
            'description': self.description,
            'logo_url': self.logo_url,
            'favicon_url': self.favicon_url,
            'theme': self.theme,
            'language': self.language,
            'timezone': self.timezone,
            'settings': self.settings,
            'is_active': self.is_active,
            'is_default': self.is_default,
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
        return f'<Site id={self.id}>'


