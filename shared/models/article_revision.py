"""
SQLAlchemy 模型定义 - ArticleRevision
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from . import Base  # 使用统一的 Base


class ArticleRevision(Base):
    """文章修订历史模型模型"""
    __tablename__ = 'article_revisions'


    __table_args__ = (
        Index('idx_article_revisions_article_id', 'article_id'),
        Index('idx_article_revisions_number', 'revision_number'),
        Index('idx_article_revisions_created', 'created_at'),
        Index('idx_article_revisions_hash', 'hash_code'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='修订ID')

    article_id = Column(BigInteger, ForeignKey('articles.id'), doc='关联的文章ID')


    revision_number = Column(BigInteger, doc='修订版本号')


    title = Column(String(255), nullable=True, doc='修订时的标题')

    excerpt = Column(String(255), nullable=True, doc='修订时的摘要')

    content = Column(Text, nullable=False, doc='修订时的文章内容')


    cover_image = Column(String(255), nullable=True, doc='修订时的封面图')

    tags_list = Column(String(255), nullable=True, doc='修订时的标签')

    category_id = Column(BigInteger, nullable=True, doc='修订时的分类ID')


    status = Column(BigInteger, default=0, doc='修订时的文章状态')


    hidden = Column(Boolean, default=False, doc='修订时的隐藏状态')


    is_featured = Column(Boolean, default=False, doc='修订时的精选状态')


    is_vip_only = Column(Boolean, default=False, doc='修订时的VIP限制')


    required_vip_level = Column(BigInteger, default=0, doc='修订时的VIP等级要求')


    author_id = Column(BigInteger, ForeignKey('users.id'), nullable=True, doc='执行修订的用户ID')


    change_summary = Column(String(500), nullable=True, doc='修订说明/变更摘要')

    hash_code = Column(String(64), index=True, nullable=True, doc='内容哈希码（用于去重）')

    created_at = Column(DateTime, doc='修订创建时间')

    # 关系定义
    article = relationship('Article', back_populates='revisions', primaryjoin="ArticleRevision.article_id == Article.id")

    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'article_id': self.article_id,
            'revision_number': self.revision_number,
            'title': self.title,
            'excerpt': self.excerpt,
            'content': self.content,
            'cover_image': self.cover_image,
            'tags_list': self.tags_list,
            'category_id': self.category_id,
            'status': self.status,
            'hidden': self.hidden,
            'is_featured': self.is_featured,
            'is_vip_only': self.is_vip_only,
            'required_vip_level': self.required_vip_level,
            'author_id': self.author_id,
            'change_summary': self.change_summary,
            'hash_code': self.hash_code,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<ArticleRevision id={self.id}>'


