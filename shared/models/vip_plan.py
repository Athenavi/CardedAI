"""
SQLAlchemy 模型定义 - VIPPlan
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Numeric

from . import Base  # 使用统一的 Base


class VIPPlan(Base):
    """VIP 套餐模型模型"""
    __tablename__ = 'vip_plans'




    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='套餐 ID')

    name = Column(String(100), nullable=True, doc='套餐名称')

    description = Column(String(255), nullable=True, doc='套餐描述')

    price = Column(Numeric(10, 2), doc='价格')


    original_price = Column(Numeric(10, 2), nullable=True, doc='原价')


    duration_days = Column(Integer, doc='有效期天数')


    level = Column(BigInteger, default=1, doc='VIP 等级')


    features = Column(String(255), nullable=True, doc='特权功能 JSON')

    is_active = Column(Boolean, default=True, doc='是否激活')


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
            'description': self.description,
            'price': self.price,
            'original_price': self.original_price,
            'duration_days': self.duration_days,
            'level': self.level,
            'features': self.features,
            'is_active': self.is_active,
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
        return f'<VIPPlan id={self.id}>'


