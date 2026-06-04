"""
RSS/Atom Feed API
提供博客内容的 RSS 和 Atom 订阅源
"""
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import User, Article, Category
from src.extensions import get_async_db_session as get_async_db
from src.setting import AppConfig
from src.utils.feed_generator import FeedItem, RSSFeedGenerator

router = APIRouter(tags=["feed"])


async def get_feed_items(
        db: AsyncSession,
        articles: list,
        site_url: str,
        feed_type: str = 'rss'
) -> list:
    """从文章列表生成 Feed 条目"""
    items = []

    for article in articles:
        # 获取作者信息
        author_name = None
        if article.user:
            user_result = await db.execute(
                select(User).where(User.id == article.user)
            )
            user = user_result.scalar_one_or_none()
            if user:
                author_name = user.username

        # 获取分类
        categories = []
        if hasattr(article, 'categories'):
            for cat in article.categories:
                categories.append(cat.name)

        # 构建链接
        article_url = f"{site_url}/blog/p/{article.slug}" if article.slug else f"{site_url}/blog/{article.id}.html"

        # 创建 Feed 条目
        item = FeedItem(
            title=article.title,
            link=article_url,
            description=article.excerpt or article.content[:200] if article.content else '',
            pub_date=article.created_at or datetime.now(),
            author=author_name,
            categories=categories,
            content=article.content if hasattr(article, 'content') else None,
            image=article.cover_image,  # 使用文章封面图片
        )
        items.append(item)

    return items


@router.get("/feed")
@router.get("/rss")
async def get_rss_feed(
        request: Request,
        db: AsyncSession = Depends(get_async_db),
        limit: int = Query(default=20, ge=1, le=100, description="文章数量限制"),
        format: str = Query(default='rss', pattern='^(rss|atom)$', description="Feed 格式"),
):
    """
    获取全站文章 Feed

    支持 RSS 2.0 和 Atom 1.0 格式
    """

    # 查询已发布的文章
    stmt = (
        select(Article)
        .where(Article.status == 'published')
        .order_by(Article.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    articles = result.scalars().all()

    # 站点配置
    site_url = str(request.base_url).rstrip('/')
    site_title = AppConfig.site_title or "FastBlog"
    site_description = AppConfig.site_description or "FastBlog - 现代化博客系统"

    # 创建 Feed 生成器
    generator = RSSFeedGenerator(
        title=site_title,
        link=site_url,
        description=site_description,
        language='zh-CN',
        feed_url=f"{site_url}/feed",
        icon_url=f"{site_url}/api/v2/static/logo.png",
        copyright=f"© {datetime.now().year} {site_title}",
    )

    # 添加文章条目
    feed_items = await get_feed_items(db, articles, site_url, format)
    for item in feed_items:
        generator.add_item(item)

    # 生成 Feed
    if format == 'atom':
        content = generator.generate_atom()
        media_type = 'application/atom+xml'
    else:
        content = generator.generate_rss()
        media_type = 'application/rss+xml'

    return Response(
        content=content,
        media_type=media_type,
        headers={
            'Cache-Control': 'public, max-age=3600',  # 缓存 1 小时
        }
    )


@router.get("/atom")
async def get_atom_feed(
        request: Request,
        db: AsyncSession = Depends(get_async_db),
        limit: int = Query(default=20, ge=1, le=100),
):
    """获取 Atom Feed（快捷方式）"""
    return await get_rss_feed(request, db, limit, format='atom')


@router.get("/category/{slug}/feed")
async def get_category_feed(
        slug: str,
        request: Request,
        db: AsyncSession = Depends(get_async_db),
        limit: int = Query(default=20, ge=1, le=100),
        format: str = Query(default='rss', pattern='^(rss|atom)$'),
):
    """获取分类 Feed"""

    # 查询分类
    stmt = select(Category).where(Category.slug == slug)
    result = await db.execute(stmt)
    category = result.scalar_one_or_none()

    if not category:
        return PlainTextResponse("Category not found", status_code=404)

    # 查询该分类下的文章
    stmt = (
        select(Article)
        .where(
            Article.category == category.id,
            Article.status == 'published'
        )
        .order_by(Article.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    articles = result.scalars().all()

    # 创建 Feed
    site_url = str(request.base_url).rstrip('/')
    generator = RSSFeedGenerator(
        title=f"{category.name} - {AppConfig.site_title or 'FastBlog'}",
        link=f"{site_url}/category/{slug}",
        description=category.description or f"{category.name} 分类下的文章",
        language='zh-CN',
        feed_url=f"{site_url}/category/{slug}/feed",
        copyright=f"© {datetime.now().year} {AppConfig.site_title}",
    )

    feed_items = await get_feed_items(db, articles, site_url, format)
    for item in feed_items:
        generator.add_item(item)

    if format == 'atom':
        content = generator.generate_atom()
        media_type = 'application/atom+xml'
    else:
        content = generator.generate_rss()
        media_type = 'application/rss+xml'

    return Response(content=content, media_type=media_type)


@router.get("/tag/{name}/feed")
async def get_tag_feed(
        name: str,
        request: Request,
        db: AsyncSession = Depends(get_async_db),
        limit: int = Query(default=20, ge=1, le=100),
        format: str = Query(default='rss', pattern='^(rss|atom)$'),
):
    """获取标签 Feed"""

    # 查询包含该标签的文章（tags_list 字段是逗号分隔的字符串）
    from sqlalchemy import or_
    stmt = (
        select(Article)
        .where(
            Article.status == 'published',
            Article.tags_list.isnot(None),
            Article.tags_list != '',
            or_(
                Article.tags_list.like(f"{name},%"),
                Article.tags_list.like(f"%,{name},%"),
                Article.tags_list.like(f"%,{name}"),
                Article.tags_list == name
            )
        )
        .order_by(Article.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    articles = result.scalars().all()

    # 创建 Feed
    site_url = str(request.base_url).rstrip('/')
    generator = RSSFeedGenerator(
        title=f"#{name} - {AppConfig.site_title or 'FastBlog'}",
        link=f"{site_url}/tag/{name}",
        description=f"标签 #{name} 下的文章",
        language='zh-CN',
        feed_url=f"{site_url}/tag/{name}/feed",
        copyright=f"© {datetime.now().year} {AppConfig.site_title}",
    )

    feed_items = await get_feed_items(db, articles, site_url, format)
    for item in feed_items:
        generator.add_item(item)

    if format == 'atom':
        content = generator.generate_atom()
        media_type = 'application/atom+xml'
    else:
        content = generator.generate_rss()
        media_type = 'application/rss+xml'

    return Response(content=content, media_type=media_type)


@router.get("/author/{user_id}/feed")
async def get_author_feed(
        user_id: int,
        request: Request,
        db: AsyncSession = Depends(get_async_db),
        limit: int = Query(default=20, ge=1, le=100),
        format: str = Query(default='rss', pattern='^(rss|atom)$'),
):
    """获取作者 Feed"""

    # 查询作者
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    author = result.scalar_one_or_none()

    if not author:
        return PlainTextResponse("Author not found", status_code=404)

    # 查询该作者的文章
    stmt = (
        select(Article)
        .where(
            Article.user == user_id,
            Article.status == 'published'
        )
        .order_by(Article.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    articles = result.scalars().all()

    # 创建 Feed
    site_url = str(request.base_url).rstrip('/')
    generator = RSSFeedGenerator(
        title=f"{author.username} 的文章 - {AppConfig.site_title or 'FastBlog'}",
        link=f"{site_url}/author/{user_id}",
        description=f"{author.username} 发布的文章",
        language='zh-CN',
        feed_url=f"{site_url}/author/{user_id}/feed",
        copyright=f"© {datetime.now().year} {AppConfig.site_title}",
    )

    feed_items = await get_feed_items(db, articles, site_url, format)
    for item in feed_items:
        generator.add_item(item)

    if format == 'atom':
        content = generator.generate_atom()
        media_type = 'application/atom+xml'
    else:
        content = generator.generate_rss()
        media_type = 'application/rss+xml'

    return Response(content=content, media_type=media_type)
