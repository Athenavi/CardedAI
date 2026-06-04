"""
分享统计 API
提供分享追踪、统计分析等功能
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.share_stat import ShareStat
from shared.models.article import Article
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["shares"])


@router.post("/track")
async def track_share(
        article_id: int = Query(..., description="文章ID"),
        platform: str = Query(..., description="分享平台: wechat/weibo/twitter/facebook/linkedin/zhihu/juejin/segmentfault/telegram/copy"),
        request: Request = None,
        current_user_id: Optional[int] = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    记录分享行为
    
    Args:
        article_id: 被分享的文章ID
        platform: 分享平台
    """
    try:
        # 验证文章是否存在
        article_query = select(Article).where(Article.id == article_id)
        article_result = await db.execute(article_query)
        article = article_result.scalar_one_or_none()

        if not article:
            return ApiResponse(success=False, error="文章不存在")

        # 获取IP地址和用户代理
        ip_address = request.client.host if request and request.client else None
        user_agent = request.headers.get("user-agent") if request else None

        # 创建分享记录
        share_stat = ShareStat(
            article_id=article_id,
            platform=platform,
            shared_by=current_user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.now()
        )

        db.add(share_stat)
        await db.commit()

        return ApiResponse(
            success=True,
            message="分享记录成功"
        )

    except Exception as e:
        import traceback
        print(f"Error in track_share: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/stats/{article_id}")
async def get_article_share_stats(
        article_id: int,
        days: int = Query(30, ge=1, le=365, description="统计天数"),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取文章的分享统计数据
    
    Args:
        article_id: 文章ID
        days: 统计天数
    """
    try:
        # 验证文章是否存在
        article_query = select(Article).where(Article.id == article_id)
        article_result = await db.execute(article_query)
        article = article_result.scalar_one_or_none()

        if not article:
            return ApiResponse(success=False, error="文章不存在")

        cutoff_date = datetime.now() - timedelta(days=days)

        # 总分享数
        total_query = (
            select(func.count())
            .select_from(ShareStat)
            .where(
                ShareStat.article_id == article_id,
                ShareStat.created_at >= cutoff_date
            )
        )
        total_result = await db.execute(total_query)
        total_shares = total_result.scalar() or 0

        # 按平台统计
        platform_query = (
            select(
                ShareStat.platform,
                func.count().label('count')
            )
            .where(
                ShareStat.article_id == article_id,
                ShareStat.created_at >= cutoff_date
            )
            .group_by(ShareStat.platform)
            .order_by(desc('count'))
        )
        platform_result = await db.execute(platform_query)
        platform_stats = [
            {"platform": row.platform, "count": row.count}
            for row in platform_result.fetchall()
        ]

        # 分享趋势(按天)
        trend_query = (
            select(
                func.date(ShareStat.created_at).label('date'),
                func.count().label('count')
            )
            .where(
                ShareStat.article_id == article_id,
                ShareStat.created_at >= cutoff_date
            )
            .group_by(func.date(ShareStat.created_at))
            .order_by(desc('date'))
        )
        trend_result = await db.execute(trend_query)
        trend_data = [
            {"date": row.date.isoformat(), "count": row.count}
            for row in trend_result.fetchall()
        ]
        trend_data.reverse()  # 按时间正序

        return ApiResponse(
            success=True,
            data={
                "article_id": article_id,
                "total_shares": total_shares,
                "period_days": days,
                "by_platform": platform_stats,
                "trend": trend_data
            }
        )

    except Exception as e:
        import traceback
        print(f"Error in get_article_share_stats: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/ranking")
async def get_share_ranking(
        days: int = Query(7, ge=1, le=365, description="统计天数"),
        limit: int = Query(10, ge=1, le=100, description="返回数量"),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取热门文章分享排行榜
    
    Args:
        days: 统计天数
        limit: 返回数量
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days)

        # 按文章统计分享数
        ranking_query = (
            select(
                ShareStat.article_id,
                Article.title,
                Article.slug,
                func.count().label('share_count')
            )
            .join(Article, ShareStat.article_id == Article.id)
            .where(
                ShareStat.created_at >= cutoff_date,
                Article.status == 1  # 只统计已发布的文章
            )
            .group_by(ShareStat.article_id, Article.title, Article.slug)
            .order_by(desc('share_count'))
            .limit(limit)
        )

        result = await db.execute(ranking_query)
        ranking = []

        for row in result.fetchall():
            ranking.append({
                "article_id": row.article_id,
                "title": row.title,
                "slug": row.slug,
                "share_count": row.share_count
            })

        return ApiResponse(
            success=True,
            data={
                "period_days": days,
                "ranking": ranking
            }
        )

    except Exception as e:
        import traceback
        print(f"Error in get_share_ranking: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/platform-stats")
async def get_platform_statistics(
        days: int = Query(30, ge=1, le=365, description="统计天数"),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取各分享平台的总体统计
    
    Args:
        days: 统计天数
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days)

        # 按平台统计
        platform_query = (
            select(
                ShareStat.platform,
                func.count().label('count'),
                func.count(func.distinct(ShareStat.article_id)).label('unique_articles')
            )
            .where(ShareStat.created_at >= cutoff_date)
            .group_by(ShareStat.platform)
            .order_by(desc('count'))
        )

        result = await db.execute(platform_query)
        platform_stats = []

        for row in result.fetchall():
            platform_stats.append({
                "platform": row.platform,
                "total_shares": row.count,
                "unique_articles": row.unique_articles
            })

        # 总分享数
        total_query = (
            select(func.count())
            .select_from(ShareStat)
            .where(ShareStat.created_at >= cutoff_date)
        )
        total_result = await db.execute(total_query)
        total_shares = total_result.scalar() or 0

        return ApiResponse(
            success=True,
            data={
                "period_days": days,
                "total_shares": total_shares,
                "by_platform": platform_stats
            }
        )

    except Exception as e:
        import traceback
        print(f"Error in get_platform_statistics: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))
