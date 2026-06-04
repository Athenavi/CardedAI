"""
SQLAlchemy 模型定义 - PaymentGateway
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Index

from . import Base  # 使用统一的 Base



class PaymentGateway(Base):
    """支付网关配置模型模型"""
    __tablename__ = 'payment_gateways'


    __table_args__ = (
        Index('idx_payment_gateway_provider', 'provider'),
        Index('idx_payment_gateway_active', 'is_active'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='支付网关 ID')

    name = Column(String(100), nullable=True, doc='支付网关名称')

    provider = Column(String(50), nullable=True, doc='提供商类型 (stripe, paypal, alipay, wechat, crypto)')

    config_data = Column(Text, nullable=True, doc='配置数据 (JSON格式)')


    is_active = Column(Boolean, default=False, doc='是否激活')


    supported_currencies = Column(String(255), default='USD,CNY', doc='支持的货币列表 (逗号分隔)')

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
            'provider': self.provider,
            'config_data': self.config_data,
            'is_active': self.is_active,
            'supported_currencies': self.supported_currencies,
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
        return f'<PaymentGateway id={self.id}>'
