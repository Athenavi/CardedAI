"""
SQLAlchemy 模型定义 - DataSource
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-07-13 10:19:38
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from shared.models import Base  # 使用统一的 Base（跨子包引用）



class DataSource(Base):
    """数据源配置模型"""
    __tablename__ = 'intel_data_sources'


    __table_args__ = (
        Index('idx_intel_ds_type', 'source_type'),
        Index('idx_intel_ds_active', 'is_active'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='数据源 ID')

    name = Column(String(200), nullable=True, doc='数据源名称')

    source_type = Column(String(50), nullable=True, doc='源类型 (rss/web/api/search/social)')

    url = Column(Text, nullable=True, doc='源 URL')


    config = Column(Text, nullable=True, doc='采集配置 (JSON: 选择器、频率等)')


    schedule_cron = Column(String(100), nullable=True, doc='采集调度 Cron 表达式')

    is_active = Column(Boolean, default=True, doc='是否启用')


    last_collected_at = Column(DateTime, nullable=True, doc='最后采集时间')

    created_at = Column(DateTime, doc='创建时间')

    created_by = Column(BigInteger, ForeignKey('users.id'), nullable=True, doc='创建用户')



    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'name': self.name,
            'source_type': self.source_type,
            'url': self.url,
            'config': self.config,
            'schedule_cron': self.schedule_cron,
            'is_active': self.is_active,
            'last_collected_at': self.last_collected_at.isoformat() if self.last_collected_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<DataSource id={self.id}>'


