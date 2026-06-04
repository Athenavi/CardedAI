"""
个性化推荐 API
提供文章推荐、Trending、Rising Stars等功能
"""

from typing import Optional, List

from fastapi import APIRouter, Query, HTTPException

from shared.services.advanced_features.recommendation_service import recommendation_service
from src.api.v1.core.responses import ApiResponse

router = APIRouter(tags=["recommendations"])


@router.get("/personalized", summary="获取个性化推荐")
async def get_personalized_recommendations(
        limit: int = Query(10, ge=1, le=50, description="返回数量"),
        user_id: Optional[int] = Query(None, description="用户ID(可选)"),
):
    """
    获取个性化推荐文章
    
    基于用户的阅读历史、点赞、收藏等行为,推荐相关文章。
    如果未提供user_id,则返回热门文章。
    
    Args:
        limit: 返回数量(1-50)
        user_id: 用户ID(可选)
        
    Returns:
        推荐文章列表
    """
    try:
        # 如果提供了user_id,获取个性化推荐
        if user_id:
            recommendations = recommendation_service.get_personalized_recommendations(
                user_id=user_id,
                limit=limit
            )
        else:
            # 否则返回热门文章
            recommendations = recommendation_service._get_popular_articles(limit)

        return ApiResponse(
            success=True,
            data={
                'recommendations': recommendations,
                'count': len(recommendations),
                'algorithm': 'collaborative_filtering' if user_id else 'popularity_based',
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending", summary="获取Trending文章")
async def get_trending_articles(
        window: str = Query('24h', enum=['24h', '7d', '30d'], description="时间窗口"),
        limit: int = Query(10, ge=1, le=50, description="返回数量"),
):
    """
    获取Trending热门文章
    
    基于近期浏览量和互动数据,计算 trending 分数。
    
    Args:
        window: 时间窗口 (24h/7d/30d)
        limit: 返回数量(1-50)
        
    Returns:
        Trending文章列表
    """
    try:
        trending = recommendation_service.get_trending_articles(
            window=window,
            limit=limit
        )

        return ApiResponse(
            success=True,
            data={
                'trending': trending,
                'count': len(trending),
                'window': window,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rising-stars", summary="获取Rising Stars新锐博主")
async def get_rising_stars(
        limit: int = Query(10, ge=1, le=20, description="返回数量"),
):
    """
    获取Rising Stars(新锐博主)
    
    基于近期发文数量和互动增长,识别上升期的创作者。
    
    Args:
        limit: 返回数量(1-20)
        
    Returns:
        Rising Stars用户列表
    """
    try:
        rising_stars = recommendation_service.get_rising_stars(limit=limit)

        return ApiResponse(
            success=True,
            data={
                'rising_stars': rising_stars,
                'count': len(rising_stars),
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similar/{article_id}", summary="获取相似文章")
async def get_similar_articles(
        article_id: int,
        limit: int = Query(5, ge=1, le=20, description="返回数量"),
):
    """
    获取与指定文章相似的文章
    
    基于标签和分类的相似度计算。
    
    Args:
        article_id: 参考文章ID
        limit: 返回数量(1-20)
        
    Returns:
        相似文章列表
    """
    try:
        similar = recommendation_service.get_similar_articles(
            article_id=article_id,
            limit=limit
        )

        return ApiResponse(
            success=True,
            data={
                'similar_articles': similar,
                'count': len(similar),
                'reference_article_id': article_id,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/track-action", summary="记录用户行为")
async def track_user_action(
        user_id: int = Query(..., description="用户ID"),
        article_id: int = Query(..., description="文章ID"),
        action_type: str = Query('view', enum=['view', 'like', 'bookmark', 'comment'],
                                 description="行为类型"),
):
    """
    记录用户行为用于推荐算法
    
    包括浏览、点赞、收藏、评论等行为。
    
    Args:
        user_id: 用户ID
        article_id: 文章ID
        action_type: 行为类型 (view/like/bookmark/comment)
        
    Returns:
        操作结果
    """
    try:
        recommendation_service.record_user_action(
            user_id=user_id,
            article_id=article_id,
            action_type=action_type
        )

        return ApiResponse(
            success=True,
            message=f'Recorded {action_type} action',
            data={
                'user_id': user_id,
                'article_id': article_id,
                'action_type': action_type,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-article-features", summary="更新文章特征")
async def update_article_features(
        article_id: int = Query(..., description="文章ID"),
        tags: List[str] = Query([], description="标签列表"),
        category: str = Query('', description="分类"),
        views: int = Query(0, description="浏览量"),
        likes: int = Query(0, description="点赞数"),
        created_at: Optional[str] = Query(None, description="创建时间"),
):
    """
    更新文章特征数据
    
    用于推荐算法的内容分析。
    
    Args:
        article_id: 文章ID
        tags: 标签列表
        category: 分类
        views: 浏览量
        likes: 点赞数
        created_at: 创建时间(ISO格式)
        
    Returns:
        操作结果
    """
    try:
        features = {
            'tags': tags,
            'category': category,
            'views': views,
            'likes': likes,
            'created_at': created_at,
        }

        recommendation_service.update_article_features(article_id, features)

        return ApiResponse(
            success=True,
            message='Article features updated',
            data={
                'article_id': article_id,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
