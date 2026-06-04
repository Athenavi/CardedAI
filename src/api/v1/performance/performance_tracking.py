"""
页面性能追踪 API

提供前端性能数据的收集和查询功能
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Body

from shared.services.performance.performance_tracker import performance_tracker
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required

router = APIRouter()


@router.post("/record", summary="记录性能数据", description="记录页面加载性能数据")
async def record_performance(
        url: str = Body(..., description="页面URL"),
        user_agent: str = Body(..., description="用户代理"),
        load_time: float = Body(..., description="页面加载时间（毫秒）"),
        dom_content_loaded: float = Body(..., description="DOM加载完成时间（毫秒）"),
        first_paint: Optional[float] = Body(None, description="首次绘制时间（毫秒）"),
        fcp: Optional[float] = Body(None, description="首次内容绘制（毫秒）"),
        lcp: Optional[float] = Body(None, description="最大内容绘制（毫秒）"),
        fid: Optional[float] = Body(None, description="首次输入延迟（毫秒）"),
        cls: Optional[float] = Body(None, description="累积布局偏移"),
        custom_timings: Optional[dict] = Body(None, description="自定义计时"),
):
    """记录性能数据"""
    performance_metrics = {
        'loadTime': load_time,
        'domContentLoaded': dom_content_loaded,
    }

    if first_paint is not None:
        performance_metrics['firstPaint'] = first_paint

    core_web_vitals = {}
    if fcp is not None:
        core_web_vitals['fcp'] = fcp
    if lcp is not None:
        core_web_vitals['lcp'] = lcp
    if fid is not None:
        core_web_vitals['fid'] = fid
    if cls is not None:
        core_web_vitals['cls'] = cls

    record = performance_tracker.record_performance(
        url=url,
        user_agent=user_agent,
        performance_metrics=performance_metrics,
        core_web_vitals=core_web_vitals if core_web_vitals else None,
        custom_timings=custom_timings,
    )

    return ApiResponse(
        success=True,
        message="Performance data recorded",
        data={'recorded': True}
    )


@router.get("/page-stats", summary="获取页面统计", description="获取指定页面的性能统计")
async def get_page_stats(
        url: str = Query(..., description="页面URL"),
        hours: int = Query(24, ge=1, le=168, description="统计最近多少小时"),
        current_user=Depends(jwt_required),
):
    """获取页面统计"""
    stats = performance_tracker.get_page_stats(url=url, hours=hours)

    return ApiResponse(
        success=True,
        data=stats
    )


@router.get("/overall", summary="获取整体统计", description="获取所有页面的整体性能统计")
async def get_overall_stats(
        hours: int = Query(24, ge=1, le=168, description="统计最近多少小时"),
        current_user=Depends(jwt_required),
):
    """获取整体统计"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    stats = performance_tracker.get_overall_stats(hours=hours)

    return ApiResponse(
        success=True,
        data=stats
    )


@router.get("/slowest", summary="获取最慢页面", description="获取加载最慢的页面列表")
async def get_slowest_pages(
        hours: int = Query(24, ge=1, le=168, description="统计最近多少小时"),
        limit: int = Query(10, ge=1, le=50, description="返回数量"),
        current_user=Depends(jwt_required),
):
    """获取最慢页面"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    pages = performance_tracker.get_slowest_pages(hours=hours, limit=limit)

    return ApiResponse(
        success=True,
        data={
            'pages': pages,
            'count': len(pages),
        }
    )


@router.get("/trends", summary="获取性能趋势", description="获取页面性能趋势数据")
async def get_performance_trends(
        url: str = Query(..., description="页面URL"),
        days: int = Query(7, ge=1, le=30, description="统计天数"),
        current_user=Depends(jwt_required),
):
    """获取性能趋势"""
    trends = performance_tracker.get_performance_trends(url=url, days=days)

    return ApiResponse(
        success=True,
        data={
            'url': url,
            'trends': trends,
        }
    )
