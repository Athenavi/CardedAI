"""
SQLAlchemy 模型定义 - Menus
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-07-13 10:19:38
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Index

from . import Base  # 使用统一的 Base



class Menus(Base):
    """菜单模型（合并菜单项和菜单位置）模型"""
    __tablename__ = 'menus'


    __table_args__ = (
        Index('idx_menus_slug', 'slug', unique=True),
        Index('idx_menus_location', 'location'),
        Index('idx_menus_parent_id', 'parent_id'),
        Index('idx_menus_order', 'order_index'),
        Index('idx_menus_is_active', 'is_active'),
    )


    id = Column(Integer, primary_key=True, autoincrement=True, doc='菜单 ID')

    parent_id = Column(Integer, nullable=True, doc='父级 ID（用于层级结构）')


    name = Column(String(100), nullable=True, doc='菜单/项名称')

    slug = Column(String(100), nullable=True, doc='菜单标识')

    location = Column(String(100), nullable=True, doc='菜单位置（primary-menu, footer-menu等）')

    url = Column(String(500), nullable=True, doc='链接地址')

    target = Column(String(255), default='_self', doc='打开方式（_self, _blank）')

    order_index = Column(Integer, default=0, doc='排序索引')


    is_active = Column(Boolean, default=True, doc='是否启用')


    description = Column(String(255), nullable=True, doc='描述')

    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'parent_id': self.parent_id,
            'name': self.name,
            'slug': self.slug,
            'location': self.location,
            'url': self.url,
            'target': self.target,
            'order_index': self.order_index,
            'is_active': self.is_active,
            'description': self.description,
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
        return f'<Menus id={self.id}>'


