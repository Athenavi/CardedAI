"""
SQLAlchemy 模型定义 - KnowledgeBase
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-07-13 11:50:46
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from shared.models import Base  # 使用统一的 Base（跨子包引用）



class KnowledgeBase(Base):
    """知识库模型"""
    __tablename__ = 'knowledge_bases'


    __table_args__ = (
        Index('idx_kb_name', 'name'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='知识库 ID')

    name = Column(String(200), nullable=True, doc='知识库名称')

    description = Column(Text, nullable=True, doc='知识库描述')


    embedding_model = Column(String(100), nullable=True, doc='使用的 Embedding 模型')

    chunk_size = Column(Integer, default=512, doc='切片大小')


    chunk_overlap = Column(Integer, default=50, doc='切片重叠')


    vector_collection = Column(String(100), nullable=True, doc='向量集合名称')

    document_count = Column(Integer, default=0, doc='文档数量')


    chunk_count = Column(Integer, default=0, doc='切片数量')


    created_by = Column(BigInteger, ForeignKey('users.id'), nullable=True, doc='创建用户')


    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, nullable=True, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'embedding_model': self.embedding_model,
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'vector_collection': self.vector_collection,
            'document_count': self.document_count,
            'chunk_count': self.chunk_count,
            'created_by': self.created_by,
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
        return f'<KnowledgeBase id={self.id}>'


