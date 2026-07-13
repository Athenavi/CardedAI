"""
SQLAlchemy 模型定义 - Briefing
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-07-13 10:19:38
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Index

from shared.models import Base  # 使用统一的 Base（跨子包引用）



class Briefing(Base):
    """情报简报模型"""
    __tablename__ = 'intel_briefings'


    __table_args__ = (
        Index('idx_intel_brief_type', 'briefing_type'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='简报 ID')

    title = Column(String(500), nullable=True, doc='简报标题')

    content = Column(Text, nullable=True, doc='Markdown 格式简报内容')


    briefing_type = Column(String(50), nullable=True, doc='简报类型 (daily/weekly/alert/custom)')

    intelligence_ids = Column(Text, nullable=True, doc='包含的情报 ID 列表 (JSON)')


    channels_sent = Column(Text, nullable=True, doc='已推送渠道 (JSON)')


    created_at = Column(DateTime, doc='创建时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'briefing_type': self.briefing_type,
            'intelligence_ids': self.intelligence_ids,
            'channels_sent': self.channels_sent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<Briefing id={self.id}>'


