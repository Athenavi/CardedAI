"""
SQLAlchemy 模型定义 - UserRevenueStats
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Numeric, Index

from . import Base  # 使用统一的 Base


class UserRevenueStats(Base):
    """用户收益统计模型模型"""
    __tablename__ = 'user_revenue_stats'


    __table_args__ = (
        Index('idx_user_revenue_stats_user_id', 'user_id', unique=True),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='统计 ID')

    user_id = Column(BigInteger, doc='用户ID')


    total_earnings = Column(Numeric(10, 2), default=0, doc='总收益')


    total_paid = Column(Numeric(10, 2), default=0, doc='已支付金额')


    pending_earnings = Column(Numeric(10, 2), default=0, doc='待结算收益')


    available_balance = Column(Numeric(10, 2), default=0, doc='可用余额')


    last_payout_at = Column(DateTime, nullable=True, doc='最后提现时间')

    updated_at = Column(DateTime, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'total_earnings': self.total_earnings,
            'total_paid': self.total_paid,
            'pending_earnings': self.pending_earnings,
            'available_balance': self.available_balance,
            'last_payout_at': self.last_payout_at.isoformat() if self.last_payout_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<UserRevenueStats id={self.id}>'


