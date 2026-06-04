"""
SQLAlchemy 模型定义 - BaiduAnalyticsConfig
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base



class BaiduAnalyticsConfig(Base):
    """百度统计配置模型模型"""
    __tablename__ = 'baidu_analytics_configs'


    __table_args__ = (
        Index('idx_baidu_config_site', 'site_id'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='配置 ID')

    site_id = Column(BigInteger, ForeignKey('sites.id'), nullable=True, doc='关联的站点 ID（为空表示全局配置）')


    site_token = Column(String(100), nullable=True, doc='百度统计 Site Token')

    api_key = Column(String(255), nullable=True, doc='百度统计 API Key')

    enable_tracking = Column(Boolean, default=True, doc='是否启用追踪')


    enable_data_sync = Column(Boolean, default=False, doc='是否启用数据同步')


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
            'site_token': self.site_token,
            'api_key': self.api_key,
            'enable_tracking': self.enable_tracking,
            'enable_data_sync': self.enable_data_sync,
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
        return f'<BaiduAnalyticsConfig id={self.id}>'
