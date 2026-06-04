"""
文章分析 API
提供文章阅读量趋势、来源渠道、读者分布等分析功能
"""

from fastapi import APIRouter, Depends, Query

from shared.models.user import User as UserModel
from shared.services.articles.article_analytics_service import article_analytics_service
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import get_current_active_user

router = APIRouter(tags=["article-analytics"])


@router.get("/{article_id}/stats", summary="获取文章统计")
async def get_article_stats(
        article_id: int,
        days: int = Query(30, ge=1, le=365, description="统计天数"),
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    获取文章统计数据

    Args:
        article_id: 文章ID
        days: 统计天数(1-365)

    Returns:
        统计数据
    """
    try:
        stats = article_analytics_service.get_article_stats(article_id, days)

        return ApiResponse(
            success=True,
            data=stats
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取统计失败: {str(e)}")


@router.get("/{article_id}/trend", summary="获取阅读量趋势")
async def get_views_trend(
        article_id: int,
        days: int = Query(30, ge=1, le=365, description="统计天数"),
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    获取文章阅读量趋势图数据

    Args:
        article_id: 文章ID
        days: 统计天数(1-365)

    Returns:
        趋势数据
    """
    try:
        trend = article_analytics_service.get_views_trend(article_id, days)

        return ApiResponse(
            success=True,
            data={
                'trend': trend,
                'days': days,
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取趋势失败: {str(e)}")


@router.get("/{article_id}/sources", summary="获取流量来源")
async def get_traffic_sources(
        article_id: int,
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    获取文章流量来源分布

    Args:
        article_id: 文章ID

    Returns:
        来源分布
    """
    try:
        sources = article_analytics_service.get_traffic_sources(article_id)

        return ApiResponse(
            success=True,
            data={
                'sources': sources,
                'total': sum(sources.values()),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取来源失败: {str(e)}")


@router.get("/{article_id}/regions", summary="获取读者地域分布")
async def get_reader_regions(
        article_id: int,
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    获取文章读者地域分布

    Args:
        article_id: 文章ID

    Returns:
        地域分布
    """
    try:
        regions = article_analytics_service.get_reader_regions(article_id)

        return ApiResponse(
            success=True,
            data={
                'regions': regions,
                'total': sum(regions.values()),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取地域失败: {str(e)}")


@router.get("/{article_id}/full-report", summary="获取完整分析报告")
async def get_full_analytics_report(
        article_id: int,
        days: int = Query(30, ge=1, le=365, description="统计天数"),
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    获取文章完整分析报告

    Args:
        article_id: 文章ID
        days: 统计天数(1-365)

    Returns:
        完整分析数据
    """
    try:
        report = article_analytics_service.get_article_analytics(article_id, days)

        return ApiResponse(
            success=True,
            data=report
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取报告失败: {str(e)}")


@router.get("/top-articles", summary="获取热门文章排行")
async def get_top_articles(
        days: int = Query(7, ge=1, le=90, description="统计天数"),
        limit: int = Query(10, ge=1, le=100, description="返回数量"),
        sort_by: str = Query('views', enum=['views', 'unique_visitors', 'avg_read_time'], description="排序字段"),
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    获取热门文章排行榜

    Args:
        days: 统计天数(1-90)
        limit: 返回数量(1-100)
        sort_by: 排序字段(views/unique_visitors/avg_read_time)

    Returns:
        文章排行榜
    """
    try:
        top_articles = article_analytics_service.get_top_articles(
            days=days,
            limit=limit,
            sort_by=sort_by,
        )

        return ApiResponse(
            success=True,
            data={
                'articles': top_articles,
                'count': len(top_articles),
                'period_days': days,
                'sort_by': sort_by,
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取排行失败: {str(e)}")
