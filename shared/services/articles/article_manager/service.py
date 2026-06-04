"""
文章服务层 - 提供统一的 SQLAlchemy async 文章相关操作

该模块封装了所有文章相关的数据库操作，避免直接使用 Django ORM,
确保与 FastAPI 的异步架构保持一致。
"""


from datetime import datetime, timezone
from typing import Optional, List, Tuple

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.article import Article
from shared.models.article_content import ArticleContent
from src.unified_logger import default_logger as logger


async def get_article_by_id(db: AsyncSession, article_id: int) -> Optional[Article]:
    """
    通过 ID 获取文章

    Args:
        db: 异步数据库会话
        article_id: 文章 ID

    Returns:
        文章对象，如果不存在则返回 None
    """
    result = await db.execute(
        select(Article)
        .where(Article.id == article_id)
    )
    return result.scalar_one_or_none()


async def get_articles_by_user_id(
    db: AsyncSession,
    user_id: int,
    limit: int = 10,
    status: int = 1
) -> List[Article]:
    """
    获取用户的文章

    Args:
        db: 异步数据库会话
        user_id: 用户 ID
        limit: 数量限制
        status: 文章状态（默认 1=已发布）

    Returns:
        文章列表
    """
    result = await db.execute(
        select(Article)
        .where(Article.user == user_id, Article.status == status)
        .order_by(Article.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_article_count_by_user(
    db: AsyncSession,
    user_id: int,
    status: int = 1
) -> int:
    """
    获取用户文章数量

    Args:
        db: 异步数据库会话
        user_id: 用户 ID
        status: 文章状态（默认 1=已发布）

    Returns:
        文章总数
    """
    result = await db.execute(
        select(func.count())
        .select_from(Article)
        .where(Article.user == user_id, Article.status == status)
    )
    return result.scalar() or 0


async def get_article_with_content(
    db: AsyncSession,
    article_id: int
) -> Optional[Tuple[Article, Optional[ArticleContent]]]:
    """
    获取文章及其内容（使用 JOIN 优化查询）

    Args:
        db: 异步数据库会话
        article_id: 文章 ID

    Returns:
        (文章对象，文章内容对象) 或 None
    """
    # 使用 LEFT JOIN 一次性获取文章和内容
    result = await db.execute(
        select(Article, ArticleContent)
        .outerjoin(ArticleContent, Article.id == ArticleContent.article)
        .where(Article.id == article_id)
    )
    row = result.first()

    if not row:
        return None

    return row[0], row[1]


async def get_user_articles_with_pagination(
    db: AsyncSession,
    user_id: int,
    page: int = 1,
    per_page: int = 10,
    status: int = 1
) -> Tuple[List[Article], int]:
    """
    分页获取用户文章

    Args:
        db: 异步数据库会话
        user_id: 用户 ID
        page: 页码
        per_page: 每页数量
        status: 文章状态

    Returns:
        (文章列表，总数)
    """
    # 统计总数 - 使用简单的 COUNT 查询，避免子查询
    count_query = (
        select(func.count(Article.id))
        .where(Article.user == user_id, Article.status == status)
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页查询
    offset = (page - 1) * per_page
    query = (
        select(Article)
        .where(Article.user == user_id, Article.status == status)
        .order_by(Article.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )

    result = await db.execute(query)
    articles = list(result.scalars().all())

    return articles, total


async def create_article(
    db: AsyncSession,
    user_id: int,
    title: str,
    content: str,
    category_id: Optional[int] = None,
    excerpt: str = "",
    cover_image: Optional[str] = None,
    tags: Optional[str] = None,
    is_vip_only: bool = False,
    hidden: bool = False,
    **kwargs
) -> Article:
    """
    创建文章

    Args:
        db: 异步数据库会话
        user_id: 作者 ID
        title: 标题
        content: 内容
        category_id: 分类 ID
        excerpt: 摘要
        cover_image: 封面图
        tags: 标签（分号分隔）
        is_vip_only: 是否仅 VIP 可见
        hidden: 是否隐藏
        **kwargs: 其他字段

    Returns:
        创建的文章对象
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)  # 移除时区信息以匹配数据库字段

    # 创建文章
    article = Article(
        user=user_id,
        title=title,
        category=category_id,
        excerpt=excerpt,
        cover_image=cover_image,
        tags_list=tags,
        is_vip_only=is_vip_only,
        hidden=hidden,
        status=kwargs.get('status', 1),
        created_at=now,
        updated_at=now,
    )
    db.add(article)
    await db.flush()

    # 创建文章内容
    if content:
        content_obj = ArticleContent(
            article=article.id,
            content=content,
            created_at=now,
            updated_at=now
        )
        db.add(content_obj)

    await db.commit()
    await db.refresh(article)

    # 异步触发文章创建事件（不阻塞主流程）
    _trigger_article_event('article_published', {
        'id': article.id,
        'title': article.title,
        'slug': getattr(article, 'slug', ''),
        'content': content,
        'excerpt': article.excerpt,
        'tags': tags.split(';') if tags else [],
        'category_id': category_id,
        'user_id': user_id,
        'status': 'published',
        'created_at': article.created_at.isoformat() if article.created_at else None,
    })

    return article


async def update_article(
    db: AsyncSession,
    article_id: int,
    **kwargs
) -> Optional[Article]:
    """
    更新文章

    Args:
        db: 异步数据库会话
        article_id: 文章 ID
        **kwargs: 要更新的字段

    Returns:
        更新后的文章对象，如果不存在则返回 None
    """
    article = await get_article_by_id(db, article_id)
    if not article:
        return None

    # 允许更新的字段
    allowed_fields = {
        'title', 'excerpt', 'cover_image', 'tags_list',
        'is_vip_only', 'hidden', 'status', 'category'
    }

    update_data = {
        k: v for k, v in kwargs.items()
        if k in allowed_fields and v is not None
    }

    if update_data:
        update_data['updated_at'] = datetime.now(timezone.utc).replace(tzinfo=None)  # 移除时区信息以匹配数据库字段

        await db.execute(
            update(Article)
            .where(Article.id == article_id)
            .values(**update_data)
        )
        await db.commit()
        await db.refresh(article)

        # 异步触发文章更新事件
        _trigger_article_event('article_updated', {
            'id': article.id,
            'title': article.title,
            'updated_fields': list(update_data.keys()),
            'updated_at': article.updated_at.isoformat() if article.updated_at else None,
        })

    return article


async def update_article_content(
    db: AsyncSession,
    article_id: int,
    content: str
) -> bool:
    """
    更新文章内容（优化：减少查询次数）

    Args:
        db: 异步数据库会话
        article_id: 文章 ID
        content: 新内容

    Returns:
        是否成功
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)  # 移除时区信息以匹配数据库字段

    # 尝试更新现有内容
    result = await db.execute(
        update(ArticleContent)
        .where(ArticleContent.article == article_id)
        .values(content=content, updated_at=now)
    )

    # 如果没有更新任何行，说明内容不存在，需要创建
    if result.rowcount == 0:
        new_content = ArticleContent(
            article=article_id,
            content=content,
            created_at=now,
            updated_at=now
        )
        db.add(new_content)

    await db.commit()
    return True


async def delete_article(db: AsyncSession, article_id: int) -> bool:
    """
    删除文章（包括内容和修订历史）

    Args:
        db: 异步数据库会话
        article_id: 文章 ID

    Returns:
        是否成功
    """
    from shared.models.article_revision import ArticleRevision
    from shared.models.comment import Comment
    from shared.models.comment_vote import CommentVote
    from shared.models.comment_subscription import CommentSubscription

    article = await get_article_by_id(db, article_id)
    if not article:
        return False

    # 保存文章信息用于事件触发
    article_title = article.title

    # 删除评论投票（先于评论删除，避免孤立记录）
    comment_ids_result = await db.execute(
        select(Comment.id).where(Comment.article_id == article_id)
    )
    comment_ids = [row[0] for row in comment_ids_result.all()]
    if comment_ids:
        await db.execute(
            delete(CommentVote).where(CommentVote.comment_id.in_(comment_ids))
        )

    # 删除评论订阅
    await db.execute(
        delete(CommentSubscription).where(CommentSubscription.article_id == article_id)
    )

    # 删除评论
    await db.execute(
        delete(Comment).where(Comment.article_id == article_id)
    )

    # 删除修订历史
    await db.execute(
        delete(ArticleRevision).where(ArticleRevision.article_id == article_id)
    )

    # 删除文章内容 - 使用 delete 语句确保完全删除
    await db.execute(
        delete(ArticleContent).where(ArticleContent.article == article_id)
    )

    # 删除文章
    await db.delete(article)
    await db.commit()

    # 异步触发文章删除事件
    _trigger_article_event('article_deleted', {
        'id': article_id,
        'title': article_title,
        'deleted_at': datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),  # 移除时区信息以匹配数据库字段
    })

    return True


async def increment_article_views(db: AsyncSession, article_id: int) -> bool:
    """
    增加文章浏览量（使用 SQLAlchemy ORM 操作）

    Args:
        db: 异步数据库会话
        article_id: 文章 ID

    Returns:
        是否成功

    Note:
        此函数不会自动提交事务，调用者需要负责 commit。
        如果使用统一管理器的 get_db_session()，事务会在请求结束时自动提交。
    """
    await db.execute(
        update(Article)
        .where(Article.id == article_id)
        .values(views=Article.views + 1)
    )
    # 注意：不要在这里调用 await db.commit()
    # 让调用者或统一管理器来决定何时提交

    return True


async def search_articles(
    db: AsyncSession,
    keyword: str,
    category_id: Optional[int] = None,
    user_id: Optional[int] = None,
    page: int = 1,
    per_page: int = 10,
    hidden: bool = False,
    status: int = 1
) -> Tuple[List[Article], int]:
    """
    搜索文章

    Args:
        db: 异步数据库会话
        keyword: 搜索关键词
        category_id: 分类 ID（可选）
        user_id: 用户 ID（可选）
        page: 页码
        per_page: 每页数量
        hidden: 是否包含隐藏文章
        status: 文章状态

    Returns:
        (文章列表，总数)
    """
    # 构建查询
    query = select(Article).where(
        Article.hidden == hidden,
        Article.status == status
    )

    # 搜索条件
    if keyword:
        query = query.where(
            (Article.title.contains(keyword)) |
            (Article.excerpt.contains(keyword))
        )

    if category_id:
        query = query.where(Article.category == category_id)

    if user_id:
        query = query.where(Article.user == user_id)

    # 统计总数 - 使用简单的 COUNT 查询，避免子查询
    count_query = select(func.count(Article.id)).where(
        Article.hidden == hidden,
        Article.status == status
    )
    if keyword:
        count_query = count_query.where(
            (Article.title.contains(keyword)) |
            (Article.excerpt.contains(keyword))
        )
    if category_id:
        count_query = count_query.where(Article.category == category_id)
    if user_id:
        count_query = count_query.where(Article.user == user_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页
    offset = (page - 1) * per_page
    query = query.order_by(Article.created_at.desc()).offset(offset).limit(per_page)

    result = await db.execute(query)
    articles = list(result.scalars().all())

    return articles, total


# 导出所有公共函数
__all__ = [
    'get_article_by_id',
    'get_articles_by_user_id',
    'get_article_count_by_user',
    'get_article_with_content',
    'get_user_articles_with_pagination',
    'create_article',
    'update_article',
    'update_article_content',
    'delete_article',
    'increment_article_views',
    'search_articles',
]


def _trigger_article_event(event_name: str, data: dict):
    """
    触发文章相关事件（插件系统）

    Args:
        event_name: 事件名称
        data: 事件数据
    """
    try:
        import asyncio
        from shared.services.plugins.plugin_manager.init import trigger_plugin_event

        # 检查是否有运行的事件循环
        try:
            loop = asyncio.get_running_loop()
            # 如果有运行的事件循环，创建任务
            asyncio.create_task(trigger_plugin_event(event_name, data))
        except RuntimeError:
            # 没有运行的事件循环，记录日志但不抛出异常
            logger.debug(f"No running event loop, skipping {event_name} event trigger")
    except Exception as e:
        # 事件触发失败不应该影响主流程
        logger.debug(f"Failed to trigger {event_name} event: {e}")
