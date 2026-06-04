"""
SQLAlchemy 模型定义 - FileHash
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime

from . import Base  # 使用统一的 Base


class FileHash(Base):
    """文件哈希模型模型"""
    __tablename__ = 'file_hashs'




    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='哈希 ID')

    hash = Column(String(64), nullable=True, doc='文件哈希')

    filename = Column(String(255), nullable=True, doc='文件名')

    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')

    reference_count = Column(BigInteger, default=1, doc='引用计数')


    file_size = Column(BigInteger, doc='文件大小')


    mime_type = Column(String(100), nullable=True, doc='MIME 类型')

    storage_path = Column(String(512), nullable=True, doc='存储路径')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'hash': self.hash,
            'filename': self.filename,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'reference_count': self.reference_count,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'storage_path': self.storage_path,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<FileHash id={self.id}>'


