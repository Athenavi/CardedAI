"""
SQLAlchemy 模型定义 - PaymentTransaction
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Numeric, ForeignKey, Index

from . import Base  # 使用统一的 Base



class PaymentTransaction(Base):
    """支付交易记录模型模型"""
    __tablename__ = 'payment_transactions'


    __table_args__ = (
        Index('idx_payment_transaction_user', 'user'),
        Index('idx_payment_transaction_order', 'order_id'),
        Index('idx_payment_transaction_status', 'status'),
        Index('idx_payment_transaction_created', 'created_at'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='交易 ID')

    user = Column(BigInteger, ForeignKey('users.id'), doc='用户')


    order_id = Column(String(100), nullable=True, doc='订单ID')

    gateway = Column(BigInteger, ForeignKey('payment_gateways.id'), doc='支付网关')


    amount = Column(Numeric(10, 2), doc='金额')


    currency = Column(String(3), default='USD', doc='货币类型')

    status = Column(String(20), default='pending', doc='交易状态')

    transaction_id = Column(String(100), nullable=True, doc='第三方支付交易ID')

    payment_method = Column(String(50), nullable=True, doc='支付方式')

    extra_metadata = Column('metadata', Text, nullable=True, doc='附加元数据 (JSON格式)')


    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'user': self.user,
            'order_id': self.order_id,
            'gateway': self.gateway,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status,
            'transaction_id': self.transaction_id,
            'payment_method': self.payment_method,
            'extra_metadata': self.extra_metadata,
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
        return f'<PaymentTransaction id={self.id}>'
