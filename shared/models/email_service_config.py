"""
SQLAlchemy 模型定义 - EmailServiceConfig
邮件服务配置模型，支持 SendGrid/Mailgun/SMTP 多种邮件提供商
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime
from datetime import datetime

from . import Base  # 使用统一的 Base


class EmailServiceConfig(Base):
    """邮件服务配置模型"""
    __tablename__ = 'email_service_configs'

    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='配置 ID')

    provider = Column(String(50), nullable=False, doc='邮件提供商 (sendgrid/mailgun/smtp)')

    site_id = Column(Integer, nullable=True, doc='站点 ID（多站点支持）')

    from_email = Column(String(255), nullable=False, doc='发件人邮箱')
    from_name = Column(String(255), nullable=True, doc='发件人名称')

    # API 密钥（SendGrid/Mailgun）
    api_key = Column(Text, nullable=True, doc='API Key')

    # SMTP 配置
    smtp_host = Column(String(255), nullable=True, doc='SMTP 主机')
    smtp_port = Column(Integer, nullable=True, doc='SMTP 端口')
    smtp_username = Column(String(255), nullable=True, doc='SMTP 用户名')
    smtp_password = Column(Text, nullable=True, doc='SMTP 密码')

    # 发送设置
    enable_batch_sending = Column(Boolean, default=False, doc='是否启用批量发送')
    batch_size = Column(Integer, default=50, doc='批量大小')
    daily_limit = Column(Integer, nullable=True, doc='每日发送限制')

    is_active = Column(Boolean, default=True, doc='是否激活')

    created_at = Column(DateTime, default=datetime.utcnow, doc='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, doc='更新时间')

    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥等）
        """
        data = {
            'id': self.id,
            'provider': self.provider,
            'site_id': self.site_id,
            'from_email': self.from_email,
            'from_name': self.from_name,
            'enable_batch_sending': self.enable_batch_sending,
            'batch_size': self.batch_size,
            'daily_limit': self.daily_limit,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if not exclude_sensitive:
            sensitive_data = {
                'api_key': self.api_key,
                'smtp_host': self.smtp_host,
                'smtp_port': self.smtp_port,
                'smtp_username': self.smtp_username,
                'smtp_password': self.smtp_password,
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<EmailServiceConfig id={self.id} provider={self.provider}>'
