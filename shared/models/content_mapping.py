"""
SQLAlchemy 模型定义 - ContentMapping
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base



class ContentMapping(Base):
    """内容映射模型模型"""
    __tablename__ = 'content_mappings'


    __table_args__ = (
        Index('idx_content_mapping_source', 'source_site_id', 'content_type', 'source_content_id'),
        Index('idx_content_mapping_target', 'target_site_id', 'content_type', 'target_content_id'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='映射 ID')

    source_site_id = Column(BigInteger, ForeignKey('sites.id'), doc='源站点 ID')


    target_site_id = Column(BigInteger, ForeignKey('sites.id'), doc='目标站点 ID')


    content_type = Column(String(50), nullable=True, doc='内容类型')

    source_content_id = Column(BigInteger, doc='源内容 ID')


    target_content_id = Column(BigInteger, nullable=True, doc='目标内容 ID')


    sync_mode = Column(String(20), default='manual', doc='同步模式（manual/auto）')

    last_synced_at = Column(DateTime, nullable=True, doc='最后同步时间')

    created_at = Column(DateTime, doc='创建时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'source_site_id': self.source_site_id,
            'target_site_id': self.target_site_id,
            'content_type': self.content_type,
            'source_content_id': self.source_content_id,
            'target_content_id': self.target_content_id,
            'sync_mode': self.sync_mode,
            'last_synced_at': self.last_synced_at.isoformat() if self.last_synced_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<ContentMapping id={self.id}>'
