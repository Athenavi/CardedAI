"""
站内数据分析 API

提供页面浏览量、用户行为、流量来源等分析功能
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request

from shared.services.analytics.site_analytics import site_analytics
from src.api.v1.core.responses import ApiResponse
from src.api.v1.users.user_management import jwt_required
from src.utils.security.ip_utils import get_client_ip

router = APIRouter(prefix="/site-analytics", tags=["Site Analytics"])


@router.post("/track/page-view")
async def track_page_view(
    request: Request,
        page_path: str = Query(..., description="页面路径"),
        page_title: Optional[str] = Query("", description="页面标题"),
        user_id: Optional[str] = Query(None, description="用户ID"),
        session_id: Optional[str] = Query(None, description="会话ID"),
        referrer: Optional[str] = Query(None, description="来源页面"),
        current_user=Depends(jwt_required)
):
    """
    追踪页面浏览

    记录用户访问页面的行为
    """
    ip_address = get_client_ip(request)

    site_analytics.track_page_view(
        page_path=page_path,
        page_title=page_title,
        user_id=user_id,
        session_id=session_id,
        referrer=referrer,
        ip_address=ip_address
    )

    return ApiResponse(
        success=True,
        message="页面浏览已记录"
    )


@router.post("/track/event")
async def track_custom_event(
        event_name: str = Query(..., description="事件名称"),
        user_id: Optional[str] = Query(None, description="用户ID"),
        session_id: Optional[str] = Query(None, description="会话ID"),
        properties: Optional[dict] = Query(None, description="事件属性"),
        current_user=Depends(jwt_required)
):
    """
    追踪自定义事件

    记录用户的特定行为（如点击、表单提交等）
    """
    site_analytics.track_event(
        event_name=event_name,
        user_id=user_id,
        session_id=session_id,
        properties=properties or {}
    )

    return ApiResponse(
        success=True,
        message="事件已记录"
    )


@router.get("/page-views")
async def get_page_views(
        page_path: Optional[str] = Query(None, description="页面路径过滤"),
        current_user=Depends(jwt_required)
):
    """
    获取页面浏览量统计
    """
    views = site_analytics.get_page_views(page_path=page_path)

    return ApiResponse(
        success=True,
        data={
            "page_views": views,
            "total_pages": len(views)
        }
    )


@router.get("/popular-pages")
async def get_popular_pages(
        limit: int = Query(20, ge=1, le=100, description="返回数量"),
        current_user=Depends(jwt_required)
):
    """
    获取热门页面排行
    """
    popular = site_analytics.get_popular_pages(limit=limit)

    return ApiResponse(
        success=True,
        data={
            "popular_pages": popular,
            "total": len(popular)
        }
    )


@router.get("/traffic-sources")
async def get_traffic_sources(
        limit: int = Query(20, ge=1, le=100, description="返回数量"),
        current_user=Depends(jwt_required)
):
    """
    获取流量来源统计

    显示访问者的来源渠道（直接访问、搜索引擎、社交媒体等）
    """
    sources = site_analytics.get_traffic_sources(limit=limit)

    return ApiResponse(
        success=True,
        data={
            "traffic_sources": sources,
            "total": len(sources)
        }
    )


@router.get("/user-activity/{user_id}")
async def get_user_activity(
        user_id: str,
        days: int = Query(30, ge=1, le=365, description="统计天数"),
        current_user=Depends(jwt_required)
):
    """
    获取用户活动统计

    显示指定用户的访问行为和互动数据
    """
    activity = site_analytics.get_user_activity(user_id=user_id, days=days)

    return ApiResponse(
        success=True,
        data=activity
    )


@router.get("/session/{session_id}")
async def get_session_stats(
        session_id: str,
        current_user=Depends(jwt_required)
):
    """
    获取会话统计

    显示单次访问的详细信息
    """
    stats = site_analytics.get_session_stats(session_id=session_id)

    if stats is None:
        return ApiResponse(
            success=False,
            error="会话不存在或已过期"
        )

    return ApiResponse(
        success=True,
        data=stats
    )


@router.get("/daily-stats")
async def get_daily_stats(
        days: int = Query(30, ge=1, le=365, description="统计天数"),
        current_user=Depends(jwt_required)
):
    """
    获取每日统计数据

    显示指定时间段内的每日访问量、独立访客等指标
    """
    stats = site_analytics.get_daily_stats(days=days)

    return ApiResponse(
        success=True,
        data={
            "daily_stats": stats,
            "period_days": days,
            "summary": {
                "total_page_views": sum(s["page_views"] for s in stats),
                "total_unique_visitors": sum(s["unique_visitors"] for s in stats),
                "total_events": sum(s["events"] for s in stats),
                "avg_daily_views": sum(s["page_views"] for s in stats) / len(stats) if stats else 0
            }
        }
    )


@router.get("/real-time")
async def get_real_time_stats(
        current_user=Depends(jwt_required)
):
    """
    获取实时统计

    显示当前正在进行的访问活动
    """
    # 获取最近5分钟的事件
    cutoff = datetime.now() - timedelta(minutes=5)

    recent_events = [
        event for event in site_analytics.events_buffer
        if datetime.fromisoformat(event["timestamp"]) >= cutoff
    ]

    # 统计当前在线用户（基于最近活动的会话）
    active_sessions = set()
    page_views_last_5min = 0

    for event in recent_events:
        if event.get("session_id"):
            active_sessions.add(event["session_id"])

        if event.get("event_type") == "page_view":
            page_views_last_5min += 1

    return ApiResponse(
        success=True,
        data={
            "active_users": len(active_sessions),
            "page_views_last_5min": page_views_last_5min,
            "total_events_last_5min": len(recent_events),
            "timestamp": datetime.now().isoformat()
        }
    )


@router.get("/dashboard/overview")
async def get_analytics_overview(
        days: int = Query(30, ge=1, le=365, description="统计天数"),
        current_user=Depends(jwt_required)
):
    """
    获取数据分析概览

    综合显示关键指标和趋势
    """
    # 获取每日统计
    daily_stats = site_analytics.get_daily_stats(days=days)

    # 计算汇总数据
    total_page_views = sum(s["page_views"] for s in daily_stats)
    total_unique_visitors = sum(s["unique_visitors"] for s in daily_stats)
    avg_daily_views = total_page_views / len(daily_stats) if daily_stats else 0

    # 获取热门页面
    popular_pages = site_analytics.get_popular_pages(limit=10)

    # 获取流量来源
    traffic_sources = site_analytics.get_traffic_sources(limit=10)

    return ApiResponse(
        success=True,
        data={
            "period_days": days,
            "summary": {
                "total_page_views": total_page_views,
                "total_unique_visitors": total_unique_visitors,
                "avg_daily_page_views": round(avg_daily_views, 2),
            },
            "trends": {
                "daily_stats": daily_stats,
            },
            "top_content": {
                "popular_pages": popular_pages,
            },
            "traffic_sources": traffic_sources,
        }
    )


@router.get("/export")
async def export_analytics_data(
        start_date: str = Query(..., description="开始日期 (YYYY-MM-DD)"),
        end_date: str = Query(..., description="结束日期 (YYYY-MM-DD)"),
        format: str = Query("json", description="导出格式 (json/csv)"),
        current_user=Depends(jwt_required)
):
    """
    导出分析数据

    将指定时间段的数据导出为JSON或CSV格式
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        # 收集指定日期范围内的事件
        all_events = []
        current = start
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            events = site_analytics.load_events_from_file(date_str)
            all_events.extend(events)
            current += timedelta(days=1)

        if format == "csv":
            # 转换为CSV格式
            import csv
            import io

            output = io.StringIO()
            if all_events:
                writer = csv.DictWriter(output, fieldnames=all_events[0].keys())
                writer.writeheader()
                writer.writerows(all_events)

            csv_data = output.getvalue()
            output.close()

            return ApiResponse(
                success=True,
                data={
                    "format": "csv",
                    "content": csv_data,
                    "total_events": len(all_events)
                }
            )
        else:
            # JSON格式
            return ApiResponse(
                success=True,
                data={
                    "format": "json",
                    "events": all_events,
                    "total_events": len(all_events)
                }
            )

    except Exception as e:
        return ApiResponse(
            success=False,
            error=f"导出失败: {str(e)}"
        )


@router.get("/guide")
async def get_analytics_guide(current_user=Depends(jwt_required)):
    """
    获取数据分析使用指南
    """
    guide = {
        "overview": {
            "title": "站内数据分析系统",
            "description": "FastBlog 内置的数据分析系统，无需第三方服务即可追踪和分析网站访问数据。"
        },
        "features": [
            "页面浏览量统计",
            "用户行为追踪",
            "流量来源分析",
            "热门内容排行",
            "实时访问监控",
            "数据导出功能"
        ],
        "tracking_methods": {
            "page_view": {
                "description": "追踪页面浏览",
                "endpoint": "POST /track/page-view",
                "parameters": {
                    "page_path": "页面路径（必需）",
                    "page_title": "页面标题",
                    "user_id": "用户ID（如果已登录）",
                    "session_id": "会话ID",
                    "referrer": "来源页面URL"
                }
            },
            "custom_event": {
                "description": "追踪自定义事件",
                "endpoint": "POST /track/event",
                "parameters": {
                    "event_name": "事件名称（必需）",
                    "user_id": "用户ID",
                    "session_id": "会话ID",
                    "properties": "事件属性对象"
                },
                "examples": [
                    "button_click - 按钮点击",
                    "form_submit - 表单提交",
                    "video_play - 视频播放",
                    "download - 文件下载"
                ]
            }
        },
        "privacy_notes": [
            "所有数据存储在服务器本地，不发送到第三方",
            "可以配置数据保留期限",
            "支持匿名追踪（不使用用户ID）",
            "遵守GDPR等隐私法规",
            "用户可以要求删除其数据"
        ],
        "best_practices": [
            "在页面加载时自动追踪页面浏览",
            "为重要的用户交互添加事件追踪",
            "定期导出数据进行深度分析",
            "设置合理的数据保留策略",
            "监控异常流量模式"
        ]
    }

    return ApiResponse(
        success=True,
        data=guide
    )
