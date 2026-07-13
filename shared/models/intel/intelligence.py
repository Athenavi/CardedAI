"""
SQLAlchemy 模型定义 - Intelligence
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-07-13 10:19:38
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Numeric, Index

from shared.models import Base  # 使用统一的 Base（跨子包引用）



class Intelligence(Base):
    """AI 分析后的情报条目模型"""
    __tablename__ = 'intel_intelligence'


    __table_args__ = (
        Index('idx_intel_intel_sentiment', 'sentiment'),
        Index('idx_intel_intel_category', 'category'),
        Index('idx_intel_intel_score', 'importance_score'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='情报 ID')

    title = Column(String(500), nullable=True, doc='情报标题')

    summary = Column(Text, nullable=True, doc='AI 生成的摘要')


    sentiment = Column(String(20), nullable=True, doc='情感倾向 (positive/negative/neutral)')

    category = Column(String(100), nullable=True, doc='AI 分类')

    importance_score = Column(Numeric(10, 2), nullable=True, doc='重要性评分 (0-1)')


    item_ids = Column(Text, nullable=True, doc='关联的采集条目 ID 列表 (JSON)')


    tags = Column(Text, nullable=True, doc='AI 提取的标签 (JSON)')


    source_urls = Column(Text, nullable=True, doc='来源链接 (JSON)')


    created_at = Column(DateTime, doc='创建时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'title': self.title,
            'summary': self.summary,
            'sentiment': self.sentiment,
            'category': self.category,
            'importance_score': self.importance_score,
            'item_ids': self.item_ids,
            'tags': self.tags,
            'source_urls': self.source_urls,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<Intelligence id={self.id}>'


