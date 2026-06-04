"""
SQLAlchemy 模型定义 - MediaFolder
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base


class MediaFolder(Base):
    """媒体文件夹模型模型"""
    __tablename__ = 'media_folders'


    __table_args__ = (
        Index('idx_media_folders_user_id', 'user'),
        Index('idx_media_folders_parent_id', 'parent_id'),
        Index('idx_media_folders_unique_name', 'user', 'parent_id', 'name', unique=True),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='文件夹 ID')

    name = Column(String(255), nullable=True, doc='文件夹名称')

    parent_id = Column(BigInteger, ForeignKey('media_folders.id'), nullable=True, doc='父文件夹 ID')


    user = Column(BigInteger, ForeignKey('users.id'), doc='所属用户')


    description = Column(String(255), nullable=True, doc='文件夹描述')

    sort_order = Column(BigInteger, default=0, doc='排序顺序')


    is_public = Column(Boolean, default=True, doc='是否公开')


    media_count = Column(BigInteger, default=0, doc='文件夹内媒体数量')


    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'user': self.user,
            'description': self.description,
            'sort_order': self.sort_order,
            'is_public': self.is_public,
            'media_count': self.media_count,
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
        return f'<MediaFolder id={self.id}>'


