"""
SQLAlchemy 模型定义 - Task
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base



class Task(Base):
    """任务模型模型"""
    __tablename__ = 'tasks'


    __table_args__ = (
        Index('idx_tasks_workspace', 'workspace_id'),
        Index('idx_tasks_status', 'status'),
        Index('idx_tasks_assigned', 'assigned_to'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='任务 ID')

    workspace_id = Column(BigInteger, ForeignKey('workspaces.id'), doc='工作区 ID')


    title = Column(String(500), nullable=True, doc='任务标题')

    description = Column(Text, nullable=True, doc='任务描述')


    status = Column(String(20), index=True, default='pending', doc='状态（pending/in_progress/completed/cancelled）')

    priority = Column(String(20), default='medium', doc='优先级（low/medium/high/urgent）')

    assigned_to = Column(BigInteger, ForeignKey('users.id'), nullable=True, doc='分配给用户 ID')


    created_by = Column(BigInteger, ForeignKey('users.id'), doc='创建者 ID')


    due_date = Column(DateTime, nullable=True, doc='截止日期')

    completed_at = Column(DateTime, nullable=True, doc='完成时间')

    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'assigned_to': self.assigned_to,
            'created_by': self.created_by,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
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
        return f'<Task id={self.id}>'
