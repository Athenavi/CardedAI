"""
SQLAlchemy 模型定义 - WorkflowExecution
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-07-13 10:19:38
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from shared.models import Base  # 使用统一的 Base（跨子包引用）



class WorkflowExecution(Base):
    """工作流执行实例模型"""
    __tablename__ = 'workflow_executions'


    __table_args__ = (
        Index('idx_wfe_workflow', 'workflow_id'),
        Index('idx_wfe_status', 'status'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='执行 ID')

    workflow_id = Column(BigInteger, ForeignKey('workflow_definitions.id'), nullable=True, doc='工作流定义 ID')


    status = Column(String(20), default='pending', doc='状态 (pending/running/completed/failed/cancelled)')

    trigger_type = Column(String(50), nullable=True, doc='触发类型 (manual/scheduled/event)')

    input_data = Column(Text, nullable=True, doc='输入数据 (JSON)')


    output_data = Column(Text, nullable=True, doc='输出数据 (JSON)')


    error_message = Column(Text, nullable=True, doc='错误信息')


    started_at = Column(DateTime, nullable=True, doc='开始时间')

    completed_at = Column(DateTime, nullable=True, doc='完成时间')

    created_at = Column(DateTime, doc='创建时间')

    # 关系定义
    node_executions = relationship('NodeExecution', back_populates='execution')

    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'workflow_id': self.workflow_id,
            'status': self.status,
            'trigger_type': self.trigger_type,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'error_message': self.error_message,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<WorkflowExecution id={self.id}>'


