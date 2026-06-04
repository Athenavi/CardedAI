"""
SQLAlchemy 模型定义 - SystemSettings
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime

from . import Base  # 使用统一的 Base


class SystemSettings(Base):
    """系统设置模型模型"""
    __tablename__ = 'system_settings'




    id = Column(Integer, primary_key=True, autoincrement=True, doc='设置 ID')

    setting_key = Column(String(100), nullable=True, doc='设置键')

    setting_value = Column(String(255), nullable=True, doc='设置值')

    setting_type = Column(String(255), default='string', doc='设置类型')

    description = Column(String(255), nullable=True, doc='描述')

    is_public = Column(Boolean, default=False, doc='是否公开')


    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'setting_key': self.setting_key,
            'setting_value': self.setting_value,
            'setting_type': self.setting_type,
            'description': self.description,
            'is_public': self.is_public,
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
        return f'<SystemSettings id={self.id}>'


