"""
邮件服务集成 - 支持 SendGrid/Mailgun/SMTP 多种邮件提供商

提供邮件服务配置管理和邮件发送功能
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.email_service_config import EmailServiceConfig
from shared.utils.logger import get_logger

logger = get_logger(__name__)

# 尝试导入可选依赖
try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


class EmailServiceIntegration:
    """
    邮件服务集成

    支持多种邮件提供商：
    - SendGrid (API)
    - Mailgun (API)
    - SMTP (标准协议)
    """

    # ==================== 配置管理 ====================

    async def get_config(
            self,
            db: AsyncSession,
            provider: str,
            site_id: Optional[int] = None
    ) -> Optional[EmailServiceConfig]:
        """
        获取邮件服务配置

        Args:
            db: 数据库会话
            provider: 邮件提供商 (sendgrid/mailgun/smtp)
            site_id: 站点 ID

        Returns:
            配置对象或 None
        """
        query = select(EmailServiceConfig).where(
            EmailServiceConfig.provider == provider,
            EmailServiceConfig.is_active == True,
        )

        if site_id is not None:
            query = query.where(EmailServiceConfig.site_id == site_id)

        result = await db.execute(query)
        return result.scalars().first()

    async def create_config(
            self,
            db: AsyncSession,
            provider: str,
            from_email: str,
            api_key: Optional[str] = None,
            smtp_host: Optional[str] = None,
            smtp_port: Optional[int] = None,
            smtp_username: Optional[str] = None,
            smtp_password: Optional[str] = None,
            from_name: Optional[str] = None,
            site_id: Optional[int] = None,
            enable_batch_sending: bool = False,
            batch_size: int = 50,
            daily_limit: Optional[int] = None,
    ) -> EmailServiceConfig:
        """
        创建邮件服务配置

        Args:
            db: 数据库会话
            provider: 邮件提供商
            from_email: 发件人邮箱
            api_key: API Key（SendGrid/Mailgun）
            smtp_host: SMTP 主机
            smtp_port: SMTP 端口
            smtp_username: SMTP 用户名
            smtp_password: SMTP 密码
            from_name: 发件人名称
            site_id: 站点 ID
            enable_batch_sending: 是否启用批量发送
            batch_size: 批量大小
            daily_limit: 每日限制

        Returns:
            创建的配置对象

        Raises:
            ValueError: 参数验证失败
        """
        # 验证提供商类型
        valid_providers = ('sendgrid', 'mailgun', 'smtp')
        if provider not in valid_providers:
            raise ValueError(f"Invalid provider: {provider}. Must be one of {valid_providers}")

        # 验证必需参数
        if provider == 'sendgrid' and not api_key:
            raise ValueError("API key is required for SendGrid")
        if provider == 'mailgun' and not api_key:
            raise ValueError("API key is required for Mailgun")
        if provider == 'smtp' and not smtp_host:
            raise ValueError("SMTP host is required for SMTP provider")

        config = EmailServiceConfig(
            provider=provider,
            from_email=from_email,
            from_name=from_name,
            api_key=api_key,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            site_id=site_id,
            enable_batch_sending=enable_batch_sending,
            batch_size=batch_size,
            daily_limit=daily_limit,
            is_active=True,
        )

        db.add(config)
        await db.flush()
        await db.refresh(config)

        logger.info(f"Email service config created: provider={provider}, id={config.id}")
        return config

    async def update_config(
            self,
            db: AsyncSession,
            config_id: int,
            updates: Dict[str, Any]
    ) -> EmailServiceConfig:
        """
        更新邮件服务配置

        Args:
            db: 数据库会话
            config_id: 配置 ID
            updates: 更新字段

        Returns:
            更新后的配置对象

        Raises:
            ValueError: 配置不存在
        """
        query = select(EmailServiceConfig).where(EmailServiceConfig.id == config_id)
        result = await db.execute(query)
        config = result.scalars().first()

        if not config:
            raise ValueError(f"Email service config not found: {config_id}")

        allowed_fields = {
            'from_email', 'from_name', 'api_key', 'smtp_host', 'smtp_port',
            'smtp_username', 'smtp_password', 'enable_batch_sending',
            'batch_size', 'daily_limit', 'is_active',
        }

        for key, value in updates.items():
            if key in allowed_fields:
                setattr(config, key, value)

        await db.flush()
        await db.refresh(config)

        logger.info(f"Email service config updated: id={config_id}")
        return config

    async def deactivate_config(
            self,
            db: AsyncSession,
            config_id: int
    ) -> None:
        """
        停用邮件服务配置

        Args:
            db: 数据库会话
            config_id: 配置 ID

        Raises:
            ValueError: 配置不存在
        """
        query = select(EmailServiceConfig).where(EmailServiceConfig.id == config_id)
        result = await db.execute(query)
        config = result.scalars().first()

        if not config:
            raise ValueError(f"Email service config not found: {config_id}")

        config.is_active = False
        await db.flush()

        logger.info(f"Email service config deactivated: id={config_id}")

    async def get_all_configs(
            self,
            db: AsyncSession,
            include_inactive: bool = False
    ) -> List[EmailServiceConfig]:
        """
        获取所有邮件服务配置

        Args:
            db: 数据库会话
            include_inactive: 是否包含非活动配置

        Returns:
            配置列表
        """
        query = select(EmailServiceConfig)

        if not include_inactive:
            query = query.where(EmailServiceConfig.is_active == True)

        query = query.order_by(EmailServiceConfig.created_at.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    # ==================== 邮件发送 ====================

    async def send_email(
            self,
            config: EmailServiceConfig,
            to_email: str,
            subject: str,
            html_content: str,
            text_content: Optional[str] = None,
            from_name: Optional[str] = None,
    ) -> bool:
        """
        发送邮件

        Args:
            config: 邮件服务配置
            to_email: 收件人邮箱
            subject: 邮件主题
            html_content: HTML 内容
            text_content: 纯文本内容
            from_name: 发件人名称（覆盖配置）

        Returns:
            是否发送成功
        """
        sender_name = from_name or config.from_name or 'FastBlog'

        try:
            if config.provider == 'sendgrid':
                return await self._send_via_sendgrid(config, to_email, subject, html_content, text_content, sender_name)
            elif config.provider == 'mailgun':
                return await self._send_via_mailgun(config, to_email, subject, html_content, text_content, sender_name)
            elif config.provider == 'smtp':
                return self._send_via_smtp(config, to_email, subject, html_content, text_content, sender_name)
            else:
                logger.error(f"Unsupported email provider: {config.provider}")
                return False

        except Exception as e:
            logger.error(f"Failed to send email via {config.provider}: {e}")
            return False

    async def send_batch_emails(
            self,
            config: EmailServiceConfig,
            recipients: List[Dict[str, str]],
            subject: str,
            html_content: str,
            text_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        批量发送邮件

        Args:
            config: 邮件服务配置
            recipients: 收件人列表 [{'email': '...', 'name': '...'}]
            subject: 邮件主题
            html_content: HTML 内容
            text_content: 纯文本内容

        Returns:
            发送结果统计 {'success': int, 'failed': int, 'details': list}
        """
        results = {
            'success': 0,
            'failed': 0,
            'details': [],
        }

        batch_size = config.batch_size or 50

        for i in range(0, len(recipients), batch_size):
            batch = recipients[i:i + batch_size]

            for recipient in batch:
                email = recipient.get('email')
                name = recipient.get('name')

                if not email:
                    results['failed'] += 1
                    results['details'].append({
                        'email': email,
                        'success': False,
                        'error': 'Missing email address',
                    })
                    continue

                success = await self.send_email(
                    config, email, subject, html_content, text_content, name
                )

                if success:
                    results['success'] += 1
                else:
                    results['failed'] += 1

                results['details'].append({
                    'email': email,
                    'success': success,
                })

        logger.info(
            f"Batch email completed via {config.provider}: "
            f"success={results['success']}, failed={results['failed']}"
        )

        return results

    # ==================== 提供商实现 ====================

    async def _send_via_sendgrid(
            self,
            config: EmailServiceConfig,
            to_email: str,
            subject: str,
            html_content: str,
            text_content: Optional[str],
            from_name: str,
    ) -> bool:
        """通过 SendGrid API 发送邮件"""
        if not HAS_HTTPX:
            logger.error("httpx is required for SendGrid integration")
            return False

        url = "https://api.sendgrid.com/v3/mail/send"
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "personalizations": [
                {"to": [{"email": to_email}]}
            ],
            "from": {"email": config.from_email, "name": from_name},
            "subject": subject,
            "content": [],
        }

        if text_content:
            payload["content"].append({"type": "text/plain", "value": text_content})
        payload["content"].append({"type": "text/html", "value": html_content})

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code in (200, 201, 202):
                logger.info(f"SendGrid: Email sent to {to_email}")
                return True
            else:
                logger.error(f"SendGrid: Failed to send email: {response.status_code} {response.text}")
                return False

    async def _send_via_mailgun(
            self,
            config: EmailServiceConfig,
            to_email: str,
            subject: str,
            html_content: str,
            text_content: Optional[str],
            from_name: str,
    ) -> bool:
        """通过 Mailgun API 发送邮件"""
        if not HAS_HTTPX:
            logger.error("httpx is required for Mailgun integration")
            return False

        # Mailgun domain is typically extracted from from_email or configured separately
        # For now, use the api_key format "domain:api_key" or just the key
        api_key = config.api_key
        domain = None

        if ':' in api_key:
            domain, api_key = api_key.split(':', 1)

        if not domain:
            logger.error("Mailgun: Domain not configured. Use 'domain:api_key' format for api_key field.")
            return False

        url = f"https://api.mailgun.net/v3/{domain}/messages"
        data = {
            "from": f"{from_name} <{config.from_email}>",
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }
        if text_content:
            data["text"] = text_content

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                data=data,
                auth=("api", api_key),
            )

            if response.status_code == 200:
                logger.info(f"Mailgun: Email sent to {to_email}")
                return True
            else:
                logger.error(f"Mailgun: Failed to send email: {response.status_code} {response.text}")
                return False

    def _send_via_smtp(
            self,
            config: EmailServiceConfig,
            to_email: str,
            subject: str,
            html_content: str,
            text_content: Optional[str],
            from_name: str,
    ) -> bool:
        """通过 SMTP 发送邮件"""
        if not config.smtp_host:
            logger.error("SMTP: Host not configured")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{from_name} <{config.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject

            if text_content:
                msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))

            port = config.smtp_port or 587

            server = smtplib.SMTP(config.smtp_host, port)
            server.ehlo()
            server.starttls()
            server.ehlo()

            username = config.smtp_username or config.from_email
            password = config.smtp_password
            if password:
                server.login(username, password)

            server.sendmail(config.from_email, [to_email], msg.as_string())
            server.quit()

            logger.info(f"SMTP: Email sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"SMTP: Failed to send email: {e}")
            return False


# 模块级单例
email_service_integration = EmailServiceIntegration()
