"""
SQLAlchemy 模型定义 - CustomPostType
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Index

from . import Base  # 使用统一的 Base


class CustomPostType(Base):
    """自定义内容类型模型模型"""
    __tablename__ = 'custom_post_types'


    __table_args__ = (
        Index('idx_cpt_slug', 'slug', unique=True),
        Index('idx_cpt_is_active', 'is_active'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='内容类型ID')

    name = Column(String(100), nullable=True, doc='内容类型名称')

    slug = Column(String(100), unique=True, nullable=True, doc='内容类型标识')

    description = Column(String(255), nullable=True, doc='描述')

    supports = Column(String(255), nullable=True, doc='支持的功能(JSON数组)')

    has_archive = Column(Boolean, default=False, doc='是否有归档页')


    menu_icon = Column(String(255), nullable=True, doc='菜单图标')

    menu_position = Column(Integer, default=5, doc='菜单位置')


    is_active = Column(Boolean, default=True, doc='是否激活')


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
            'description': self.description,
            'supports': self.supports,
            'has_archive': self.has_archive,
            'menu_icon': self.menu_icon,
            'menu_position': self.menu_position,
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
        return f'<CustomPostType id={self.id}>'


