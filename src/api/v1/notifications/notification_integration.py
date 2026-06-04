"""
通知集成 API（Slack/Discord/Webhook）

提供通知渠道配置管理和通知发送功能
"""
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from shared.services.notifications.notification_integration_service import notification_integration_service
from src.api.v1.core.responses import ApiResponse
from src.api.v1.system.multisite import check_admin_permission
from src.auth.auth_deps import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["notifications"])


@router.get("/integrations/{platform}", summary="获取通知集成配置")
async def get_notification_config(
        platform: str,
        site_id: Optional[int] = Query(None, description="站点 ID"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取通知集成配置
    
    Args:
        platform: 平台类型（slack/discord/webhook）
        site_id: 站点 ID
        
    Returns:
        通知集成配置
    """
    try:
        config = await notification_integration_service.get_config(db, platform, site_id)

        if not config:
            return ApiResponse(
                success=True,
                data=None,
                message=f"No {platform} integration configured"
            )

        return ApiResponse(
            success=True,
            data={
                'id': config.id,
                'platform': config.platform,
                'webhook_url': config.webhook_url[:50] + '...' if config.webhook_url else None,
                'channel_id': config.channel_id,
                'enable_new_article_notification': config.enable_new_article_notification,
                'enable_comment_notification': config.enable_comment_notification,
                'enable_system_alert': config.enable_system_alert,
                'is_active': config.is_active,
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/integrations/{platform}", summary="创建通知集成配置")
async def create_notification_config(
        platform: str,
        webhook_url: str = Body(..., description="Webhook URL"),
        bot_token: Optional[str] = Body(None, description="Bot Token"),
        channel_id: Optional[str] = Body(None, description="Channel ID"),
        site_id: Optional[int] = Body(None, description="站点 ID"),
        enable_new_article_notification: bool = Body(True, description="新文章通知"),
        enable_comment_notification: bool = Body(True, description="评论通知"),
        enable_system_alert: bool = Body(True, description="系统告警"),
        notification_template: Optional[Dict] = Body(None, description="通知模板"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    创建通知集成配置
    
    Args:
        platform: 平台类型（slack/discord/webhook）
        
    Returns:
        创建的配置
    """
    try:
        # 检查权限
        has_permission = await check_admin_permission(db, current_user.id)
        if not has_permission:
            return ApiResponse(success=False, error="Insufficient permissions")

        config = await notification_integration_service.create_config(
            db=db,
            platform=platform,
            webhook_url=webhook_url,
            bot_token=bot_token,
            channel_id=channel_id,
            site_id=site_id,
            enable_new_article_notification=enable_new_article_notification,
            enable_comment_notification=enable_comment_notification,
            enable_system_alert=enable_system_alert,
            notification_template=notification_template,
        )

        return ApiResponse(
            success=True,
            data={
                'id': config.id,
                'platform': config.platform,
            },
            message=f"{platform.capitalize()} integration created successfully"
        )

    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.put("/integrations/{config_id}", summary="更新通知集成配置")
async def update_notification_config(
        config_id: int,
        updates: Dict[str, Any] = Body(..., description="更新字段"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    更新通知集成配置
    
    Args:
        config_id: 配置 ID
        updates: 更新字段
        
    Returns:
        更新后的配置
    """
    try:
        # 检查权限
        has_permission = await check_admin_permission(db, current_user.id)
        if not has_permission:
            return ApiResponse(success=False, error="Insufficient permissions")

        config = await notification_integration_service.update_config(db, config_id, updates)

        return ApiResponse(
            success=True,
            data={
                'id': config.id,
                'platform': config.platform,
            },
            message="Notification integration updated successfully"
        )

    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.delete("/integrations/{config_id}", summary="停用通知集成配置")
async def deactivate_notification_config(
        config_id: int,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    停用通知集成配置
    
    Args:
        config_id: 配置 ID
        
    Returns:
        操作结果
    """
    try:
        # 检查权限
        has_permission = await check_admin_permission(db, current_user.id)
        if not has_permission:
            return ApiResponse(success=False, error="Insufficient permissions")

        await notification_integration_service.deactivate_config(db, config_id)

        return ApiResponse(
            success=True,
            message="Notification integration deactivated successfully"
        )

    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/test", summary="测试通知")
async def test_notification(
        platform: str = Body(..., description="平台类型"),
        message: str = Body("This is a test notification", description="测试消息"),
        site_id: Optional[int] = Body(None, description="站点 ID"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    发送测试通知
    
    Args:
        platform: 平台类型
        message: 测试消息
        
    Returns:
        测试结果
    """
    try:
        config = await notification_integration_service.get_config(db, platform, site_id)

        if not config:
            return ApiResponse(
                success=False,
                error=f"No {platform} integration configured"
            )

        success = await notification_integration_service.send_notification(
            config,
            message,
            title="Test Notification",
            color="#36a64f"
        )

        if success:
            return ApiResponse(
                success=True,
                message="Test notification sent successfully"
            )
        else:
            return ApiResponse(
                success=False,
                error="Failed to send test notification"
            )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/integrations", summary="获取所有通知集成配置")
async def get_all_integrations(
        include_inactive: bool = Query(False, description="是否包含非活动配置"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取所有通知集成配置
    
    Args:
        include_inactive: 是否包含非活动配置
        
    Returns:
        配置列表
    """
    try:
        # 检查权限
        has_permission = await check_admin_permission(db, current_user.id)
        if not has_permission:
            return ApiResponse(success=False, error="Insufficient permissions")

        configs = await notification_integration_service.get_all_configs(db, include_inactive)

        configs_list = []
        for config in configs:
            configs_list.append({
                'id': config.id,
                'platform': config.platform,
                'site_id': config.site_id,
                'webhook_url': config.webhook_url[:50] + '...' if config.webhook_url else None,
                'channel_id': config.channel_id,
                'enable_new_article_notification': config.enable_new_article_notification,
                'enable_comment_notification': config.enable_comment_notification,
                'enable_system_alert': config.enable_system_alert,
                'is_active': config.is_active,
                'created_at': config.created_at.isoformat() if config.created_at else None,
            })

        return ApiResponse(
            success=True,
            data={
                'integrations': configs_list,
                'total': len(configs_list)
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))
