"""
SQLAlchemy 模型定义 - Form
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Index

from . import Base  # 使用统一的 Base


class Form(Base):
    """表单模型模型"""
    __tablename__ = 'forms'


    __table_args__ = (
        Index('idx_forms_slug', 'slug', unique=True),
        Index('idx_forms_status', 'status'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='表单 ID')

    title = Column(String(255), nullable=True, doc='表单标题')

    slug = Column(String(255), unique=True, nullable=True, doc='表单标识')

    description = Column(String(255), nullable=True, doc='表单描述')

    status = Column(String(255), default='draft', doc='表单状态（draft, published, archived）')

    submit_message = Column(String(255), nullable=True, doc='提交成功消息')

    email_notification = Column(Boolean, default=False, doc='是否启用邮件通知')


    notification_email = Column(String(255), nullable=True, doc='通知邮箱地址')

    store_submissions = Column(Boolean, default=True, doc='是否存储提交数据')


    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')

    published_at = Column(DateTime, nullable=True, doc='发布时间')


    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'description': self.description,
            'status': self.status,
            'submit_message': self.submit_message,
            'email_notification': self.email_notification,
            'notification_email': self.notification_email,
            'store_submissions': self.store_submissions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<Form id={self.id}>'


