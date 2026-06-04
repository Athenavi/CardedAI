"""
慢查询日志 API

提供慢查询的查看、分析和优化建议
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Body

from shared.services.performance.slow_query_logger import slow_query_logger
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required

router = APIRouter()


@router.get("/logs", summary="获取慢查询日志", description="获取数据库慢查询列表")
async def get_slow_query_logs(
        limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
        hours: int = Query(24, ge=1, le=168, description="统计最近多少小时"),
        table: Optional[str] = Query(None, description="表名过滤"),
        query_type: Optional[str] = Query(None, description="查询类型过滤"),
        current_user=Depends(jwt_required),
):
    """获取慢查询日志"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    queries = slow_query_logger.get_slow_queries(
        limit=limit,
        hours=hours,
        table=table,
        query_type=query_type,
    )

    return ApiResponse(
        success=True,
        data={
            'queries': queries,
            'count': len(queries),
        }
    )


@router.get("/statistics", summary="获取统计信息", description="获取慢查询统计信息")
async def get_statistics(
        hours: int = Query(24, ge=1, le=168, description="统计最近多少小时"),
        current_user=Depends(jwt_required),
):
    """获取统计信息"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    stats = slow_query_logger.get_statistics(hours=hours)

    return ApiResponse(
        success=True,
        data=stats
    )


@router.get("/suggestions", summary="获取优化建议", description="获取查询优化建议")
async def get_optimization_suggestions(
        current_user=Depends(jwt_required),
):
    """获取优化建议"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    suggestions = slow_query_logger.get_optimization_suggestions()

    return ApiResponse(
        success=True,
        data={
            'suggestions': suggestions,
            'count': len(suggestions),
        }
    )


@router.post("/config", summary="更新配置", description="更新慢查询日志配置")
async def update_config(
        threshold: float = Body(..., ge=0.01, le=10.0, description="慢查询阈值(秒)"),
        current_user=Depends(jwt_required),
):
    """更新配置"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    slow_query_logger.update_threshold(threshold)

    return ApiResponse(
        success=True,
        message=f"Threshold updated to {threshold}s",
        data={'threshold': threshold}
    )


@router.post("/clear", summary="清空日志", description="清空所有慢查询日志")
async def clear_logs(
        current_user=Depends(jwt_required),
):
    """清空日志"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    slow_query_logger.clear_logs()

    return ApiResponse(
        success=True,
        message="All slow query logs cleared"
    )


@router.post("/record", summary="记录查询", description="手动记录查询（用于测试）")
async def record_query(
        sql: str = Body(..., description="SQL语句"),
        duration: float = Body(..., ge=0, description="执行时间(秒)"),
        table: Optional[str] = Body(None, description="表名"),
        query_type: Optional[str] = Body(None, description="查询类型"),
        current_user=Depends(jwt_required),
):
    """记录查询"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    slow_query_logger.log_query(
        sql=sql,
        duration=duration,
        table=table,
        query_type=query_type,
    )

    return ApiResponse(
        success=True,
        message="Query recorded"
    )
