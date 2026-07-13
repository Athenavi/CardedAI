"""
SQLAlchemy 模型定义 - NodeExecution
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-07-13 10:19:38
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from shared.models import Base  # 使用统一的 Base（跨子包引用）



class NodeExecution(Base):
    """工作流节点执行记录模型"""
    __tablename__ = 'workflow_node_executions'


    __table_args__ = (
        Index('idx_ne_execution', 'execution_id'),
        Index('idx_ne_status', 'status'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='节点执行 ID')

    execution_id = Column(BigInteger, ForeignKey('workflow_executions.id'), nullable=True, doc='所属执行实例 ID')


    node_id = Column(String(100), nullable=True, doc='节点在 DAG 中的 ID')

    node_type = Column(String(50), nullable=True, doc='节点类型 (llm/collector/rag/transform/condition/notify)')

    status = Column(String(20), nullable=True, doc='状态 (pending/running/completed/failed/skipped)')

    input_data = Column(Text, nullable=True, doc='输入数据 (JSON)')


    output_data = Column(Text, nullable=True, doc='输出数据 (JSON)')


    error_message = Column(Text, nullable=True, doc='错误信息')


    duration_ms = Column(Integer, nullable=True, doc='执行耗时 (毫秒)')


    started_at = Column(DateTime, nullable=True, doc='开始时间')

    completed_at = Column(DateTime, nullable=True, doc='完成时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'execution_id': self.execution_id,
            'node_id': self.node_id,
            'node_type': self.node_type,
            'status': self.status,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'error_message': self.error_message,
            'duration_ms': self.duration_ms,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<NodeExecution id={self.id}>'


