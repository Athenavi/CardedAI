"""
邮件服务集成（SendGrid/Mailgun/SMTP）

功能：
1. 邮件服务配置管理
2. 邮件模板管理
3. 批量发送支持
4. 发送统计
"""

from typing import Optional, Dict, Any, List

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from shared.models.email_service_config import EmailServiceConfig

from src.unified_logger import default_logger as logger


class EmailServiceIntegration:
    """
    邮件服务集成
    
    支持 SendGrid、Mailgun 和 SMTP
    """

    def __init__(self):
        pass

    async def get_config(self, db: AsyncSession, provider: Optional[str] = None, site_id: Optional[int] = None) -> \
    Optional[EmailServiceConfig]:
        """
        获取邮件服务配置
        
        Args:
            db: 数据库会话
            provider: 邮件提供商（可选）
            site_id: 站点 ID（可选）
            
        Returns:
            邮件服务配置对象
        """
        query = select(EmailServiceConfig).where(
            EmailServiceConfig.is_active == True
        )

        if provider:
            query = query.where(EmailServiceConfig.provider == provider)

        if site_id:
            query = query.where(EmailServiceConfig.site_id == site_id)
        else:
            query = query.where(EmailServiceConfig.site_id.is_(None))

        result = await db.execute(query)
        config = result.scalar_one_or_none()

        return config

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
            provider: 邮件提供商（sendgrid/mailgun/smtp）
            from_email: 发件人邮箱
            api_key: API Key（SendGrid/Mailgun）
            smtp_host: SMTP 主机
            smtp_port: SMTP 端口
            smtp_username: SMTP 用户名
            smtp_password: SMTP 密码
            from_name: 发件人名称
            site_id: 站点 ID
            enable_batch_sending: 是否启用批量发送
            batch_size: 批量发送大小
            daily_limit: 每日发送限制
            
        Returns:
            创建的配置对象
        """
        # 检查是否已存在配置
        existing = await self.get_config(db, provider, site_id)
        if existing:
            raise ValueError(f"Email service configuration for {provider} already exists")

        config = EmailServiceConfig(
            site_id=site_id,
            provider=provider,
            api_key=api_key,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            from_email=from_email,
            from_name=from_name,
            enable_batch_sending=enable_batch_sending,
            batch_size=batch_size,
            daily_limit=daily_limit,
            is_active=True,
        )

        db.add(config)
        await db.commit()
        await db.refresh(config)

        logger.info(f"Email service config created for {provider}")
        return config

    async def update_config(
            self,
            db: AsyncSession,
            config_id: int,
            updates: Dict[str, Any],
    ) -> EmailServiceConfig:
        """
        更新邮件服务配置
        
        Args:
            db: 数据库会话
            config_id: 配置 ID
            updates: 更新字段字典
            
        Returns:
            更新后的配置对象
        """
        config = await db.get(EmailServiceConfig, config_id)
        if not config:
            raise ValueError("Email service configuration not found")

        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)

        await db.commit()
        await db.refresh(config)

        logger.info(f"Email service config {config_id} updated")
        return config

    async def deactivate_config(self, db: AsyncSession, config_id: int):
        """
        停用邮件服务配置
        
        Args:
            db: 数据库会话
            config_id: 配置 ID
        """
        config = await db.get(EmailServiceConfig, config_id)
        if not config:
            raise ValueError("Email service configuration not found")

        config.is_active = False
        await db.commit()

        logger.info(f"Email service config {config_id} deactivated")

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
            from_name: 发件人名称
            
        Returns:
            是否发送成功
        """
        try:
            if config.provider == 'sendgrid':
                return await self._send_via_sendgrid(config, to_email, subject, html_content, text_content, from_name)
            elif config.provider == 'mailgun':
                return await self._send_via_mailgun(config, to_email, subject, html_content, text_content, from_name)
            elif config.provider == 'smtp':
                return await self._send_via_smtp(config, to_email, subject, html_content, text_content, from_name)
            else:
                logger.error(f"Unsupported email provider: {config.provider}")
                return False
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    async def _send_via_sendgrid(
            self,
            config: EmailServiceConfig,
            to_email: str,
            subject: str,
            html_content: str,
            text_content: Optional[str] = None,
            from_name: Optional[str] = None,
    ) -> bool:
        """通过 SendGrid 发送邮件"""
        url = "https://api.sendgrid.com/v3/mail/send"

        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "personalizations": [
                {
                    "to": [{"email": to_email}],
                    "subject": subject,
                }
            ],
            "from": {
                "email": config.from_email,
                "name": from_name or config.from_name or "FastBlog",
            },
            "content": [
                {
                    "type": "text/html",
                    "value": html_content,
                }
            ],
        }

        if text_content:
            payload["content"].append({
                "type": "text/plain",
                "value": text_content,
            })

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status in [200, 202]:
                    logger.info(f"Email sent via SendGrid to {to_email}")
                    return True
                else:
                    error_body = await response.text()
                    logger.error(f"SendGrid email failed: {response.status} - {error_body}")
                    return False

    async def _send_via_mailgun(
            self,
            config: EmailServiceConfig,
            to_email: str,
            subject: str,
            html_content: str,
            text_content: Optional[str] = None,
            from_name: Optional[str] = None,
    ) -> bool:
        """通过 Mailgun 发送邮件"""
        # Mailgun API URL 需要根据区域配置
        domain = "api.mailgun.net"  # US region
        url = f"https://{domain}/v3/{config.from_email.split('@')[1]}/messages"

        auth = aiohttp.BasicAuth(login="api", password=config.api_key)

        data = {
            "from": f"{from_name or config.from_name or 'FastBlog'} <{config.from_email}>",
            "to": to_email,
            "subject": subject,
            "html": html_content,
        }

        if text_content:
            data["text"] = text_content

        async with aiohttp.ClientSession() as session:
            async with session.post(url, auth=auth, data=data) as response:
                if response.status == 200:
                    logger.info(f"Email sent via Mailgun to {to_email}")
                    return True
                else:
                    error_body = await response.text()
                    logger.error(f"Mailgun email failed: {response.status} - {error_body}")
                    return False

    async def _send_via_smtp(
            self,
            config: EmailServiceConfig,
            to_email: str,
            subject: str,
            html_content: str,
            text_content: Optional[str] = None,
            from_name: Optional[str] = None,
    ) -> bool:
        """通过 SMTP 发送邮件"""
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{from_name or config.from_name or 'FastBlog'} <{config.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject

            if text_content:
                msg.attach(MIMEText(text_content, 'plain'))

            msg.attach(MIMEText(html_content, 'html'))

            server = smtplib.SMTP(config.smtp_host, config.smtp_port)
            server.ehlo()
            server.starttls()
            server.login(config.smtp_username, config.smtp_password)
            server.sendmail(config.from_email, to_email, msg.as_string())
            server.quit()

            logger.info(f"Email sent via SMTP to {to_email}")
            return True
        except Exception as e:
            logger.error(f"SMTP email failed: {e}")
            return False

    async def send_batch_emails(
            self,
            config: EmailServiceConfig,
            recipients: List[Dict[str, str]],
            subject: str,
            html_content: str,
            text_content: Optional[str] = None,
    ) -> Dict[str, int]:
        """
        批量发送邮件
        
        Args:
            config: 邮件服务配置
            recipients: 收件人列表 [{'email': '...', 'name': '...'}]
            subject: 邮件主题
            html_content: HTML 内容
            text_content: 纯文本内容
            
        Returns:
            发送结果统计 {'success': count, 'failed': count}
        """
        success_count = 0
        failed_count = 0

        batch_size = config.batch_size if config.enable_batch_sending else len(recipients)

        for i in range(0, len(recipients), batch_size):
            batch = recipients[i:i + batch_size]

            for recipient in batch:
                success = await self.send_email(
                    config,
                    recipient['email'],
                    subject,
                    html_content,
                    text_content,
                    recipient.get('name'),
                )

                if success:
                    success_count += 1
                else:
                    failed_count += 1

        logger.info(f"Batch email completed: {success_count} succeeded, {failed_count} failed")
        return {'success': success_count, 'failed': failed_count}

    async def get_all_configs(
            self,
            db: AsyncSession,
            include_inactive: bool = False,
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

        result = await db.execute(query)
        return result.scalars().all()


# 全局实例
email_service_integration = EmailServiceIntegration()
