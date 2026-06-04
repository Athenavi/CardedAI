"""
SQLAlchemy 模型定义 - BlockPattern
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base


class BlockPattern(Base):
    """自定义块模式模型模型"""
    __tablename__ = 'block_patterns'


    __table_args__ = (
        Index('idx_block_patterns_name', 'name', unique=True),
        Index('idx_block_patterns_category', 'category'),
        Index('idx_block_patterns_user_id', 'user_id'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='模式ID')

    name = Column(String(100), unique=True, nullable=True, doc='模式名称（唯一标识）')

    title = Column(String(255), nullable=True, doc='模式标题（显示名称）')

    description = Column(Text, nullable=True, doc='模式描述')


    category = Column(String(50), default='custom', doc='分类（custom, hero, features等）')

    blocks = Column(Text, nullable=False, doc='块数据（JSON格式）')


    keywords = Column(Text, nullable=True, doc='关键词（逗号分隔）')


    thumbnail = Column(String(500), nullable=True, doc='缩略图URL')

    is_public = Column(Boolean, default=False, doc='是否公开（false=私有，true=公开）')


    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=True, doc='创建者用户ID')


    viewport_width = Column(BigInteger, default=800, doc='预览宽度')


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
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'blocks': self.blocks,
            'keywords': self.keywords,
            'thumbnail': self.thumbnail,
            'is_public': self.is_public,
            'user_id': self.user_id,
            'viewport_width': self.viewport_width,
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
        return f'<BlockPattern id={self.id}>'


