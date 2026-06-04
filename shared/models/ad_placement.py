"""
SQLAlchemy 模型定义 - AdPlacement
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Index

from . import Base  # 使用统一的 Base


class AdPlacement(Base):
    """广告位模型模型"""
    __tablename__ = 'ad_placements'


    __table_args__ = (
        Index('idx_ad_placements_code', 'code', unique=True),
        Index('idx_ad_placements_is_active', 'is_active'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='广告位 ID')

    name = Column(String(100), nullable=True, doc='广告位名称')

    code = Column(String(50), unique=True, nullable=True, doc='广告位代码')

    description = Column(Text, nullable=True, doc='广告位描述')


    position = Column(String(50), nullable=True, doc='广告位置 (header, sidebar, footer, content等)')

    width = Column(Integer, nullable=True, doc='广告位宽度')


    height = Column(Integer, nullable=True, doc='广告位高度')


    is_active = Column(Boolean, default=True, doc='是否激活')


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
            'code': self.code,
            'description': self.description,
            'position': self.position,
            'width': self.width,
            'height': self.height,
            'is_active': self.is_active,
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
        return f'<AdPlacement id={self.id}>'


