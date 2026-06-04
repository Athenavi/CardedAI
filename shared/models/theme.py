"""
SQLAlchemy 模型定义 - Theme
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Index

from . import Base  # 使用统一的 Base


class Theme(Base):
    """主题模型模型"""
    __tablename__ = 'themes'


    __table_args__ = (
        Index('idx_themes_slug', 'slug', unique=True),
        Index('idx_themes_is_active', 'is_active'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='主题ID')

    name = Column(String(100), nullable=True, doc='主题名称')

    slug = Column(String(100), unique=True, nullable=True, doc='主题唯一标识')

    version = Column(String(20), nullable=True, doc='主题版本')

    description = Column(String(255), nullable=True, doc='主题描述')

    author = Column(String(100), nullable=True, doc='主题作者')

    author_url = Column(String(255), nullable=True, doc='作者网站')

    theme_url = Column(String(255), nullable=True, doc='主题官网')

    screenshot = Column(String(500), nullable=True, doc='主题截图路径')

    tags = Column(String(255), nullable=True, doc='标签列表（JSON格式）')

    requires = Column(String(255), nullable=True, doc='依赖要求（JSON格式）')

    settings_schema = Column(String(255), nullable=True, doc='设置架构（JSON格式）')

    theme_path = Column(String(500), nullable=True, doc='主题文件路径')

    is_active = Column(Boolean, default=False, doc='是否为当前激活主题')


    is_installed = Column(Boolean, default=True, doc='是否已安装')


    settings = Column(String(255), nullable=True, doc='主题配置（JSON格式）')

    supports = Column(String(255), nullable=True, doc='支持的功能（JSON数组）')

    created_at = Column(DateTime, doc='安装时间')

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
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'author_url': self.author_url,
            'theme_url': self.theme_url,
            'screenshot': self.screenshot,
            'tags': self.tags,
            'requires': self.requires,
            'settings_schema': self.settings_schema,
            'theme_path': self.theme_path,
            'is_active': self.is_active,
            'is_installed': self.is_installed,
            'settings': self.settings,
            'supports': self.supports,
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
        return f'<Theme id={self.id}>'


