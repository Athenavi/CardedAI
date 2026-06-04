"""
SQLAlchemy 模型定义 - Comment
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Numeric, ForeignKey, Index

from . import Base  # 使用统一的 Base


class Comment(Base):
    """评论模型模型"""
    __tablename__ = 'comments'


    __table_args__ = (
        Index('idx_comments_article_id', 'article_id'),
        Index('idx_comments_user_id', 'user_id'),
        Index('idx_comments_parent_id', 'parent_id'),
        Index('idx_comments_is_approved', 'is_approved'),
        Index('idx_comments_created_at', 'created_at'),
        Index('idx_comments_article_approved_created', 'article_id', 'is_approved', 'created_at'),
        Index('idx_comments_user_created', 'user_id', 'created_at'),
        Index('idx_comments_email', 'author_email'),
        Index('idx_comments_spam_score', 'spam_score'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='评论 ID')

    article_id = Column(BigInteger, ForeignKey('articles.id'), doc='文章 ID')


    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=True, doc='用户 ID（访客评论可为空）')


    parent_id = Column(BigInteger, ForeignKey('comments.id'), nullable=True, doc='父评论 ID（用于回复）')


    content = Column(Text, nullable=False, doc='评论内容')


    author_name = Column(String(100), nullable=True, doc='作者姓名（访客填写）')

    author_email = Column(String(255), nullable=True, doc='作者邮箱（访客填写）')

    author_url = Column(String(500), nullable=True, doc='作者网站（访客填写）')

    author_ip = Column(String(45), nullable=True, doc='作者 IP 地址')

    user_agent = Column(String(500), nullable=True, doc='用户代理')

    is_approved = Column(Boolean, default=True, doc='是否已审核通过')


    likes = Column(BigInteger, default=0, doc='点赞数')


    spam_score = Column(Numeric(10, 2), nullable=True, doc='垃圾评分')


    spam_reasons = Column(String(255), nullable=True, doc='垃圾检测原因（JSON格式）')

    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'article_id': self.article_id,
            'user_id': self.user_id,
            'parent_id': self.parent_id,
            'content': self.content,
            'author_name': self.author_name,
            'author_email': self.author_email,
            'author_url': self.author_url,
            'author_ip': self.author_ip,
            'user_agent': self.user_agent,
            'is_approved': self.is_approved,
            'likes': self.likes,
            'spam_score': self.spam_score,
            'spam_reasons': self.spam_reasons,
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
        return f'<Comment id={self.id}>'


