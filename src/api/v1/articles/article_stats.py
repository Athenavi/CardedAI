"""
文章阅读统计 API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from shared.services.articles.article_view_stats import article_view_stats
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["article-stats"])


@router.get("/{article_id}")
async def get_article_views(
        article_id: int,
        current_user=Depends(jwt_required),
):
    """
    获取文章阅读量
    
    Args:
        article_id: 文章ID
        
    Returns:
        阅读量
    """
    view_count = await article_view_stats.get_view_count(article_id)

    return {
        "success": True,
        "data": {
            "article_id": article_id,
            "views": view_count
        }
    }


@router.post("/sync/{article_id}")
async def sync_article_views(
        article_id: int,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):
    """
    同步单篇文章阅读量到数据库（管理员）
    
    Args:
        article_id: 文章ID
        
    Returns:
        同步结果
    """
    # 检查管理员权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied. Admin access required.")

    await article_view_stats.sync_to_database(article_id, db)

    return {
        "success": True,
        "message": f"Article {article_id} views synced to database"
    }


@router.post("/sync-all")
async def sync_all_article_views(
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):
    """
    批量同步所有文章阅读量到数据库（管理员）
    
    Returns:
        同步结果
    """
    # 检查管理员权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied. Admin access required.")

    result = await article_view_stats.batch_sync_all(db)

    return {
        "success": True,
        "data": result,
        "message": f"Synced {result['synced']} articles"
    }


@router.get("/top-articles")
async def get_top_articles(
        limit: int = 10,
        current_user=Depends(jwt_required),
):
    """
    获取热门文章
    
    Args:
        limit: 返回数量
        
    Returns:
        热门文章列表
    """
    top_articles = await article_view_stats.get_top_articles(limit)

    return {
        "success": True,
        "data": [
            {"article_id": aid, "views": count}
            for aid, count in top_articles
        ]
    }


@router.delete("/reset/{article_id}")
async def reset_article_views(
        article_id: int,
        current_user=Depends(jwt_required),
):
    """
    重置文章阅读计数（管理员）
    
    Args:
        article_id: 文章ID
        
    Returns:
        操作结果
    """
    # 检查管理员权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied. Admin access required.")

    await article_view_stats.reset_article_views(article_id)

    return {
        "success": True,
        "message": f"Article {article_id} view count reset"
    }
