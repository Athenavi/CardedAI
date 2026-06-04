"""
简化版首页API接口
解决异步greenlet问题，提供稳定的首页数据服务
"""
import re
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import SystemSettings
from shared.models.article import Article
from shared.models.category import Category
from shared.models.user import User
from src.api.v1.core.responses import ApiResponse
from src.utils.database.main import get_async_session

router = APIRouter(tags=["home"])


async def send_subscription_confirmation_email(email: str):
    """
    后台发送订阅确认邮件(不阻塞主进程)

    Args:
        email: 订阅邮箱
    """
    try:
        from datetime import datetime

        subject = "感谢订阅 FastBlog"

        html_content = f"""
        <h2>感谢订阅!</h2>
        <p>您已成功订阅 FastBlog 的更新通知。</p>
        <p>我们将定期向您发送:</p>
        <ul>
            <li>最新文章推荐</li>
            <li>精选内容汇总</li>
            <li>特别活动通知</li>
        </ul>
        <p>如果您不想继续接收邮件,可以随时取消订阅。</p>
        <p style="color: #999; font-size: 12px;">订阅时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """

        text_content = f"""感谢订阅 FastBlog!

您已成功订阅我们的更新通知。

我们将定期向您发送:
- 最新文章推荐
- 精选内容汇总
- 特别活动通知

如果您不想继续接收邮件,可以随时取消订阅。

订阅时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """

        # 发送邮件
        from shared.services.notifications.email_service import email_service
        email_service.send_email(
            to_email=email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )

        print(f"订阅确认邮件已发送到: {email}")

    except Exception as e:
        print(f"发送订阅确认邮件失败: {e}")
        import traceback
        traceback.print_exc()


@router.get("/data")
async def get_home_data(
        limit_featured: int = Query(4, description="特色文章数量"),
        limit_popular: int = Query(5, description="热门文章数量"),
        limit_recent: int = Query(9, description="最新文章数量"),
        limit_categories: int = Query(8, description="分类数量"),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取首页数据（不含配置）
    使用简化查询避免 greenlet 错误
    """
    try:
        # 简化数据获取 - 逐一查询避免复杂并行查询
        featured_articles = await _get_featured_articles(db, limit_featured)
        recent_articles = await _get_recent_articles_simple(db, limit_recent)
        popular_articles = await _get_popular_articles(db, limit_popular)
        categories = await _get_categories(db, limit_categories)
        stats = await _get_site_stats(db)

        data = {
            "featuredArticles": featured_articles,
            "recentArticles": recent_articles,
            "popularArticles": popular_articles,
            "categories": categories,
            "stats": stats
        }

        return ApiResponse(success=True, data=data)
    except Exception as e:

        from src.unified_logger import default_logger as logger
        logger.error(f"获取首页数据失败：{str(e)}")
        # 返回简化数据而不是错误
        return ApiResponse(success=True, data={
            "featuredArticles": [],
            "recentArticles": [],
            "popularArticles": [],
            "categories": [],
            "stats": {"totalArticles": 0, "totalUsers": 0, "totalViews": 0}
        })


@router.get("/config")
async def get_home_config(db: AsyncSession = Depends(get_async_session)):
    """
    获取首页配置信息
    使用 home_ 前缀键名与 AdminSettings 保持一致
    """
    try:
        # 定义需要的配置键（使用 home_ 前缀，与 AdminSettings 一致）
        config_keys = [
            'site_name',
            'home_hero_title',
            'home_hero_subtitle',
            'home_hero_cta_text',
            'home_hero_cta_link',
            'home_cta_target',
            'home_hero_background_image',
            'home_featured_title',
            'home_main_title',
            'home_newsletter_title',
            'home_newsletter_subtitle',
            'home_newsletter_button_text',
            'home_no_summary_msg',
        ]

        # 简化查询 - 逐个获取配置项避免复杂批量查询
        config_dict = {}
        for key in config_keys:
            try:
                query = select(SystemSettings).where(SystemSettings.setting_key == key)
                result = await db.execute(query)
                item = result.scalar_one_or_none()
                if item:
                    config_dict[key] = item.setting_value
            except Exception as key_error:
                from src.unified_logger import default_logger as logger
                logger.warning(f"获取配置项 {key} 失败：{str(key_error)}")
                continue

        # 获取站点名称
        site_name = config_dict.get('site_name')
        if not site_name:
            from src.setting import app_config
            site_name = getattr(app_config, "sitename", "FastBlog")

        config = {
            "hero": {
                "title": config_dict.get('home_hero_title', f"用文字连接每一个想法"),
                "subtitle": config_dict.get('home_hero_subtitle',
                                            f"FastBlog 是一个现代化的内容创作平台，为创作者提供极致的写作体验，让灵感自由流动。"),
                "backgroundImage": config_dict.get('home_hero_background_image', ""),
                "ctaText": config_dict.get('home_hero_cta_text', "开始阅读"),
                "ctaLink": config_dict.get('home_hero_cta_link', "/articles"),
                "ctaTarget": config_dict.get('home_cta_target', "_self"),
            },
            "sections": {
                "featuredTitle": config_dict.get('home_featured_title', "精选推荐"),
                "mainTitle": config_dict.get('home_main_title', "最新发布"),
                "categoriesTitle": "探索分类",
            },
            "newsletter": {
                "title": config_dict.get('home_newsletter_title', "订阅更新"),
                "subtitle": config_dict.get('home_newsletter_subtitle', "获取最新文章推送"),
                "buttonText": config_dict.get('home_newsletter_button_text', "订阅"),
            },
            "messages": {
                "noSummary": config_dict.get('home_no_summary_msg', "暂无摘要"),
            }
        }

        return ApiResponse(success=True, data=config)
    except Exception as e:

        from src.unified_logger import default_logger as logger
        logger.error(f"获取首页配置失败: {str(e)}")
        return ApiResponse(success=True, data={
            "hero": {
                "title": "用文字连接每一个想法",
                "subtitle": "FastBlog 是一个现代化的内容创作平台",
                "backgroundImage": "",
                "ctaText": "开始阅读",
                "ctaLink": "/articles",
                "ctaTarget": "_self",
            },
            "sections": {
                "featuredTitle": "精选推荐",
                "mainTitle": "最新发布",
                "categoriesTitle": "探索分类",
            },
            "newsletter": {
                "title": "订阅更新",
                "subtitle": "获取最新文章推送",
                "buttonText": "订阅",
            },
            "messages": {
                "noSummary": "暂无摘要",
            }
        })


@router.get("/featured")
async def get_featured_articles(
        limit: int = Query(4, description="返回文章数量"),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取特色文章
    """
    try:
        articles = await _get_featured_articles(db, limit)
        return ApiResponse(success=True, data=articles)
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/articles")
async def get_home_articles_api(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(9, ge=1, le=50),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取首页文章列表（分页）
    用于前端首页展示最新文章
    """
    try:
        # 构建查询 - 只获取已发布、非隐藏、非VIP的文章
        query = select(Article).where(
            Article.hidden == False,
            Article.status == 1,
            Article.is_vip_only == False
        ).order_by(desc(Article.created_at))

        # 获取总数
        count_query = select(func.count(Article.id)).where(
            Article.hidden == False,
            Article.status == 1,
            Article.is_vip_only == False
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        offset = (page - 1) * per_page
        articles_result = await db.execute(query.offset(offset).limit(per_page))
        articles = articles_result.scalars().unique().all()

        # 批量加载分类信息（避免 N+1）
        category_ids = [art.category for art in articles if art.category]
        categories_dict = {}
        if category_ids:
            cat_query = select(Category).where(Category.id.in_(category_ids))
            cat_result = await db.execute(cat_query)
            for cat in cat_result.scalars().all():
                categories_dict[cat.id] = cat

        # 格式化文章数据
        articles_data = [_format_article_with_category(article, categories_dict) for article in articles]

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


@router.get("/recent")
async def get_recent_articles(
        page: int = Query(1, ge=1, description="页码"),
        per_page: int = Query(9, ge=1, le=50, description="每页数量"),
        category_id: Optional[int] = Query(None, description="分类ID"),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取最新文章（分页）- 别名接口，与 /articles 相同
    """
    try:
        articles, pagination = None, None
        return ApiResponse(success=True, data={
            "articles": articles,
            "pagination": pagination
        })
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/popular")
async def get_popular_articles(
        limit: int = Query(5, description="返回文章数量"),
        days: int = Query(30, description="统计天数"),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取热门文章（按浏览量排序）
    """
    try:
        articles = await _get_popular_articles(db, limit, days)
        return ApiResponse(success=True, data=articles)
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/categories")
async def get_home_categories(
        limit: int = Query(8, description="返回分类数量"),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取首页显示的分类
    """
    try:
        categories = await _get_categories(db, limit)
        return ApiResponse(success=True, data=categories)
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/stats")
async def get_home_stats(db: AsyncSession = Depends(get_async_session)):
    """
    获取网站统计数据
    """
    try:
        stats = await _get_site_stats(db)
        return ApiResponse(success=True, data=stats)
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/menus")
async def get_home_menus(request: Request = None):
    """
    获取首页菜单配置
    从数据库获取所有已激活的菜单及其菜单项
    """
    try:
        from src.extensions import get_async_db_session
        from src.utils.menu_builder import get_all_menus_with_items_async

        # 获取数据库会话
        async for db in get_async_db_session():
            try:
                menus_dict = await get_all_menus_with_items_async(db)

                # 将字典转为列表格式，方便前端使用
                menus_list = []
                for menu_id, menu_data in menus_dict.items():
                    menus_list.append({
                        "id": menu_data['id'],
                        "name": menu_data['name'],
                        "slug": menu_data['slug'],
                        "description": menu_data.get('description', ''),
                        "items": menu_data.get('items', [])
                    })

                return ApiResponse(success=True, data={"menus": menus_list})
            finally:
                await db.close()
    except Exception as e:
        import traceback
        print(f"Error in get_home_menus: {str(e)}")
        print(traceback.format_exc())
        # 出错时返回默认菜单
        from src.utils.menu_builder import get_default_menu
        default_items = get_default_menu()
        return ApiResponse(success=True, data={
            "menus": [{
                "id": 0,
                "name": "默认菜单",
                "slug": "default",
                "description": "系统默认菜单",
                "items": default_items
            }]
        })


@router.get("/search")
async def search_home_articles(
        q: str = Query(..., description="搜索关键词"),
        page: int = Query(1, ge=1, description="页码"),
        per_page: int = Query(10, ge=1, le=50, description="每页数量"),
        db: AsyncSession = Depends(get_async_session)
):
    """
    首页文章搜索 - 使用批量查询优化
    """
    try:
        # 构建搜索查询
        query = select(Article).where(
            Article.status == 1,
            Article.hidden == False,
            Article.is_vip_only == False
        )

        # 添加搜索条件
        if q:
            query = query.where(
                Article.title.contains(q) |
                Article.excerpt.contains(q)
            )

        # 分页
        offset = (page - 1) * per_page
        articles_result = await db.execute(
            query.order_by(desc(Article.created_at))
            .offset(offset)
            .limit(per_page)
        )
        articles = articles_result.scalars().all()

        # 批量加载分类信息（避免 N+1）
        category_ids = [art.category_id for art in articles if art.category_id]
        categories_dict = {}
        if category_ids:
            cat_query = select(Category).where(Category.id.in_(category_ids))
            cat_result = await db.execute(cat_query)
            for cat in cat_result.scalars().all():
                categories_dict[cat.id] = cat

        # 获取总数
        count_query = select(func.count(Article.id)).where(
            Article.status == 1,
            Article.hidden == False,
            Article.is_vip_only == False
        )
        if q:
            count_query = count_query.where(
                Article.title.contains(q) |
                Article.excerpt.contains(q)
            )
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # 格式化文章数据
        articles_data = [_format_article_with_category(article, categories_dict) for article in articles]

        pagination = {
            "current_page": page,
            "per_page": per_page,
            "total": total or 0,
            "total_pages": (total + per_page - 1) // per_page if total else 1,
            "has_next": page < ((total + per_page - 1) // per_page if total else 1),
            "has_prev": page > 1
        }

        return ApiResponse(success=True, data={
            "articles": articles_data,
            "pagination": pagination
        })
    except Exception as e:

        from src.unified_logger import default_logger as logger
        logger.error(f"搜索接口错误：{str(e)}")
        return ApiResponse(success=False, error="搜索服务暂时不可用")


# 简化版辅助函数
async def _get_featured_articles(db: AsyncSession, limit: int) -> list:
    """简化版获取特色文章 - 使用批量查询优化"""
    try:
        # 获取特色文章
        query = select(Article).where(
            Article.status == 1,
            Article.hidden == False,
            Article.is_featured == True,
            Article.is_vip_only == False
        ).order_by(desc(Article.created_at)).limit(limit)

        result = await db.execute(query)
        articles = result.scalars().unique().all()

        # 批量加载分类信息（避免 N+1）
        category_ids = [art.category_id for art in articles if art.category_id]
        categories_dict = {}
        if category_ids:
            cat_query = select(Category).where(Category.id.in_(category_ids))
            cat_result = await db.execute(cat_query)
            for cat in cat_result.scalars().all():
                categories_dict[cat.id] = cat

        return [_format_article_with_category(article, categories_dict) for article in articles]
    except Exception as e:

        from src.unified_logger import default_logger as logger
        logger.warning(f"获取特色文章失败：{str(e)}")
        return []


async def _get_recent_articles_simple(db: AsyncSession, limit: int) -> list:
    """简化版获取最新文章 - 使用批量查询优化"""
    try:
        # 获取最新文章
        query = select(Article).where(
            Article.status == 1,
            Article.hidden == False,
            Article.is_vip_only == False
        ).order_by(desc(Article.created_at)).limit(limit)

        result = await db.execute(query)
        articles = result.scalars().unique().all()

        # 批量加载分类信息（避免 N+1）
        category_ids = [art.category_id for art in articles if art.category_id]
        categories_dict = {}
        if category_ids:
            cat_query = select(Category).where(Category.id.in_(category_ids))
            cat_result = await db.execute(cat_query)
            for cat in cat_result.scalars().all():
                categories_dict[cat.id] = cat

        return [_format_article_with_category(article, categories_dict) for article in articles]
    except Exception as e:

        from src.unified_logger import default_logger as logger
        logger.warning(f"获取最新文章失败：{str(e)}")
        return []


async def _get_popular_articles(db: AsyncSession, limit: int) -> list:
    """简化版获取热门文章 - 使用批量查询优化"""
    try:
        # 获取热门文章
        query = select(Article).where(
            Article.status == 1,
            Article.hidden == False,
            Article.is_vip_only == False
        ).order_by(desc(Article.views)).limit(limit)

        result = await db.execute(query)
        articles = result.scalars().unique().all()

        # 批量加载分类信息（避免 N+1）
        category_ids = [art.category_id for art in articles if art.category_id]
        categories_dict = {}
        if category_ids:
            cat_query = select(Category).where(Category.id.in_(category_ids))
            cat_result = await db.execute(cat_query)
            for cat in cat_result.scalars().all():
                categories_dict[cat.id] = cat

        return [_format_article_with_category(article, categories_dict) for article in articles]
    except Exception as e:

        from src.unified_logger import default_logger as logger
        logger.warning(f"获取热门文章失败：{str(e)}")
        return []


async def _get_categories(db: AsyncSession, limit: int) -> list:
    """简化版获取分类"""
    try:
        from sqlalchemy import func
        # 获取分类及其文章数
        category_query = select(
            Category,
            func.count(Article.id).label('article_count')
        ).outerjoin(
            Article,
            (Category.id == Article.category) & (Article.status == 1)
        ).group_by(Category.id).order_by(Category.id.desc()).limit(limit)

        result = await db.execute(category_query)
        categories_with_count = result.all()

        return [{
            "id": cat.id,
            "name": cat.name,
            "description": cat.description or "",
            "article_count": article_count or 0
        } for cat, article_count in categories_with_count]
    except Exception as e:

        from src.unified_logger import default_logger as logger
        logger.warning(f"获取分类失败：{str(e)}")
        return []


async def _get_site_stats(db: AsyncSession) -> Dict[str, Any]:
    """简化版获取网站统计"""
    try:
        # 文章总数
        articles_query = select(func.count(Article.id)).where(Article.status == 1)
        articles_result = await db.execute(articles_query)
        total_articles = articles_result.scalar()

        # 用户总数
        users_query = select(func.count(User.id))
        users_result = await db.execute(users_query)
        total_users = users_result.scalar()

        # 总浏览量
        views_query = select(func.sum(Article.views)).where(Article.views.isnot(None))
        views_result = await db.execute(views_query)
        total_views = views_result.scalar() or 0

        return {
            "totalArticles": total_articles or 0,
            "totalUsers": total_users or 0,
            "totalViews": int(total_views)
        }
    except Exception as e:

        from src.unified_logger import default_logger as logger
        logger.warning(f"获取网站统计失败: {str(e)}")
        return {
            "totalArticles": 0,
            "totalUsers": 0,
            "totalViews": 0
        }


def _format_article_with_category(article, categories_dict=None) -> Dict[str, Any]:
    """增强版文章格式化（包含分类和作者信息）"""
    # 获取分类名称
    category_name = "未分类"
    if categories_dict and article.category in categories_dict:
        category_name = categories_dict[article.category].name
    elif hasattr(article, 'category') and article.category:
        # 如果有关联但未加载，使用 category 占位
        category_name = f"分类-{article.category}"

    # 获取作者信息（由于 author 关系已注释，使用 user）
    author_info = {
        "id": article.user,
        "username": "匿名",
        "email": ""
    }

    return {
        "id": article.id,
        "title": article.title,
        "slug": getattr(article, 'slug', f'article-{article.id}'),
        "excerpt": article.excerpt or "",
        "summary": article.excerpt or "",
        "cover_image": article.cover_image or "",
        "author": author_info,
        "category_id": article.category,
        "category_name": category_name,
        "views": article.views or 0,
        "views_count": article.views or 0,
        "likes": getattr(article, 'likes', 0),
        "created_at": article.created_at.isoformat() if hasattr(article.created_at, 'isoformat') else str(
            article.created_at),
        "updated_at": article.updated_at.isoformat() if hasattr(article.updated_at, 'isoformat') else str(
            article.updated_at),
        "status": article.status,
        "is_featured": getattr(article, 'is_featured', False),
        "tags": [t.strip() for t in re.split(r'[,;]', article.tags_list) if t.strip()] if article.tags_list else []
    }


def _format_article(article) -> Dict[str, Any]:
    """简化版文章格式化（向后兼容）"""
    return _format_article_with_category(article)
