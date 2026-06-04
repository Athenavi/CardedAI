"""
SQLAlchemy 模型定义 - GlobalStyle
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime

from . import Base  # 使用统一的 Base



class GlobalStyle(Base):
    """全局样式配置模型模型"""
    __tablename__ = 'global_styles'

    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='配置 ID')

    theme_name = Column(String(100), unique=True, nullable=True, doc='主题/方案名称')

    variables_json = Column(Text, nullable=False, doc='CSS 变量 JSON (colors, fonts, spacing)')

    is_active = Column(Boolean, default=False, doc='是否当前激活')

    created_at = Column(DateTime, doc='创建时间')

    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'theme_name': self.theme_name,
            'variables_json': self.variables_json,
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
        return f'<GlobalStyle id={self.id}>'
