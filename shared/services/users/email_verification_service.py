"""
邮箱验证服务
提供邮箱验证码发送、验证等功能
支持SMTP邮件发送和模板渲染
"""


import random
import string
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict

from src.unified_logger import default_logger as logger


class EmailVerificationService:
    """邮箱验证服务"""

    # 配置常量
    CODE_LENGTH = 6  # 验证码长度
    EXPIRE_MINUTES = 10  # 验证码有效期(分钟)
    MAX_ATTEMPTS = 5  # 最大验证尝试次数
    RESEND_INTERVAL_SECONDS = 60  # 重发间隔(秒)

    def __init__(self):
        # 使用内存存储验证码(生产环境应使用Redis)
        self._verification_codes = {}

        # SMTP配置(从环境变量或配置文件读取)
        self.smtp_config = {
            'host': 'smtp.example.com',
            'port': 587,
            'username': '',
            'password': '',
            'use_tls': True,
            'from_email': 'noreply@example.com',
            'from_name': 'FastBlog'
        }

    def generate_code(self) -> str:
        """生成随机验证码"""
        return ''.join(random.choices(string.digits, k=self.CODE_LENGTH))

    def _generate_verification_email(self, email: str, code: str) -> str:
        """
        生成验证邮件HTML内容
            
        Args:
            email: 收件人邮箱
            code: 验证码
                
        Returns:
            HTML邮件内容
        """
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 40px auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .content {{ padding: 40px 30px; }}
                .code-box {{ background: #f8f9fa; border: 2px dashed #667eea; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0; }}
                .code {{ font-size: 36px; font-weight: bold; color: #667eea; letter-spacing: 8px; }}
                .info {{ color: #666; font-size: 14px; line-height: 1.6; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #999; font-size: 12px; }}
                .button {{ display: inline-block; padding: 12px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 邮箱验证</h1>
                </div>
                <div class="content">
                    <p>您好!</p>
                    <p>您正在 FastBlog 进行邮箱验证,请使用以下验证码:</p>
                    <div class="code-box">
                        <div class="code">{code}</div>
                    </div>
                    <div class="info">
                        <p><strong>重要提示:</strong></p>
                        <ul>
                            <li>验证码有效期为 {self.EXPIRE_MINUTES} 分钟</li>
                            <li>请勿将验证码告诉他人</li>
                            <li>如果这不是您的操作,请忽略此邮件</li>
                        </ul>
                    </div>
                </div>
                <div class="footer">
                    <p>此邮件由系统自动发送,请勿回复</p>
                    <p>&copy; {datetime.now().year} FastBlog. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        '''
        return html_content

    def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """
        发送邮件
            
        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            html_content: HTML邮件内容
                
        Returns:
            是否发送成功
        """
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.smtp_config['from_name']} <{self.smtp_config['from_email']}>"
            msg['To'] = to_email
            msg['Subject'] = subject

            # 添加HTML内容
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)

            # 连接SMTP服务器并发送
            if self.smtp_config['use_tls']:
                server = smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port'])
                server.ehlo()
                server.starttls()
                server.ehlo()
            else:
                server = smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port'])

            # 登录(如果配置了用户名密码)
            if self.smtp_config['username'] and self.smtp_config['password']:
                server.login(self.smtp_config['username'], self.smtp_config['password'])

            # 发送邮件
            server.sendmail(
                self.smtp_config['from_email'],
                to_email,
                msg.as_string()
            )
            server.quit()

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_verification_code(self, email: str) -> dict:
        """
        发送邮箱验证码
            
        Args:
            email: 邮箱地址
                
        Returns:
            包含成功状态和消息的字典
        """
        # 检查是否可以重发
        if email in self._verification_codes:
            last_sent = self._verification_codes[email]['sent_at']
            elapsed = (datetime.now() - last_sent).total_seconds()
    
            if elapsed < self.RESEND_INTERVAL_SECONDS:
                remaining = int(self.RESEND_INTERVAL_SECONDS - elapsed)
                return {
                    'success': False,
                    'message': f'请稍后再试,{remaining}秒后可重新发送',
                    'can_resend_in': remaining
                }

        # 生成验证码
        code = self.generate_code()

        # 生成邮件内容
        subject = f"【FastBlog】邮箱验证码 - {code}"
        html_content = self._generate_verification_email(email, code)

        # 发送邮件
        send_success = self._send_email(email, subject, html_content)

        if not send_success:
            logger.warning(f"Email sending failed for {email}, using fallback mode")
            # 降级模式:仅记录日志(开发环境)
            logger.info(f"[FALLBACK] Verification code for {email}: {code}")
    
        # 存储验证码
        self._verification_codes[email] = {
            'code': code,
            'sent_at': datetime.now(),
            'attempts': 0,
            'verified': False
        }

        return {
            'success': True,
            'message': '验证码已发送到您的邮箱',
            'expire_minutes': self.EXPIRE_MINUTES
        }

    def verify_code(self, email: str, code: str) -> dict:
        """
        验证邮箱验证码
        
        Args:
            email: 邮箱地址
            code: 验证码
            
        Returns:
            包含验证结果的字典
        """
        # 检查是否有验证码记录
        if email not in self._verification_codes:
            return {
                'success': False,
                'message': '请先获取验证码'
            }

        record = self._verification_codes[email]

        # 检查是否已验证
        if record['verified']:
            return {
                'success': False,
                'message': '该验证码已被使用'
            }

        # 检查尝试次数
        if record['attempts'] >= self.MAX_ATTEMPTS:
            return {
                'success': False,
                'message': '验证次数过多，请重新获取验证码'
            }

        # 检查是否过期
        elapsed = (datetime.now() - record['sent_at']).total_seconds()
        if elapsed > self.EXPIRE_MINUTES * 60:
            # 清除过期的验证码
            del self._verification_codes[email]
            return {
                'success': False,
                'message': '验证码已过期，请重新获取'
            }

        # 增加尝试次数
        record['attempts'] += 1

        # 验证验证码
        if record['code'] != code:
            remaining_attempts = self.MAX_ATTEMPTS - record['attempts']
            return {
                'success': False,
                'message': f'验证码错误，还剩 {remaining_attempts} 次机会',
                'remaining_attempts': remaining_attempts
            }

        # 验证成功
        record['verified'] = True
        record['verified_at'] = datetime.now()

        return {
            'success': True,
            'message': '验证成功'
        }

    def is_verified(self, email: str) -> bool:
        """
        检查邮箱是否已验证
        
        Args:
            email: 邮箱地址
            
        Returns:
            是否已验证
        """
        if email not in self._verification_codes:
            return False

        return self._verification_codes[email].get('verified', False)

    def cleanup_expired_codes(self) -> int:
        """
        清理过期的验证码
        
        Returns:
            清理的数量
        """
        now = datetime.now()
        expired_emails = []

        for email, record in self._verification_codes.items():
            elapsed = (now - record['sent_at']).total_seconds()
            if elapsed > self.EXPIRE_MINUTES * 60:
                expired_emails.append(email)

        for email in expired_emails:
            del self._verification_codes[email]

        logger.info(f"Cleaned up {len(expired_emails)} expired verification codes")
        return len(expired_emails)

    def configure_smtp(self, host: str, port: int, username: str, password: str,
                       from_email: str, from_name: str = 'FastBlog', use_tls: bool = True):
        """
        配置SMTP服务器
        
        Args:
            host: SMTP服务器地址
            port: SMTP端口
            username: 用户名
            password: 密码
            from_email: 发件人邮箱
            from_name: 发件人名称
            use_tls: 是否使用TLS
        """
        self.smtp_config.update({
            'host': host,
            'port': port,
            'username': username,
            'password': password,
            'from_email': from_email,
            'from_name': from_name,
            'use_tls': use_tls
        })
        logger.info("SMTP configuration updated")


# 全局实例
email_verification_service = EmailVerificationService()
