"""
SQLAlchemy 模型定义 - TaxConfig
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Numeric, Index

from . import Base  # 使用统一的 Base



class TaxConfig(Base):
    """税务配置模型模型"""
    __tablename__ = 'tax_configs'


    __table_args__ = (
        Index('idx_tax_config_country', 'country'),
        Index('idx_tax_config_region', 'region'),
        Index('idx_tax_config_active', 'is_active'),
        Index('idx_tax_config_effective_dates', 'effective_from', 'effective_to'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='税务配置 ID')

    country = Column(String(2), nullable=True, doc='国家代码 (ISO 3166-1 alpha-2)')

    region = Column(String(100), nullable=True, doc='地区/州/省')

    tax_type = Column(String(50), nullable=True, doc='税种类型 (VAT, GST, Sales Tax, etc.)')

    rate = Column(Numeric(10, 2), doc='税率 (百分比)')


    description = Column(String(255), nullable=True, doc='描述')

    is_active = Column(Boolean, default=True, doc='是否激活')


    effective_from = Column(DateTime, doc='生效日期')

    effective_to = Column(DateTime, nullable=True, doc='失效日期')

    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')

    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'country': self.country,
            'region': self.region,
            'tax_type': self.tax_type,
            'rate': self.rate,
            'description': self.description,
            'is_active': self.is_active,
            'effective_from': self.effective_from.isoformat() if self.effective_from else None,
            'effective_to': self.effective_to.isoformat() if self.effective_to else None,
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
        return f'<TaxConfig id={self.id}>'
