"""
SQLAlchemy 模型定义 - DocumentChunk
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-06-04 16:28:03
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from shared.models import Base  # 使用统一的 Base（跨子包引用）



class DocumentChunk(Base):
    """文档切片模型"""
    __tablename__ = 'knowledge_document_chunks'


    __table_args__ = (
        Index('idx_dc_doc', 'document_id'),
        Index('idx_dc_kb', 'knowledge_base_id'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='切片 ID')

    document_id = Column(BigInteger, ForeignKey('knowledge_documents.id'), nullable=True, doc='所属文档 ID')


    knowledge_base_id = Column(BigInteger, ForeignKey('knowledge_bases.id'), nullable=True, doc='所属知识库 ID')


    chunk_index = Column(Integer, nullable=True, doc='切片序号')


    content = Column(Text, nullable=True, doc='切片内容')


    embedding_id = Column(String(100), nullable=True, doc='向量数据库中的 ID')

    metadata_json = Column(Text, nullable=True, doc='元数据 (JSON: 页码、章节等)')


    token_count = Column(Integer, nullable=True, doc='Token 数量')


    created_at = Column(DateTime, doc='创建时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'document_id': self.document_id,
            'knowledge_base_id': self.knowledge_base_id,
            'chunk_index': self.chunk_index,
            'content': self.content,
            'embedding_id': self.embedding_id,
            'metadata_json': self.metadata_json,
            'token_count': self.token_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<DocumentChunk id={self.id}>'


