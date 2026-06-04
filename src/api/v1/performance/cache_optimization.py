"""
缓存管理 API
提供缓存查询、清理、统计等功能
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Body

from shared.services.core.enhanced_cache_strategy import enhanced_cache
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import admin_required

router = APIRouter(tags=["cache"])


@router.get("/stats", summary="获取缓存统计")
async def get_cache_stats(current_user=Depends(admin_required)):
    """
    获取缓存统计信息
    
    Returns:
        缓存统计数据
    """
    try:
        stats = enhanced_cache.get_stats()

        return ApiResponse(
            success=True,
            data=stats
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取统计失败: {str(e)}")


@router.post("/clear", summary="清空所有缓存")
async def clear_all_cache(current_user=Depends(admin_required)):
    """
    清空所有缓存
    
    Returns:
        操作结果
    """
    try:
        enhanced_cache.cache.clear()
        enhanced_cache.reset_stats()

        return ApiResponse(
            success=True,
            data={'message': '所有缓存已清空'}
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"清空缓存失败: {str(e)}")


@router.delete("/tag/{tag}", summary="根据标签删除缓存")
async def delete_cache_by_tag(
        tag: str,
        current_user=Depends(admin_required)
):
    """
    根据标签删除相关缓存
    
    Args:
        tag: 缓存标签
        
    Returns:
        删除的键列表
    """
    try:
        deleted_keys = enhanced_cache.delete_with_tags(tag)

        return ApiResponse(
            success=True,
            data={
                'message': f'已删除 {len(deleted_keys)} 个缓存',
                'deleted_keys': deleted_keys[:50],  # 最多返回50个
                'total_deleted': len(deleted_keys),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"删除缓存失败: {str(e)}")


@router.post("/warmup", summary="缓存预热")
async def warmup_cache(
        cache_type: str = Body(..., description="缓存类型"),
        current_user=Depends(admin_required)
):
    """
    预热指定类型的缓存
    
    Args:
        cache_type: 缓存类型 (articles/categories/users/stats)
        
    Returns:
        预热结果
    """
    try:
        import asyncio

        if cache_type == 'articles':
            # 预热热门文章
            from shared.models.article import Article
            from sqlalchemy import select, desc
            from src.utils.database.main import get_async_session

            async for db in get_async_session():
                result = await db.execute(
                    select(Article).where(Article.status == 1).order_by(desc(Article.view_count)).limit(20)
                )
                articles = result.scalars().all()

                # 构建预热任务
                tasks = []
                for article in articles:
                    key = f"article:{article.id}"
                    tasks.append({
                        'key': key,
                        'fetcher': lambda aid=article.id: _fetch_article(aid, db),
                        'ttl': 3600,
                        'tags': ['article'],
                    })

                await enhanced_cache.warmup_cache(tasks)
                break

            return ApiResponse(
                success=True,
                data={'message': f'已预热热门文章缓存'}
            )

        elif cache_type == 'categories':
            # 预热分类缓存
            from shared.models.category import Category
            from sqlalchemy import select
            from src.utils.database.main import get_async_session

            async for db in get_async_session():
                result = await db.execute(select(Category))
                categories = result.scalars().all()

                tasks = []
                for category in categories:
                    key = f"category:{category.id}"
                    tasks.append({
                        'key': key,
                        'fetcher': lambda cid=category.id: _fetch_category(cid, db),
                        'ttl': 7200,
                        'tags': ['category'],
                    })

                await enhanced_cache.warmup_cache(tasks)
                break

            return ApiResponse(
                success=True,
                data={'message': f'已预热分类缓存'}
            )

        else:
            return ApiResponse(success=False, error=f"不支持的缓存类型: {cache_type}")

    except Exception as e:
        import traceback
        print(f"Cache warmup error: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=f"缓存预热失败: {str(e)}")


@router.get("/keys", summary="列出缓存键")
async def list_cache_keys(
        prefix: Optional[str] = Query(None, description="键前缀"),
        limit: int = Query(100, ge=1, le=1000, description="返回数量"),
        current_user=Depends(admin_required)
):
    """
    列出缓存中的键
    
    Args:
        prefix: 键前缀过滤
        limit: 返回数量
        
    Returns:
        缓存键列表
    """
    try:
        # 获取内存缓存的键
        keys = list(enhanced_cache.cache.cache.keys())

        # 过滤
        if prefix:
            keys = [k for k in keys if k.startswith(prefix)]

        # 限制数量
        keys = keys[:limit]

        return ApiResponse(
            success=True,
            data={
                'keys': keys,
                'count': len(keys),
                'total': len(keys),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取缓存键失败: {str(e)}")


@router.delete("/pattern", summary="根据模式删除缓存")
async def delete_cache_by_pattern(
        pattern: str = Body(..., description="键模式，支持*通配符"),
        current_user=Depends(admin_required)
):
    """
    根据模式删除缓存
    
    Args:
        pattern: 键模式（如 "article:*"）
        
    Returns:
        删除结果
    """
    try:
        deleted_keys = enhanced_cache.invalidate_by_pattern(pattern)

        return ApiResponse(
            success=True,
            data={
                'message': f'已删除 {len(deleted_keys)} 个缓存',
                'pattern': pattern,
                'deleted_count': len(deleted_keys),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"删除缓存失败: {str(e)}")


# 辅助函数
async def _fetch_article(article_id: int, db) -> dict:
    """获取文章数据用于缓存"""
    from shared.models.article import Article
    from sqlalchemy import select

    result = await db.execute(
        select(Article).where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()

    if article:
        return {
            'id': article.id,
            'title': article.title,
            'content': article.content,
            'status': article.status,
        }
    return None


async def _fetch_category(category_id: int, db) -> dict:
    """获取分类数据用于缓存"""
    from shared.models.category import Category
    from sqlalchemy import select

    result = await db.execute(
        select(Category).where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()

    if category:
        return {
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
        }
    return None
