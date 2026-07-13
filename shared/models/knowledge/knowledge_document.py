"""
SQLAlchemy 模型定义 - KnowledgeDocument
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-07-13 11:50:46
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from shared.models import Base  # 使用统一的 Base（跨子包引用）



class KnowledgeDocument(Base):
    """知识库文档模型"""
    __tablename__ = 'knowledge_documents'


    __table_args__ = (
        Index('idx_kd_kb', 'knowledge_base_id'),
        Index('idx_kd_status', 'status'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='文档 ID')

    knowledge_base_id = Column(BigInteger, ForeignKey('knowledge_bases.id'), nullable=True, doc='所属知识库 ID')


    title = Column(String(500), nullable=True, doc='文档标题')

    file_path = Column(Text, nullable=True, doc='文件存储路径')


    file_type = Column(String(50), nullable=True, doc='文件类型 (pdf/docx/txt/html/url)')

    content_text = Column(Text, nullable=True, doc='提取的纯文本')


    chunk_count = Column(Integer, default=0, doc='切片数量')


    status = Column(String(20), default='uploading', doc='状态 (uploading/parsing/indexed/failed)')

    metadata_json = Column(Text, nullable=True, doc='文档元数据 (JSON)')


    created_at = Column(DateTime, doc='创建时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'knowledge_base_id': self.knowledge_base_id,
            'title': self.title,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'content_text': self.content_text,
            'chunk_count': self.chunk_count,
            'status': self.status,
            'metadata_json': self.metadata_json,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<KnowledgeDocument id={self.id}>'


