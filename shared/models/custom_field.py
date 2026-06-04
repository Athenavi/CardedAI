"""
SQLAlchemy 模型定义 - CustomField
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey

from . import Base  # 使用统一的 Base


class CustomField(Base):
    """自定义字段模型模型"""
    __tablename__ = 'custom_fields'




    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='字段 ID')

    user = Column(BigInteger, ForeignKey('users.id'), doc='用户')


    field_name = Column(String(100), nullable=True, doc='字段名称')

    field_value = Column(String(255), nullable=True, doc='字段值')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'user': self.user,
            'field_name': self.field_name,
            'field_value': self.field_value,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<CustomField id={self.id}>'


