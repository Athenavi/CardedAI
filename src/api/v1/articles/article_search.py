"""
文章搜索 API
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared.services.articles.article_search import (article_search_service)
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["search"])


@router.get("")
async def search_articles(
        q: str = Query(..., min_length=1, description="搜索关键词"),
        category_id: Optional[int] = Query(None, description="分类ID"),
        author_id: Optional[int] = Query(None, description="作者ID"),
        date_from: Optional[str] = Query(None, description="起始日期 (YYYY-MM-DD)"),
        date_to: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
        status: str = Query("published", description="文章状态"),
        page: int = Query(1, ge=1, description="页码"),
        per_page: int = Query(20, ge=1, le=100, description="每页数量"),
        sort_by: str = Query("relevance", enum=["relevance", "date", "views"], description="排序方式"),
        db: AsyncSession = Depends(get_async_db),
):
    """
    搜索文章
    
    Args:
        q: 搜索关键词
        category_id: 分类ID过滤
        author_id: 作者ID过滤
        date_from: 起始日期
        date_to: 结束日期
        status: 文章状态
        page: 页码
        per_page: 每页数量
        sort_by: 排序方式
        
    Returns:
        搜索结果
    """
    try:
        # 解析日期
        date_from_dt = None
        date_to_dt = None

        if date_from:
            try:
                date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_from format. Use YYYY-MM-DD")

        if date_to:
            try:
                date_to_dt = datetime.strptime(date_to, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_to format. Use YYYY-MM-DD")

        result = await article_search_service.search_articles(
            db=db,
            query=q,
            category_id=category_id,
            author_id=author_id,
            date_from=date_from_dt,
            date_to=date_to_dt,
            status=status,
            page=page,
            per_page=per_page,
            sort_by=sort_by
        )

        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions")
async def get_search_suggestions(
        q: str = Query(..., min_length=1, description="搜索前缀"),
        limit: int = Query(5, ge=1, le=10, description="返回数量"),
        db: AsyncSession = Depends(get_async_db),
):
    """
    获取搜索建议（自动完成）
    
    Args:
        q: 搜索前缀
        limit: 返回数量
        
    Returns:
        搜索建议列表
    """
    try:
        suggestions = await article_search_service.get_search_suggestions(
            db=db,
            query=q,
            limit=limit
        )

        return {
            "success": True,
            "data": {
                "query": q,
                "suggestions": suggestions
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/popular")
async def get_popular_searches(
        days: int = Query(7, ge=1, le=30, description="统计天数"),
        limit: int = Query(10, ge=1, le=20, description="返回数量"),
        db: AsyncSession = Depends(get_async_db),
):
    """
    获取热门搜索
    
    Args:
        days: 统计天数
        limit: 返回数量
        
    Returns:
        热门搜索列表
    """
    try:
        popular = await article_search_service.get_popular_searches(
            db=db,
            days=days,
            limit=limit
        )

        return {
            "success": True,
            "data": popular
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/history/clear")
async def clear_search_history(
        days: int = Query(30, ge=1, description="清理天数"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db),
):
    """
    清理搜索历史（管理员）
    
    Args:
        days: 清理多少天前的记录
        
    Returns:
        操作结果
    """
    try:
        # 检查管理员权限
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="Permission denied. Admin access required.")

        await article_search_service.clear_old_search_history(
            db=db,
            days=days
        )

        return {
            "success": True,
            "message": f"已清理 {days} 天前的搜索历史"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
