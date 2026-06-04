"""
SQLAlchemy 模型定义 - RevenueRecord
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Numeric, Index

from . import Base  # 使用统一的 Base


class RevenueRecord(Base):
    """收益记录模型模型"""
    __tablename__ = 'revenue_records'


    __table_args__ = (
        Index('idx_revenue_records_user_id', 'user_id'),
        Index('idx_revenue_records_type', 'revenue_type'),
        Index('idx_revenue_records_status', 'status'),
        Index('idx_revenue_records_created_at', 'created_at'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='收益记录 ID')

    user_id = Column(BigInteger, doc='用户ID (创作者)')


    revenue_type = Column(String(50), nullable=True, doc='收益类型: advertisement, vip_subscription, article_purchase, donation, other')

    amount = Column(Numeric(10, 2), doc='收益金额')


    platform_fee = Column(Numeric(10, 2), default=0, doc='平台手续费')


    creator_earnings = Column(Numeric(10, 2), doc='创作者实际收益')


    description = Column(Text, nullable=True, doc='收益描述')


    reference_id = Column(BigInteger, nullable=True, doc='关联记录ID (如广告ID、订单ID等)')


    reference_type = Column(String(50), nullable=True, doc='关联记录类型')

    status = Column(String(20), default='pending', doc='状态: pending, confirmed, paid')

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
            'revenue_type': self.revenue_type,
            'amount': self.amount,
            'platform_fee': self.platform_fee,
            'creator_earnings': self.creator_earnings,
            'description': self.description,
            'reference_id': self.reference_id,
            'reference_type': self.reference_type,
            'status': self.status,
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
        return f'<RevenueRecord id={self.id}>'


