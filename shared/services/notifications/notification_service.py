"""
第三方通知服务集成
支持 Slack、Discord、Email 等通知渠道
"""
import json

from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    import aiohttp

    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

from src.unified_logger import default_logger as logger


class NotificationService:
    """
    通知服务
    
    支持多种通知渠道：
    - Slack Webhook
    - Discord Webhook
    - Email (SMTP)
    """

    def __init__(self):
        self.slack_webhook_url = None
        self.discord_webhook_url = None
        self.email_config = None

    def configure_slack(self, webhook_url: str):
        """
        配置 Slack Webhook
        
        Args:
            webhook_url: Slack Incoming Webhook URL
        """
        self.slack_webhook_url = webhook_url
        logger.info("Slack notification configured")

    def configure_discord(self, webhook_url: str):
        """
        配置 Discord Webhook
        
        Args:
            webhook_url: Discord Webhook URL
        """
        self.discord_webhook_url = webhook_url
        logger.info("Discord notification configured")

    def configure_email(self, config: Dict[str, Any]):
        """
        配置邮件服务
        
        Args:
            config: 邮件配置 {
                'smtp_server': 'smtp.example.com',
                'smtp_port': 587,
                'username': 'user@example.com',
                'password': 'password',
                'from_email': 'noreply@example.com',
                'to_emails': ['admin@example.com']
            }
        """
        self.email_config = config
        logger.info("Email notification configured")

    async def send_slack_notification(
            self,
            message: str,
            title: Optional[str] = None,
            color: str = "#36a64f",
            fields: Optional[List[Dict]] = None
    ) -> bool:
        """
        发送 Slack 通知
        
        Args:
            message: 消息内容
            title: 标题
            color: 颜色（十六进制）
            fields: 附加字段
            
        Returns:
            是否发送成功
        """
        if not self.slack_webhook_url:
            logger.warning("Slack webhook not configured")
            return False

        if not HAS_AIOHTTP:
            logger.error("aiohttp not installed")
            return False

        try:
            # 构建 Slack 消息
            attachment = {
                "color": color,
                "text": message,
                "ts": int(datetime.now().timestamp())
            }

            if title:
                attachment["title"] = title

            if fields:
                attachment["fields"] = fields

            payload = {
                "attachments": [attachment]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                        self.slack_webhook_url,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info("Slack notification sent successfully")
                        return True
                    else:
                        logger.error(f"Slack notification failed: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False

    async def send_discord_notification(
            self,
            message: str,
            title: Optional[str] = None,
            color: int = 0x36a64f,
            fields: Optional[List[Dict]] = None
    ) -> bool:
        """
        发送 Discord 通知
        
        Args:
            message: 消息内容
            title: 标题
            color: 颜色（十进制整数）
            fields: 附加字段
            
        Returns:
            是否发送成功
        """
        if not self.discord_webhook_url:
            logger.warning("Discord webhook not configured")
            return False

        if not HAS_AIOHTTP:
            logger.error("aiohttp not installed")
            return False

        try:
            # 构建 Discord Embed
            embed = {
                "description": message,
                "color": color,
                "timestamp": datetime.now().isoformat()
            }

            if title:
                embed["title"] = title

            if fields:
                embed["fields"] = fields

            payload = {
                "embeds": [embed]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                        self.discord_webhook_url,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status in [200, 204]:
                        logger.info("Discord notification sent successfully")
                        return True
                    else:
                        logger.error(f"Discord notification failed: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
            return False

    def send_email_notification(
            self,
            subject: str,
            html_content: str,
            to_emails: Optional[List[str]] = None
    ) -> bool:
        """
        发送邮件通知
        
        Args:
            subject: 邮件主题
            html_content: HTML内容
            to_emails: 收件人列表（如果为None则使用配置的默认收件人）
            
        Returns:
            是否发送成功
        """
        if not self.email_config:
            logger.warning("Email not configured")
            return False

        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            config = self.email_config

            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = config['from_email']
            msg['To'] = ', '.join(to_emails or config['to_emails'])

            # 添加HTML内容
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)

            # 发送邮件
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            server.ehlo()
            server.starttls()
            server.login(config['username'], config['password'])
            server.sendmail(
                config['from_email'],
                to_emails or config['to_emails'],
                msg.as_string()
            )
            server.quit()

            logger.info("Email notification sent successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False

    async def send_article_published_notification(
            self,
            article_title: str,
            article_url: str,
            author_name: str
    ):
        """
        发送文章发布通知
        
        Args:
            article_title: 文章标题
            article_url: 文章URL
            author_name: 作者名称
        """
        message = f"新文章已发布：**{article_title}**\n作者：{author_name}\n查看：{article_url}"

        # 发送到 Slack
        if self.slack_webhook_url:
            await self.send_slack_notification(
                message=message,
                title="📝 新文章发布",
                color="#36a64f",
                fields=[
                    {"title": "文章", "value": article_title, "short": False},
                    {"title": "作者", "value": author_name, "short": True},
                    {"title": "链接", "value": f"<{article_url}|查看详情>", "short": True},
                ]
            )

        # 发送到 Discord
        if self.discord_webhook_url:
            await self.send_discord_notification(
                message=message,
                title="📝 新文章发布",
                color=0x36a64f,
                fields=[
                    {"name": "文章", "value": article_title, "inline": False},
                    {"name": "作者", "value": author_name, "inline": True},
                    {"name": "链接", "value": f"[查看详情]({article_url})", "inline": True},
                ]
            )

    async def send_comment_notification(
            self,
            article_title: str,
            article_url: str,
            commenter_name: str,
            comment_preview: str
    ):
        """
        发送评论通知
        
        Args:
            article_title: 文章标题
            article_url: 文章URL
            commenter_name: 评论者名称
            comment_preview: 评论预览
        """
        message = f"**{commenter_name}** 在文章 **{article_title}** 下发表了评论\n\n{comment_preview[:200]}"

        # 发送到 Slack
        if self.slack_webhook_url:
            await self.send_slack_notification(
                message=message,
                title="💬 新评论",
                color="#ff9500",
                fields=[
                    {"title": "文章", "value": f"<{article_url}|{article_title}>", "short": False},
                    {"title": "评论者", "value": commenter_name, "short": True},
                ]
            )

        # 发送到 Discord
        if self.discord_webhook_url:
            await self.send_discord_notification(
                message=message,
                title="💬 新评论",
                color=0xff9500,
                fields=[
                    {"name": "文章", "value": f"[{article_title}]({article_url})", "inline": False},
                    {"name": "评论者", "value": commenter_name, "inline": True},
                ]
            )

    async def send_system_alert(
            self,
            alert_type: str,
            message: str,
            severity: str = "warning"
    ):
        """
        发送系统告警
        
        Args:
            alert_type: 告警类型
            message: 告警消息
            severity: 严重程度 (info, warning, error, critical)
        """
        color_map = {
            "info": "#36a64f",
            "warning": "#ff9500",
            "error": "#ff0000",
            "critical": "#990000"
        }

        emoji_map = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🚨"
        }

        color = color_map.get(severity, "#ff9500")
        emoji = emoji_map.get(severity, "⚠️")

        full_message = f"{emoji} **{alert_type}**\n\n{message}"

        # 发送到 Slack
        if self.slack_webhook_url:
            await self.send_slack_notification(
                message=full_message,
                title=f"系统告警 - {severity.upper()}",
                color=color
            )

        # 发送到 Discord
        if self.discord_webhook_url:
            await self.send_discord_notification(
                message=full_message,
                title=f"系统告警 - {severity.upper()}",
                color=int(color.lstrip('#'), 16)
            )

        # 发送邮件（仅严重告警）
        if severity in ['error', 'critical'] and self.email_config:
            html_content = f"""
            <h2>{emoji} 系统告警 - {severity.upper()}</h2>
            <p><strong>类型：</strong>{alert_type}</p>
            <p><strong>消息：</strong></p>
            <pre>{message}</pre>
            <p><small>时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
            """
            self.send_email_notification(
                subject=f"[FastBlog] 系统告警 - {alert_type}",
                html_content=html_content
            )


# 全局实例
notification_service = NotificationService()
