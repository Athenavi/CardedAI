"""
实时监控 API
提供系统性能、在线用户、访问量等实时数据
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from shared.services.analytics.realtime_monitor import realtime_monitor_service
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import admin_required as admin_required_api

router = APIRouter(tags=["monitoring"])


@router.get("/dashboard", summary="获取监控仪表板数据")
async def get_monitor_dashboard(
        current_user=Depends(admin_required_api)
):
    """
    获取完整的监控仪表板数据
    
    包括在线用户、访问量、热门文章、系统健康状态等。
    需要管理员权限。
    
    Returns:
        仪表板完整数据
    """
    try:
        data = realtime_monitor_service.get_dashboard_data()

        return ApiResponse(
            success=True,
            data=data
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取监控数据失败: {str(e)}")


@router.get("/online-users", summary="获取在线用户")
async def get_online_users(
        limit: int = Query(50, ge=1, le=200, description="返回数量"),
        current_user=Depends(admin_required_api)
):
    """
    获取当前在线用户列表
    
    Args:
        limit: 返回数量(1-200)
        
    Returns:
        在线用户列表和总数
    """
    try:
        count = realtime_monitor_service.get_online_users_count()
        users = realtime_monitor_service.get_online_users_list(limit=limit)

        return ApiResponse(
            success=True,
            data={
                'count': count,
                'users': users,
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取在线用户失败: {str(e)}")


@router.get("/visits/today", summary="获取今日访问量")
async def get_today_visits(
        current_user=Depends(admin_required_api)
):
    """
    获取今日总访问量
    
    Returns:
        今日访问次数
    """
    try:
        visits = realtime_monitor_service.get_today_visits()

        return ApiResponse(
            success=True,
            data={
                'today_visits': visits,
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取访问量失败: {str(e)}")


@router.get("/visits/realtime", summary="获取实时访问量")
async def get_realtime_visits(
        window: int = Query(5, ge=1, le=60, description="时间窗口(分钟)"),
        current_user=Depends(admin_required_api)
):
    """
    获取最近N分钟的实时访问量
    
    Args:
        window: 时间窗口(1-60分钟)
        
    Returns:
        实时访问次数
    """
    try:
        visits = realtime_monitor_service.get_realtime_visits(window_minutes=window)

        return ApiResponse(
            success=True,
            data={
                'window_minutes': window,
                'visits': visits,
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取实时访问量失败: {str(e)}")


@router.get("/visits/popular-endpoints", summary="获取热门访问端点")
async def get_popular_endpoints(
        limit: int = Query(10, ge=1, le=50, description="返回数量"),
        window: int = Query(60, ge=1, le=1440, description="时间窗口(分钟)"),
        current_user=Depends(admin_required_api)
):
    """
    获取热门访问的API端点
        
    Args:
        limit: 返回数量(1-50)
        window: 时间窗口(1-1440分钟)
        
    Returns:
        热门端点列表
    """
    try:
        endpoints = realtime_monitor_service.get_popular_endpoints(
            limit=limit,
            window_minutes=window
        )

        return ApiResponse(
            success=True,
            data={
                'window_minutes': window,
                'endpoints': endpoints,
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取热门端点失败: {str(e)}")


@router.get("/system-metrics", summary="获取系统指标")
async def get_system_metrics(
        current_user=Depends(admin_required_api)
):
    """
    获取系统性能指标(CPU、内存、磁盘、网络)
    
    Returns:
        系统指标数据
    """
    try:
        metrics = realtime_monitor_service.get_system_metrics()

        return ApiResponse(
            success=True,
            data=metrics
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取系统指标失败: {str(e)}")


@router.get("/health", summary="获取系统健康状态")
async def get_health_status(
        current_user=Depends(admin_required_api)
):
    """
    获取系统整体健康状态
    
    Returns:
        健康状态和告警信息
    """
    try:
        health = realtime_monitor_service.get_health_status()

        return ApiResponse(
            success=True,
            data=health
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取健康状态失败: {str(e)}")


@router.get("/trending-articles", summary="获取实时热门文章")
async def get_trending_articles(
        limit: int = Query(10, ge=1, le=50, description="返回数量"),
        current_user=Depends(admin_required_api)
):
    """
    获取实时热门文章列表
    
    Args:
        limit: 返回数量(1-50)
        
    Returns:
        热门文章列表
    """
    try:
        articles = realtime_monitor_service.get_trending_articles(limit=limit)

        return ApiResponse(
            success=True,
            data={
                'articles': articles,
                'count': len(articles),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取热门文章失败: {str(e)}")


@router.post("/record-activity", summary="记录用户活动")
async def record_user_activity(
        user_id: int = Query(..., description="用户ID"),
):
    """
    记录用户活动(用于追踪在线状态)
    
    前端应定期调用此接口以保持在线状态。
    
    Args:
        user_id: 用户ID
        
    Returns:
        操作结果
    """
    try:
        realtime_monitor_service.record_user_activity(user_id)

        return ApiResponse(
            success=True,
            message='活动已记录'
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"记录活动失败: {str(e)}")


@router.post("/record-page-view", summary="记录页面访问")
async def record_page_view(
        endpoint: str = Query(..., description="访问的端点"),
        article_id: Optional[int] = Query(None, description="文章ID"),
):
    """
    记录页面访问(用于统计流量)
    
    Args:
        endpoint: 访问的端点路径
        article_id: 文章ID(可选)
        
    Returns:
        操作结果
    """
    try:
        realtime_monitor_service.record_page_view(endpoint, article_id)

        return ApiResponse(
            success=True,
            message='访问已记录'
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"记录访问失败: {str(e)}")
