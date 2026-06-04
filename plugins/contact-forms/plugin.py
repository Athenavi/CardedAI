"""
联系表单插件 (Contact Forms)
提供可视化表单构建器、表单提交管理、邮件通知和反垃圾保护功能
"""

import hashlib
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

from shared.services.plugins.plugin_manager.core import BasePlugin, plugin_hooks


class ContactFormsPlugin(BasePlugin):
    """
    联系表单插件
    
    功能:
    1. 可视化表单构建器 - 拖拽式表单设计
    2. 表单提交管理 - 查看和管理所有提交
    3. 邮件通知 - 新提交时发送邮件通知
    4. 反垃圾保护 - Honeypot、时间验证、关键词过滤
    """

    def __init__(self):
        super().__init__(
            plugin_id=0,
            name="联系表单",
            slug="contact-forms",
            version="1.0.0"
        )

        # 默认设置
        self.settings = {
            'enable_spam_protection': True,
            'email_notifications': True,
            'notification_email': '',
            'auto_reply': True,
            'form_fields': ['name', 'email', 'message'],
        }

        # 表单提交记录
        self.submissions: List[Dict[str, Any]] = []

        # 表单模板
        self.form_templates = [
            {
                'id': 'simple_contact',
                'name': '简单联系表单',
                'fields': ['name', 'email', 'message'],
            },
            {
                'id': 'detailed_contact',
                'name': '详细联系表单',
                'fields': ['name', 'email', 'phone', 'subject', 'message'],
            },
            {
                'id': 'feedback',
                'name': '反馈表单',
                'fields': ['name', 'email', 'subject', 'message'],
            },
        ]

        # 反垃圾保护配置
        self.spam_config = {
            'honeypot_field': 'website_url',  # 隐藏字段
            'min_submit_time': 3,  # 最小提交时间(秒)
            'blocked_keywords': ['viagra', 'casino', 'poker'],  # 屏蔽关键词
        }

    def register_hooks(self):
        """注册钩子"""
        # 表单提交处理
        plugin_hooks.add_action(
            "form_submission",
            self.handle_form_submission,
            priority=10
        )

    def activate(self):
        """激活插件"""
        super().activate()
        print("[ContactForms] Plugin activated")

    def deactivate(self):
        """停用插件"""
        super().deactivate()
        print("[ContactForms] Plugin deactivated")

    def handle_form_submission(self, submission_data: Dict[str, Any]):
        """
        处理表单提交
        
        Args:
            submission_data: 提交数据 {form_id, fields, ip, user_agent, timestamp}
        """
        try:
            # 反垃圾检查
            if self.settings.get('enable_spam_protection'):
                is_spam = self._check_spam(submission_data)
                if is_spam:
                    print(f"[ContactForms] Spam detected and blocked")
                    return {'success': False, 'error': 'Submission blocked as spam'}

            # 保存提交记录
            submission_record = {
                'id': self._generate_submission_id(),
                'form_id': submission_data.get('form_id', 'default'),
                'fields': submission_data.get('fields', {}),
                'ip': submission_data.get('ip', ''),
                'user_agent': submission_data.get('user_agent', ''),
                'timestamp': submission_data.get('timestamp', datetime.now().isoformat()),
                'status': 'new',  # new, read, replied
            }

            self.submissions.append(submission_record)

            # 发送邮件通知
            if self.settings.get('email_notifications'):
                self._send_notification_email(submission_record)

            # 发送自动回复
            if self.settings.get('auto_reply') and submission_record['fields'].get('email'):
                self._send_auto_reply(submission_record)

            print(f"[ContactForms] Form submission received: {submission_record['id']}")
            return {'success': True, 'submission_id': submission_record['id']}

        except Exception as e:
            print(f"[ContactForms] Failed to handle submission: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _check_spam(self, submission_data: Dict[str, Any]) -> bool:
        """
        检查是否为垃圾提交
        
        Args:
            submission_data: 提交数据
            
        Returns:
            是否为垃圾邮件
        """
        fields = submission_data.get('fields', {})

        # 1. Honeypot检查 - 如果隐藏字段被填充，则为垃圾邮件
        if fields.get(self.spam_config['honeypot_field']):
            print("[ContactForms] Spam detected: Honeypot field filled")
            return True

        # 2. 时间检查 - 提交太快可能是机器人
        submit_time = submission_data.get('submit_time', 0)
        if submit_time < self.spam_config['min_submit_time']:
            print(f"[ContactForms] Spam detected: Too fast ({submit_time}s)")
            return True

        # 3. 关键词检查
        message = fields.get('message', '').lower()
        for keyword in self.spam_config['blocked_keywords']:
            if keyword in message:
                print(f"[ContactForms] Spam detected: Blocked keyword '{keyword}'")
                return True

        # 4. 链接数量检查 - 过多链接可能是垃圾邮件
        link_count = message.count('http://') + message.count('https://')
        if link_count > 3:
            print(f"[ContactForms] Spam detected: Too many links ({link_count})")
            return True

        return False

    def _send_notification_email(self, submission: Dict[str, Any]):
        """
        发送通知邮件给管理员
        
        Args:
            submission: 提交记录
        """
        notification_email = self.settings.get('notification_email', '')
        if not notification_email:
            print("[ContactForms] No notification email configured")
            return

        try:
            fields = submission['fields']
            subject = f"New Contact Form Submission from {fields.get('name', 'Anonymous')}"

            body = f"""
New contact form submission received:

Name: {fields.get('name', 'N/A')}
Email: {fields.get('email', 'N/A')}
Phone: {fields.get('phone', 'N/A')}
Subject: {fields.get('subject', 'N/A')}

Message:
{fields.get('message', 'N/A')}

---
Submitted at: {submission['timestamp']}
IP Address: {submission['ip']}
            """

            # 这里应该集成实际的邮件发送服务
            # 例如: send_email(notification_email, subject, body)
            print(f"[ContactForms] Would send notification to: {notification_email}")
            print(f"[ContactForms] Email subject: {subject}")

        except Exception as e:
            print(f"[ContactForms] Failed to send notification: {str(e)}")

    def _send_auto_reply(self, submission: Dict[str, Any]):
        """
        发送自动回复给提交者
        
        Args:
            submission: 提交记录
        """
        try:
            recipient_email = submission['fields'].get('email')
            if not recipient_email:
                return

            subject = "Thank you for contacting us"
            body = f"""
Dear {submission['fields'].get('name', 'Valued Customer')},

Thank you for reaching out to us. We have received your message and will get back to you as soon as possible.

Your message:
{submission['fields'].get('message', '')}

Best regards,
The Team
            """

            # 这里应该集成实际的邮件发送服务
            print(f"[ContactForms] Would send auto-reply to: {recipient_email}")

        except Exception as e:
            print(f"[ContactForms] Failed to send auto-reply: {str(e)}")

    def get_submissions(self, form_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取表单提交记录
        
        Args:
            form_id: 表单ID过滤
            limit: 返回数量限制
            
        Returns:
            提交记录列表
        """
        filtered = self.submissions

        if form_id:
            filtered = [s for s in filtered if s['form_id'] == form_id]

        # 按时间倒序排列
        sorted_submissions = sorted(
            filtered,
            key=lambda x: x['timestamp'],
            reverse=True
        )

        return sorted_submissions[:limit]

    def get_submission_stats(self) -> Dict[str, Any]:
        """获取提交统计"""
        total = len(self.submissions)
        new_count = len([s for s in self.submissions if s['status'] == 'new'])
        read_count = len([s for s in self.submissions if s['status'] == 'read'])
        replied_count = len([s for s in self.submissions if s['status'] == 'replied'])

        # 按表单分组
        by_form = {}
        for submission in self.submissions:
            form_id = submission['form_id']
            by_form[form_id] = by_form.get(form_id, 0) + 1

        return {
            'total_submissions': total,
            'new': new_count,
            'read': read_count,
            'replied': replied_count,
            'by_form': by_form,
        }

    def update_submission_status(self, submission_id: str, status: str) -> bool:
        """
        更新提交状态
        
        Args:
            submission_id: 提交ID
            status: 新状态 (new, read, replied)
            
        Returns:
            是否成功
        """
        for submission in self.submissions:
            if submission['id'] == submission_id:
                submission['status'] = status
                print(f"[ContactForms] Updated submission {submission_id} status to {status}")
                return True
        return False

    def delete_submission(self, submission_id: str) -> bool:
        """
        删除提交记录
        
        Args:
            submission_id: 提交ID
            
        Returns:
            是否成功
        """
        original_count = len(self.submissions)
        self.submissions = [s for s in self.submissions if s['id'] != submission_id]

        if len(self.submissions) < original_count:
            print(f"[ContactForms] Deleted submission {submission_id}")
            return True
        return False

    def get_form_templates(self) -> List[Dict[str, Any]]:
        """获取表单模板列表"""
        return self.form_templates

    def generate_form_html(self, form_id: str = 'default') -> str:
        """
        生成表单HTML
        
        Args:
            form_id: 表单ID
            
        Returns:
            HTML表单代码
        """
        fields = self.settings.get('form_fields', ['name', 'email', 'message'])

        html = '<form class="contact-form" method="POST" action="/api/contact/submit">\n'

        # Honeypot字段（隐藏）
        html += f'  <div style="display:none;">\n'
        html += f'    <input type="text" name="{self.spam_config["honeypot_field"]}" tabindex="-1" autocomplete="off">\n'
        html += f'  </div>\n\n'

        # 动态字段
        field_labels = {
            'name': '姓名',
            'email': '邮箱',
            'phone': '电话',
            'subject': '主题',
            'message': '留言',
        }

        field_types = {
            'name': 'text',
            'email': 'email',
            'phone': 'tel',
            'subject': 'text',
            'message': 'textarea',
        }

        for field in fields:
            if field == 'message':
                html += f'  <div class="form-group">\n'
                html += f'    <label for="{field}">{field_labels.get(field, field)}</label>\n'
                html += f'    <textarea id="{field}" name="{field}" rows="5" required></textarea>\n'
                html += f'  </div>\n\n'
            else:
                html += f'  <div class="form-group">\n'
                html += f'    <label for="{field}">{field_labels.get(field, field)}</label>\n'
                html += f'    <input type="{field_types.get(field, "text")}" id="{field}" name="{field}" required>\n'
                html += f'  </div>\n\n'

        html += f'  <button type="submit">提交</button>\n'
        html += f'</form>\n'

        return html

    def _generate_submission_id(self) -> str:
        """生成提交ID"""
        timestamp = str(time.time())
        random_str = str(time.time_ns())
        return hashlib.md5(f"{timestamp}{random_str}".encode()).hexdigest()[:12]

    def export_submissions(self, format: str = 'csv') -> str:
        """
        导出提交记录
        
        Args:
            format: 导出格式 (csv, json)
            
        Returns:
            导出的数据
        """
        if format == 'json':
            return json.dumps(self.submissions, indent=2, ensure_ascii=False)

        elif format == 'csv':
            import csv
            import io

            if not self.submissions:
                return ""

            output = io.StringIO()
            fieldnames = ['id', 'form_id', 'timestamp', 'status', 'ip']

            # 添加动态字段名
            if self.submissions:
                sample_fields = self.submissions[0]['fields'].keys()
                fieldnames.extend(sample_fields)

            writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()

            for submission in self.submissions:
                row = {
                    'id': submission['id'],
                    'form_id': submission['form_id'],
                    'timestamp': submission['timestamp'],
                    'status': submission['status'],
                    'ip': submission['ip'],
                }
                row.update(submission['fields'])
                writer.writerow(row)

            return output.getvalue()

        return ""

    def get_settings_ui(self) -> Dict[str, Any]:
        """返回设置界面配置"""
        return {
            'fields': [
                {
                    'key': 'enable_spam_protection',
                    'type': 'boolean',
                    'label': '启用反垃圾保护',
                },
                {
                    'key': 'email_notifications',
                    'type': 'boolean',
                    'label': '启用邮件通知',
                },
                {
                    'key': 'notification_email',
                    'type': 'text',
                    'label': '通知邮箱地址',
                },
                {
                    'key': 'auto_reply',
                    'type': 'boolean',
                    'label': '自动回复',
                },
                {
                    'key': 'form_fields',
                    'type': 'multiselect',
                    'label': '表单字段',
                    'options': [
                        {'value': 'name', 'label': '姓名'},
                        {'value': 'email', 'label': '邮箱'},
                        {'value': 'phone', 'label': '电话'},
                        {'value': 'subject', 'label': '主题'},
                        {'value': 'message', 'label': '留言'},
                    ],
                },
            ],
            'actions': [
                {
                    'type': 'button',
                    'label': '导出提交记录',
                    'action': 'export_submissions',
                    'variant': 'outline',
                },
            ]
        }


# 插件实例
plugin_instance = ContactFormsPlugin()
