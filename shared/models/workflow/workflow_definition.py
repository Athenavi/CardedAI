"""
SQLAlchemy 模型定义 - WorkflowDefinition
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-07-13 10:19:38
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from shared.models import Base  # 使用统一的 Base（跨子包引用）



class WorkflowDefinition(Base):
    """工作流定义模型"""
    __tablename__ = 'workflow_definitions'


    __table_args__ = (
        Index('idx_wfd_active', 'is_active'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='工作流 ID')

    name = Column(String(200), nullable=True, doc='工作流名称')

    description = Column(Text, nullable=True, doc='工作流描述')


    version = Column(Integer, default=1, doc='版本号')


    graph = Column(Text, nullable=True, doc='DAG 图结构 (JSON: {nodes, edges})')


    trigger_config = Column(Text, nullable=True, doc='触发配置 (JSON: {type, cron, event})')


    is_active = Column(Boolean, default=False, doc='是否启用')


    created_by = Column(BigInteger, ForeignKey('users.id'), nullable=True, doc='创建用户')


    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, nullable=True, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'graph': self.graph,
            'trigger_config': self.trigger_config,
            'is_active': self.is_active,
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
        return f'<WorkflowDefinition id={self.id}>'


