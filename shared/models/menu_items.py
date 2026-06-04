"""
SQLAlchemy 模型定义 - MenuItems
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Index

from . import Base  # 使用统一的 Base


class MenuItems(Base):
    """菜单项模型模型"""
    __tablename__ = 'menu_items'


    __table_args__ = (
        Index('idx_menu_items_menu_id', 'menu_id'),
        Index('idx_menu_items_parent_id', 'parent_id'),
        Index('idx_menu_items_order', 'order_index'),
    )


    id = Column(Integer, primary_key=True, autoincrement=True, doc='菜单项 ID')

    menu_id = Column(Integer, doc='菜单 ID')


    parent_id = Column(Integer, nullable=True, doc='父菜单项 ID')


    title = Column(String(255), nullable=True, doc='标题')

    url = Column(String(500), nullable=True, doc='URL')

    target = Column(String(255), default='_self', doc='打开方式')

    order_index = Column(Integer, default=0, doc='排序索引')


    is_active = Column(Boolean, default=True, doc='是否激活')


    created_at = Column(DateTime, doc='创建时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'menu_id': self.menu_id,
            'parent_id': self.parent_id,
            'title': self.title,
            'url': self.url,
            'target': self.target,
            'order_index': self.order_index,
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
        return f'<MenuItems id={self.id}>'


