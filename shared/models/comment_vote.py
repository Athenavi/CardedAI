"""
SQLAlchemy 模型定义 - CommentVote
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base


class CommentVote(Base):
    """评论投票模型模型"""
    __tablename__ = 'comment_votes'


    __table_args__ = (
        Index('idx_comment_votes_comment_user', 'comment_id', 'user', unique=True),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='投票 ID')

    comment_id = Column(BigInteger, index=True, doc='评论 ID')


    user = Column(BigInteger, ForeignKey('users.id'), nullable=True, doc='用户 ID（匿名投票可为空）')


    vote_type = Column(Integer, doc='投票类型 (1: 赞, -1: 踩)')


    ip_address = Column(String(45), nullable=True, doc='IP 地址（用于防刷）')

    created_at = Column(DateTime, doc='投票时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'comment_id': self.comment_id,
            'user': self.user,
            'vote_type': self.vote_type,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<CommentVote id={self.id}>'


