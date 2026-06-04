"""
SQLAlchemy 模型定义 - CommentSubscription
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base


class CommentSubscription(Base):
    """评论订阅模型模型"""
    __tablename__ = 'comment_subscriptions'


    __table_args__ = (
        Index('idx_comment_subscriptions_article', 'article_id'),
        Index('idx_comment_subscriptions_email', 'email'),
        Index('idx_comment_subscriptions_user', 'user_id'),
        Index('idx_comment_subscriptions_unique', 'article_id', 'email', unique=True),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='订阅 ID')

    article_id = Column(BigInteger, index=True, doc='文章 ID')


    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=True, doc='用户 ID（访客订阅可为空）')


    email = Column(String(255), nullable=True, doc='订阅邮箱')

    notify_type = Column(String(255), default='new_comment', doc='通知类型 (new_comment: 新评论, reply_to_me: 回复我, all_replies: 所有回复)')

    is_active = Column(Boolean, default=True, doc='是否激活')


    confirm_token = Column(String(64), nullable=True, doc='确认token（用于访客验证）')

    confirmed_at = Column(DateTime, nullable=True, doc='确认时间')

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
            'email': self.email,
            'notify_type': self.notify_type,
            'is_active': self.is_active,
            'confirm_token': self.confirm_token,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
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
        return f'<CommentSubscription id={self.id}>'


