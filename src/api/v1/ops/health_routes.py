"""
P8-2: 健康检查 API
提供系统健康状态查询和监控端点
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from shared.services.ops.health_checker import health_checker
from src.auth.auth_deps import jwt_required_dependency as jwt_required
from shared.models.user import User

router = APIRouter(prefix="/health", tags=["Health Check"])


@router.get("/")
async def health_check():
    """
    P8-2: 基础健康检查端点（无需认证，用于负载均衡器）
    
    Returns:
        简单健康状态
    """
    return {"status": "healthy", "timestamp": health_checker.check_system_resources().get('last_check')}


@router.get("/detailed")
async def detailed_health_check(current_user: User = Depends(jwt_required)):
    """
    P8-2: 详细健康检查（需要认证）
    
    Returns:
        完整健康信息
    """
    health = await health_checker.check_application_health()
    return health


@router.get("/alerts")
async def get_alert_history(
        limit: int = Query(20, ge=1, le=100),
        current_user: User = Depends(jwt_required)
):
    """
    P8-2: 获取告警历史
    
    Args:
        limit: 返回数量限制
        
    Returns:
        告警历史列表
    """
    alerts = health_checker.get_alert_history(limit)
    return {
        "alerts": alerts,
        "total": len(alerts)
    }


@router.get("/metrics")
async def get_system_metrics(current_user: User = Depends(jwt_required)):
    """
    P8-2: 获取系统指标（Prometheus 格式）
    
    Returns:
        系统指标数据
    """
    import psutil

    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    # Prometheus 格式指标
    metrics_text = f"""# HELP fastblog_cpu_usage_percent CPU 使用率
# TYPE fastblog_cpu_usage_percent gauge
fastblog_cpu_usage_percent {cpu_percent}

# HELP fastblog_memory_usage_bytes 内存使用量（字节）
# TYPE fastblog_memory_usage_bytes gauge
fastblog_memory_usage_bytes {memory.used}

# HELP fastblog_memory_total_bytes 内存总量（字节）
# TYPE fastblog_memory_total_bytes gauge
fastblog_memory_total_bytes {memory.total}

# HELP fastblog_disk_usage_bytes 磁盘使用量（字节）
# TYPE fastblog_disk_usage_bytes gauge
fastblog_disk_usage_bytes {disk.used}

# HELP fastblog_disk_total_bytes 磁盘总量（字节）
# TYPE fastblog_disk_total_bytes gauge
fastblog_disk_total_bytes {disk.total}
"""

    from fastapi.responses import Response
    return Response(content=metrics_text, media_type="text/plain")


class AlertThresholdUpdate(BaseModel):
    """告警阈值更新请求"""
    cpu_percent: Optional[int] = None
    memory_percent: Optional[int] = None
    disk_percent: Optional[int] = None
    db_pool_usage: Optional[int] = None


@router.post("/thresholds")
async def update_alert_thresholds(
        thresholds: AlertThresholdUpdate,
        current_user: User = Depends(jwt_required)
):
    """
    P8-2: 更新告警阈值
    
    Args:
        thresholds: 新的阈值配置
        
    Returns:
        更新结果
    """
    if thresholds.cpu_percent is not None:
        health_checker.alert_thresholds['cpu_percent'] = thresholds.cpu_percent

    if thresholds.memory_percent is not None:
        health_checker.alert_thresholds['memory_percent'] = thresholds.memory_percent

    if thresholds.disk_percent is not None:
        health_checker.alert_thresholds['disk_percent'] = thresholds.disk_percent

    if thresholds.db_pool_usage is not None:
        health_checker.alert_thresholds['db_pool_usage'] = thresholds.db_pool_usage

    return {
        "success": True,
        "message": "告警阈值已更新",
        "current_thresholds": health_checker.alert_thresholds
    }
