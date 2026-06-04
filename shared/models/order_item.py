"""
SQLAlchemy 模型定义 - OrderItem
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Numeric, ForeignKey, Index

from . import Base  # 使用统一的 Base


class OrderItem(Base):
    """订单项模型模型"""
    __tablename__ = 'order_items'


    __table_args__ = (
        Index('idx_order_item_order', 'order'),
        Index('idx_order_item_product', 'product_id'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='订单项 ID')

    order = Column(BigInteger, ForeignKey('orders.id'), doc='订单')


    product_id = Column(BigInteger, nullable=True, doc='产品ID')


    product_name = Column(String(255), nullable=True, doc='产品名称')

    quantity = Column(Integer, default=1, doc='数量')

    unit_price = Column(Numeric(10, 2), doc='单价')

    total_price = Column(Numeric(10, 2), doc='总价')

    extra_metadata = Column('metadata', Text, nullable=True, doc='附加信息 (JSON格式)')


    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'order': self.order,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total_price': self.total_price,
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
        return f'<OrderItem id={self.id}>'


