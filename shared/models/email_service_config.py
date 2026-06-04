"""
SQLAlchemy 模型定义 - EmailServiceConfig
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base



class EmailServiceConfig(Base):
    """邮件服务配置模型（SendGrid/Mailgun等）模型"""
    __tablename__ = 'email_service_configs'


    __table_args__ = (
        Index('idx_email_provider', 'provider'),
        Index('idx_email_site', 'site_id'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='配置 ID')

    site_id = Column(BigInteger, ForeignKey('sites.id'), nullable=True, doc='关联的站点 ID（为空表示全局配置）')


    provider = Column(String(50), nullable=True, doc='邮件服务提供商（sendgrid/mailgun/smtp）')

    api_key = Column(String(255), nullable=True, doc='API Key')

    smtp_host = Column(String(255), nullable=True, doc='SMTP 主机')

    smtp_port = Column(Integer, nullable=True, doc='SMTP 端口')


    smtp_username = Column(String(255), nullable=True, doc='SMTP 用户名')

    smtp_password = Column(String(255), nullable=True, doc='SMTP 密码')

    from_email = Column(String(255), nullable=True, doc='发件人邮箱')

    from_name = Column(String(255), nullable=True, doc='发件人名称')

    enable_batch_sending = Column(Boolean, default=False, doc='是否启用批量发送')


    batch_size = Column(Integer, default=50, doc='批量发送大小')

    daily_limit = Column(Integer, nullable=True, doc='每日发送限制')

    is_active = Column(Boolean, default=False, doc='是否激活')

    created_at = Column(DateTime, doc='创建时间')

    updated_at = Column(DateTime, doc='更新时间')

    def to_dict(self, exclude_sensitive=True):
        """转换为字典

        Args:
            exclude_sensitive: 是否排除敏感字段（密码、密钥、token 等）
        """
        data = {
            'id': self.id,
            'site_id': self.site_id,
            'provider': self.provider,
            'api_key': self.api_key,
            'smtp_host': self.smtp_host,
            'smtp_port': self.smtp_port,
            'smtp_username': self.smtp_username,
            'smtp_password': self.smtp_password,
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
            }
            data.update(sensitive_data)

        return data

    def __repr__(self):
        """字符串表示"""
        return f'<EmailServiceConfig id={self.id}>'
