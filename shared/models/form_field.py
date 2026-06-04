"""
SQLAlchemy 模型定义 - FormField
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base


class FormField(Base):
    """表单字段模型模型"""
    __tablename__ = 'form_fields'


    __table_args__ = (
        Index('idx_form_fields_form_id', 'form_id'),
        Index('idx_form_fields_order', 'order_index'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='字段 ID')

    form_id = Column(BigInteger, ForeignKey('forms.id'), doc='所属表单 ID')


    label = Column(String(255), nullable=True, doc='字段标签')

    field_type = Column(String(50), nullable=True, doc='字段类型（text, email, textarea, select, checkbox, radio, number, date, file）')

    placeholder = Column(String(255), nullable=True, doc='占位符文本')

    help_text = Column(String(255), nullable=True, doc='帮助文本')

    required = Column(Boolean, default=False, doc='是否必填')


    options = Column(String(255), nullable=True, doc='选项列表（JSON格式，用于select/radio/checkbox）')

    validation_rules = Column(String(255), nullable=True, doc='验证规则（JSON格式）')

    default_value = Column(String(255), nullable=True, doc='默认值')

    order_index = Column(BigInteger, default=0, doc='显示顺序')


    is_active = Column(Boolean, default=True, doc='是否启用')


    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'form_id': self.form_id,
            'label': self.label,
            'field_type': self.field_type,
            'placeholder': self.placeholder,
            'help_text': self.help_text,
            'required': self.required,
            'options': self.options,
            'validation_rules': self.validation_rules,
            'default_value': self.default_value,
            'order_index': self.order_index,
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
        return f'<FormField id={self.id}>'


