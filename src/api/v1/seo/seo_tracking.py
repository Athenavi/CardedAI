"""
SEO 效果追踪 API
提供搜索引擎流量、关键词排名、流量来源等查询功能
"""

from fastapi import APIRouter, Depends, Query

from shared.services.seo.seo_tracker import seo_tracker
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import get_current_active_user, admin_required as admin_required_api

router = APIRouter(tags=["seo-tracking"])


@router.get("/search-traffic", summary="获取搜索引擎流量汇总")
async def get_search_traffic(
        days: int = Query(30, ge=7, le=90, description="统计天数"),
        current_user=Depends(admin_required_api)
):
    """
    获取搜索引擎流量汇总数据
    
    仅管理员可访问。
    
    Args:
        days: 统计天数（7-90天）
        
    Returns:
        搜索引擎流量汇总
    """
    try:
        summary = seo_tracker.get_search_traffic_summary(days)

        return ApiResponse(
            success=True,
            data=summary
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取流量汇总失败: {str(e)}")


@router.get("/top-keywords", summary="获取热门关键词")
async def get_top_keywords(
        limit: int = Query(20, ge=1, le=100, description="返回数量"),
        days: int = Query(30, ge=7, le=90, description="统计天数"),
        current_user=Depends(admin_required_api)
):
    """
    获取热门搜索关键词
    
    仅管理员可访问。
    
    Args:
        limit: 返回数量（1-100）
        days: 统计天数（7-90天）
        
    Returns:
        热门关键词列表
    """
    try:
        keywords = seo_tracker.get_top_keywords(limit, days)

        return ApiResponse(
            success=True,
            data={
                'keywords': keywords,
                'count': len(keywords),
                'period_days': days,
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取关键词失败: {str(e)}")


@router.get("/article/{article_id}/performance", summary="获取文章 SEO 表现")
async def get_article_seo_performance(
        article_id: int,
        days: int = Query(30, ge=7, le=90, description="统计天数"),
        current_user=Depends(get_current_active_user)
):
    """
    获取指定文章的 SEO 表现数据
    
    Args:
        article_id: 文章ID
        days: 统计天数（7-90天）
        
    Returns:
        文章 SEO 表现
    """
    try:
        performance = seo_tracker.get_article_seo_performance(article_id, days)

        return ApiResponse(
            success=True,
            data=performance
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取 SEO 表现失败: {str(e)}")


@router.get("/traffic-sources", summary="获取流量来源分析")
async def get_traffic_sources(
        article_id: int = Query(None, description="文章ID（可选）"),
        days: int = Query(30, ge=7, le=90, description="统计天数"),
        current_user=Depends(admin_required_api)
):
    """
    获取流量来源分析
    
    分析自然搜索、直接访问、引荐流量、社交媒体等来源占比。
    
    Args:
        article_id: 文章ID（可选，不传则统计全站）
        days: 统计天数（7-90天）
        
    Returns:
        流量来源数据
    """
    try:
        sources = seo_tracker.get_traffic_sources(article_id, days)

        return ApiResponse(
            success=True,
            data=sources
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取流量来源失败: {str(e)}")


@router.post("/track-visit", summary="记录页面访问")
async def track_visit(
        article_id: int = Query(..., description="文章ID"),
        referrer: str = Query('', description="来源URL"),
        user_agent: str = Query('', description="用户代理"),
):
    """
    记录页面访问用于 SEO 分析
    
    前端应在页面加载时调用此接口。
    
    Args:
        article_id: 文章ID
        referrer: 来源URL
        user_agent: 用户代理
        
    Returns:
        操作结果
    """
    try:
        seo_tracker.track_visit(
            article_id=article_id,
            referrer=referrer,
            user_agent=user_agent,
        )

        return ApiResponse(
            success=True,
            message='访问已记录'
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"记录访问失败: {str(e)}")


@router.get("/dashboard", summary="获取 SEO 仪表板数据")
async def get_seo_dashboard(
        days: int = Query(30, ge=7, le=90, description="统计天数"),
        current_user=Depends(admin_required_api)
):
    """
    获取 SEO 仪表板综合数据
    
    包括搜索引擎流量、热门关键词、流量来源等。
    
    Args:
        days: 统计天数（7-90天）
        
    Returns:
        SEO 仪表板数据
    """
    try:
        # 获取各项数据
        traffic_summary = seo_tracker.get_search_traffic_summary(days)
        top_keywords = seo_tracker.get_top_keywords(10, days)
        traffic_sources = seo_tracker.get_traffic_sources(days=days)

        return ApiResponse(
            success=True,
            data={
                'traffic_summary': traffic_summary,
                'top_keywords': top_keywords,
                'traffic_sources': traffic_sources,
                'period_days': days,
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取仪表板数据失败: {str(e)}")
