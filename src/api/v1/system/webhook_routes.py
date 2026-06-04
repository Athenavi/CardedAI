"""
Webhook 管理 API 路由
"""
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, desc

from shared.models.user import User
from shared.models.webhook import Webhook
from shared.models.webhook_delivery import WebhookDelivery
from src.auth.auth_deps import jwt_required_dependency as jwt_required
from src.utils.database.main import get_async_session

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


class WebhookCreateRequest(BaseModel):
    url: str
    events: List[str]  # e.g., ["article.published", "comment.created"]
    is_active: bool = True


@router.post("")
async def create_webhook(
        req: WebhookCreateRequest,
        current_user: User = Depends(jwt_required)
):
    """创建新的 Webhook 订阅"""
    async for db in get_async_session():
        webhook = Webhook(
            url=req.url,
            events=req.events,
            is_active=req.is_active,
            created_by=current_user.id
        )
        db.add(webhook)
        await db.commit()
        return {"success": True, "id": webhook.id}


@router.get("/deliveries")
async def get_deliveries(
        webhook_id: int = None,
        limit: int = 50,
        current_user: User = Depends(jwt_required)
):
    """查询 Webhook 投递记录"""
    async for db in get_async_session():
        query = select(WebhookDelivery).order_by(desc(WebhookDelivery.created_at)).limit(limit)
        if webhook_id:
            query = query.where(WebhookDelivery.webhook_id == webhook_id)

        result = await db.execute(query)
        deliveries = result.scalars().all()
        return {"success": True, "data": [d.to_dict() for d in deliveries]}
