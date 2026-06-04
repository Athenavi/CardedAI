"""
Webhook 服务实现
负责在内容变更时向配置的端点发送实时通知
"""
import json
from datetime import datetime

import httpx
from sqlalchemy import select

from shared.models.webhook import Webhook
from shared.models.webhook_delivery import WebhookDelivery
from src.utils.database.main import get_async_session


class WebhookService:
    """Webhook 核心服务"""

    @staticmethod
    async def trigger_event(event_name: str, payload: dict):
        """触发 Webhook 事件并发送给所有订阅者"""
        async for db in get_async_session():
            query = select(Webhook).where(Webhook.is_active == True)
            result = await db.execute(query)
            webhooks = result.scalars().all()

            for wh in webhooks:
                if event_name in wh.events:
                    # 为每个 Webhook 创建独立的异步任务，不阻塞主流程
                    import asyncio
                    asyncio.create_task(WebhookService._send_delivery(wh, event_name, payload))

    @staticmethod
    async def _send_delivery(webhook: Webhook, event: str, payload: dict):
        """执行单次 Webhook 投递"""
        async for db in get_async_session():
            delivery = WebhookDelivery(
                webhook_id=webhook.id,
                event=event,
                payload=json.dumps(payload),
                status="pending",
                created_at=datetime.utcnow()
            )
            db.add(delivery)
            await db.flush()

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        webhook.url,
                        json=payload,
                        headers={"Content-Type": "application/json", "X-FastBlog-Event": event}
                    )
                    delivery.status_code = response.status_code
                    delivery.response_body = response.text[:1000]
                    delivery.status = "success" if response.status_code < 400 else "failed"
            except Exception as e:
                delivery.status = "failed"
                delivery.error_message = str(e)

            delivery.completed_at = datetime.utcnow()
            await db.commit()


webhook_service = WebhookService()
