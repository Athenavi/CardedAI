"""
SQLAlchemy 模型定义 - Pages
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Index

from . import Base  # 使用统一的 Base


class Pages(Base):
    """页面模型模型"""
    __tablename__ = 'pages'


    __table_args__ = (
        Index('idx_pages_slug', 'slug', unique=True),
        Index('idx_pages_status', 'status'),
        Index('idx_pages_author_id', 'author_id'),
        Index('idx_pages_parent_id', 'parent_id'),
        Index('idx_pages_order', 'order_index'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='页面 ID')

    title = Column(String(255), nullable=True, doc='标题')

    slug = Column(String(255), nullable=True, doc='页面 slug')

    content = Column(String(255), nullable=True, doc='页面内容')

    excerpt = Column(String(255), nullable=True, doc='摘要')

    template = Column(String(255), nullable=True, doc='模板')

    status = Column(BigInteger, default=0, doc='状态')


    author_id = Column(BigInteger, nullable=True, doc='作者 ID')


    parent_id = Column(BigInteger, nullable=True, doc='父页面 ID')


    order_index = Column(Integer, default=0, doc='排序索引')


    meta_title = Column(String(255), nullable=True, doc='元标题')

    meta_description = Column(String(255), nullable=True, doc='元描述')

    meta_keywords = Column(String(255), nullable=True, doc='元关键词')

    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')

    published_at = Column(DateTime, nullable=True, doc='发布时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'content': self.content,
            'excerpt': self.excerpt,
            'template': self.template,
            'status': self.status,
            'author_id': self.author_id,
            'parent_id': self.parent_id,
            'order_index': self.order_index,
            'meta_title': self.meta_title,
            'meta_description': self.meta_description,
            'meta_keywords': self.meta_keywords,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<Pages id={self.id}>'


