"""
通知集成服务（Slack/Discord/Webhook）

功能：
1. 通知渠道配置管理
2. 新文章发布通知
3. 评论通知
4. 系统告警
5. 自定义通知模板
"""
import json

from datetime import datetime
from typing import Optional, Dict, Any, List

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from shared.models.notification_integration import NotificationIntegration

from src.unified_logger import default_logger as logger


class NotificationIntegrationService:
    """
    通知集成服务
    
    支持 Slack、Discord 和通用 Webhook
    """

    def __init__(self):
        pass

    async def get_config(self, db: AsyncSession, platform: str, site_id: Optional[int] = None) -> Optional[
        NotificationIntegration]:
        """
        获取通知集成配置
        
        Args:
            db: 数据库会话
            platform: 平台类型（slack/discord/webhook）
            site_id: 站点 ID（可选）
            
        Returns:
            通知集成配置对象
        """
        query = select(NotificationIntegration).where(
            NotificationIntegration.platform == platform,
            NotificationIntegration.is_active == True
        )

        if site_id:
            query = query.where(NotificationIntegration.site_id == site_id)
        else:
            query = query.where(NotificationIntegration.site_id.is_(None))

        result = await db.execute(query)
        config = result.scalar_one_or_none()

        return config

    async def create_config(
            self,
            db: AsyncSession,
            platform: str,
            webhook_url: str,
            bot_token: Optional[str] = None,
            channel_id: Optional[str] = None,
            site_id: Optional[int] = None,
            enable_new_article_notification: bool = True,
            enable_comment_notification: bool = True,
            enable_system_alert: bool = True,
            notification_template: Optional[Dict] = None,
    ) -> NotificationIntegration:
        """
        创建通知集成配置
        
        Args:
            db: 数据库会话
            platform: 平台类型
            webhook_url: Webhook URL
            bot_token: Bot Token
            channel_id: 频道 ID
            site_id: 站点 ID
            enable_new_article_notification: 是否启用新文章通知
            enable_comment_notification: 是否启用评论通知
            enable_system_alert: 是否启用系统告警
            notification_template: 通知模板
            
        Returns:
            创建的配置对象
        """
        # 检查是否已存在配置
        existing = await self.get_config(db, platform, site_id)
        if existing:
            raise ValueError(f"Notification integration for {platform} already exists")

        config = NotificationIntegration(
            site_id=site_id,
            platform=platform,
            webhook_url=webhook_url,
            bot_token=bot_token,
            channel_id=channel_id,
            enable_new_article_notification=enable_new_article_notification,
            enable_comment_notification=enable_comment_notification,
            enable_system_alert=enable_system_alert,
            notification_template=json.dumps(notification_template) if notification_template else None,
            is_active=True,
        )

        db.add(config)
        await db.commit()
        await db.refresh(config)

        logger.info(f"Notification integration created for {platform}")
        return config

    async def update_config(
            self,
            db: AsyncSession,
            config_id: int,
            updates: Dict[str, Any],
    ) -> NotificationIntegration:
        """
        更新通知集成配置
        
        Args:
            db: 数据库会话
            config_id: 配置 ID
            updates: 更新字段字典
            
        Returns:
            更新后的配置对象
        """
        config = await db.get(NotificationIntegration, config_id)
        if not config:
            raise ValueError("Notification integration configuration not found")

        # 特殊处理 notification_template
        if 'notification_template' in updates and isinstance(updates['notification_template'], dict):
            updates['notification_template'] = json.dumps(updates['notification_template'])

        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)

        await db.commit()
        await db.refresh(config)

        logger.info(f"Notification integration config {config_id} updated")
        return config

    async def deactivate_config(self, db: AsyncSession, config_id: int):
        """
        停用通知集成配置
        
        Args:
            db: 数据库会话
            config_id: 配置 ID
        """
        config = await db.get(NotificationIntegration, config_id)
        if not config:
            raise ValueError("Notification integration configuration not found")

        config.is_active = False
        await db.commit()

        logger.info(f"Notification integration config {config_id} deactivated")

    async def send_notification(
            self,
            config: NotificationIntegration,
            message: str,
            title: Optional[str] = None,
            color: Optional[str] = None,
            fields: Optional[List[Dict]] = None,
    ) -> bool:
        """
        发送通知
        
        Args:
            config: 通知配置
            message: 消息内容
            title: 标题
            color: 颜色（十六进制）
            fields: 附加字段
            
        Returns:
            是否发送成功
        """
        try:
            if config.platform == 'slack':
                return await self._send_slack_notification(config, message, title, color, fields)
            elif config.platform == 'discord':
                return await self._send_discord_notification(config, message, title, color, fields)
            elif config.platform == 'webhook':
                return await self._send_webhook_notification(config, message, title, color, fields)
            else:
                logger.error(f"Unsupported platform: {config.platform}")
                return False
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False

    async def _send_slack_notification(
            self,
            config: NotificationIntegration,
            message: str,
            title: Optional[str] = None,
            color: Optional[str] = None,
            fields: Optional[List[Dict]] = None,
    ) -> bool:
        """发送 Slack 通知"""
        payload = {
            "text": message,
        }

        if title or fields:
            attachments = [{
                "color": color or "#36a64f",
            }]

            if title:
                attachments[0]["title"] = title

            if fields:
                attachments[0]["fields"] = fields

            payload["attachments"] = attachments

        async with aiohttp.ClientSession() as session:
            async with session.post(config.webhook_url, json=payload) as response:
                if response.status == 200:
                    logger.info("Slack notification sent successfully")
                    return True
                else:
                    logger.error(f"Slack notification failed: {response.status}")
                    return False

    async def _send_discord_notification(
            self,
            config: NotificationIntegration,
            message: str,
            title: Optional[str] = None,
            color: Optional[str] = None,
            fields: Optional[List[Dict]] = None,
    ) -> bool:
        """发送 Discord 通知"""
        embed = {
            "description": message,
            "color": int(color.lstrip('#'), 16) if color else 5763719,
        }

        if title:
            embed["title"] = title

        if fields:
            embed["fields"] = fields

        payload = {
            "embeds": [embed]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(config.webhook_url, json=payload) as response:
                if response.status in [200, 204]:
                    logger.info("Discord notification sent successfully")
                    return True
                else:
                    logger.error(f"Discord notification failed: {response.status}")
                    return False

    async def _send_webhook_notification(
            self,
            config: NotificationIntegration,
            message: str,
            title: Optional[str] = None,
            color: Optional[str] = None,
            fields: Optional[List[Dict]] = None,
    ) -> bool:
        """发送通用 Webhook 通知"""
        payload = {
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }

        if title:
            payload["title"] = title

        if color:
            payload["color"] = color

        if fields:
            payload["fields"] = fields

        async with aiohttp.ClientSession() as session:
            async with session.post(config.webhook_url, json=payload) as response:
                if response.status in [200, 201, 204]:
                    logger.info("Webhook notification sent successfully")
                    return True
                else:
                    logger.error(f"Webhook notification failed: {response.status}")
                    return False

    async def notify_new_article(
            self,
            db: AsyncSession,
            article_title: str,
            article_url: str,
            author_name: str,
            site_id: Optional[int] = None,
    ):
        """
        发送新文章发布通知
        
        Args:
            db: 数据库会话
            article_title: 文章标题
            article_url: 文章 URL
            author_name: 作者名称
            site_id: 站点 ID
        """
        configs = await self.get_configs_for_event(db, 'enable_new_article_notification', site_id)

        for config in configs:
            message = f"📝 新文章发布\n**{article_title}**\nby {author_name}"
            await self.send_notification(
                config,
                message,
                title="New Article Published",
                color="#36a64f",
                fields=[
                    {"name": "Author", "value": author_name, "short": True},
                    {"name": "Link", "value": article_url, "short": False},
                ]
            )

    async def notify_new_comment(
            self,
            db: AsyncSession,
            comment_content: str,
            article_title: str,
            commenter_name: str,
            site_id: Optional[int] = None,
    ):
        """
        发送新评论通知
        
        Args:
            db: 数据库会话
            comment_content: 评论内容
            article_title: 文章标题
            commenter_name: 评论者名称
            site_id: 站点 ID
        """
        configs = await self.get_configs_for_event(db, 'enable_comment_notification', site_id)

        for config in configs:
            message = f"💬 新评论\n**{commenter_name}** commented on **{article_title}**\n\n{comment_content[:200]}"
            await self.send_notification(
                config,
                message,
                title="New Comment",
                color="#2196F3",
                fields=[
                    {"name": "Commenter", "value": commenter_name, "short": True},
                    {"name": "Article", "value": article_title, "short": False},
                ]
            )

    async def notify_system_alert(
            self,
            db: AsyncSession,
            alert_message: str,
            alert_level: str = "warning",
            site_id: Optional[int] = None,
    ):
        """
        发送系统告警
        
        Args:
            db: 数据库会话
            alert_message: 告警消息
            alert_level: 告警级别（info/warning/error/critical）
            site_id: 站点 ID
        """
        configs = await self.get_configs_for_event(db, 'enable_system_alert', site_id)

        color_map = {
            "info": "#2196F3",
            "warning": "#FF9800",
            "error": "#F44336",
            "critical": "#9C27B0",
        }

        for config in configs:
            await self.send_notification(
                config,
                alert_message,
                title=f"System Alert - {alert_level.upper()}",
                color=color_map.get(alert_level, "#FF9800"),
            )

    async def get_configs_for_event(
            self,
            db: AsyncSession,
            event_field: str,
            site_id: Optional[int] = None,
    ) -> List[NotificationIntegration]:
        """
        获取指定事件的通知配置
        
        Args:
            db: 数据库会话
            event_field: 事件字段名
            site_id: 站点 ID
            
        Returns:
            配置列表
        """
        query = select(NotificationIntegration).where(
            NotificationIntegration.is_active == True,
            getattr(NotificationIntegration, event_field) == True
        )

        if site_id:
            query = query.where(NotificationIntegration.site_id == site_id)
        else:
            query = query.where(NotificationIntegration.site_id.is_(None))

        result = await db.execute(query)
        return result.scalars().all()

    async def get_all_configs(
            self,
            db: AsyncSession,
            include_inactive: bool = False,
    ) -> List[NotificationIntegration]:
        """
        获取所有通知集成配置
        
        Args:
            db: 数据库会话
            include_inactive: 是否包含非活动配置
            
        Returns:
            配置列表
        """
        query = select(NotificationIntegration)

        if not include_inactive:
            query = query.where(NotificationIntegration.is_active == True)

        result = await db.execute(query)
        return result.scalars().all()


# 全局实例
notification_integration_service = NotificationIntegrationService()
