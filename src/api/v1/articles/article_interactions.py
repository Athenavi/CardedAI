"""
文章互动 API
提供文章点赞、浏览记录等功能
"""


from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.article import Article
from shared.models.article_like import ArticleLike
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import cache, get_async_db_session as get_async_db

from src.unified_logger import default_logger as logger

router = APIRouter(tags=["article-interactions"])


@router.post('/{article_id}/like')
async def like_article(
        article_id: int,
        request: Request,
        current_user_obj=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """用户点赞文章"""
    try:
        # 获取文章
        article_query = select(Article).where(
            Article.id == article_id,
            Article.status != -1  # 排除已删除的文章
        )
        article_result = await db.execute(article_query)
        article = article_result.scalar_one_or_none()
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")

        # 检查用户是否已经点过赞
        existing_like_query = select(ArticleLike).where(
            ArticleLike.user_id == current_user_obj.id,
            ArticleLike.article_id == article_id
        )
        existing_like_result = await db.execute(existing_like_query)
        existing_like = existing_like_result.scalar_one_or_none()
        if existing_like:
            raise HTTPException(status_code=400, detail="您已经点过赞了")

        # 增加点赞数
        article.likes += 1

        # 记录用户点赞
        new_like = ArticleLike(user_id=current_user_obj.id, article_id=article_id)
        db.add(new_like)

        await db.commit()

        return {
            'success': True,
            'message': '点赞成功',
            'likes': article.likes
        }
    except HTTPException:
        raise
    except Exception as e:
        if db is not None:
            await db.rollback()
        raise HTTPException(status_code=500, detail="点赞失败")


@router.post('/{article_id}/view')
async def record_article_view(
        article_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    """记录文章浏览量（使用缓存异步更新数据库）"""
    try:
        # 检查文章是否存在
        article_query = select(Article).where(
            Article.id == article_id,
            Article.status != -1  # 排除已删除的文章
        )
        article_result = await db.execute(article_query)
        article = article_result.scalar_one_or_none()
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")

        # 使用缓存来记录浏览量，避免频繁写入数据库
        cache_key = f"article_views_{article_id}"
        current_views = cache.get(cache_key)

        if current_views is None:
            # 如果缓存中没有，则从数据库获取当前浏览量
            current_views = article.views

        # 增加浏览量计数
        current_views += 1

        # 将新的浏览量存回缓存
        cache.set(cache_key, current_views, timeout=300)  # 缓存5分钟

        return {'success': True, 'message': '浏览量记录成功'}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"记录浏览量失败: {str(e)}")
