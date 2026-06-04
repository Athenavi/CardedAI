"""
文章相关 API（整合博客功能）
"""
import asyncio
import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from sqlalchemy import func, select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.models.article import Article
from shared.models.article_content import ArticleContent
from shared.models.article_revision import ArticleRevision
from shared.models.category import Category
from shared.models.user import User
from shared.models.vip_plan import VIPPlan
from shared.services.articles.article_manager import article_query_service, password_protection_service, \
    save_article_revision
from shared.services.content_management.shortcode_service import shortcode_service
from shared.services.core.api_embed import APIEmbedService
from shared.services.notifications.webhook_service import webhook_service
from shared.services.static_generation.isr_service import isr_service
from src.api.v1.core.openapi_examples import ARTICLE_LIST_EXAMPLE, ERROR_RESPONSE_EXAMPLE, ARTICLE_DETAIL_EXAMPLE, \
    ARTICLE_CREATE_EXAMPLE
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_optional_dependency, jwt_required_dependency as jwt_required
from src.setting import app_config
from src.utils.database.main import get_async_session
from src.utils.field_filter import filter_fields
from src.utils.filters import markdown_to_html

router = APIRouter()


def _split_tags(tags_str: str) -> list:
    """将标签字符串拆分为数组，同时支持逗号和分号分隔符"""
    if not tags_str:
        return []
    return [t.strip() for t in re.split(r'[,;]', tags_str) if t.strip()]


# ---------- 通用辅助函数 ----------
async def _get_article_author(db: AsyncSession, user_id: int) -> dict:
    """获取文章作者信息字典"""
    author_query = select(User).where(User.id == user_id)
    result = await db.execute(author_query)
    author = result.scalar_one_or_none()
    return {
        "id": author.id if author else user_id,
        "username": author.username if author else "Unknown",
        "bio": author.bio if author else "",
        "profile_picture": author.profile_picture if author else None,
        "email": author.email if author else ""
    }


async def _get_article_detail(
        request: Request,
        db: AsyncSession,
        article: Article,
        current_user: Optional[User] = None
) -> Optional[dict]:
    """
    统一处理文章详情的权限、密码保护、浏览量增加和数据组装。
    返回完整的文章数据字典，若无权限则返回 None。
    """
    # 1. 检查文章是否被删除
    if article.status == -1:
        return None

    # 2. 检查隐藏文章权限
    if article.hidden:
        is_author = current_user and current_user.id == article.user
        is_admin = current_user and getattr(current_user, "is_superuser", False)
        if not (is_author or is_admin):
            # 检查密码保护
            content_query = select(ArticleContent).where(ArticleContent.article == article.id)
            content_result = await db.execute(content_query)
            content_obj = content_result.scalar_one_or_none()
            has_password = content_obj and content_obj.passwd

            if has_password:
                access_token = request.cookies.get(f"article_access_{article.id}") or request.query_params.get(
                    "access_token")
                if not access_token or access_token != password_protection_service.generate_access_token(article.id):
                    return {
                        "requires_password": True,
                        "article_id": article.id,
                        "article_title": article.title,
                        "excerpt": article.excerpt
                    }
            else:
                return None

    # 3. 检查草稿权限
    if article.status == 0:
        is_author = current_user and current_user.id == article.user
        is_admin = current_user and getattr(current_user, "is_superuser", False)
        if not (is_author or is_admin):
            return None

    # 4. 原子增加浏览量（浏览量有专门接口实现）
    # await db.execute(update(Article).where(Article.id == article.id).values(views=Article.views + 1))

    # 5. 获取相关内容
    content_query = select(ArticleContent).where(ArticleContent.article == article.id)
    content_result = await db.execute(content_query)
    article_content = content_result.scalar_one_or_none()
    raw_content = article_content.content if article_content else ""

    # 6. Markdown 转 HTML 并解析 Shortcode
    if raw_content:
        theme = 'github'
        if request.cookies.get("theme"):
            theme = request.cookies.get("theme")
        html_content = markdown_to_html(markdown_text=raw_content, theme=theme, enable_toc=True)
        html_content = shortcode_service.parse(html_content)
    else:
        html_content = ""

    # 7. 获取作者和 SEO 数据
    author_info = await _get_article_author(db, article.user)
    seo_data_dict = article.seo_data.to_dict() if article.seo_data else {}

    # 8. 获取多语言版本
    i18n_query = select(ArticleContent).where(ArticleContent.article == article.id)
    i18n_result = await db.execute(i18n_query)
    i18n_versions = i18n_result.scalars().all()
    i18n_data = [
        {
            "language_code": trans.language_code,
            "content_preview": trans.content[:200] if trans.content else "",
        }
        for trans in i18n_versions
    ]

    # 9. 组装返回数据
    article_data = {
        "id": article.id,
        "title": article.title,
        "slug": article.slug,
        "excerpt": article.excerpt,
        "content": html_content,
        "cover_image": article.cover_image,
        "tags": _split_tags(article.tags_list),
        "views": article.views or 0,
        "likes": article.likes or 0,
        "status": article.status,
        "hidden": article.hidden,
        "is_vip_only": article.is_vip_only,
        "required_vip_level": article.required_vip_level,
        "article_ad": article.article_ad,
        "created_at": article.created_at.isoformat() if hasattr(article.created_at, 'isoformat') else str(
            article.created_at),
        "updated_at": article.updated_at.isoformat() if hasattr(article.updated_at, 'isoformat') else str(
            article.updated_at),
        "user_id": article.user,
        "category_id": article.category,
        "is_featured": article.is_featured,
        "seo_title": seo_data_dict.get("seo_title"),
        "seo_description": seo_data_dict.get("seo_description"),
        "seo_keywords": seo_data_dict.get("seo_keywords"),
        "og_title": seo_data_dict.get("og_title"),
        "og_description": seo_data_dict.get("og_description"),
        "og_image": seo_data_dict.get("og_image"),
        "twitter_title": seo_data_dict.get("twitter_title"),
        "twitter_description": seo_data_dict.get("twitter_description"),
        "twitter_image": seo_data_dict.get("twitter_image"),
        "canonical_url": seo_data_dict.get("canonical_url"),
        "i18n_versions": i18n_data,
        "author": author_info,
    }

    # 尝试调用插件钩子增强文章数据
    try:
        from shared.services.plugins.plugin_manager.init import apply_plugin_filter

        # 添加当前用户ID（供插件使用）
        if current_user:
            article_data['current_user_id'] = str(current_user.id)

        # 应用插件过滤器
        enhanced_data = apply_plugin_filter('article_data', article_data)

        # 使用增强后的数据
        if enhanced_data:
            article_data = enhanced_data
    except Exception as e:
        # 插件钩子失败不应影响主功能
        print(f"[Plugin] article_data hook failed: {e}")

    return article_data


# ---------- 文章列表 ----------
@router.get("/",
            summary=ARTICLE_LIST_EXAMPLE["summary"],
            description=ARTICLE_LIST_EXAMPLE["description"],
            responses=ERROR_RESPONSE_EXAMPLE)
async def get_articles_api(
        request: Request,
        page: int = Query(1, ge=1, description=ARTICLE_LIST_EXAMPLE["parameters"]["page"]["description"],
                          examples=[ARTICLE_LIST_EXAMPLE["parameters"]["page"]["example"]]),
        per_page: int = Query(10, ge=1, le=100,
                              description=ARTICLE_LIST_EXAMPLE["parameters"]["per_page"]["description"],
                              examples=[ARTICLE_LIST_EXAMPLE["parameters"]["per_page"]["example"]]),
        search: str = Query("", description=ARTICLE_LIST_EXAMPLE["parameters"]["search"]["description"],
                            examples=[ARTICLE_LIST_EXAMPLE["parameters"]["search"]["example"]]),
        category_id: Optional[int] = Query(None,
                                           description=ARTICLE_LIST_EXAMPLE["parameters"]["category_id"]["description"],
                                           examples=[ARTICLE_LIST_EXAMPLE["parameters"]["category_id"]["example"]]),
        user_id: Optional[int] = Query(None, description=ARTICLE_LIST_EXAMPLE["parameters"]["user_id"]["description"],
                                       examples=[ARTICLE_LIST_EXAMPLE["parameters"]["user_id"]["example"]]),
        status: Optional[str] = Query(None, description=ARTICLE_LIST_EXAMPLE["parameters"]["status"]["description"],
                                      examples=[ARTICLE_LIST_EXAMPLE["parameters"]["status"]["example"]]),
        fields: Optional[str] = Query(None,
                                      description="指定返回的字段，逗号分隔。支持嵌套字段如: id,title,author.username"),
        embed: Optional[str] = Query(None, description="嵌入关联资源，逗号分隔。支持: author,category"),
        db: AsyncSession = Depends(get_async_session)
):
    try:
        is_admin = False
        if 'user' in request.scope and request.scope['user'] is not None:
            user = request.scope['user']
            is_admin = getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False)

        articles, total = await article_query_service.get_articles_list(
            db=db,
            page=page,
            per_page=per_page,
            search=search if search else None,
            category_id=category_id,
            user_id=user_id,
            status=status,
            include_sticky=True,
            is_admin=is_admin
        )

        # 批量加载作者和分类
        user_ids = list({a.user for a in articles if a.user})
        category_ids = list({a.category for a in articles if a.category})

        users_dict, categories_dict = {}, {}
        if user_ids:
            result = await db.execute(select(User).where(User.id.in_(user_ids)))
            users_dict = {u.id: u for u in result.scalars().all()}
        if category_ids:
            result = await db.execute(select(Category).where(Category.id.in_(category_ids)))
            categories_dict = {c.id: c for c in result.scalars().all()}

        articles_data = []
        for article in articles:
            articles_data.append({
                "id": article.id,
                "title": article.title,
                "slug": article.slug,
                "excerpt": article.excerpt,
                "cover_image": article.cover_image,
                "tags": _split_tags(article.tags_list),
                "author": {
                    "id": article.user,
                    "username": users_dict[article.user].username if article.user in users_dict else "Unknown"
                },
                "category_id": article.category,
                "category_name": categories_dict[
                    article.category].name if article.category in categories_dict else None,
                "views": article.views or 0,
                "likes": article.likes or 0,
                "status": article.status,
                "created_at": article.created_at.isoformat() if article.created_at else None,
                "updated_at": article.updated_at.isoformat() if article.updated_at else None
            })

        # 应用嵌入功能
        if embed:
            embed_service = APIEmbedService(db)
            embed_fields = APIEmbedService.parse_embed_param(embed)
            allowed_fields = ['author', 'category']
            valid_fields = APIEmbedService.validate_embed_fields(embed_fields, allowed_fields)

            if valid_fields:
                articles_data = await embed_service.embed_article_relations(articles, valid_fields)

        # 应用字段过滤
        if fields:
            articles_data = filter_fields(articles_data, fields)

        return ApiResponse(
            success=True,
            data=articles_data,
            pagination={
                "current_page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": (total + per_page - 1) // per_page,
                "has_next": page < (total + per_page - 1) // per_page,
                "has_prev": page > 1
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_articles_api: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))


# ---------- 首页文章列表 (应在 /{article_id} 之前) ----------
@router.get("/home/articles")
async def get_home_articles_api(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(9, ge=1, le=50),
        db: AsyncSession = Depends(get_async_session)
):
    try:
        query = select(Article).where(
            Article.hidden == False,
            Article.status == 1,
            Article.is_vip_only == False
        ).order_by(Article.id.desc())

        offset = (page - 1) * per_page
        result = await db.execute(query.offset(offset).limit(per_page))
        articles = result.scalars().all()

        total = await db.scalar(select(func.count()).select_from(Article).where(
            Article.hidden == False,
            Article.status == 1,
            Article.is_vip_only == False
        ))

        # 批量加载作者和分类
        user_ids = list({a.user for a in articles if a.user})
        category_ids = list({a.category for a in articles if a.category})
        users_dict, categories_dict = {}, {}
        if user_ids:
            res = await db.execute(select(User).where(User.id.in_(user_ids)))
            users_dict = {u.id: u for u in res.scalars().all()}
        if category_ids:
            res = await db.execute(select(Category).where(Category.id.in_(category_ids)))
            categories_dict = {c.id: c for c in res.scalars().all()}

        articles_data = []
        for article in articles:
            articles_data.append({
                "id": article.id,
                "title": article.title,
                "slug": article.slug,
                "excerpt": article.excerpt,
                "cover_image": article.cover_image,
                "tags": _split_tags(article.tags_list),
                "author": {
                    "id": article.user,
                    "username": users_dict[article.user].username if article.user in users_dict else "Unknown"
                },
                "category_id": article.category,
                "category_name": categories_dict[
                    article.category].name if article.category in categories_dict else None,
                "views": article.views or 0,
                "likes": article.likes or 0,
                "created_at": article.created_at.isoformat() if article.created_at else None,
                "updated_at": article.updated_at.isoformat() if article.updated_at else None
            })

        return ApiResponse(
            success=True,
            data={
                "data": articles_data,
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
        print(f"Error in get_home_articles_api: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))


# ---------- 用户文章列表 (应在 /{article_id} 之前) ----------
@router.get("/user/{user_id}")
async def get_user_articles_api(
        request: Request,
        user_id: int = Path(...),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=100),
        current_user: Optional[User] = Depends(jwt_optional_dependency),
        db: AsyncSession = Depends(get_async_session)
):
    try:
        if current_user and current_user.id != user_id and not getattr(current_user, 'is_superuser', False):
            raise HTTPException(status_code=403, detail="Permission denied")

        offset = (page - 1) * per_page
        query = select(Article).where(Article.user == user_id).order_by(Article.created_at.desc())
        result = await db.execute(query.offset(offset).limit(per_page))
        articles = result.scalars().all()
        total = await db.scalar(select(func.count()).select_from(Article).where(Article.user == user_id))

        # 批量加载分类
        category_ids = list({a.category for a in articles if a.category})
        categories_dict = {}
        if category_ids:
            res = await db.execute(select(Category).where(Category.id.in_(category_ids)))
            categories_dict = {c.id: c for c in res.scalars().all()}

        articles_data = []
        for article in articles:
            articles_data.append({
                "id": article.id,
                "title": article.title,
                "excerpt": article.excerpt,
                "cover_image": article.cover_image,
                "tags": _split_tags(article.tags_list),
                "category_id": article.category,
                "category_name": categories_dict[
                    article.category].name if article.category in categories_dict else None,
                "views": article.views or 0,
                "likes": article.likes or 0,
                "status": article.status,
                "created_at": article.created_at.isoformat() if article.created_at else None,
                "updated_at": article.updated_at.isoformat() if article.updated_at else None
            })

        return ApiResponse(
            success=True,
            data=articles_data,
            pagination={
                "current_page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": (total + per_page - 1) // per_page,
                "has_next": page < (total + per_page - 1) // per_page,
                "has_prev": page > 1
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_user_articles_api: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))


@router.get("/user/{user_id}/stats")
async def get_user_articles_stats_api(
        request: Request,
        user_id: int = Path(...),
        current_user: Optional[User] = Depends(jwt_optional_dependency),
        db: AsyncSession = Depends(get_async_session)
):
    try:
        if current_user and current_user.id != user_id and not getattr(current_user, 'is_superuser', False):
            raise HTTPException(status_code=403, detail="Permission denied")
        articles_count = await db.scalar(select(func.count()).select_from(Article).where(Article.user == user_id))
        return ApiResponse(success=True,
                           data={"articles_count": articles_count, "followers_count": 0, "following_count": 0})
    except Exception as e:
        import traceback
        print(f"Error in get_user_articles_stats_api: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))


# ---------- 通过 slug 获取文章 (来自 blog) ----------
@router.get("/p/{slug}",
            summary=ARTICLE_DETAIL_EXAMPLE["summary"],
            description=ARTICLE_DETAIL_EXAMPLE["description"],
            responses=ERROR_RESPONSE_EXAMPLE)
async def get_article_by_slug_api(
        request: Request,
        slug: str,
        current_user=Depends(jwt_optional_dependency),
        db: AsyncSession = Depends(get_async_session)
):
    try:
        article_query = select(Article).options(selectinload(Article.seo_data)).where(Article.slug == slug)
        result = await db.execute(article_query)
        article = result.scalar_one_or_none()
        if not article:
            return ApiResponse(success=False, error="Article not found")

        data = await _get_article_detail(request, db, article, current_user)
        if data is None:
            return ApiResponse(success=False, error="Article not found")
        if isinstance(data, dict) and data.get("requires_password"):
            return ApiResponse(success=False, error="Password required", data=data)

        return ApiResponse(success=True, data={"article": data})
    except Exception as e:
        import traceback
        print(f"Error in get_article_by_slug_api: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))


# ---------- 通过 ID 获取文章 (.html) 来自 blog ----------
@router.get("/{article_id}.html")
async def get_article_by_id_html_api(
        request: Request,
        article_id: int,
        current_user=Depends(jwt_optional_dependency),
        db: AsyncSession = Depends(get_async_session)
):
    try:
        article_query = select(Article).options(selectinload(Article.seo_data)).where(Article.id == article_id)
        result = await db.execute(article_query)
        article = result.scalar_one_or_none()
        if not article:
            return ApiResponse(success=False, error="Article not found")

        data = await _get_article_detail(request, db, article, current_user)
        if data is None:
            return ApiResponse(success=False, error="Article not found")
        if isinstance(data, dict) and data.get("requires_password"):
            return ApiResponse(success=False, error="Password required", data=data)

        return ApiResponse(success=True, data={"article": data, "aid": article_id})
    except Exception as e:
        import traceback
        print(f"Error in get_article_by_id_html_api: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))


# ---------- 文章详情 (原有) ----------
@router.get("/detail")
async def get_article_detail_by_query_api(
        request: Request,
        id: int = Query(..., description="文章ID"),
        db: AsyncSession = Depends(get_async_session)
):
    return await get_article_by_id_html_api(request, id, current_user=None, db=db)


@router.get("/{article_id}")
async def get_article_detail_api(
        request: Request,
        article_id: int,
        db: AsyncSession = Depends(get_async_session)
):
    return await get_article_by_id_html_api(request, article_id, current_user=None, db=db)


# ---------- 原始内容 (用于编辑) ----------
@router.get("/{article_id}/raw")
async def get_article_raw_content_api(
        request: Request,
        article_id: int,
        db: AsyncSession = Depends(get_async_session)
):
    try:
        article_query = select(Article).where(Article.id == article_id, Article.status != -1)
        result = await db.execute(article_query)
        article = result.scalar_one_or_none()
        if not article:
            return ApiResponse(success=False, error="Article not found")

        content_query = select(ArticleContent).where(ArticleContent.article == article_id)
        content_result = await db.execute(content_query)
        content_obj = content_result.scalar_one_or_none()
        raw_content = content_obj.content if content_obj else ""

        author_info = await _get_article_author(db, article.user)

        return ApiResponse(success=True, data={
            "id": article.id,
            "title": article.title,
            "slug": article.slug,
            "excerpt": article.excerpt,
            "content": raw_content,
            "cover_image": article.cover_image,
            "tags": _split_tags(article.tags_list),
            "category_id": article.category,
            "status": article.status,
            "hidden": article.hidden,
            "is_vip_only": article.is_vip_only,
            "required_vip_level": article.required_vip_level,
            "author": author_info,
            "created_at": article.created_at.isoformat() if article.created_at else None,
            "updated_at": article.updated_at.isoformat() if article.updated_at else None
        })
    except Exception as e:
        import traceback
        print(f"Error in get_article_raw_content_api: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))


# ---------- 创建文章 ----------
@router.post("/",
             summary=ARTICLE_CREATE_EXAMPLE["summary"],
             description=ARTICLE_CREATE_EXAMPLE["description"],
             responses=ERROR_RESPONSE_EXAMPLE)
async def create_article_api(
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    try:
        form_data = await request.form()

        # Slug 处理：用户输入或自动生成，统一规范化
        slug = form_data.get('slug', '').strip()
        if not slug:
            title = form_data.get('title', '')
            if title:
                slug = title.lower().strip()
            else:
                slug = f"untitled-{datetime.now().timestamp()}"
        # 统一规范化：空格替换为 -，去除特殊字符，合并连续 -
        slug = re.sub(r'[\s\u3000]+', '-', slug.lower().strip())
        slug = re.sub(r'[^\w\-]+', '-', slug)
        slug = re.sub(r'-+', '-', slug).strip('-')
        # 唯一性检查
        base_slug = slug
        counter = 1
        while await db.scalar(select(Article.id).where(Article.slug == slug)):
            slug = f"{base_slug}-{counter}"
            counter += 1

        # 处理标签（统一用逗号分隔）
        tags = form_data.get('tags', '')
        if isinstance(tags, list):
            tags_str = ','.join(tags)
        else:
            tags_str = str(tags)

        # 敏感词过滤检查
        from shared.services.security.sensitive_word_service import sensitive_word_service
        content_to_check = form_data.get('content', '') + ' ' + form_data.get('title', '')
        sensitive_check = await sensitive_word_service.check_content(content_to_check)

        # 如果包含需要拦截的敏感词，直接拒绝
        if sensitive_check['has_sensitive'] and 'block' in sensitive_check['actions']:
            return ApiResponse(
                success=False,
                error="文章内容包含违规内容，已拒绝",
                data={
                    "sensitive_words_detected": True,
                    "words_found": len(sensitive_check['words_found'])
                }
            )

        # 如果内容需要替换敏感词，进行替换
        filtered_title = form_data.get('title', '')
        filtered_content = form_data.get('content', '')
        if sensitive_check['has_sensitive'] and 'replace' in sensitive_check['actions']:
            filtered_title, _ = await sensitive_word_service.filter_content(form_data.get('title', ''))
            filtered_content, _ = await sensitive_word_service.filter_content(form_data.get('content', ''))

        new_article = Article(
            title=filtered_title,  # 使用过滤后的标题
            slug=slug,
            user=current_user.id,
            excerpt=form_data.get('excerpt', ''),
            cover_image=form_data.get('cover_image', ''),
            tags_list=tags_str,
            status=int(form_data.get('status', 0)),
            hidden=form_data.get('hidden', '0') in ('1', 'true', 'True', True),
            is_vip_only=form_data.get('is_vip_only', '0') in ('1', 'true', 'True', True),
            required_vip_level=int(form_data.get('required_vip_level', 0)),
            is_featured=form_data.get('is_featured', '0') in ('1', 'true', 'True', True),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # 分类（仅设置正数 ID，0 或空字符串跳过）
        category_id = form_data.get('category_id')
        if category_id and category_id.isdigit() and int(category_id) > 0:
            new_article.category = int(category_id)

        # 定时发布
        scheduled = form_data.get('scheduled_publish_at')
        if scheduled and scheduled.strip():
            try:
                new_article.scheduled_publish_at = datetime.fromisoformat(scheduled.replace('Z', '+00:00'))
            except ValueError:
                pass

        db.add(new_article)
        await db.flush()

        # 文章内容
        now = datetime.now()
        new_content = ArticleContent(
            article=new_article.id,
            content=filtered_content,  # 使用过滤后的内容
            created_at=now,
            updated_at=now
        )
        db.add(new_content)

        # 修订记录
        if form_data.get('create_revision', 'true').lower() in ('true', '1', 'yes'):

            try:
                await save_article_revision(
                    db=db,
                    article_id=new_article.id,
                    author_id=current_user.id,
                    change_summary=form_data.get('change_summary', '创建文章')
                )
            except Exception as rev_err:
                print(f"保存修订失败: {rev_err}")

        await db.commit()

        # 触发 Webhook 事件
        try:
            asyncio.create_task(webhook_service.trigger_event(
                'article.created',
                {
                    'article_id': new_article.id,
                    'title': new_article.title,
                    'slug': new_article.slug,
                    'author_id': current_user.id,
                    'status': new_article.status,
                    'created_at': new_article.created_at.isoformat() if new_article.created_at else None,
                }
            ))
        except Exception as webhook_err:
            print(f"Webhook trigger failed: {webhook_err}")

        # 触发 ISR 重新生成
        try:
            asyncio.create_task(isr_service.on_article_update(new_article.slug))
        except Exception as isr_err:
            print(f"ISR trigger failed: {isr_err}")

        # 记录审计日志
        try:
            from shared.services.security.audit_log_service import audit_log_service, AuditLogAction
            await audit_log_service.log_action(
                db=db, user_id=current_user.id, user_name=getattr(current_user, 'username', None),
                action=AuditLogAction.CREATE, resource_type='article', resource_id=str(new_article.id),
                description=f"创建文章：{new_article.title}",
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get('user-agent'),
            )
        except Exception as audit_err:
            print(f"审计日志记录失败: {audit_err}")

        return ApiResponse(success=True, data={"message": "Article created successfully", "article_id": new_article.id})
    except Exception as e:
        await db.rollback()
        import traceback
        print(f"Error in create_article_api: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))


# ---------- 更新文章 ----------
@router.put("/{article_id}")
async def update_article_api(
        request: Request,
        article_id: int,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    try:
        result = await db.execute(select(Article).where(Article.id == article_id))
        article = result.scalar_one_or_none()
        if not article:
            return ApiResponse(success=False, error="Article not found")

        if article.user != current_user.id and not getattr(current_user, 'is_superuser', False):
            raise HTTPException(status_code=403, detail="Permission denied")

        form_data = await request.form()

        # 更新字段
        article.title = form_data.get('title', article.title)

        slug = form_data.get('slug', '').strip()
        if not slug:
            title = form_data.get('title', '')
            if title:
                slug = title.lower().strip()
            else:
                slug = f"untitled-{article_id}"
        # 统一规范化：空格替换为 -，去除特殊字符，合并连续 -
        slug = re.sub(r'[\s\u3000]+', '-', slug.lower().strip())
        slug = re.sub(r'[^\w\-]+', '-', slug)
        slug = re.sub(r'-+', '-', slug).strip('-')
        base_slug = slug
        counter = 1
        while await db.scalar(select(Article.id).where(Article.slug == slug, Article.id != article_id)):
            slug = f"{base_slug}-{counter}"
            counter += 1
        article.slug = slug

        article.excerpt = form_data.get('excerpt', article.excerpt)
        article.cover_image = form_data.get('cover_image', article.cover_image)

        # 标签
        tags = form_data.get('tags', '')
        if isinstance(tags, list):
            article.tags_list = ','.join(tags)
        else:
            article.tags_list = str(tags)

        article.status = int(form_data.get('status', article.status))
        # 修复：正确解析布尔值（支持 '1', '0', 'true', 'false', True, False）
        hidden_value = form_data.get('hidden', '0')
        article.hidden = hidden_value in ('1', 'true', 'True', True)

        is_vip_only_value = form_data.get('is_vip_only', '0')
        article.is_vip_only = is_vip_only_value in ('1', 'true', 'True', True)

        article.required_vip_level = int(form_data.get('required_vip_level', article.required_vip_level))

        is_featured_value = form_data.get('is_featured', '0')
        article.is_featured = is_featured_value in ('1', 'true', 'True', True)

        category_id = form_data.get('category_id')
        article.category = int(category_id) if category_id and category_id.isdigit() and int(category_id) > 0 else None

        scheduled = form_data.get('scheduled_publish_at')
        if scheduled:
            try:
                article.scheduled_publish_at = datetime.fromisoformat(scheduled.replace('Z', '+00:00'))
            except ValueError:
                article.scheduled_publish_at = None
        elif scheduled == '':
            article.scheduled_publish_at = None

        # 敏感词过滤检查与替换
        try:
            new_title = form_data.get('title', article.title)
            content_text_raw = form_data.get('content', '')
            from shared.services.security.sensitive_word_service import sensitive_word_service
            content_to_check = content_text_raw + ' ' + new_title
            sensitive_check = await sensitive_word_service.check_content(content_to_check)
            if sensitive_check.get('has_sensitive') and 'block' in sensitive_check.get('actions', []):
                return ApiResponse(success=False, error="文章内容包含违规内容，已拒绝")
            if sensitive_check.get('has_sensitive') and 'replace' in sensitive_check.get('actions', []):
                article.title, _ = await sensitive_word_service.filter_content(new_title)
                content_text = (await sensitive_word_service.filter_content(content_text_raw))[0]
            else:
                content_text = content_text_raw
        except Exception as filter_err:
            print(f"敏感词过滤失败: {filter_err}")
            content_text = form_data.get('content', '')

        article.updated_at = datetime.now()

        # 内容更新
        content_result = await db.execute(select(ArticleContent).where(ArticleContent.article == article_id))
        content_obj = content_result.scalar_one_or_none()
        if content_obj:
            content_obj.content = content_text
            content_obj.updated_at = datetime.now()
        else:
            db.add(ArticleContent(article=article_id, content=content_text, created_at=datetime.now(),
                                  updated_at=datetime.now()))

        # 修订记录
        if form_data.get('create_revision', 'true').lower() in ('true', '1', 'yes'):

            try:
                await save_article_revision(
                    db=db,
                    article_id=article_id,
                    author_id=current_user.id,
                    change_summary=form_data.get('change_summary', '手动保存')
                )
            except Exception as rev_err:
                print(f"保存修订失败: {rev_err}")

        await db.commit()

        # 触发 Webhook 事件
        try:

            await webhook_service.trigger_event(
                'article.updated',
                {
                    'article_id': article_id,
                    'title': article.title,
                    'slug': article.slug,
                    'updated_fields': list(form_data.keys()),
                    'updated_at': article.updated_at.isoformat() if article.updated_at else None,
                },
                db=db
            )
        except Exception as webhook_err:
            print(f"Webhook trigger failed: {webhook_err}")

        # 记录审计日志
        try:
            from shared.services.security.audit_log_service import audit_log_service, AuditLogAction
            await audit_log_service.log_action(
                db=db, user_id=current_user.id, user_name=getattr(current_user, 'username', None),
                action=AuditLogAction.UPDATE, resource_type='article', resource_id=str(article_id),
                description=f"更新文章：{article.title}",
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get('user-agent'),
            )
        except Exception as audit_err:
            print(f"审计日志记录失败: {audit_err}")

        return ApiResponse(success=True, data={"message": "Article updated successfully"})
    except Exception as e:
        await db.rollback()
        import traceback
        print(f"Error in update_article_api: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))


# ---------- 删除文章 ----------
@router.delete("/{article_id}")
async def delete_article_api(
        request: Request,
        article_id: int,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    try:
        result = await db.execute(select(Article).where(Article.id == article_id))
        article = result.scalar_one_or_none()
        if not article:
            return ApiResponse(success=False, error="Article not found")
        if article.user != current_user.id and not getattr(current_user, 'is_superuser', False):
            raise HTTPException(status_code=403, detail="Permission denied")

        # 级联删除评论投票（先于评论删除，避免孤立记录）
        from shared.models.comment import Comment
        from shared.models.comment_vote import CommentVote
        from shared.models.comment_subscription import CommentSubscription

        comment_ids_result = await db.execute(
            select(Comment.id).where(Comment.article_id == article_id)
        )
        comment_ids = [row[0] for row in comment_ids_result.all()]
        if comment_ids:
            await db.execute(
                delete(CommentVote).where(CommentVote.comment_id.in_(comment_ids))
            )

        # 级联删除评论订阅
        await db.execute(
            delete(CommentSubscription).where(CommentSubscription.article_id == article_id)
        )

        # 级联删除评论
        await db.execute(
            delete(Comment).where(Comment.article_id == article_id)
        )

        # 级联删除修订历史
        revisions_query = select(ArticleRevision).where(ArticleRevision.article_id == article_id)
        revisions_result = await db.execute(revisions_query)
        for revision in revisions_result.scalars().all():
            await db.delete(revision)

        # 级联删除内容 - 使用 delete 语句确保完全删除
        await db.execute(
            delete(ArticleContent).where(ArticleContent.article == article_id)
        )

        await db.delete(article)
        await db.commit()

        # 触发 Webhook 事件
        try:

            await webhook_service.trigger_event(
                'article.deleted',
                {
                    'article_id': article_id,
                    'title': article.title,
                    'slug': article.slug,
                    'deleted_at': datetime.now().isoformat(),
                },
                db=db
            )
        except Exception as webhook_err:
            print(f"Webhook trigger failed: {webhook_err}")

        # 记录审计日志
        try:
            from shared.services.security.audit_log_service import audit_log_service, AuditLogAction
            await audit_log_service.log_action(
                db=db, user_id=current_user.id, user_name=getattr(current_user, 'username', None),
                action=AuditLogAction.DELETE, resource_type='article', resource_id=str(article_id),
                description=f"删除文章：{article.title}",
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get('user-agent'),
            )
        except Exception as audit_err:
            print(f"审计日志记录失败: {audit_err}")

        return ApiResponse(success=True, data={"message": "Article deleted successfully"})
    except Exception as e:
        import traceback
        print(f"Error in delete_article_api: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))


# ---------- 标签文章列表 (来自 blog) ----------
@router.get("/tag/{tag_name}")
async def get_articles_by_tag_api(
        request: Request,
        tag_name: str,
        db: AsyncSession = Depends(get_async_session)
):
    try:
        query = select(Article).where(
            Article.tags_list.like(f"%{tag_name}%"),
            Article.status == 1,
            Article.hidden == False,
            Article.is_vip_only == False
        ).order_by(Article.created_at.desc())
        result = await db.execute(query)
        articles = result.scalars().all()

        # 批量加载作者和分类
        user_ids = list({a.user for a in articles})
        category_ids = list({a.category for a in articles if a.category})
        users_dict, categories_dict = {}, {}
        if user_ids:
            res = await db.execute(select(User).where(User.id.in_(user_ids)))
            users_dict = {u.id: u for u in res.scalars().all()}
        if category_ids:
            res = await db.execute(select(Category).where(Category.id.in_(category_ids)))
            categories_dict = {c.id: c for c in res.scalars().all()}

        articles_data = []
        for article in articles:
            articles_data.append({
                "id": article.id,
                "title": article.title,
                "slug": article.slug,
                "excerpt": article.excerpt,
                "cover_image": article.cover_image,
                "tags": _split_tags(article.tags_list),
                "author": {
                    "id": article.user,
                    "username": users_dict[article.user].username if article.user in users_dict else "Unknown"
                },
                "category_id": article.category,
                "category_name": categories_dict[
                    article.category].name if article.category in categories_dict else None,
                "views": article.views or 0,
                "likes": article.likes or 0,
                "created_at": article.created_at.isoformat() if article.created_at else None,
            })
        return ApiResponse(success=True, data={"tag_name": tag_name, "articles": articles_data})
    except Exception as e:
        import traceback
        print(f"Error in get_articles_by_tag_api: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))


# ---------- 推荐文章 (来自 blog) ----------
@router.get("/featured")
async def get_featured_articles_api(
        request: Request,
        db: AsyncSession = Depends(get_async_session)
):
    try:
        query = select(Article).where(
            Article.is_featured == True,
            Article.status == 1,
            Article.hidden == False,
            Article.is_vip_only == False
        )
        result = await db.execute(query)
        articles = result.scalars().all()

        user_ids = list({a.user for a in articles})
        category_ids = list({a.category for a in articles if a.category})
        users_dict, categories_dict = {}, {}
        if user_ids:
            res = await db.execute(select(User).where(User.id.in_(user_ids)))
            users_dict = {u.id: u for u in res.scalars().all()}
        if category_ids:
            res = await db.execute(select(Category).where(Category.id.in_(category_ids)))
            categories_dict = {c.id: c for c in res.scalars().all()}

        articles_data = []
        for article in articles:
            articles_data.append({
                "id": article.id,
                "title": article.title,
                "slug": article.slug,
                "excerpt": article.excerpt,
                "cover_image": article.cover_image,
                "tags": _split_tags(article.tags_list),
                "author": {
                    "id": article.user,
                    "username": users_dict[article.user].username if article.user in users_dict else "Unknown"
                },
                "category_id": article.category,
                "category_name": categories_dict[
                    article.category].name if article.category in categories_dict else None,
                "views": article.views or 0,
                "likes": article.likes or 0,
                "created_at": article.created_at.isoformat() if article.created_at else None,
            })
        return ApiResponse(success=True, data={"featured_articles": articles_data})
    except Exception as e:
        import traceback
        print(f"Error in get_featured_articles_api: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))


# ---------- 贡献翻译 (来自 blog) ----------
@router.get("/contribute/{article_id}")
async def get_contribute_info_api(article_id: int):
    return ApiResponse(success=True, data={"aid": article_id})


@router.post("/contribute/{article_id}")
async def submit_contribution_api(request: Request, article_id: int):
    try:
        data = await request.json()
        required = ['contribute_type', 'contribute_content', 'contribute_language', 'contribute_title',
                    'contribute_slug']
        if not all(data.get(k) for k in required):
            return ApiResponse(success=False, error='All fields are required')
        return ApiResponse(success=True, data={"message": "Translation submitted successfully", "i18n_id": 1})
    except Exception as e:
        import traceback
        print(f"Error in submit_contribution_api: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))


# ---------- 编辑页面数据 (来自 blog) ----------
@router.get("/edit/{article_id}")
async def get_edit_article_api(
        article_id: int,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    try:
        result = await db.execute(select(Article).where(Article.id == article_id))
        article = result.scalar_one_or_none()
        if not article:
            return ApiResponse(success=False, error="文章不存在")
        if article.user != current_user.id and not getattr(current_user, 'is_superuser', False):
            raise HTTPException(status_code=403, detail="您没有权限编辑此文章")

        content_result = await db.execute(select(ArticleContent).where(ArticleContent.article == article_id))
        content_obj = content_result.scalar_one_or_none()
        content_text = content_obj.content if content_obj else ""

        categories = (await db.execute(select(Category))).scalars().all()
        vip_plans = (await db.execute(select(VIPPlan))).scalars().all()

        return ApiResponse(success=True, data={
            "article": {
                "id": article.id,
                "title": article.title,
                "slug": article.slug,
                "excerpt": article.excerpt,
                "cover_image": article.cover_image,
                "tags": _split_tags(article.tags_list),
                "status": article.status,
                "hidden": article.hidden,
                "is_vip_only": article.is_vip_only,
                "required_vip_level": article.required_vip_level,
                "article_ad": article.article_ad,
                "category_id": article.category,
                "is_featured": article.is_featured,
            },
            "content": content_text,
            "categories": [{"id": c.id, "name": c.name, "description": c.description} for c in categories],
            "vip_plans": [{"id": p.id, "name": p.name, "level": p.level, "price": p.price} for p in vip_plans],
            "domain": app_config.domain
        })
    except Exception as e:
        import traceback
        print(f"Error in get_edit_article_api: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))


@router.get("/new")
async def get_new_article_form_api(
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    try:
        categories = (await db.execute(select(Category))).scalars().all()
        vip_plans = (await db.execute(select(VIPPlan))).scalars().all()
        return ApiResponse(success=True, data={
            "categories": [{"id": c.id, "name": c.name, "description": c.description} for c in categories],
            "vip_plans": [{"id": p.id, "name": p.name, "level": p.level, "price": p.price} for p in vip_plans],
            "domain": app_config.domain
        })
    except Exception as e:
        import traceback
        print(f"Error in get_new_article_form_api: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))


# ---------- 粘性文章管理 ----------
@router.post("/{article_id}/sticky")
async def toggle_article_sticky_api(
        request: Request,
        article_id: int,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    try:
        if not getattr(current_user, 'is_staff', False) and not getattr(current_user, 'is_superuser', False):
            result = await db.execute(select(Article.user).where(Article.id == article_id))
            author_id = result.scalar_one_or_none()
            if not author_id or author_id != current_user.id:
                raise HTTPException(status_code=403, detail="Permission denied")

        body = await request.json()
        is_sticky = body.get('is_sticky', False)
        sticky_until = None
        if body.get('sticky_until'):
            try:
                sticky_until = datetime.fromisoformat(body['sticky_until'].replace('Z', '+00:00'))
            except ValueError as e:
                return ApiResponse(success=False, error=f"Invalid sticky_until format: {e}")

        updated = await article_query_service.toggle_sticky_status(db, article_id, is_sticky, sticky_until)
        if not updated:
            return ApiResponse(success=False, error="Article not found")

        return ApiResponse(success=True, data={
            "message": "Sticky status updated",
            "article_id": updated.id,
            "is_sticky": updated.is_sticky,
            "sticky_until": updated.sticky_until.isoformat() if updated.sticky_until else None
        })
    except Exception as e:
        import traceback
        print(f"Error in toggle_article_sticky_api: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))


@router.post("/admin/clean-expired-sticky")
async def clean_expired_sticky_articles_api(
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    try:
        if not getattr(current_user, 'is_staff', False) and not getattr(current_user, 'is_superuser', False):
            raise HTTPException(status_code=403, detail="Admin permission required")
        cleaned = await article_query_service.clean_expired_sticky_articles(db)
        return ApiResponse(success=True,
                           data={"message": f"Cleaned {cleaned} expired sticky articles", "cleaned_count": cleaned})
    except Exception as e:
        import traceback
        print(f"Error in clean_expired_sticky_articles_api: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))


# ---------- 文章拖拽排序 ----------
@router.post("/reorder")
async def reorder_articles_api(
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    """
    文章拖拽排序

    请求体格式：
    {
        "articles": [
            {"id": 1, "sort_order": 0},
            {"id": 2, "sort_order": 1},
            ...
        ]
    }
    """
    try:
        body = await request.json()
        articles_data = body.get('articles', [])

        if not articles_data:
            return ApiResponse(success=False, error="缺少文章数据")

        # 提取文章ID列表
        article_ids = [item['id'] for item in articles_data]

        # 验证权限：只能排序自己的文章，管理员可以排序所有文章
        is_admin = getattr(current_user, 'is_superuser', False)

        if is_admin:
            query = select(Article).where(Article.id.in_(article_ids))
        else:
            query = select(Article).where(
                Article.id.in_(article_ids),
                Article.user == current_user.id
            )

        result = await db.execute(query)
        articles = {article.id: article for article in result.scalars().all()}

        # 更新排序
        updated_count = 0
        for item in articles_data:
            article_id = item['id']
            new_sort_order = item.get('sort_order', 0)

            if article_id in articles:
                articles[article_id].sort_order = new_sort_order
                articles[article_id].updated_at = datetime.now()
                updated_count += 1

        await db.commit()

        return ApiResponse(
            success=True,
            data={
                "message": "排序更新成功",
                "updated_count": updated_count
            }
        )
    except Exception as e:
        await db.rollback()
        import traceback
        print(f"Error in reorder_articles_api: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))


# ---------- 文章批量操作 ----------
@router.post("/batch-operation")
async def batch_article_operation_api(
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    """
    文章批量操作

    支持的操作：
    - delete: 批量删除
    - publish: 批量发布
    - draft: 批量设为草稿
    - feature: 批量推荐
    - unfeature: 批量取消推荐
    """
    try:
        body = await request.json()
        operation = body.get('operation')
        article_ids = body.get('article_ids', [])

        if not operation or not article_ids:
            return ApiResponse(success=False, error="缺少必要参数")

        # 验证权限：只能操作自己的文章，管理员可以操作所有文章
        is_admin = getattr(current_user, 'is_superuser', False)

        if is_admin:
            query = select(Article).where(Article.id.in_(article_ids))
        else:
            query = select(Article).where(
                Article.id.in_(article_ids),
                Article.user == current_user.id
            )

        result = await db.execute(query)
        articles = result.scalars().all()

        if not articles:
            return ApiResponse(success=False, error="没有找到可操作的文章或权限不足")

        updated_count = 0
        for article in articles:
            if operation == 'delete':
                article.status = -1
            elif operation == 'publish':
                article.status = 1
            elif operation == 'draft':
                article.status = 0
            elif operation == 'feature':
                article.is_featured = True
            elif operation == 'unfeature':
                article.is_featured = False
            else:
                continue

            article.updated_at = datetime.now()
            updated_count += 1

        await db.commit()

        return ApiResponse(
            success=True,
            data={
                "message": f"成功{updated_count}篇文章",
                "operation": operation,
                "updated_count": updated_count
            }
        )
    except Exception as e:
        await db.rollback()
        import traceback
        print(f"Error in batch_article_operation_api: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))
