"""
邮件服务 - 发送邮件通知
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from shared.utils.logger import get_logger

logger = get_logger(__name__)


class EmailService:
    """邮件发送服务"""

    def __init__(self):
        # 从环境变量读取配置
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.qq.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_user)
        self.from_name = os.getenv('FROM_NAME', 'FastBlog')

    def send_email(
            self,
            to_email: str,
            subject: str,
            html_content: str,
            text_content: Optional[str] = None
    ) -> bool:
        """
        发送邮件
        
        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            html_content: HTML内容
            text_content: 纯文本内容（可选）
            
        Returns:
            bool: 是否发送成功
        """
        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP配置未完成，跳过邮件发送")
            return False

        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject

            # 添加纯文本版本
            if text_content:
                msg.attach(MIMEText(text_content, 'plain', 'utf-8'))

            # 添加HTML版本
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))

            # 连接SMTP服务器并发送
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.from_email, [to_email], msg.as_string())
            server.quit()

            logger.info(f"邮件发送成功: {to_email}")
            return True

        except Exception as e:
            logger.error(f"邮件发送失败: {str(e)}")
            return False

    def send_batch_emails(
            self,
            emails: List[str],
            subject: str,
            html_content: str,
            text_content: Optional[str] = None
    ) -> dict:
        """
        批量发送邮件
        
        Args:
            emails: 收件人邮箱列表
            subject: 邮件主题
            html_content: HTML内容
            text_content: 纯文本内容
            
        Returns:
            dict: {success: int, failed: int, details: list}
        """
        results = {
            'success': 0,
            'failed': 0,
            'details': []
        }

        for email in emails:
            success = self.send_email(email, subject, html_content, text_content)
            if success:
                results['success'] += 1
            else:
                results['failed'] += 1

            results['details'].append({
                'email': email,
                'success': success
            })

        logger.info(f"批量邮件发送完成: 成功{results['success']}, 失败{results['failed']}")
        return results


# 全局实例
email_service = EmailService()
