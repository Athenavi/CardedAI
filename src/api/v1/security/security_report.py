"""
安全报告 API

提供安全报告的生成和查看功能
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from shared.services.articles.anomaly_detector import anomaly_detector
from shared.services.security.security_alert import security_alert_service
from shared.services.security.security_report import report_generator
from shared.services.security.audit_service import audit_service
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required

router = APIRouter()


@router.get("/daily", summary="生成日报", description="生成今日安全日报")
async def generate_daily_report(
        current_user=Depends(jwt_required),
):
    """生成日报"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    # 获取数据
    anomalies = anomaly_detector.get_anomalies(hours=24)
    alerts = security_alert_service.get_alert_history(hours=24)
    audit_logs = await audit_service.get_logs(limit=200)

    report = report_generator.generate_daily_report(
        anomalies=anomalies,
        alerts=alerts,
        audit_logs=audit_logs,
    )

    return ApiResponse(
        success=True,
        data=report
    )


@router.get("/weekly", summary="生成周报", description="生成本周安全周报")
async def generate_weekly_report(
        current_user=Depends(jwt_required),
):
    """生成周报"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    # 获取数据
    anomalies = anomaly_detector.get_anomalies(hours=168)  # 7天
    alerts = security_alert_service.get_alert_history(hours=168)
    audit_logs = await audit_service.get_logs(limit=500)

    report = report_generator.generate_weekly_report(
        anomalies=anomalies,
        alerts=alerts,
        audit_logs=audit_logs,
    )

    return ApiResponse(
        success=True,
        data=report
    )


@router.get("/monthly", summary="生成月报", description="生成本月安全月报")
async def generate_monthly_report(
        current_user=Depends(jwt_required),
):
    """生成月报"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    # 获取数据
    anomalies = anomaly_detector.get_anomalies(hours=720)  # 30天
    alerts = security_alert_service.get_alert_history(hours=720)
    audit_logs = await audit_service.get_logs(limit=2000)

    report = report_generator.generate_monthly_report(
        anomalies=anomalies,
        alerts=alerts,
        audit_logs=audit_logs,
    )

    return ApiResponse(
        success=True,
        data=report
    )


@router.get("/history", summary="获取报告历史", description="获取历史报告列表")
async def get_report_history(
        report_type: Optional[str] = Query(None, description="报告类型过滤 (daily, weekly, monthly)"),
        limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
        current_user=Depends(jwt_required),
):
    """获取报告历史"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    history = report_generator.get_report_history(
        report_type=report_type,
        limit=limit,
    )

    return ApiResponse(
        success=True,
        data={
            'reports': history,
            'count': len(history),
        }
    )
