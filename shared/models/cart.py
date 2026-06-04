"""
SQLAlchemy 模型定义 - Cart
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base


class Cart(Base):
    """购物车模型模型"""
    __tablename__ = 'carts'


    __table_args__ = (
        Index('idx_carts_user', 'user_id'),
        Index('idx_carts_session', 'session_id'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='购物车 ID')

    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=True, doc='用户ID(访客可为空)')


    session_id = Column(String(255), index=True, nullable=True, doc='会话ID(用于访客购物车)')

    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'session_id': self.session_id,
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
        return f'<Cart id={self.id}>'


