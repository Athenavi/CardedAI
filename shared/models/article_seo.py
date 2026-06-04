"""
SQLAlchemy 模型定义 - ArticleSEO
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from . import Base  # 使用统一的 Base


class ArticleSEO(Base):
    """文章SEO元数据模型模型"""
    __tablename__ = 'article_seo'


    __table_args__ = (
        Index('idx_article_seo_article_id', 'article_id', unique=True),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='SEO记录ID')

    article_id = Column(BigInteger, ForeignKey('articles.id'), doc='关联的文章ID')


    seo_title = Column(String(255), nullable=True, doc='SEO标题')

    seo_description = Column(Text, nullable=True, doc='SEO描述')


    seo_keywords = Column(String(500), nullable=True, doc='SEO关键词')

    og_title = Column(String(255), nullable=True, doc='Open Graph标题')

    og_description = Column(Text, nullable=True, doc='Open Graph描述')


    og_image = Column(String(500), nullable=True, doc='Open Graph图片')

    og_type = Column(String(50), default='article', doc='Open Graph类型')

    twitter_title = Column(String(255), nullable=True, doc='Twitter Card标题')

    twitter_description = Column(Text, nullable=True, doc='Twitter Card描述')


    twitter_image = Column(String(500), nullable=True, doc='Twitter Card图片')

    twitter_card = Column(String(50), default='summary_large_image', doc='Twitter Card类型')

    canonical_url = Column(String(500), nullable=True, doc='规范URL')

    robots_meta = Column(String(100), default='index,follow', doc='Robots元标签')

    schema_org_enabled = Column(Boolean, default=True, doc='是否启用Schema.org')


    schema_org_type = Column(String(50), default='BlogPosting', doc='Schema.org类型')

    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')

    # 关系定义
    article = relationship('Article', back_populates='seo_data', primaryjoin="ArticleSEO.article_id == Article.id")

    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'article_id': self.article_id,
            'seo_title': self.seo_title,
            'seo_description': self.seo_description,
            'seo_keywords': self.seo_keywords,
            'og_title': self.og_title,
            'og_description': self.og_description,
            'og_image': self.og_image,
            'og_type': self.og_type,
            'twitter_title': self.twitter_title,
            'twitter_description': self.twitter_description,
            'twitter_image': self.twitter_image,
            'twitter_card': self.twitter_card,
            'canonical_url': self.canonical_url,
            'robots_meta': self.robots_meta,
            'schema_org_enabled': self.schema_org_enabled,
            'schema_org_type': self.schema_org_type,
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
        return f'<ArticleSEO id={self.id}>'


