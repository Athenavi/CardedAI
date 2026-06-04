"""
SQLAlchemy 模型定义 - AgentTool
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-06-04 16:28:03
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Index

from shared.models import Base  # 使用统一的 Base（跨子包引用）



class AgentTool(Base):
    """AI Agent 工具注册模型"""
    __tablename__ = 'workflow_agent_tools'


    __table_args__ = (
        Index('idx_tool_type', 'tool_type'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='工具 ID')

    name = Column(String(200), nullable=True, doc='工具名称')

    description = Column(Text, nullable=True, doc='工具描述')


    tool_type = Column(String(50), nullable=True, doc='工具类型 (api/function/collector/transformer)')

    schema = Column(Text, nullable=True, doc='工具参数 JSON Schema')


    config = Column(Text, nullable=True, doc='工具配置 (JSON)')


    is_active = Column(Boolean, default=True, doc='是否启用')


    created_at = Column(DateTime, doc='创建时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'tool_type': self.tool_type,
            'schema': self.schema,
            'config': self.config,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<AgentTool id={self.id}>'


