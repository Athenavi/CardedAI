"""
SQLAlchemy 模型定义 - Category
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Index

from . import Base  # 使用统一的 Base


class Category(Base):
    """分类模型模型"""
    __tablename__ = 'categories'


    __table_args__ = (
        Index('idx_categories_slug', 'slug', unique=True),
        Index('idx_categories_parent', 'parent_id'),
        Index('idx_categories_sort_order', 'sort_order'),
        Index('idx_categories_is_visible', 'is_visible'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='分类 ID')

    name = Column(String(100), nullable=True, doc='分类名')

    slug = Column(String(255), nullable=True, doc='分类 slug')

    description = Column(String(255), nullable=True, doc='分类描述')

    parent_id = Column(BigInteger, nullable=True, doc='父分类 ID')


    sort_order = Column(BigInteger, default=0, doc='排序')


    icon = Column(String(255), nullable=True, doc='图标')

    color = Column(String(255), nullable=True, doc='颜色')

    is_visible = Column(Boolean, default=True, doc='是否可见')


    articles_count = Column(BigInteger, doc='分类下的文章数量')


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
            'parent_id': self.parent_id,
            'sort_order': self.sort_order,
            'icon': self.icon,
            'color': self.color,
            'is_visible': self.is_visible,
            'articles_count': self.articles_count,
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
        return f'<Category id={self.id}>'


