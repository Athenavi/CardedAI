"""
SQLAlchemy 模型定义 - Article
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-07-13 11:50:46
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from . import Base  # 使用统一的 Base



class Article(Base):
    """文章模型模型"""
    __tablename__ = 'articles'


    __table_args__ = (
        Index('idx_articles_slug', 'slug', unique=True),
        Index('idx_articles_status_created', 'status', 'created_at'),
        Index('idx_articles_category_status_created', 'category', 'status', 'created_at'),
        Index('idx_articles_user_status_created', 'user', 'status', 'created_at'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='文章 ID')

    title = Column(String(255), nullable=True, doc='标题')

    slug = Column(String(255), nullable=True, doc='文章 slug')

    excerpt = Column(String(255), nullable=True, doc='摘要')

    cover_image = Column(String(255), nullable=True, doc='封面图 URL')

    category = Column(BigInteger, ForeignKey('categories.id'), nullable=True, doc='分类')


    tags_list = Column(String(255), nullable=True, doc='标签列表')

    views = Column(BigInteger, default=0, doc='浏览数')


    user = Column(BigInteger, ForeignKey('users.id'), doc='用户')


    status = Column(Integer, doc='状态(-1:已删除，0:草稿，1:已发布)')


    hidden = Column(Boolean, default=False, doc='是否隐藏')


    is_featured = Column(Boolean, default=False, doc='是否推荐')


    is_vip_only = Column(Boolean, default=False, doc='是否仅 VIP 可见')


    required_vip_level = Column(Integer, default=0, doc='所需 VIP 等级')


    article_ad = Column(String(255), nullable=True, doc='广告内容')

    scheduled_publish_at = Column(DateTime, nullable=True, doc='定时发布时间（设置为未来时间后自动发布）')

    post_type = Column(String(50), index=True, default='article', doc='内容类型(article/book/product等)')

    is_sticky = Column(Boolean, default=False, doc='是否置顶（粘性文章）')


    sticky_until = Column(DateTime, nullable=True, doc='置顶过期时间（可选，过期后自动取消置顶）')

    sort_order = Column(BigInteger, index=True, default=0, doc='排序顺序（用于拖拽排序）')


    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')

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

    # 关系定义
    revisions = relationship('ArticleRevision', back_populates='article', primaryjoin="Article.id == ArticleRevision.article_id")

    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'excerpt': self.excerpt,
            'cover_image': self.cover_image,
            'category': self.category,
            'tags_list': self.tags_list,
            'views': self.views,
            'user': self.user,
            'status': self.status,
            'hidden': self.hidden,
            'is_featured': self.is_featured,
            'is_vip_only': self.is_vip_only,
            'required_vip_level': self.required_vip_level,
            'article_ad': self.article_ad,
            'scheduled_publish_at': self.scheduled_publish_at.isoformat() if self.scheduled_publish_at else None,
            'post_type': self.post_type,
            'is_sticky': self.is_sticky,
            'sticky_until': self.sticky_until.isoformat() if self.sticky_until else None,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
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
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<Article id={self.id}>'


