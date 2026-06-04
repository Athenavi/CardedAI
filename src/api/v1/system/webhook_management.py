"""
Webhook管理API端点

提供Webhook配置管理和事件触发的REST API接口
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.webhook import Webhook
from shared.services.notifications.webhook_service import WebhookService
from src.api.v1.core.responses import ApiResponse
from src.auth import admin_required
from src.utils.database.unified_manager import db_manager

router = APIRouter(tags=["Webhooks"])


@router.get("/", summary="获取Webhook列表")
async def list_webhooks(
        is_active: Optional[bool] = Query(None, description="是否激活"),
        limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
        offset: int = Query(0, ge=0, description="偏移量"),
        current_user=Depends(admin_required),
        db: AsyncSession = Depends(db_manager.get_session)
):
    """获取Webhook列表"""
    try:
        query = select(Webhook)

        if is_active is not None:
            query = query.where(Webhook.is_active == is_active)

        query = query.order_by(Webhook.created_at.desc()).offset(offset).limit(limit)

        result = await db.execute(query)
        webhooks = result.scalars().all()

        # 获取总数
        count_query = select(Webhook)
        if is_active is not None:
            count_query = count_query.where(Webhook.is_active == is_active)
        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())

        return ApiResponse(
            success=True,
            data={
                'webhooks': [
                    {
                        'id': w.id,
                        'name': w.name,
                        'url': w.url,
                        'events': w.events,
                        'is_active': w.is_active,
                        'created_at': w.created_at.isoformat() if w.created_at else None,
                        'updated_at': w.updated_at.isoformat() if w.updated_at else None
                    }
                    for w in webhooks
                ],
                'total': total,
                'limit': limit,
                'offset': offset
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取列表失败: {str(e)}")


@router.post("/", summary="创建Webhook")
async def create_webhook(
        name: str = Body(..., embed=True, description="Webhook名称"),
        url: str = Body(..., embed=True, description="Webhook URL"),
        events: List[str] = Body(..., embed=True, description="订阅的事件列表"),
        secret: Optional[str] = Body(None, embed=True, description="签名密钥"),
        current_user=Depends(admin_required),
        db: AsyncSession = Depends(db_manager.get_session)
):
    """创建新的Webhook"""
    try:
        service = WebhookService(db)
        webhook = await service.create_webhook(name, url, events, secret)

        return ApiResponse(
            success=True,
            data={
                'id': webhook.id,
                'name': webhook.name,
                'url': webhook.url,
                'events': webhook.events,
                'is_active': webhook.is_active,
                'created_at': webhook.created_at.isoformat() if webhook.created_at else None
            },
            message='Webhook创建成功'
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"创建失败: {str(e)}")


@router.put("/{webhook_id}", summary="更新Webhook")
async def update_webhook(
        webhook_id: int,
        name: Optional[str] = Body(None, embed=True),
        url: Optional[str] = Body(None, embed=True),
        events: Optional[List[str]] = Body(None, embed=True),
        secret: Optional[str] = Body(None, embed=True),
        is_active: Optional[bool] = Body(None, embed=True),
        current_user=Depends(admin_required),
        db: AsyncSession = Depends(db_manager.get_session)
):
    """更新Webhook配置"""
    try:
        service = WebhookService(db)

        update_data = {}
        if name is not None:
            update_data['name'] = name
        if url is not None:
            update_data['url'] = url
        if events is not None:
            update_data['events'] = events
        if secret is not None:
            update_data['secret'] = secret
        if is_active is not None:
            update_data['is_active'] = is_active

        webhook = await service.update_webhook(webhook_id, **update_data)

        if not webhook:
            return ApiResponse(success=False, error='Webhook不存在')

        return ApiResponse(
            success=True,
            data={
                'id': webhook.id,
                'name': webhook.name,
                'url': webhook.url,
                'is_active': webhook.is_active
            },
            message='Webhook更新成功'
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"更新失败: {str(e)}")


@router.delete("/{webhook_id}", summary="删除Webhook")
async def delete_webhook(
        webhook_id: int,
        current_user=Depends(admin_required),
        db: AsyncSession = Depends(db_manager.get_session)
):
    """删除Webhook"""
    try:
        service = WebhookService(db)
        success = await service.delete_webhook(webhook_id)
        
        if not success:
            return ApiResponse(success=False, error='Webhook不存在')

        return ApiResponse(success=True, message='Webhook删除成功')
    except Exception as e:
        return ApiResponse(success=False, error=f"删除失败: {str(e)}")


@router.post("/trigger", summary="触发事件")
async def trigger_event(
        event: str = Body(..., embed=True, description="事件类型"),
        payload: dict = Body(..., embed=True, description="事件数据"),
        current_user=Depends(admin_required),
        db: AsyncSession = Depends(db_manager.get_session)
):
    """
    手动触发Webhook事件
    
    - **event**: 事件类型（如 article.published）
    - **payload**: 事件数据
    """
    try:
        service = WebhookService(db)
        result = await service.trigger_event(event, payload)

        return ApiResponse(
            success=True,
            data=result,
            message=f"事件 '{event}' 已触发"
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"触发失败: {str(e)}")


@router.get("/{webhook_id}/deliveries", summary="获取投递记录")
async def get_deliveries(
        webhook_id: int,
        limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
        offset: int = Query(0, ge=0, description="偏移量"),
        current_user=Depends(admin_required),
        db: AsyncSession = Depends(db_manager.get_session)
):
    """获取Webhook的投递历史记录"""
    try:
        service = WebhookService(db)
        deliveries = await service.get_webhook_deliveries(webhook_id, limit, offset)

        return ApiResponse(
            success=True,
            data={
                'deliveries': [
                    {
                        'id': d.id,
                        'event': d.event,
                        'success': d.success,
                        'response_status': d.response_status,
                        'retry_count': d.retry_count,
                        'created_at': d.created_at.isoformat() if d.created_at else None
                    }
                    for d in deliveries
                ],
                'total': len(deliveries),
                'limit': limit,
                'offset': offset
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取投递记录失败: {str(e)}")


@router.get("/{webhook_id}/stats", summary="获取投递统计")
async def get_delivery_stats(
        webhook_id: int,
        current_user=Depends(admin_required),
        db: AsyncSession = Depends(db_manager.get_session)
):
    """获取Webhook投递统计信息"""
    try:
        service = WebhookService(db)
        stats = await service.get_delivery_stats(webhook_id)

        return ApiResponse(success=True, data=stats)
    except Exception as e:
        return ApiResponse(success=False, error=f"获取统计失败: {str(e)}")


@router.get("/events", summary="获取支持的事件列表")
async def get_supported_events(current_user=Depends(admin_required), WEBHOOK_EVENTS=None):
    """获取所有支持的Webhook事件类型"""
    try:
        return ApiResponse(
            success=True,
            data={
                'events': WEBHOOK_EVENTS,
                'total': len(WEBHOOK_EVENTS)
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取事件列表失败: {str(e)}")
