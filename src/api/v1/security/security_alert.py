"""
安全事件告警 API

提供告警配置、发送和查看功能
"""

from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Body

from shared.services.security.security_alert import security_alert_service, EmailAlertChannel, \
    WebhookAlertChannel
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required

router = APIRouter()


@router.post("/send", summary="发送告警", description="手动发送安全告警")
async def send_alert(
        alert_type: str = Body(..., description="告警类型"),
        title: str = Body(..., description="标题"),
        message: str = Body(..., description="消息内容"),
        severity: str = Body('medium', description="严重程度 (low, medium, high, critical)"),
        details: Optional[dict] = Body(None, description="详细信息"),
        force_send: bool = Body(False, description="强制发送（忽略频率限制）"),
        current_user=Depends(jwt_required),
):
    """发送告警"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    result = await security_alert_service.send_alert(
        alert_type=alert_type,
        title=title,
        message=message,
        severity=severity,
        details=details,
        force_send=force_send,
    )

    return ApiResponse(
        success=result['success'],
        data=result
    )


@router.get("/history", summary="获取告警历史", description="获取告警历史记录")
async def get_alert_history(
        hours: int = Query(24, ge=1, le=168, description="最近多少小时"),
        alert_type: Optional[str] = Query(None, description="告警类型过滤"),
        severity: Optional[str] = Query(None, description="严重程度过滤"),
        current_user=Depends(jwt_required),
):
    """获取告警历史"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    history = security_alert_service.get_alert_history(
        hours=hours,
        alert_type=alert_type,
        severity=severity,
    )

    return ApiResponse(
        success=True,
        data={
            'alerts': history,
            'count': len(history),
        }
    )


@router.get("/statistics", summary="获取统计信息", description="获取告警统计信息")
async def get_statistics(
        hours: int = Query(24, ge=1, le=168, description="统计最近多少小时"),
        current_user=Depends(jwt_required),
):
    """获取统计信息"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    stats = security_alert_service.get_statistics(hours=hours)

    return ApiResponse(
        success=True,
        data=stats
    )


@router.post("/channel/email", summary="添加邮件渠道", description="添加邮件告警渠道")
async def add_email_channel(
        channel_id: str = Body(..., description="渠道ID"),
        smtp_server: str = Body(..., description="SMTP服务器"),
        smtp_port: int = Body(587, description="SMTP端口"),
        username: str = Body(..., description="用户名"),
        password: str = Body(..., description="密码"),
        from_email: str = Body(..., description="发件人邮箱"),
        to_emails: List[str] = Body(..., description="收件人邮箱列表"),
        use_tls: bool = Body(True, description="使用TLS"),
        current_user=Depends(jwt_required),
):
    """添加邮件渠道"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    channel = EmailAlertChannel(
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        username=username,
        password=password,
        from_email=from_email,
        to_emails=to_emails,
        use_tls=use_tls,
    )

    security_alert_service.add_channel(channel_id, channel)

    return ApiResponse(
        success=True,
        message=f"Email channel '{channel_id}' added"
    )


@router.post("/channel/webhook", summary="添加Webhook渠道", description="添加Webhook告警渠道")
async def add_webhook_channel(
        channel_id: str = Body(..., description="渠道ID"),
        webhook_url: str = Body(..., description="Webhook URL"),
        headers: Optional[dict] = Body(None, description="自定义请求头"),
        current_user=Depends(jwt_required),
):
    """添加Webhook渠道"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    channel = WebhookAlertChannel(
        webhook_url=webhook_url,
        headers=headers,
    )

    security_alert_service.add_channel(channel_id, channel)

    return ApiResponse(
        success=True,
        message=f"Webhook channel '{channel_id}' added"
    )


@router.delete("/channel/{channel_id}", summary="删除告警渠道", description="删除告警渠道")
async def remove_channel(
        channel_id: str,
        current_user=Depends(jwt_required),
):
    """删除告警渠道"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    security_alert_service.remove_channel(channel_id)

    return ApiResponse(
        success=True,
        message=f"Channel '{channel_id}' removed"
    )


@router.post("/rule", summary="添加告警规则", description="添加告警规则")
async def add_rule(
        rule_id: str = Body(..., description="规则ID"),
        alert_type: str = Body(..., description="告警类型"),
        severity: str = Body(..., description="严重程度"),
        channels: List[str] = Body(..., description="使用的渠道列表"),
        enabled: bool = Body(True, description="是否启用"),
        current_user=Depends(jwt_required),
):
    """添加告警规则"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    security_alert_service.add_rule(
        rule_id=rule_id,
        alert_type=alert_type,
        severity=severity,
        channels=channels,
        enabled=enabled,
    )

    return ApiResponse(
        success=True,
        message=f"Rule '{rule_id}' added"
    )


@router.post("/config/rate-limit", summary="更新频率限制", description="更新告警频率限制")
async def update_rate_limit(
        minutes: int = Body(..., ge=1, le=60, description="最小间隔分钟数"),
        current_user=Depends(jwt_required),
):
    """更新频率限制"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    security_alert_service.update_rate_limit(minutes)

    return ApiResponse(
        success=True,
        message=f"Rate limit updated to {minutes} minutes"
    )

