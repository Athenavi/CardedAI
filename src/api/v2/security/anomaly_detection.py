"""
异常行为检测 API

提供异常行为的检测、查看和管理功能
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Body

from shared.services.articles.anomaly_detector import anomaly_detector
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required

router = APIRouter()


@router.get("/anomalies", summary="获取异常事件", description="获取检测到的异常行为事件")
async def get_anomalies(
        hours: int = Query(24, ge=1, le=168, description="最近多少小时"),
        anomaly_type: Optional[str] = Query(None, description="异常类型过滤"),
        current_user=Depends(jwt_required),
):
    """获取异常事件"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    anomalies = anomaly_detector.get_anomalies(hours=hours, anomaly_type=anomaly_type)

    return ApiResponse(
        success=True,
        data={
            'anomalies': anomalies,
            'count': len(anomalies),
        }
    )


@router.get("/statistics", summary="获取统计信息", description="获取异常行为统计信息")
async def get_statistics(
        hours: int = Query(24, ge=1, le=168, description="统计最近多少小时"),
        current_user=Depends(jwt_required),
):
    """获取统计信息"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    stats = anomaly_detector.get_statistics(hours=hours)

    return ApiResponse(
        success=True,
        data=stats
    )


@router.post("/record-login", summary="记录登录尝试", description="记录登录尝试用于检测")
async def record_login_attempt(
        ip_address: str = Body(..., description="IP地址"),
        username: str = Body(..., description="用户名"),
        success: bool = Body(..., description="是否成功"),
        current_user=Depends(jwt_required),
):
    """记录登录尝试"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    anomaly_detector.record_login_attempt(
        ip_address=ip_address,
        username=username,
        success=success,
    )

    return ApiResponse(
        success=True,
        message="Login attempt recorded"
    )


@router.post("/record-activity", summary="记录用户活动", description="记录用户活动用于检测")
async def record_user_activity(
        user_id: int = Body(..., description="用户ID"),
        action: str = Body(..., description="操作类型"),
        details: Optional[dict] = Body(None, description="详细信息"),
        current_user=Depends(jwt_required),
):
    """记录用户活动"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    anomaly_detector.record_user_activity(
        user_id=user_id,
        action=action,
        details=details,
    )

    return ApiResponse(
        success=True,
        message="User activity recorded"
    )


@router.post("/config", summary="更新配置", description="更新检测阈值配置")
async def update_config(
        login_failures_per_hour: Optional[int] = Body(None, ge=1, description="每小时失败登录次数阈值"),
        requests_per_minute: Optional[int] = Body(None, ge=1, description="每分钟请求数阈值"),
        data_export_size_mb: Optional[int] = Body(None, ge=1, description="数据导出大小阈值(MB)"),
        current_user=Depends(jwt_required),
):
    """更新配置"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    updates = {}
    if login_failures_per_hour is not None:
        updates['login_failures_per_hour'] = login_failures_per_hour
    if requests_per_minute is not None:
        updates['requests_per_minute'] = requests_per_minute
    if data_export_size_mb is not None:
        updates['data_export_size_mb'] = data_export_size_mb

    anomaly_detector.update_thresholds(**updates)

    return ApiResponse(
        success=True,
        message="Configuration updated",
        data=anomaly_detector.thresholds
    )