"""
SQLAlchemy 模型定义 - Product
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Numeric, ForeignKey, Index

from . import Base  # 使用统一的 Base


class Product(Base):
    """商品模型模型"""
    __tablename__ = 'products'


    __table_args__ = (
        Index('idx_products_slug', 'slug', unique=True),
        Index('idx_products_category', 'category_id'),
        Index('idx_products_is_active', 'is_active'),
        Index('idx_products_sku', 'sku'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='商品 ID')

    name = Column(String(255), nullable=True, doc='商品名称')

    slug = Column(String(255), unique=True, nullable=True, doc='商品标识')

    description = Column(Text, nullable=True, doc='商品描述')


    price = Column(Numeric(10, 2), doc='价格')


    original_price = Column(Numeric(10, 2), nullable=True, doc='原价')


    stock = Column(Integer, default=0, doc='库存数量')


    sku = Column(String(100), index=True, nullable=True, doc='SKU编码')

    images = Column(Text, nullable=True, doc='商品图片(JSON数组)')


    category_id = Column(BigInteger, ForeignKey('categories.id'), nullable=True, doc='分类ID')


    is_active = Column(Boolean, default=True, doc='是否上架')


    is_featured = Column(Boolean, default=False, doc='是否推荐')


    weight = Column(Numeric(10, 2), nullable=True, doc='重量(kg)')


    dimensions = Column(Text, nullable=True, doc='尺寸(长x宽x高,JSON格式)')


    attributes = Column(Text, nullable=True, doc='商品属性(JSON格式)')


    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'price': self.price,
            'original_price': self.original_price,
            'stock': self.stock,
            'sku': self.sku,
            'images': self.images,
            'category_id': self.category_id,
            'is_active': self.is_active,
            'is_featured': self.is_featured,
            'weight': self.weight,
            'dimensions': self.dimensions,
            'attributes': self.attributes,
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
        return f'<Product id={self.id}>'


