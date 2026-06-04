"""
SQLAlchemy 模型定义 - Order
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Numeric, ForeignKey, Index

from . import Base  # 使用统一的 Base



class Order(Base):
    """订单模型模型"""
    __tablename__ = 'orders'


    __table_args__ = (
        Index('idx_orders_order_number', 'order_number', unique=True),
        Index('idx_orders_user', 'user_id'),
        Index('idx_orders_status', 'status'),
        Index('idx_orders_payment_status', 'payment_status'),
        Index('idx_orders_created', 'created_at'),
        Index('idx_orders_user_status_created', 'user_id', 'status', 'created_at'),
        Index('idx_orders_status_payment_created', 'status', 'payment_status', 'created_at'),
        Index('idx_orders_payment_transaction', 'transaction_id'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='订单 ID')

    order_number = Column(String(50), unique=True, nullable=True, doc='订单号')

    user_id = Column(BigInteger, ForeignKey('users.id'), doc='用户ID')

    status = Column(String(50), default='pending',
                    doc='订单状态 (pending:待支付, paid:已支付, processing:处理中, shipped:已发货, delivered:已送达, cancelled:已取消, refunded:已退款)')

    total_amount = Column(Numeric(10, 2), doc='订单总金额')


    shipping_amount = Column(Numeric(10, 2), default=0, doc='运费')


    discount_amount = Column(Numeric(10, 2), default=0, doc='折扣金额')

    payment_method = Column(String(50), nullable=True, doc='支付方式')

    payment_status = Column(String(50), default='pending',
                            doc='支付状态 (pending:待支付, paid:已支付, failed:支付失败, refunded:已退款)')

    transaction_id = Column(String(255), nullable=True, doc='交易ID')

    shipping_address = Column(String(255), nullable=True, doc='收货地址(JSON格式)')

    billing_address = Column(String(255), nullable=True, doc='账单地址(JSON格式)')

    notes = Column(Text, nullable=True, doc='订单备注')


    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')

    paid_at = Column(DateTime, nullable=True, doc='支付时间')

    shipped_at = Column(DateTime, nullable=True, doc='发货时间')

    delivered_at = Column(DateTime, nullable=True, doc='送达时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'order_number': self.order_number,
            'user_id': self.user_id,
            'status': self.status,
            'total_amount': self.total_amount,
            'shipping_amount': self.shipping_amount,
            'discount_amount': self.discount_amount,
            'payment_method': self.payment_method,
            'payment_status': self.payment_status,
            'transaction_id': self.transaction_id,
            'shipping_address': self.shipping_address,
            'billing_address': self.billing_address,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'shipped_at': self.shipped_at.isoformat() if self.shipped_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<Order id={self.id}>'


