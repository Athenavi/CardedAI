"""
SQLAlchemy 模型定义 - Workspace
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base



class Workspace(Base):
    """团队工作区模型模型"""
    __tablename__ = 'workspaces'


    __table_args__ = (
        Index('idx_workspaces_slug', 'slug'),
        Index('idx_workspaces_owner', 'owner_id'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='工作区 ID')

    name = Column(String(255), nullable=True, doc='工作区名称')

    slug = Column(String(255), unique=True, nullable=True, doc='工作区标识')

    description = Column(Text, nullable=True, doc='工作区描述')


    owner_id = Column(BigInteger, ForeignKey('users.id'), doc='所有者 ID')


    is_active = Column(Boolean, default=True, doc='是否激活')


    settings = Column(Text, nullable=True, doc='工作区设置（JSON格式）')


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
            'slug': self.slug,
            'description': self.description,
            'owner_id': self.owner_id,
            'is_active': self.is_active,
            'settings': self.settings,
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
        return f'<Workspace id={self.id}>'
