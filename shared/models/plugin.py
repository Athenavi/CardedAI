"""
SQLAlchemy 模型定义 - Plugin
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Index

from . import Base  # 使用统一的 Base


class Plugin(Base):
    """插件模型模型"""
    __tablename__ = 'plugins'


    __table_args__ = (
        Index('idx_plugins_slug', 'slug', unique=True),
        Index('idx_plugins_is_active', 'is_active'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='插件ID')

    name = Column(String(100), nullable=True, doc='插件名称')

    slug = Column(String(100), unique=True, nullable=True, doc='插件唯一标识')

    version = Column(String(20), nullable=True, doc='插件版本')

    description = Column(String(255), nullable=True, doc='插件描述')

    author = Column(String(100), nullable=True, doc='插件作者')

    author_url = Column(String(255), nullable=True, doc='作者网站')

    plugin_url = Column(String(255), nullable=True, doc='插件官网')

    is_active = Column(Boolean, default=False, doc='是否激活')


    is_installed = Column(Boolean, default=True, doc='是否已安装')


    settings = Column(Text, nullable=True, doc='插件配置（JSON格式）')


    priority = Column(Integer, default=0, doc='执行优先级')


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
            'plugin_url': self.plugin_url,
            'is_active': self.is_active,
            'is_installed': self.is_installed,
            'settings': self.settings,
            'priority': self.priority,
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
        return f'<Plugin id={self.id}>'


