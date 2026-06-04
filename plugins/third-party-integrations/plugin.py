"""
第三方服务集成插件
统一管理 Google Analytics、Baidu Analytics、Slack、Discord、SendGrid 等第三方服务
"""
from typing import Dict, Any

from shared.services.notifications.notification_service import notification_service
from shared.services.plugins.plugin_manager.core import BasePlugin, plugin_hooks


class ThirdPartyIntegrationsPlugin(BasePlugin):
    """
    第三方服务集成插件
    
    功能:
    1. Google Analytics 集成（页面追踪、事件追踪）
    2. Baidu Analytics 集成
    3. Slack 通知集成
    4. Discord 通知集成
    5. SendGrid/Mailgun 邮件服务集成
    6. 统一配置管理
    """

    def __init__(self):
        super().__init__(
            plugin_id=0,
            name="第三方服务集成",
            slug="third-party-integrations",
            version="1.0.0"
        )

        # 默认设置
        self.settings = {
            # Google Analytics
            'enable_google_analytics': False,
            'google_analytics_id': '',  # G-XXXXXXXXXX

            # Baidu Analytics
            'enable_baidu_analytics': False,
            'baidu_analytics_id': '',  # UM-XXXXXXXX-X

            # Slack
            'enable_slack_notifications': False,
            'slack_webhook_url': '',
            'slack_notify_on_article': True,
            'slack_notify_on_comment': True,
            'slack_notify_on_error': True,

            # Discord
            'enable_discord_notifications': False,
            'discord_webhook_url': '',
            'discord_notify_on_article': True,
            'discord_notify_on_comment': True,
            'discord_notify_on_error': True,

            # Email (SendGrid/Mailgun)
            'enable_email_notifications': False,
            'email_service': 'smtp',  # smtp, sendgrid, mailgun
            'email_smtp_server': '',
            'email_smtp_port': 587,
            'email_username': '',
            'email_password': '',
            'email_from': '',
            'email_to': [],

            # SendGrid
            'sendgrid_api_key': '',
            'sendgrid_from_email': '',

            # Mailgun
            'mailgun_api_key': '',
            'mailgun_domain': '',
            'mailgun_from_email': '',
        }

    def register_hooks(self):
        """注册钩子"""
        # 初始化通知服务
        self._initialize_notification_service()

        # 在页面头部注入分析代码
        if self.settings.get('enable_google_analytics') or self.settings.get('enable_baidu_analytics'):
            plugin_hooks.add_action(
                "page_head",
                self.inject_analytics_codes,
                priority=5
            )

        # 文章发布通知
        if (self.settings.get('enable_slack_notifications') and self.settings.get('slack_notify_on_article')) or \
                (self.settings.get('enable_discord_notifications') and self.settings.get('discord_notify_on_article')):
            plugin_hooks.add_action(
                "article_published",
                self.on_article_published,
                priority=10
            )

        # 评论通知
        if (self.settings.get('enable_slack_notifications') and self.settings.get('slack_notify_on_comment')) or \
                (self.settings.get('enable_discord_notifications') and self.settings.get('discord_notify_on_comment')):
            plugin_hooks.add_action(
                "comment_created",
                self.on_comment_created,
                priority=10
            )

    def _initialize_notification_service(self):
        """初始化通知服务"""
        # 配置 Slack
        if self.settings.get('enable_slack_notifications') and self.settings.get('slack_webhook_url'):
            notification_service.configure_slack(self.settings['slack_webhook_url'])

        # 配置 Discord
        if self.settings.get('enable_discord_notifications') and self.settings.get('discord_webhook_url'):
            notification_service.configure_discord(self.settings['discord_webhook_url'])

        # 配置邮件
        if self.settings.get('enable_email_notifications'):
            email_config = self._build_email_config()
            if email_config:
                notification_service.configure_email(email_config)

    def _build_email_config(self) -> Dict[str, Any]:
        """构建邮件配置"""
        service = self.settings.get('email_service', 'smtp')

        if service == 'smtp':
            return {
                'smtp_server': self.settings.get('email_smtp_server', ''),
                'smtp_port': self.settings.get('email_smtp_port', 587),
                'username': self.settings.get('email_username', ''),
                'password': self.settings.get('email_password', ''),
                'from_email': self.settings.get('email_from', ''),
                'to_emails': self.settings.get('email_to', []),
            }
        elif service == 'sendgrid':
            # SendGrid 使用 SMTP 接口
            return {
                'smtp_server': 'smtp.sendgrid.net',
                'smtp_port': 587,
                'username': 'apikey',
                'password': self.settings.get('sendgrid_api_key', ''),
                'from_email': self.settings.get('sendgrid_from_email', ''),
                'to_emails': self.settings.get('email_to', []),
            }
        elif service == 'mailgun':
            # Mailgun 使用 SMTP 接口
            return {
                'smtp_server': f'smtp.mailgun.org',
                'smtp_port': 587,
                'username': f'postmaster@{self.settings.get("mailgun_domain", "")}',
                'password': self.settings.get('mailgun_api_key', ''),
                'from_email': self.settings.get('mailgun_from_email', ''),
                'to_emails': self.settings.get('email_to', []),
            }

        return None

    def inject_analytics_codes(self, context: Dict[str, Any]):
        """
        注入分析代码到页面头部
        
        Args:
            context: 上下文数据
        """
        scripts = []

        # Google Analytics 4
        if self.settings.get('enable_google_analytics') and self.settings.get('google_analytics_id'):
            ga_script = self._generate_ga4_code(self.settings['google_analytics_id'])
            scripts.append(ga_script)

        # Baidu Analytics
        if self.settings.get('enable_baidu_analytics') and self.settings.get('baidu_analytics_id'):
            baidu_script = self._generate_baidu_code(self.settings['baidu_analytics_id'])
            scripts.append(baidu_script)

        # 添加到上下文
        if scripts:
            if 'tracking_scripts' not in context:
                context['tracking_scripts'] = []
            context['tracking_scripts'].extend(scripts)

    def _generate_ga4_code(self, measurement_id: str) -> str:
        """生成Google Analytics 4追踪代码"""
        return f'''
<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id={measurement_id}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{measurement_id}');
</script>
'''

    def _generate_baidu_code(self, analytics_id: str) -> str:
        """生成百度统计代码"""
        return f'''
<!-- Baidu Analytics -->
<script>
  var _hmt = _hmt || [];
  (function() {{
    var hm = document.createElement("script");
    hm.src = "https://hm.baidu.com/hm.js?{analytics_id}";
    var s = document.getElementsByTagName("script")[0]; 
    s.parentNode.insertBefore(hm, s);
  }})();
</script>
'''

    async def on_article_published(self, article_data: Dict[str, Any]):
        """
        文章发布事件处理
        
        Args:
            article_data: 文章数据 {id, title, url, author_name}
        """
        try:
            await notification_service.send_article_published_notification(
                article_title=article_data.get('title', ''),
                article_url=article_data.get('url', ''),
                author_name=article_data.get('author_name', '')
            )
        except Exception as e:
            print(f"[ThirdPartyIntegrations] Failed to send article notification: {e}")

    async def on_comment_created(self, comment_data: Dict[str, Any]):
        """
        评论创建事件处理
        
        Args:
            comment_data: 评论数据 {article_title, article_url, commenter_name, comment_preview}
        """
        try:
            await notification_service.send_comment_notification(
                article_title=comment_data.get('article_title', ''),
                article_url=comment_data.get('article_url', ''),
                commenter_name=comment_data.get('commenter_name', ''),
                comment_preview=comment_data.get('comment_preview', '')
            )
        except Exception as e:
            print(f"[ThirdPartyIntegrations] Failed to send comment notification: {e}")

    def get_settings_schema(self) -> Dict[str, Any]:
        """获取设置模式"""
        return {
            'sections': [
                {
                    'title': 'Google Analytics',
                    'fields': [
                        {
                            'key': 'enable_google_analytics',
                            'type': 'boolean',
                            'label': '启用 Google Analytics',
                        },
                        {
                            'key': 'google_analytics_id',
                            'type': 'text',
                            'label': 'Measurement ID',
                            'placeholder': 'G-XXXXXXXXXX',
                            'help': 'GA4 Measurement ID',
                        },
                    ]
                },
                {
                    'title': 'Baidu Analytics',
                    'fields': [
                        {
                            'key': 'enable_baidu_analytics',
                            'type': 'boolean',
                            'label': '启用百度统计',
                        },
                        {
                            'key': 'baidu_analytics_id',
                            'type': 'text',
                            'label': '站点ID',
                            'placeholder': 'UM-XXXXXXXX-X',
                        },
                    ]
                },
                {
                    'title': 'Slack 通知',
                    'fields': [
                        {
                            'key': 'enable_slack_notifications',
                            'type': 'boolean',
                            'label': '启用 Slack 通知',
                        },
                        {
                            'key': 'slack_webhook_url',
                            'type': 'password',
                            'label': 'Webhook URL',
                            'help': 'Slack Incoming Webhook URL',
                        },
                        {
                            'key': 'slack_notify_on_article',
                            'type': 'boolean',
                            'label': '新文章通知',
                        },
                        {
                            'key': 'slack_notify_on_comment',
                            'type': 'boolean',
                            'label': '新评论通知',
                        },
                        {
                            'key': 'slack_notify_on_error',
                            'type': 'boolean',
                            'label': '错误告警',
                        },
                    ]
                },
                {
                    'title': 'Discord 通知',
                    'fields': [
                        {
                            'key': 'enable_discord_notifications',
                            'type': 'boolean',
                            'label': '启用 Discord 通知',
                        },
                        {
                            'key': 'discord_webhook_url',
                            'type': 'password',
                            'label': 'Webhook URL',
                            'help': 'Discord Webhook URL',
                        },
                        {
                            'key': 'discord_notify_on_article',
                            'type': 'boolean',
                            'label': '新文章通知',
                        },
                        {
                            'key': 'discord_notify_on_comment',
                            'type': 'boolean',
                            'label': '新评论通知',
                        },
                        {
                            'key': 'discord_notify_on_error',
                            'type': 'boolean',
                            'label': '错误告警',
                        },
                    ]
                },
                {
                    'title': '邮件服务',
                    'fields': [
                        {
                            'key': 'enable_email_notifications',
                            'type': 'boolean',
                            'label': '启用邮件通知',
                        },
                        {
                            'key': 'email_service',
                            'type': 'select',
                            'label': '邮件服务商',
                            'options': [
                                {'value': 'smtp', 'label': 'SMTP'},
                                {'value': 'sendgrid', 'label': 'SendGrid'},
                                {'value': 'mailgun', 'label': 'Mailgun'},
                            ],
                        },
                        {
                            'key': 'email_to',
                            'type': 'array',
                            'label': '收件人邮箱',
                            'help': '多个邮箱用逗号分隔',
                        },
                    ]
                },
            ],
            'actions': [
                {
                    'type': 'button',
                    'label': '测试 Slack 通知',
                    'action': 'test_slack',
                    'variant': 'outline',
                },
                {
                    'type': 'button',
                    'label': '测试 Discord 通知',
                    'action': 'test_discord',
                    'variant': 'outline',
                },
                {
                    'type': 'button',
                    'label': '测试邮件',
                    'action': 'test_email',
                    'variant': 'outline',
                },
            ]
        }


# 插件实例
plugin_instance = ThirdPartyIntegrationsPlugin()
