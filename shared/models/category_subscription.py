"""
SQLAlchemy 模型定义 - CategorySubscription
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey

from . import Base  # 使用统一的 Base


class CategorySubscription(Base):
    """分类订阅模型模型"""
    __tablename__ = 'category_subscriptions'




    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='订阅 ID')

    category = Column(BigInteger, ForeignKey('categories.id'), doc='分类')


    subscriber = Column(BigInteger, ForeignKey('users.id'), doc='订阅用户')


    created_at = Column(DateTime, doc='创建时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'category': self.category,
            'subscriber': self.subscriber,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<CategorySubscription id={self.id}>'


