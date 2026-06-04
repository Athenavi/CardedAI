"""
SQLAlchemy 模型定义 - DeploymentScript
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base



class DeploymentScript(Base):
    """部署脚本模型模型"""
    __tablename__ = 'deployment_scripts'


    __table_args__ = (
        Index('idx_script_type', 'script_type'),
        Index('idx_script_active', 'is_active'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='脚本 ID')

    name = Column(String(255), nullable=True, doc='脚本名称')

    script_type = Column(String(50), nullable=True, doc='脚本类型')

    content = Column(Text, nullable=False, doc='脚本内容')


    version = Column(String(20), nullable=True, doc='脚本版本')

    description = Column(Text, nullable=True, doc='脚本描述')

    parameters = Column(Text, nullable=True, doc='参数定义（JSON格式）')

    is_active = Column(Boolean, default=True, doc='是否激活')

    created_by = Column(BigInteger, ForeignKey('users.id'), nullable=True, doc='创建者 ID')

    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')

    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'name': self.name,
            'script_type': self.script_type,
            'content': self.content,
            'version': self.version,
            'description': self.description,
            'parameters': self.parameters,
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
        return f'<DeploymentScript id={self.id}>'
