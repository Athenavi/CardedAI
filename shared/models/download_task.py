"""
SQLAlchemy 模型定义 - DownloadTask
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-07-13 11:50:46
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base



class DownloadTask(Base):
    """外部资源下载任务模型模型"""
    __tablename__ = 'download_tasks'


    __table_args__ = (
        Index('idx_download_tasks_user', 'user_id'),
        Index('idx_download_tasks_status', 'status'),
        Index('idx_download_tasks_priority', 'priority', 'created_at'),
        Index('idx_download_tasks_created', 'created_at'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='任务ID')

    user_id = Column(BigInteger, ForeignKey('users.id'), doc='用户ID')


    source_url = Column(String(2048), nullable=True, doc='源URL地址')

    resource_type = Column(String(50), default='image', doc='资源类型')

    filename = Column(String(255), nullable=True, doc='文件名')

    total_size = Column(BigInteger, nullable=True, doc='文件总大小(字节)')


    downloaded_size = Column(BigInteger, default=0, doc='已下载大小(字节)')


    progress = Column(Integer, default=0, doc='下载进度(0-100)')


    priority = Column(Integer, default=0, doc='任务优先级（数字越小优先级越高）')


    status = Column(String(50), default='pending', doc='任务状态')

    error_message = Column(Text, nullable=True, doc='错误信息')


    media_id = Column(BigInteger, ForeignKey('media.id'), nullable=True, doc='关联的媒体ID')


    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'source_url': self.source_url,
            'resource_type': self.resource_type,
            'filename': self.filename,
            'total_size': self.total_size,
            'downloaded_size': self.downloaded_size,
            'progress': self.progress,
            'priority': self.priority,
            'status': self.status,
            'error_message': self.error_message,
            'media_id': self.media_id,
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
        return f'<DownloadTask id={self.id}>'


