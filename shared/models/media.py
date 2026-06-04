"""
SQLAlchemy 模型定义 - Media
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base


class Media(Base):
    """媒体文件模型模型"""
    __tablename__ = 'media'


    __table_args__ = (
        Index('idx_media_user', 'user'),
        Index('idx_media_hash', 'hash', unique=True),
        Index('idx_media_file_type', 'file_type'),
        Index('idx_media_is_public', 'is_public'),
        Index('idx_media_created_at', 'created_at'),
        Index('idx_media_folder', 'folder_id'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='媒体 ID')

    user = Column(BigInteger, ForeignKey('users.id'), doc='上传用户')


    hash = Column(String(64), nullable=True, doc='文件哈希')

    filename = Column(String(255), nullable=True, doc='文件名')

    original_filename = Column(String(255), nullable=True, doc='原始文件名')

    file_path = Column(String(500), nullable=True, doc='文件路径')

    file_url = Column(String(500), nullable=True, doc='文件 URL')

    file_size = Column(BigInteger, default=0, doc='文件大小 (字节)')


    file_type = Column(String(255), default='other', doc='文件类型')

    mime_type = Column(String(255), nullable=True, doc='MIME 类型')

    width = Column(BigInteger, nullable=True, doc='宽度')


    height = Column(BigInteger, nullable=True, doc='高度')


    duration = Column(BigInteger, nullable=True, doc='时长 (秒)')


    thumbnail_path = Column(String(255), nullable=True, doc='缩略图路径')

    thumbnail_url = Column(String(255), nullable=True, doc='缩略图 URL')

    description = Column(String(255), nullable=True, doc='描述')

    alt_text = Column(String(255), nullable=True, doc='替代文本')

    is_public = Column(Boolean, default=True, doc='是否公开')


    download_count = Column(BigInteger, default=0, doc='下载次数')


    category = Column(String(100), nullable=True, doc='媒体分类')

    tags = Column(String(500), nullable=True, doc='标签(逗号分隔)')

    folder_id = Column(BigInteger, ForeignKey('media_folders.id'), nullable=True, doc='所属文件夹 ID')


    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'user': self.user,
            'hash': self.hash,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'file_url': self.file_url,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'mime_type': self.mime_type,
            'width': self.width,
            'height': self.height,
            'duration': self.duration,
            'thumbnail_path': self.thumbnail_path,
            'thumbnail_url': self.thumbnail_url,
            'description': self.description,
            'alt_text': self.alt_text,
            'is_public': self.is_public,
            'download_count': self.download_count,
            'category': self.category,
            'tags': self.tags,
            'folder_id': self.folder_id,
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
        return f'<Media id={self.id}>'


