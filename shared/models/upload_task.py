"""
SQLAlchemy 模型定义 - UploadTask
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime
import uuid
from datetime import datetime

from . import Base  # 使用统一的 Base


class UploadTask(Base):
    """上传任务模型模型"""
    __tablename__ = 'upload_tasks'




    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), doc='任务 ID (UUID)')

    user_id = Column(BigInteger, doc='用户 ID')


    filename = Column(String(255), nullable=True, doc='文件名')

    total_size = Column(BigInteger, doc='文件总大小')


    total_chunks = Column(BigInteger, doc='总分块数')


    uploaded_chunks = Column(BigInteger, default=0, doc='已上传分块数')


    file_hash = Column(String(64), nullable=True, doc='文件哈希')

    status = Column(String(255), default='initialized', doc='状态')

    created_at = Column(DateTime, default=datetime.utcnow, doc='创建时间')

    updated_at = Column(DateTime, default=datetime.utcnow, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'total_size': self.total_size,
            'total_chunks': self.total_chunks,
            'uploaded_chunks': self.uploaded_chunks,
            'file_hash': self.file_hash,
            'status': self.status,
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
        return f'<UploadTask id={self.id}>'


