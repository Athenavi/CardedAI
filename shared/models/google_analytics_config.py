"""
SQLAlchemy 模型定义 - GoogleAnalyticsConfig
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Numeric, ForeignKey, Index

from . import Base  # 使用统一的 Base



class GoogleAnalyticsConfig(Base):
    """Google Analytics 配置模型模型"""
    __tablename__ = 'google_analytics_configs'


    __table_args__ = (
        Index('idx_ga_config_site', 'site_id'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='配置 ID')

    site_id = Column(BigInteger, ForeignKey('sites.id'), nullable=True, doc='关联的站点 ID（为空表示全局配置）')


    tracking_id = Column(String(50), nullable=True, doc='Google Analytics Tracking ID (如 G-XXXXXXXXXX)')

    measurement_id = Column(String(50), nullable=True, doc='GA4 Measurement ID')

    api_secret = Column(String(255), nullable=True, doc='Google Analytics API Secret')

    enable_page_view_tracking = Column(Boolean, default=True, doc='是否启用页面浏览追踪')


    enable_event_tracking = Column(Boolean, default=True, doc='是否启用事件追踪')


    enable_user_behavior_analysis = Column(Boolean, default=False, doc='是否启用用户行为分析')

    anonymize_ip = Column(Boolean, default=True, doc='是否匿名化 IP 地址')

    sample_rate = Column(Numeric(10, 2), default=100.0, doc='采样率（0-100）')

    is_active = Column(Boolean, default=False, doc='是否激活')

    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')

    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'site_id': self.site_id,
            'tracking_id': self.tracking_id,
            'measurement_id': self.measurement_id,
            'api_secret': self.api_secret,
            'enable_page_view_tracking': self.enable_page_view_tracking,
            'enable_event_tracking': self.enable_event_tracking,
            'enable_user_behavior_analysis': self.enable_user_behavior_analysis,
            'anonymize_ip': self.anonymize_ip,
            'sample_rate': self.sample_rate,
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
        return f'<GoogleAnalyticsConfig id={self.id}>'
