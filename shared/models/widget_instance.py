"""
SQLAlchemy 模型定义 - WidgetInstance
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Index

from . import Base  # 使用统一的 Base


class WidgetInstance(Base):
    """Widget实例模型（持久化存储）模型"""
    __tablename__ = 'widget_instances'


    __table_args__ = (
        Index('idx_widget_instances_area', 'area'),
        Index('idx_widget_instances_order', 'order_index'),
        Index('idx_widget_instances_type', 'widget_type'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='Widget实例 ID')

    widget_type = Column(String(50), nullable=True, doc='Widget类型（search, recent_posts, categories等）')

    area = Column(String(50), nullable=True, doc='显示区域（sidebar_primary, footer_1等）')

    title = Column(String(255), nullable=True, doc='Widget标题')

    config = Column(String(255), nullable=True, doc='Widget配置（JSON格式）')

    order_index = Column(BigInteger, default=0, doc='显示顺序')


    is_active = Column(Boolean, default=True, doc='是否启用')


    conditions = Column(String(255), nullable=True, doc='显示条件（JSON格式）')

    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'widget_type': self.widget_type,
            'area': self.area,
            'title': self.title,
            'config': self.config,
            'order_index': self.order_index,
            'is_active': self.is_active,
            'conditions': self.conditions,
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
        return f'<WidgetInstance id={self.id}>'


