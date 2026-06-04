"""
SQLAlchemy 模型定义 - AgentMemory
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-06-04 16:28:03
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Index

from shared.models import Base  # 使用统一的 Base（跨子包引用）



class AgentMemory(Base):
    """AI Agent 记忆存储模型"""
    __tablename__ = 'workflow_agent_memories'


    __table_args__ = (
        Index('idx_mem_agent', 'agent_id'),
        Index('idx_mem_session', 'session_id'),
        Index('idx_mem_type', 'memory_type'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='记忆 ID')

    agent_id = Column(String(100), nullable=True, doc='Agent 标识')

    session_id = Column(String(100), nullable=True, doc='会话 ID')

    memory_type = Column(String(50), nullable=True, doc='记忆类型 (short_term/long_term/episodic)')

    content = Column(Text, nullable=True, doc='记忆内容')


    metadata_json = Column(Text, nullable=True, doc='元数据 (JSON)')


    created_at = Column(DateTime, doc='创建时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'agent_id': self.agent_id,
            'session_id': self.session_id,
            'memory_type': self.memory_type,
            'content': self.content,
            'metadata_json': self.metadata_json,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<AgentMemory id={self.id}>'


