"""
SQLAlchemy 模型定义 - CollectedItem
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-07-13 10:19:38
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from shared.models import Base  # 使用统一的 Base（跨子包引用）



class CollectedItem(Base):
    """采集到的原始数据条目模型"""
    __tablename__ = 'intel_collected_items'


    __table_args__ = (
        Index('idx_intel_ci_source', 'source_id'),
        Index('idx_intel_ci_status', 'status'),
        Index('idx_intel_ci_hash', 'content_hash'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='条目 ID')

    source_id = Column(BigInteger, ForeignKey('intel_data_sources.id'), nullable=True, doc='数据源 ID')


    url = Column(Text, nullable=True, doc='原始 URL')


    title = Column(String(500), nullable=True, doc='标题')

    content_raw = Column(Text, nullable=True, doc='原始内容')


    content_cleaned = Column(Text, nullable=True, doc='清洗后内容')


    content_hash = Column(String(64), index=True, nullable=True, doc='内容哈希 (用于去重)')

    metadata_json = Column(Text, nullable=True, doc='元数据 (JSON: 作者、发布时间等)')


    status = Column(String(20), default='raw', doc='状态 (raw/cleaned/analyzed/archived)')

    collected_at = Column(DateTime, nullable=True, doc='采集时间')

    analyzed_at = Column(DateTime, nullable=True, doc='分析时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'source_id': self.source_id,
            'url': self.url,
            'title': self.title,
            'content_raw': self.content_raw,
            'content_cleaned': self.content_cleaned,
            'content_hash': self.content_hash,
            'metadata_json': self.metadata_json,
            'status': self.status,
            'collected_at': self.collected_at.isoformat() if self.collected_at else None,
            'analyzed_at': self.analyzed_at.isoformat() if self.analyzed_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<CollectedItem id={self.id}>'


