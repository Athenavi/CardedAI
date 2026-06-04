"""
SQLAlchemy 模型定义 - DeploymentLog
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base



class DeploymentLog(Base):
    """部署日志模型模型"""
    __tablename__ = 'deployment_logs'


    __table_args__ = (
        Index('idx_deployment_script', 'script_id'),
        Index('idx_deployment_status', 'status'),
        Index('idx_deployment_created', 'created_at'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='日志 ID')

    script_id = Column(BigInteger, ForeignKey('deployment_scripts.id'), doc='脚本 ID')


    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=True, doc='执行者用户 ID')

    status = Column(String(20), default='pending', doc='执行状态')

    output = Column(Text, nullable=True, doc='执行输出')

    error_message = Column(Text, nullable=True, doc='错误信息')

    started_at = Column(DateTime, nullable=True, doc='开始时间')

    completed_at = Column(DateTime, nullable=True, doc='完成时间')

    created_at = Column(DateTime, doc='创建时间')

    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'script_id': self.script_id,
            'user_id': self.user_id,
            'status': self.status,
            'output': self.output,
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
        return f'<DeploymentLog id={self.id}>'
