"""
SQLAlchemy 模型定义 - UserBlock
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base


class UserBlock(Base):
    """用户屏蔽/拉黑模型模型"""
    __tablename__ = 'user_blocks'


    __table_args__ = (
        Index('idx_user_blocks_unique', 'blocker', 'blocked_user', unique=True),
        Index('idx_user_blocks_blocker', 'blocker'),
        Index('idx_user_blocks_blocked', 'blocked_user'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='屏蔽记录ID')

    blocker = Column(BigInteger, ForeignKey('users.id'), doc='屏蔽者用户ID')


    blocked_user = Column(BigInteger, ForeignKey('users.id'), doc='被屏蔽用户ID')


    reason = Column(String(500), nullable=True, doc='屏蔽原因')

    created_at = Column(DateTime, doc='屏蔽时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'blocker': self.blocker,
            'blocked_user': self.blocked_user,
            'reason': self.reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<UserBlock id={self.id}>'


