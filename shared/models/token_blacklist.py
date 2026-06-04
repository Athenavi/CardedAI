"""
SQLAlchemy 模型定义 - TokenBlacklist
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import event
from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Index

from . import Base  # 使用统一的 Base


class TokenBlacklist(Base):
    """Token 黑名单模型（UNLOGGED 表，用于存储被撤销的 JWT Token）模型"""
    __tablename__ = 'token_blacklist'


    __table_args__ = (
        Index('idx_token_blacklist_expires', 'expires_at'),
        Index('idx_token_blacklist_created', 'created_at'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='ID')

    token_identifier = Column(String(64), unique=True, nullable=True, doc='Token 唯一标识符（token 前32个字符）')

    token_hash = Column(String(128), nullable=True, doc='Token 哈希值（用于调试和审计）')

    expires_at = Column(DateTime, doc='Token 过期时间')

    created_at = Column(DateTime, doc='创建时间')

    reason = Column(String(255), nullable=True, doc='撤销原因')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'token_identifier': self.token_identifier,
            'token_hash': self.token_hash,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'reason': self.reason,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<TokenBlacklist id={self.id}>'

# UNLOGGED 表监听器（PostgreSQL 专用）
@event.listens_for(TokenBlacklist.__table__, "after_create")
def _set_tokenblacklist_unlogged(target, connection, **kw):
    connection.execute(f"ALTER TABLE {target.name} SET UNLOGGED")

