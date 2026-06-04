"""
SQLAlchemy 模型定义 - ArticleAnnotation
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base



class ArticleAnnotation(Base):
    """文章批注模型（支持协作编辑时的评论和批注）模型"""
    __tablename__ = 'article_annotations'


    __table_args__ = (
        Index('idx_article_annotations_article', 'article'),
        Index('idx_article_annotations_user', 'user'),
        Index('idx_article_annotations_parent', 'parent'),
        Index('idx_article_annotations_resolved', 'is_resolved'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='批注 ID')

    article = Column(BigInteger, ForeignKey('articles.id'), doc='文章 ID')


    user = Column(BigInteger, ForeignKey('users.id'), doc='创建者')


    parent = Column(BigInteger, ForeignKey('article_annotations.id'), nullable=True, doc='父批注 ID（用于回复）')


    content = Column(Text, nullable=False, doc='批注内容')


    position = Column(Text, nullable=True, doc='批注位置（JSON格式，包含start/end等）')


    selection_text = Column(String(500), nullable=True, doc='选中的文本片段')

    is_resolved = Column(Boolean, default=False, doc='是否已解决')


    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'article': self.article,
            'user': self.user,
            'parent': self.parent,
            'content': self.content,
            'position': self.position,
            'selection_text': self.selection_text,
            'is_resolved': self.is_resolved,
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
        return f'<ArticleAnnotation id={self.id}>'
