"""
SQLAlchemy 模型定义 - MenuLocation
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Index

from . import Base  # 使用统一的 Base


class MenuLocation(Base):
    """菜单位置模型（主菜单、页脚菜单等）模型"""
    __tablename__ = 'menu_locations'


    __table_args__ = (
        Index('idx_menu_locations_slug', 'slug', unique=True),
    )


    id = Column(Integer, primary_key=True, autoincrement=True, doc='位置 ID')

    name = Column(String(100), nullable=True, doc='位置显示名称')

    slug = Column(String(100), unique=True, nullable=True, doc='位置标识（primary-menu, footer-menu等）')

    description = Column(String(255), nullable=True, doc='位置描述')

    theme_supports = Column(String(255), nullable=True, doc='支持的主题列表（JSON格式）')

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
            'theme_supports': self.theme_supports,
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
        return f'<MenuLocation id={self.id}>'


