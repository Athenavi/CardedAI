"""
安全监控面板 API
提供实时安全数据查询、异常流量检测及审计日志可视化支持
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query

from shared.models.user import User
from shared.services.security.audit_service import audit_service
from src.auth.auth_deps import jwt_required_dependency as jwt_required

router = APIRouter(prefix="/security", tags=["Security Monitoring"])


@router.get("/dashboard/summary")
async def get_security_summary(current_user: User = Depends(jwt_required)):
    """P4-2: 获取安全监控概览数据"""
    # 实际实现应聚合最近 24 小时的登录尝试、敏感操作次数等
    return {
        "success": True,
        "data": {
            "total_actions_24h": 150,
            "failed_logins_24h": 3,
            "suspicious_ips": [],
            "recent_critical_events": []
        }
    }


@router.get("/audit/logs")
async def get_audit_logs(
        user_id: Optional[int] = Query(None),
        action: Optional[str] = Query(None),
        limit: int = Query(50, le=500),
        current_user: User = Depends(jwt_required)
):
    """P4-2: 查询审计日志（支持管理后台展示）"""
    logs = await audit_service.get_logs(user_id=user_id, action=action, limit=limit)
    return {
        "success": True,
        "data": [log.to_dict() for log in logs]
    }


@router.get("/monitor/alerts")
async def get_security_alerts(current_user: User = Depends(jwt_required)):
    """P4-2: 获取实时安全告警"""
    # 实际实现应集成入侵检测逻辑
    return {
        "success": True,
        "alerts": []
    }
