"""
SQLAlchemy 模型定义 - MigrationTask
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base



class MigrationTask(Base):
    """迁移任务模型模型"""
    __tablename__ = 'migration_tasks'


    __table_args__ = (
        Index('idx_migration_status', 'status'),
        Index('idx_migration_platform', 'source_platform'),
        Index('idx_migration_created', 'created_at'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='迁移任务 ID')

    task_name = Column(String(255), nullable=True, doc='任务名称')

    source_platform = Column(String(50), nullable=True, doc='源平台')

    status = Column(String(20), default='pending', doc='任务状态')

    config = Column(Text, nullable=True, doc='迁移配置（JSON格式）')


    progress = Column(Integer, default=0, doc='进度百分比（0-100）')

    total_items = Column(BigInteger, default=0, doc='总项目数')

    migrated_items = Column(BigInteger, default=0, doc='已迁移项目数')

    error_message = Column(Text, nullable=True, doc='错误信息')

    started_at = Column(DateTime, nullable=True, doc='开始时间')

    completed_at = Column(DateTime, nullable=True, doc='完成时间')

    created_by = Column(BigInteger, ForeignKey('users.id'), doc='创建者用户 ID')

    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')

    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'task_name': self.task_name,
            'source_platform': self.source_platform,
            'status': self.status,
            'config': self.config,
            'progress': self.progress,
            'total_items': self.total_items,
            'migrated_items': self.migrated_items,
            'error_message': self.error_message,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
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
        return f'<MigrationTask id={self.id}>'
