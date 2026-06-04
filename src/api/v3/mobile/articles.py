"""
移动端文章API
提供适合移动端的文章相关接口，包括列表、详情、搜索等功能
"""
import re
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.article import Article
from shared.models.category import Category
from shared.models.user import User
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_optional_dependency
from src.utils.database.main import get_async_session

router = APIRouter(tags=["mobile-articles"])


@router.get("/list")
async def get_mobile_articles_list(
        request: Request,
        page: int = Query(1, ge=1, description="页码"),
        per_page: int = Query(20, ge=1, le=50, description="每页数量"),
        category_id: Optional[int] = Query(None, description="分类ID"),
        search: Optional[str] = Query(None, description="搜索关键词"),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取文章列表（移动端优化）
    返回精简的文章信息，适合移动端展示
    """
    try:
        # 构建查询
        query = select(Article).where(
            Article.status == 1,  # 只返回已发布的文章
            Article.hidden == False  # 不返回隐藏文章
        )

        # 添加分类过滤
        if category_id:
            query = query.where(Article.category == category_id)

        # 添加搜索
        if search:
            query = query.where(Article.title.contains(search))

        # 按创建时间倒序排列
        query = query.order_by(Article.created_at.desc())

        # 获取总数
        count_query = select(func.count()).select_from(Article).where(
            Article.status == 1,
            Article.hidden == False
        )
        if category_id:
            count_query = count_query.where(Article.category == category_id)
        if search:
            count_query = count_query.where(Article.title.contains(search))

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        result = await db.execute(query)
        articles = result.scalars().all()

        # 批量加载作者和分类
        user_ids = list({a.user for a in articles if a.user})
        category_ids = list({a.category for a in articles if a.category})

        users_dict = {}
        categories_dict = {}

        if user_ids:
            users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
            users_dict = {u.id: u for u in users_result.scalars().all()}

        if category_ids:
            categories_result = await db.execute(select(Category).where(Category.id.in_(category_ids)))
            categories_dict = {c.id: c for c in categories_result.scalars().all()}

        # 构建响应数据
        articles_data = []
        for article in articles:
            author = users_dict.get(article.user)
            category = categories_dict.get(article.category)

            articles_data.append({
                "id": article.id,
                "title": article.title,
                "excerpt": article.excerpt[:200] if article.excerpt else "",  # 限制摘要长度
                "cover_image": article.cover_image,
                "author": {
                    "id": author.id if author else None,
                    "username": author.username if author else "Unknown",
                    "avatar": author.profile_picture if author else None
                },
                "category": {
                    "id": category.id if category else None,
                    "name": category.name if category else None
                },
                "views": article.views or 0,
                "likes": article.likes or 0,
                "created_at": article.created_at.isoformat() if article.created_at else None,
                "tags": [t.strip() for t in re.split(r'[,;]', article.tags_list) if
                         t.strip()] if article.tags_list else []
            })

        return ApiResponse(
            success=True,
            data={
                "articles": articles_data,
                "pagination": {
                    "current_page": page,
                    "per_page": per_page,
                    "total": total,
                    "total_pages": (total + per_page - 1) // per_page,
                    "has_next": page < (total + per_page - 1) // per_page,
                    "has_prev": page > 1
                }
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_mobile_articles_list: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))


@router.get("/{article_id}")
async def get_mobile_article_detail(
        request: Request,
        article_id: int,
        db: AsyncSession = Depends(get_async_session),
        current_user=Depends(jwt_optional_dependency)
):
    """
    获取文章详情（移动端优化）
    返回完整的文章内容，适合移动端阅读
    """
    try:
        from shared.models.article_content import ArticleContent
        from sqlalchemy.orm import selectinload

        # 查询文章
        article_query = select(Article).options(selectinload(Article.seo_data)).where(
            Article.id == article_id,
            Article.status == 1
        )
        article_result = await db.execute(article_query)
        article = article_result.scalar_one_or_none()

        if not article:
            return ApiResponse(success=False, error="文章不存在")

        # 查询文章内容
        content_query = select(ArticleContent).where(ArticleContent.article == article_id)
        content_result = await db.execute(content_query)
        article_content = content_result.scalar_one_or_none()

        # 获取作者信息
        author_query = select(User).where(User.id == article.user)
        author_result = await db.execute(author_query)
        author = author_result.scalar_one_or_none()

        # 获取分类信息
        category = None
        if article.category:
            category_query = select(Category).where(Category.id == article.category)
            category_result = await db.execute(category_query)
            category = category_result.scalar_one_or_none()

        # 增加浏览量
        article.views = (article.views or 0) + 1
        await db.commit()

        return ApiResponse(
            success=True,
            data={
                "id": article.id,
                "title": article.title,
                "slug": article.slug,
                "excerpt": article.excerpt,
                "content": article_content.content if article_content else "",
                "cover_image": article.cover_image,
                "author": {
                    "id": author.id if author else None,
                    "username": author.username if author else "Unknown",
                    "avatar": author.profile_picture if author else None,
                    "bio": author.bio if author and hasattr(author, 'bio') else ""
                },
                "category": {
                    "id": category.id if category else None,
                    "name": category.name if category else None
                },
                "views": article.views or 0,
                "likes": article.likes or 0,
                "created_at": article.created_at.isoformat() if article.created_at else None,
                "updated_at": article.updated_at.isoformat() if article.updated_at else None,
                "tags": [t.strip() for t in re.split(r'[,;]', article.tags_list) if
                         t.strip()] if article.tags_list else [],
                "is_vip_only": article.is_vip_only,
                "required_vip_level": article.required_vip_level
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_mobile_article_detail: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))


@router.get("/search")
async def search_mobile_articles(
        request: Request,
        keyword: str = Query(..., min_length=1, description="搜索关键词"),
        page: int = Query(1, ge=1, description="页码"),
        per_page: int = Query(20, ge=1, le=50, description="每页数量"),
        db: AsyncSession = Depends(get_async_session)
):
    """
    搜索文章（移动端）
    """
    try:
        # 构建搜索查询
        query = select(Article).where(
            Article.status == 1,
            Article.hidden == False,
            (
                    Article.title.contains(keyword) |
                    Article.excerpt.contains(keyword)
            )
        ).order_by(Article.created_at.desc())

        # 获取总数
        count_query = select(func.count()).select_from(Article).where(
            Article.status == 1,
            Article.hidden == False,
            (
                    Article.title.contains(keyword) |
                    Article.excerpt.contains(keyword)
            )
        )

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        result = await db.execute(query)
        articles = result.scalars().all()

        # 批量加载作者
        user_ids = list({a.user for a in articles if a.user})
        users_dict = {}

        if user_ids:
            users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
            users_dict = {u.id: u for u in users_result.scalars().all()}

        # 构建响应数据
        articles_data = []
        for article in articles:
            author = users_dict.get(article.user)

            articles_data.append({
                "id": article.id,
                "title": article.title,
                "excerpt": article.excerpt[:200] if article.excerpt else "",
                "cover_image": article.cover_image,
                "author": {
                    "id": author.id if author else None,
                    "username": author.username if author else "Unknown"
                },
                "views": article.views or 0,
                "likes": article.likes or 0,
                "created_at": article.created_at.isoformat() if article.created_at else None
            })

        return ApiResponse(
            success=True,
            data={
                "articles": articles_data,
                "keyword": keyword,
                "pagination": {
                    "current_page": page,
                    "per_page": per_page,
                    "total": total,
                    "total_pages": (total + per_page - 1) // per_page
                }
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in search_mobile_articles: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))
