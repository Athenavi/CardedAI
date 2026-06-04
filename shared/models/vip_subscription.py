"""
SQLAlchemy 模型定义 - VIPSubscription
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Numeric, ForeignKey

from . import Base  # 使用统一的 Base


class VIPSubscription(Base):
    """VIP 订阅模型模型"""
    __tablename__ = 'vip_subscriptions'




    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='订阅 ID')

    user = Column(BigInteger, ForeignKey('users.id'), doc='用户')


    plan = Column(Integer, ForeignKey('vip_plans.id'), doc='套餐')


    starts_at = Column(DateTime, doc='开始时间')

    expires_at = Column(DateTime, doc='过期时间')

    status = Column(BigInteger, default=0, doc='状态')


    payment_amount = Column(Numeric(10, 2), nullable=True, doc='实际支付金额')


    transaction_id = Column(String(255), nullable=True, doc='支付交易 ID')

    created_at = Column(DateTime, doc='创建时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'user': self.user,
            'plan': self.plan,
            'starts_at': self.starts_at.isoformat() if self.starts_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'status': self.status,
            'payment_amount': self.payment_amount,
            'transaction_id': self.transaction_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<VIPSubscription id={self.id}>'


