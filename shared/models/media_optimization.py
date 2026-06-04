"""
SQLAlchemy 模型定义 - MediaOptimization
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base


class MediaOptimization(Base):
    """媒体优化配置模型（支持 WebP 转换、多尺寸生成、CDN 集成）模型"""
    __tablename__ = 'media_optimizations'

    __table_args__ = (
        Index('idx_media_optimization_media', 'media_id'),
        Index('idx_media_optimization_status', 'optimization_status'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='配置 ID')

    media_id = Column(BigInteger, ForeignKey('media.id'), doc='媒体 ID')

    webp_url = Column(String(500), nullable=True, doc='WebP 格式 URL')

    sizes_json = Column(Text, nullable=True, doc='多尺寸 JSON (thumbnail, medium, large)')

    cdn_url = Column(String(500), nullable=True, doc='CDN URL')

    optimization_status = Column(String(20), default='pending', doc='优化状态 (pending, processing, completed, failed)')

    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')

    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'media_id': self.media_id,
            'webp_url': self.webp_url,
            'sizes_json': self.sizes_json,
            'cdn_url': self.cdn_url,
            'optimization_status': self.optimization_status,
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
        return f'<MediaOptimization id={self.id}>'
