"""
SQLAlchemy 模型定义 - CartItem
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Numeric, ForeignKey, Index

from . import Base  # 使用统一的 Base


class CartItem(Base):
    """购物车项模型模型"""
    __tablename__ = 'cart_items'


    __table_args__ = (
        Index('idx_cart_items_cart', 'cart_id'),
        Index('idx_cart_items_product', 'product_id'),
        Index('idx_cart_items_unique', 'cart_id', 'product_id', unique=True),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='购物车项 ID')

    cart_id = Column(BigInteger, ForeignKey('carts.id'), doc='购物车ID')


    product_id = Column(BigInteger, ForeignKey('products.id'), doc='商品ID')


    quantity = Column(Integer, default=1, doc='数量')


    price = Column(Numeric(10, 2), doc='单价(加入购物车时的价格)')


    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'cart_id': self.cart_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'price': self.price,
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
        return f'<CartItem id={self.id}>'


