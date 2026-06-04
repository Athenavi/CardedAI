"""
SQLAlchemy 模型定义 - AIWorkflow
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base



class AIWorkflow(Base):
    """AI 智能工作流记录模型模型"""
    __tablename__ = 'ai_workflows'


    __table_args__ = (
        Index('idx_ai_workflows_user_id', 'user_id'),
        Index('idx_ai_workflows_task_type', 'task_type'),
        Index('idx_ai_workflows_status', 'status'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='工作流 ID')

    user_id = Column(BigInteger, ForeignKey('users.id'), doc='用户 ID')

    task_type = Column(String(50), nullable=True, doc='任务类型 (writing_assist, seo_optimize, tag_recommend)')

    input_data = Column(Text, nullable=False, doc='输入数据 (JSON)')

    output_data = Column(Text, nullable=True, doc='输出结果 (JSON)')

    model_used = Column(String(100), nullable=True, doc='使用的 AI 模型')

    tokens_used = Column(Integer, default=0, doc='消耗的 Token 数量')

    status = Column(String(20), default='pending', doc='状态 (pending, processing, completed, failed)')

    error_message = Column(Text, nullable=True, doc='错误信息')

    created_at = Column(DateTime, doc='创建时间')

    completed_at = Column(DateTime, nullable=True, doc='完成时间')

    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'task_type': self.task_type,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'model_used': self.model_used,
            'tokens_used': self.tokens_used,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<AIWorkflow id={self.id}>'
