"""
SQLAlchemy 模型定义 - Trigger
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-07-13 11:50:46
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from shared.models import Base  # 使用统一的 Base（跨子包引用）



class Trigger(Base):
    """工作流触发器模型"""
    __tablename__ = 'workflow_triggers'


    __table_args__ = (
        Index('idx_trigger_workflow', 'workflow_id'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='触发器 ID')

    workflow_id = Column(BigInteger, ForeignKey('workflow_definitions.id'), nullable=True, doc='关联的工作流 ID')


    trigger_type = Column(String(50), nullable=True, doc='触发类型 (cron/event/webhook/manual)')

    config = Column(Text, nullable=True, doc='触发器配置 (JSON)')


    is_active = Column(Boolean, default=True, doc='是否启用')


    last_fired_at = Column(DateTime, nullable=True, doc='最后触发时间')

    created_at = Column(DateTime, doc='创建时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'workflow_id': self.workflow_id,
            'trigger_type': self.trigger_type,
            'config': self.config,
            'is_active': self.is_active,
            'last_fired_at': self.last_fired_at.isoformat() if self.last_fired_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<Trigger id={self.id}>'


