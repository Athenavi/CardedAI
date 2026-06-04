"""
SQLAlchemy 模型定义 - NotificationIntegration
由代码生成器自动生成 (基于 models.yaml / routes.yaml) - 请勿手动修改
生成时间：2026-05-25 10:58:31
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Index

from . import Base  # 使用统一的 Base



class NotificationIntegration(Base):
    """通知集成配置模型（Slack/Discord等）模型"""
    __tablename__ = 'notification_integrations'


    __table_args__ = (
        Index('idx_notification_platform', 'platform'),
        Index('idx_notification_site', 'site_id'),
    )


    id = Column(BigInteger, primary_key=True, autoincrement=True, doc='配置 ID')

    site_id = Column(BigInteger, ForeignKey('sites.id'), nullable=True, doc='关联的站点 ID（为空表示全局配置）')


    platform = Column(String(50), nullable=True, doc='平台类型（slack/discord/webhook）')

    webhook_url = Column(String(500), nullable=True, doc='Webhook URL')

    bot_token = Column(String(255), nullable=True, doc='Bot Token（Discord/Slack）')

    channel_id = Column(String(100), nullable=True, doc='频道/通道 ID')

    enable_new_article_notification = Column(Boolean, default=True, doc='是否启用新文章通知')


    enable_comment_notification = Column(Boolean, default=True, doc='是否启用评论通知')


    enable_system_alert = Column(Boolean, default=True, doc='是否启用系统告警')

    notification_template = Column(Text, nullable=True, doc='通知模板（JSON格式）')

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
            'platform': self.platform,
            'webhook_url': self.webhook_url,
            'bot_token': self.bot_token,
            'channel_id': self.channel_id,
            'enable_new_article_notification': self.enable_new_article_notification,
            'enable_comment_notification': self.enable_comment_notification,
            'enable_system_alert': self.enable_system_alert,
            'notification_template': self.notification_template,
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
        return f'<NotificationIntegration id={self.id}>'
