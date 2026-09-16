"""
数据分析 API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared.services.articles.analytics import create_analytics_service
from src.utils.database.main import get_async_session

router = APIRouter(tags=["analytics"])


@router.get("/overview")
async def get_overview_stats(
        days: int = Query(30, ge=1, le=365, description="统计天数"),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取概览统计数据

    Args:
        days: 统计天数
        db: 数据库会话

    Returns:
        概览数据
    """
    try:
        service = create_analytics_service(db)
        stats = await service.get_overview_stats(days)

        return {
            'success': True,
            'data': stats,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/article-views-trend")
async def get_article_views_trend(
        days: int = Query(30, ge=1, le=365, description="统计天数"),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取文章浏览量趋势

    Args:
        days: 统计天数
        db: 数据库会话

    Returns:
        每日浏览量列表
    """
    try:
        service = create_analytics_service(db)
        trend = await service.get_article_views_trend(days)

        return {
            'success': True,
            'data': trend,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/popular-articles")
async def get_popular_articles(
        limit: int = Query(10, ge=1, le=100, description="返回数量"),
        days: int = Query(7, ge=1, le=365, description="统计天数"),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取热门文章

    Args:
        limit: 返回数量
        days: 统计天数
        db: 数据库会话

    Returns:
        热门文章列表
    """
    try:
        service = create_analytics_service(db)
        articles = await service.get_popular_articles(limit, days)

        return {
            'success': True,
            'data': articles,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/category-distribution")
async def get_category_distribution(
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取分类分布

    Args:
        db: 数据库会话

    Returns:
        分类统计列表
    """
    try:
        service = create_analytics_service(db)
        distribution = await service.get_category_distribution()

        return {
            'success': True,
            'data': distribution,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user-activity")
async def get_user_activity(
        days: int = Query(30, ge=1, le=365, description="统计天数"),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取用户活动统计

    Args:
        days: 统计天数
        db: 数据库会话

    Returns:
        用户活动数据
    """
    try:
        service = create_analytics_service(db)
        activity = await service.get_user_activity(days)

        return {
            'success': True,
            'data': activity,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/content-performance")
async def get_content_performance(
        days: int = Query(30, ge=1, le=365, description="统计天数"),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取内容表现分析

    Args:
        days: 统计天数
        db: 数据库会话

    Returns:
        内容表现数据
    """
    try:
        service = create_analytics_service(db)
        performance = await service.get_content_performance(days)

        return {
            'success': True,
            'data': performance,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/traffic-sources")
async def get_traffic_sources(
        days: int = Query(30, ge=1, le=365, description="统计天数"),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取流量来源分析

    Args:
        days: 统计天数
        db: 数据库会话

    Returns:
        流量来源列表
    """
    try:
        service = create_analytics_service(db)
        sources = await service.get_traffic_sources(days)

        return {
            'success': True,
            'data': sources,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/device-stats")
async def get_device_stats(
        days: int = Query(30, ge=1, le=365, description="统计天数"),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取设备统计

    Args:
        days: 统计天数
        db: 数据库会话

    Returns:
        设备分布数据
    """
    try:
        service = create_analytics_service(db)
        stats = await service.get_device_stats(days)

        return {
            'success': True,
            'data': stats,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tag-distribution")
async def get_tag_distribution(
    limit: int = Query(15, ge=1, le=100, description="返回数量"),
    db: AsyncSession = Depends(get_async_session)
):
    """
    获取标签分布（Top N）

    数据来源：articles.tags_list 真实聚合
    """
    try:
        service = create_analytics_service(db)
        tags = await service.get_tag_distribution(limit)

        return {
            'success': True,
            'data': tags,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search-keywords")
async def get_search_keywords(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    db: AsyncSession = Depends(get_async_session)
):
    """
    获取搜索热词

    数据来源：search_history 真实聚合
    """
    try:
        service = create_analytics_service(db)
        keywords = await service.get_search_keywords(limit, days)

        return {
            'success': True,
            'data': keywords,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit-activity")
async def get_audit_activity(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    limit: int = Query(8, ge=1, le=50, description="动作类型数量"),
    db: AsyncSession = Depends(get_async_session)
):
    """
    获取后台操作活跃度

    数据来源：audit_logs（按日 + 按动作 Top）
    """
    try:
        service = create_analytics_service(db)
        activity = await service.get_audit_activity(days, limit)

        return {
            'success': True,
            'data': activity,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/media-stats")
async def get_media_stats(db: AsyncSession = Depends(get_async_session)):
    """
    获取媒体库统计

    数据来源：media（数量 / 总占用 / 按类型）
    """
    try:
        service = create_analytics_service(db)
        stats = await service.get_media_stats()

        return {
            'success': True,
            'data': stats,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
