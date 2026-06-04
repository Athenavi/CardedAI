"""
全文搜索 API 端点
提供基于 Meilisearch 的高性能搜索功能
"""
import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from shared.services.integrations.meilisearch_service import meilisearch_service
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["fulltext-search"])


@router.get("/articles")
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
):
    """
    使用 Meilisearch 搜索文章

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
                # 包含整天
                date_to_dt = date_to_dt.replace(hour=23, minute=59, second=59)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_to format. Use YYYY-MM-DD")

        # 执行搜索
        result = await meilisearch_service.search(
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

        return ApiResponse(
            success=True,
            data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in search_articles: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/suggestions")
async def get_search_suggestions(
        q: str = Query(..., min_length=1, description="搜索前缀"),
        limit: int = Query(5, ge=1, le=10, description="返回数量")
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
        suggestions = await meilisearch_service.get_search_suggestions(
            query=q,
            limit=limit
        )

        return ApiResponse(
            success=True,
            data={
                'suggestions': suggestions,
                'query': q
            }
        )

    except Exception as e:
        print(f"Error in get_search_suggestions: {str(e)}")
        return ApiResponse(success=False, error=str(e))


@router.post("/rebuild-index")
async def rebuild_search_index(
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    重建搜索索引（仅管理员）

    重新索引所有已发布的文章

    Returns:
        重建结果
    """
    try:
        # 检查权限
        if not current_user.is_superuser:
            return ApiResponse(
                success=False,
                error="Permission denied. Admin access required."
            )

        from shared.models.article import Article
        from shared.models.article_content import ArticleContent
        from shared.models.category import Category
        from shared.models.user import User
        from sqlalchemy import select

        # 获取所有已发布文章
        stmt = (
            select(Article, ArticleContent, Category.name.label('category_name'), User.username.label('author_name'))
            .outerjoin(ArticleContent, Article.id == ArticleContent.article)
            .outerjoin(Category, Article.category == Category.id)
            .outerjoin(User, Article.user == User.id)
            .where(Article.status == 1)
        )

        result = await db.execute(stmt)
        rows = result.all()

        # 准备索引数据
        articles = []
        for row in rows:
            article, content, category_name, author_name = row

            article_data = {
                'id': article.id,
                'title': article.title,
                'slug': article.slug,
                'excerpt': article.excerpt or '',
                'content': content.content if content else '',
                'cover_image': article.cover_image or '',
                'category_id': article.category,
                'category_name': category_name or '',
                'author_id': article.user,
                'author_name': author_name or '',
                'tags': [t.strip() for t in re.split(r'[,;]', article.tags_list) if
                         t.strip()] if article.tags_list else [],
                'views': article.views,
                'likes': article.likes,
                'status': 'published',
                'is_featured': article.is_featured,
                'created_at': int(article.created_at.timestamp()) if article.created_at else 0,
                'updated_at': int(article.updated_at.timestamp()) if article.updated_at else 0,
            }

            articles.append(article_data)

        # 重建索引
        success = await meilisearch_service.rebuild_index(articles)

        if success:
            return ApiResponse(
                success=True,
                data={
                    'message': f'Search index rebuilt successfully with {len(articles)} articles',
                    'indexed_count': len(articles)
                }
            )
        else:
            return ApiResponse(
                success=False,
                error='Failed to rebuild search index'
            )

    except Exception as e:
        import traceback
        print(f"Error in rebuild_search_index: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/stats")
async def get_search_stats(
        current_user=Depends(jwt_required)
):
    """
    获取搜索索引统计信息（仅管理员）

    Returns:
        统计信息
    """
    try:
        # 检查权限
        if not current_user.is_superuser:
            return ApiResponse(
                success=False,
                error="Permission denied. Admin access required."
            )

        stats = await meilisearch_service.get_index_stats()

        return ApiResponse(
            success=True,
            data=stats
        )

    except Exception as e:
        print(f"Error in get_search_stats: {str(e)}")
        return ApiResponse(success=False, error=str(e))


@router.post("/sync-article/{article_id}")
async def sync_article_to_index(
        article_id: int,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    手动同步单篇文章到搜索索引

    Args:
        article_id: 文章ID

    Returns:
        同步结果
    """
    try:
        from shared.models.article import Article
        from shared.models.article_content import ArticleContent
        from shared.models.category import Category
        from shared.models.user import User
        from sqlalchemy import select

        # 获取文章
        stmt = (
            select(Article, ArticleContent, Category.name.label('category_name'), User.username.label('author_name'))
            .outerjoin(ArticleContent, Article.id == ArticleContent.article)
            .outerjoin(Category, Article.category == Category.id)
            .outerjoin(User, Article.user == User.id)
            .where(Article.id == article_id)
        )

        result = await db.execute(stmt)
        row = result.first()

        if not row:
            return ApiResponse(
                success=False,
                error=f'Article {article_id} not found'
            )

        article, content, category_name, author_name = row

        # 准备索引数据
        article_data = {
            'id': article.id,
            'title': article.title,
            'slug': article.slug,
            'excerpt': article.excerpt or '',
            'content': content.content if content else '',
            'cover_image': article.cover_image or '',
            'category_id': article.category,
            'category_name': category_name or '',
            'author_id': article.user,
            'author_name': author_name or '',
            'tags': [t.strip() for t in re.split(r'[,;]', article.tags_list) if t.strip()] if article.tags_list else [],
            'views': article.views,
            'likes': article.likes,
            'status': 'published' if article.status == 1 else 'draft',
            'is_featured': article.is_featured,
            'created_at': int(article.created_at.timestamp()) if article.created_at else 0,
            'updated_at': int(article.updated_at.timestamp()) if article.updated_at else 0,
        }

        # 索引文章
        if article.status == 1:  # 已发布
            success = await meilisearch_service.index_article(article_data)
        else:
            # 草稿则删除索引
            success = await meilisearch_service.delete_article(article_id)

        if success:
            return ApiResponse(
                success=True,
                data={'message': f'Article {article_id} synced successfully'}
            )
        else:
            return ApiResponse(
                success=False,
                error='Failed to sync article'
            )

    except Exception as e:
        import traceback
        print(f"Error in sync_article_to_index: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))
