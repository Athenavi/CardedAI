"""
SQLAlchemy 模型定义 - MigrationLog
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base



class MigrationLog(Base):
    """迁移日志模型模型"""
    __tablename__ = 'migration_logs'


    __table_args__ = (
        Index('idx_migration_log_task', 'task_id'),
        Index('idx_migration_log_level', 'log_level'),
        Index('idx_migration_log_created', 'created_at'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='日志 ID')

    task_id = Column(BigInteger, ForeignKey('migration_tasks.id'), doc='迁移任务 ID')


    log_level = Column(String(20), default='info', doc='日志级别')

    message = Column(Text, nullable=False, doc='日志消息')

    item_type = Column(String(50), nullable=True, doc='项目类型（post/category/user等）')

    item_id = Column(BigInteger, nullable=True, doc='项目 ID')

    created_at = Column(DateTime, doc='创建时间')

    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'task_id': self.task_id,
            'log_level': self.log_level,
            'message': self.message,
            'item_type': self.item_type,
            'item_id': self.item_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<MigrationLog id={self.id}>'
