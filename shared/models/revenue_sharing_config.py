"""
SQLAlchemy 模型定义 - RevenueSharingConfig
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Numeric, Index

from . import Base  # 使用统一的 Base


class RevenueSharingConfig(Base):
    """收益分成配置模型模型"""
    __tablename__ = 'revenue_sharing_configs'


    __table_args__ = (
        Index('idx_revenue_sharing_configs_type', 'revenue_type', unique=True),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='配置 ID')

    revenue_type = Column(String(50), unique=True, nullable=True, doc='收益类型')

    platform_percentage = Column(Numeric(10, 2), default=30.0, doc='平台分成百分比')


    creator_percentage = Column(Numeric(10, 2), default=70.0, doc='创作者分成百分比')


    min_payout_amount = Column(Numeric(10, 2), default=100.0, doc='最低提现金额')


    is_active = Column(Boolean, default=True, doc='是否激活')


    description = Column(Text, nullable=True, doc='配置描述')


    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'revenue_type': self.revenue_type,
            'platform_percentage': self.platform_percentage,
            'creator_percentage': self.creator_percentage,
            'min_payout_amount': self.min_payout_amount,
            'is_active': self.is_active,
            'description': self.description,
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
        return f'<RevenueSharingConfig id={self.id}>'


