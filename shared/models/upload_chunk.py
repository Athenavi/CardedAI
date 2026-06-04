"""
SQLAlchemy 模型定义 - UploadChunk
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime
from datetime import datetime

from . import Base  # 使用统一的 Base


class UploadChunk(Base):
    """上传分块模型模型"""
    __tablename__ = 'upload_chunks'




    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='分块 ID')

    upload_id = Column(String(36), nullable=True, doc='上传任务 ID')

    chunk_index = Column(BigInteger, doc='分块索引')


    chunk_hash = Column(String(64), nullable=True, doc='分块哈希')

    chunk_size = Column(BigInteger, doc='分块大小')


    chunk_path = Column(String(500), nullable=True, doc='分块路径')

    created_at = Column(DateTime, default=datetime.utcnow, doc='创建时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'upload_id': self.upload_id,
            'chunk_index': self.chunk_index,
            'chunk_hash': self.chunk_hash,
            'chunk_size': self.chunk_size,
            'chunk_path': self.chunk_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<UploadChunk id={self.id}>'


