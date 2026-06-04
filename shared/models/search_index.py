"""
SQLAlchemy 模型定义 - SearchIndex
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base


class SearchIndex(Base):
    """搜索索引状态模型模型"""
    __tablename__ = 'search_index'


    __table_args__ = (
        Index('idx_search_index_article', 'article_id', unique=True),
        Index('idx_search_index_indexed', 'indexed'),
        Index('idx_search_index_last_indexed', 'last_indexed_at'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='索引记录ID')

    article_id = Column(BigInteger, ForeignKey('articles.id'), doc='文章ID')


    indexed = Column(Boolean, default=False, doc='是否已索引')


    last_indexed_at = Column(DateTime, nullable=True, doc='最后索引时间')

    index_hash = Column(String(64), nullable=True, doc='索引内容哈希(用于检测变更)')

    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'article_id': self.article_id,
            'indexed': self.indexed,
            'last_indexed_at': self.last_indexed_at.isoformat() if self.last_indexed_at else None,
            'index_hash': self.index_hash,
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
        return f'<SearchIndex id={self.id}>'


