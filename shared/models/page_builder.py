"""
SQLAlchemy 模型定义 - PageBuilder
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Index

from . import Base  # 使用统一的 Base



class PageBuilder(Base):
    """可视化页面构建器模型模型"""
    __tablename__ = 'page_builder'


    __table_args__ = (
        Index('idx_page_builder_slug', 'slug', unique=True),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='页面 ID')

    title = Column(String(255), nullable=True, doc='页面标题')

    slug = Column(String(255), unique=True, nullable=True, doc='页面路径标识')

    blocks_data = Column(Text, nullable=False, doc='页面块数据 (JSON 格式存储拖拽布局)')

    template_name = Column(String(100), nullable=True, doc='关联的主题模板名称')

    is_published = Column(Boolean, default=False, doc='是否发布')

    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')

    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'blocks_data': self.blocks_data,
            'template_name': self.template_name,
            'is_published': self.is_published,
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
        return f'<PageBuilder id={self.id}>'
