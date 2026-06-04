"""
SQLAlchemy 模型定义 - EnterpriseLicense
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Numeric, Index

from . import Base  # 使用统一的 Base



class EnterpriseLicense(Base):
    """企业许可证模型模型"""
    __tablename__ = 'enterprise_licenses'


    __table_args__ = (
        Index('idx_license_key', 'license_key', unique=True),
        Index('idx_license_type', 'license_type'),
        Index('idx_license_active', 'is_active'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='许可证 ID')

    license_key = Column(String(255), unique=True, nullable=True, doc='许可证密钥')

    license_type = Column(String(50), default='professional', doc='许可证类型')

    company_name = Column(String(255), nullable=True, doc='公司名称')

    contact_email = Column(String(255), nullable=True, doc='联系邮箱')

    max_sites = Column(Integer, default=-1, doc='最大站点数（-1表示无限）')


    features = Column(Text, nullable=True, doc='功能列表（JSON格式）')

    valid_from = Column(DateTime, doc='生效日期')

    valid_until = Column(DateTime, nullable=True, doc='过期日期（null表示永久）')

    is_active = Column(Boolean, default=True, doc='是否激活')

    support_level = Column(String(50), default='standard', doc='技术支持级别')

    sla_enabled = Column(Boolean, default=False, doc='是否启用SLA保障')

    sla_uptime_guarantee = Column(Numeric(10, 2), nullable=True, doc='SLA可用性保证（如99.9）')

    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')

    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'license_key': self.license_key,
            'license_type': self.license_type,
            'company_name': self.company_name,
            'contact_email': self.contact_email,
            'max_sites': self.max_sites,
            'features': self.features,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'is_active': self.is_active,
            'support_level': self.support_level,
            'sla_enabled': self.sla_enabled,
            'sla_uptime_guarantee': self.sla_uptime_guarantee,
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
        return f'<EnterpriseLicense id={self.id}>'
