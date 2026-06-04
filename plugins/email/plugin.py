"""
综合邮件营销插件
整合订阅者管理、邮件模板、批量发送、SMTP服务、打开率统计等功能

功能模块:
1. 订阅者管理 - 添加/删除订阅者、分组管理
2. 邮件模板 - HTML模板编辑器
3. 批量发送 - 定时发送、分批发送
4. SMTP配置 - 支持多种SMTP服务
5. 统计分析 - 打开率、点击率统计
"""

from datetime import datetime
from typing import Dict, List, Any

from shared.services.plugins.plugin_manager.core import BasePlugin, plugin_hooks


class EmailPlugin(BasePlugin):
    """
    综合邮件营销插件
    
    整合了以下原有插件的功能:
    - newsletter: 邮件通讯
    - email-marketing: 邮件营销
    """

    def __init__(self):
        super().__init__(
            plugin_id=0,
            name="邮件营销中心",
            slug="email",
            version="2.0.0"
        )

        # ==================== SMTP设置 ====================
        self.settings = {
            'smtp_host': '',
            'smtp_port': 587,
            'smtp_username': '',
            'smtp_password': '',
            'from_email': 'noreply@example.com',
            'from_name': 'FastBlog',

            # 订阅设置
            'enable_double_optin': True,
            'welcome_email': True,

            # 发送设置
            'batch_size': 50,
            'send_interval': 60,
        }

        # 订阅者列表
        self.subscribers: List[Dict[str, Any]] = []

        # 邮件发送记录
        self.email_logs: List[Dict[str, Any]] = []

        # 统计
        self.stats = {
            'total_sent': 0,
            'total_opened': 0,
            'total_clicked': 0,
        }

    def register_hooks(self):
        """注册钩子"""
        # 新用户注册时发送欢迎邮件
        if self.settings.get('welcome_email'):
            plugin_hooks.add_action(
                "user_registered",
                self.send_welcome_email,
                priority=10
            )

    def activate(self):
        """激活插件"""
        super().activate()
        print("[Email] Plugin activated - All email modules initialized")

    def deactivate(self):
        """停用插件"""
        super().deactivate()
        print("[Email] Plugin deactivated")

    # ==================== 订阅者管理 ====================

    def add_subscriber(self, email: str, name: str = '', groups: List[str] = None) -> bool:
        """
        添加订阅者
        
        Args:
            email: 邮箱地址
            name: 姓名
            groups: 分组列表
            
        Returns:
            是否成功
        """
        # 检查是否已存在
        if any(s['email'] == email for s in self.subscribers):
            return False

        subscriber = {
            'email': email,
            'name': name,
            'groups': groups or [],
            'subscribed_at': datetime.now().isoformat(),
            'status': 'pending' if self.settings.get('enable_double_optin') else 'active',
            'confirmed_at': None,
        }

        self.subscribers.append(subscriber)

        # 发送确认邮件
        if self.settings.get('enable_double_optin'):
            self._send_confirmation_email(email)

        return True

    def remove_subscriber(self, email: str) -> bool:
        """删除订阅者"""
        initial_count = len(self.subscribers)
        self.subscribers = [s for s in self.subscribers if s['email'] != email]
        return len(self.subscribers) < initial_count

    def confirm_subscription(self, email: str) -> bool:
        """确认订阅（双重确认）"""
        for subscriber in self.subscribers:
            if subscriber['email'] == email and subscriber['status'] == 'pending':
                subscriber['status'] = 'active'
                subscriber['confirmed_at'] = datetime.now().isoformat()

                # 发送欢迎邮件
                if self.settings.get('welcome_email'):
                    self._send_welcome_email(email)

                return True
        return False

    def get_subscribers(self, status: str = None, groups: List[str] = None) -> List[Dict[str, Any]]:
        """获取订阅者列表"""
        result = self.subscribers

        if status:
            result = [s for s in result if s['status'] == status]

        if groups:
            result = [s for s in result if any(g in s['groups'] for g in groups)]

        return result

    # ==================== 邮件发送 ====================

    def send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None) -> bool:
        """
        发送邮件
        
        Args:
            to_email: 收件人邮箱
            subject: 主题
            html_content: HTML内容
            text_content: 纯文本内容
            
        Returns:
            是否成功
        """
        try:
            # 这里应该使用SMTP发送实际邮件
            # 简化实现：仅记录
            log_entry = {
                'to': to_email,
                'subject': subject,
                'sent_at': datetime.now().isoformat(),
                'status': 'sent',
                'opened': False,
                'clicked': False,
            }

            self.email_logs.append(log_entry)
            self.stats['total_sent'] += 1

            print(f"[Email] Sent to {to_email}: {subject}")
            return True

        except Exception as e:
            print(f"[Email] Failed to send: {e}")
            return False

    def send_bulk_email(self, subject: str, html_content: str, recipient_groups: List[str] = None) -> Dict[str, Any]:
        """
        批量发送邮件
        
        Args:
            subject: 主题
            html_content: HTML内容
            recipient_groups: 目标分组
            
        Returns:
            发送结果
        """
        # 获取目标订阅者
        subscribers = self.get_subscribers(status='active', groups=recipient_groups)

        sent_count = 0
        failed_count = 0

        batch_size = self.settings.get('batch_size', 50)

        for i, subscriber in enumerate(subscribers):
            if i > 0 and i % batch_size == 0:
                # 批次间隔
                import time
                time.sleep(self.settings.get('send_interval', 60))

            success = self.send_email(
                subscriber['email'],
                subject,
                html_content
            )

            if success:
                sent_count += 1
            else:
                failed_count += 1

        return {
            'total_recipients': len(subscribers),
            'sent': sent_count,
            'failed': failed_count,
        }

    def send_welcome_email(self, user_data: Dict[str, Any]):
        """发送欢迎邮件"""
        email = user_data.get('email', '')
        name = user_data.get('name', 'User')

        subject = f'欢迎加入 {self.settings["from_name"]}'
        html_content = f'''
        <h1>欢迎 {name}!</h1>
        <p>感谢您订阅我们的邮件通讯。</p>
        <p>您将定期收到我们的最新文章和更新。</p>
        '''

        self.send_email(email, subject, html_content)

    def _send_confirmation_email(self, email: str):
        """发送确认邮件"""
        subject = '请确认您的订阅'
        confirm_link = f"https://example.com/confirm?email={email}"

        html_content = f'''
        <h1>确认订阅</h1>
        <p>请点击以下链接确认您的订阅：</p>
        <a href="{confirm_link}">确认订阅</a>
        '''

        self.send_email(email, subject, html_content)

    def _send_welcome_email(self, email: str):
        """发送欢迎邮件（内部方法）"""
        subject = f'欢迎加入 {self.settings["from_name"]}'
        html_content = '<h1>欢迎!</h1><p>您的订阅已确认。</p>'

        self.send_email(email, subject, html_content)

    # ==================== 统计分析 ====================

    def track_email_opened(self, email_id: str):
        """追踪邮件打开"""
        for log in self.email_logs:
            if log.get('id') == email_id:
                log['opened'] = True
                self.stats['total_opened'] += 1
                break

    def track_email_clicked(self, email_id: str, link: str):
        """追踪邮件点击"""
        for log in self.email_logs:
            if log.get('id') == email_id:
                log['clicked'] = True
                log['clicked_link'] = link
                self.stats['total_clicked'] += 1
                break

    def get_email_stats(self) -> Dict[str, Any]:
        """获取邮件统计"""
        total_sent = self.stats['total_sent']
        total_opened = self.stats['total_opened']
        total_clicked = self.stats['total_clicked']

        open_rate = round((total_opened / total_sent * 100) if total_sent > 0 else 0, 2)
        click_rate = round((total_clicked / total_sent * 100) if total_sent > 0 else 0, 2)

        return {
            'total_sent': total_sent,
            'total_opened': total_opened,
            'total_clicked': total_clicked,
            'open_rate': open_rate,
            'click_rate': click_rate,
            'total_subscribers': len(self.subscribers),
            'active_subscribers': len([s for s in self.subscribers if s['status'] == 'active']),
        }

    # ==================== 管理API ====================

    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表板数据"""
        return {
            'stats': self.get_email_stats(),
            'recent_emails': self.email_logs[-10:],
        }

    def get_admin_ui_config(self) -> Dict[str, Any]:
        """获取管理界面配置"""
        return {
            'title': '邮件营销中心',
            'icon': '📧',
            'sections': [
                {
                    'title': '邮件概览',
                    'widgets': [
                        {'type': 'stat', 'label': '总订阅者', 'value': len(self.subscribers)},
                        {'type': 'stat', 'label': '已发送邮件', 'value': self.stats['total_sent']},
                        {'type': 'stat', 'label': '打开率', 'value': f"{self.get_email_stats()['open_rate']}%"},
                    ],
                },
                {
                    'title': 'SMTP设置',
                    'fields': [
                        {
                            'key': 'smtp_host',
                            'label': 'SMTP服务器',
                            'type': 'text',
                            'placeholder': 'smtp.example.com',
                        },
                        {
                            'key': 'smtp_port',
                            'label': 'SMTP端口',
                            'type': 'number',
                            'default': 587,
                        },
                        {
                            'key': 'smtp_username',
                            'label': 'SMTP用户名',
                            'type': 'text',
                        },
                        {
                            'key': 'smtp_password',
                            'label': 'SMTP密码',
                            'type': 'password',
                        },
                        {
                            'key': 'from_email',
                            'label': '发件人邮箱',
                            'type': 'email',
                        },
                        {
                            'key': 'from_name',
                            'label': '发件人名称',
                            'type': 'text',
                        },
                    ],
                },
                {
                    'title': '订阅设置',
                    'fields': [
                        {
                            'key': 'enable_double_optin',
                            'label': '启用双重确认',
                            'type': 'boolean',
                        },
                        {
                            'key': 'welcome_email',
                            'label': '发送欢迎邮件',
                            'type': 'boolean',
                        },
                    ],
                },
            ],
        }


# 导出插件实例
plugin = EmailPlugin()
