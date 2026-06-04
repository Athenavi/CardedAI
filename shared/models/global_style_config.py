"""
SQLAlchemy 模型定义 - GlobalStyleConfig
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base



class GlobalStyleConfig(Base):
    """全局样式配置模型模型"""
    __tablename__ = 'global_style_configs'


    __table_args__ = (
        Index('idx_global_style_slug', 'slug', unique=True),
        Index('idx_global_style_is_active', 'is_active'),
        Index('idx_global_style_theme_type', 'theme_type'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='配置 ID')

    name = Column(String(100), unique=True, nullable=True, doc='配置名称（如 Dark Mode、Minimal、Corporate）')

    slug = Column(String(100), unique=True, nullable=True, doc='配置标识符')

    is_active = Column(Boolean, default=False, doc='是否当前启用')

    theme_type = Column(String(50), default='custom', doc='主题类型')

    color_scheme = Column(Text, nullable=False,
                          doc='配色方案（JSON，包含 primary、secondary、accent、background、text 等颜色）')

    typography = Column(Text, nullable=False,
                        doc='字体配置（JSON，包含 font_family、font_size_base、line_height、heading_weights 等）')


    spacing = Column(Text, nullable=False, doc='间距配置（JSON，包含 padding_base、margin_base、gap_sizes 等）')

    border_radius = Column(Text, nullable=False, doc='圆角配置（JSON，包含 sm、md、lg、xl 等级别）')

    shadows = Column(Text, nullable=True, doc='阴影配置（JSON，包含 sm、md、lg、xl 等级别）')

    breakpoints = Column(Text, nullable=True, doc='响应式断点（JSON，包含 sm、md、lg、xl 像素值）')

    css_variables = Column(Text, nullable=True, doc='自定义 CSS 变量（JSON，键值对格式）')

    preview_image = Column(String(500), nullable=True, doc='预览图 URL')

    created_by = Column(BigInteger, ForeignKey('users.id'), nullable=True, doc='创建者用户 ID')

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
            'is_active': self.is_active,
            'theme_type': self.theme_type,
            'color_scheme': self.color_scheme,
            'typography': self.typography,
            'spacing': self.spacing,
            'border_radius': self.border_radius,
            'shadows': self.shadows,
            'breakpoints': self.breakpoints,
            'css_variables': self.css_variables,
            'preview_image': self.preview_image,
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
        return f'<GlobalStyleConfig id={self.id}>'
