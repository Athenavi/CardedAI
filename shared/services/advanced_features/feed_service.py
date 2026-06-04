"""
RSS/Atom Feed生成服务
提供标准的RSS 2.0和Atom 1.0格式输出
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from xml.dom.minidom import parseString
from xml.etree.ElementTree import Element, SubElement, tostring

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.article import Article
from shared.models.article_content import ArticleContent
from shared.models.category import Category
from shared.models.user import User


async def generate_rss_feed(
        db: AsyncSession,
        base_url: str = "http://localhost:8000",
        limit: int = 20,
        category_id: Optional[int] = None
) -> str:
    """
    生成RSS 2.0格式的Feed
    
    Args:
        db: 数据库会话
        base_url: 网站基础URL
        limit: 文章数量限制
        category_id: 分类ID（可选）
        
    Returns:
        RSS XML字符串
    """
    try:
        # 查询已发布的文章
        query = (
            select(Article)
            .where(Article.status == 1)  # 已发布
            .order_by(Article.created_at.desc())
            .limit(limit)
        )

        if category_id:
            query = query.where(Article.category == category_id)

        result = await db.execute(query)
        articles = result.scalars().all()

        # 构建RSS
        rss = Element('rss', version='2.0')
        channel = SubElement(rss, 'channel')

        # Channel信息
        title_elem = SubElement(channel, 'title')
        title_elem.text = "博客RSS订阅"

        link_elem = SubElement(channel, 'link')
        link_elem.text = base_url

        description_elem = SubElement(channel, 'description')
        description_elem.text = "最新文章订阅"

        language_elem = SubElement(channel, 'language')
        language_elem.text = "zh-CN"

        last_build_date = SubElement(channel, 'lastBuildDate')
        last_build_date.text = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')

        # 添加文章
        for article in articles:
            item = SubElement(channel, 'item')

            # 标题
            title = SubElement(item, 'title')
            title.text = article.title

            # 链接
            link = SubElement(item, 'link')
            link.text = f"{base_url}/article/{article.slug}"

            # 描述（摘要）
            description = SubElement(item, 'description')
            description.text = article.excerpt or ""

            # GUID
            guid = SubElement(item, 'guid')
            guid.text = f"{base_url}/article/{article.id}"
            guid.set('isPermaLink', 'false')

            # 发布时间
            pub_date = SubElement(item, 'pubDate')
            if article.created_at:
                pub_date.text = article.created_at.strftime('%a, %d %b %Y %H:%M:%S +0000')

            # 作者
            if article.user:
                author_query = select(User).where(User.id == article.user)
                author_result = await db.execute(author_query)
                author = author_result.scalar_one_or_none()
                if author:
                    author_elem = SubElement(item, 'author')
                    author_elem.text = author.email or author.username

            # 分类
            if article.category:
                category_query = select(Category).where(Category.id == article.category)
                category_result = await db.execute(category_query)
                category = category_result.scalar_one_or_none()
                if category:
                    category_elem = SubElement(item, 'category')
                    category_elem.text = category.name

        # 格式化XML
        rough_string = tostring(rss, encoding='unicode')
        reparsed = parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ", encoding='UTF-8')

        return pretty_xml.decode('utf-8')

    except Exception as e:
        print(f"生成RSS失败: {e}")
        import traceback
        traceback.print_exc()
        return ""


async def generate_atom_feed(
        db: AsyncSession,
        base_url: str = "http://localhost:8000",
        limit: int = 20,
        category_id: Optional[int] = None
) -> str:
    """
    生成Atom 1.0格式的Feed
    
    Args:
        db: 数据库会话
        base_url: 网站基础URL
        limit: 文章数量限制
        category_id: 分类ID（可选）
        
    Returns:
        Atom XML字符串
    """
    try:
        from xml.etree.ElementTree import Element, SubElement, tostring
        from xml.dom.minidom import parseString

        # 查询已发布的文章
        query = (
            select(Article)
            .where(Article.status == 1)
            .order_by(Article.created_at.desc())
            .limit(limit)
        )

        if category_id:
            query = query.where(Article.category == category_id)

        result = await db.execute(query)
        articles = result.scalars().all()

        # 构建Atom Feed
        atom_ns = "http://www.w3.org/2005/Atom"
        feed = Element('{%s}feed' % atom_ns)

        # Feed标题
        title = SubElement(feed, '{%s}title' % atom_ns)
        title.text = "博客Atom订阅"

        # Feed链接
        link = SubElement(feed, '{%s}link' % atom_ns)
        link.set('href', base_url)
        link.set('rel', 'alternate')

        # Feed ID
        id_elem = SubElement(feed, '{%s}id' % atom_ns)
        id_elem.text = base_url

        # 更新时间
        updated = SubElement(feed, '{%s}updated' % atom_ns)
        updated.text = datetime.now(timezone.utc).isoformat()

        # 添加文章条目
        for article in articles:
            entry = SubElement(feed, '{%s}entry' % atom_ns)

            # 标题
            entry_title = SubElement(entry, '{%s}title' % atom_ns)
            entry_title.text = article.title

            # 链接
            entry_link = SubElement(entry, '{%s}link' % atom_ns)
            entry_link.set('href', f"{base_url}/article/{article.slug}")
            entry_link.set('rel', 'alternate')

            # ID
            entry_id = SubElement(entry, '{%s}id' % atom_ns)
            entry_id.text = f"{base_url}/article/{article.id}"

            # 更新时间
            entry_updated = SubElement(entry, '{%s}updated' % atom_ns)
            if article.updated_at:
                entry_updated.text = article.updated_at.isoformat()
            else:
                entry_updated.text = datetime.now(timezone.utc).isoformat()

            # 发布时间
            entry_published = SubElement(entry, '{%s}published' % atom_ns)
            if article.created_at:
                entry_published.text = article.created_at.isoformat()

            # 摘要
            summary = SubElement(entry, '{%s}summary' % atom_ns)
            summary.text = article.excerpt or ""
            summary.set('type', 'text')

            # 内容
            content = SubElement(entry, '{%s}content' % atom_ns)
            content.set('type', 'html')

            # 获取文章内容
            content_query = select(ArticleContent).where(ArticleContent.aid == article.id)
            content_result = await db.execute(content_query)
            content_obj = content_result.scalar_one_or_none()
            content.text = content_obj.content if content_obj else ""

            # 作者
            if article.user:
                author_query = select(User).where(User.id == article.user)
                author_result = await db.execute(author_query)
                author = author_result.scalar_one_or_none()
                if author:
                    entry_author = SubElement(entry, '{%s}author' % atom_ns)
                    author_name = SubElement(entry_author, '{%s}name' % atom_ns)
                    author_name.text = author.username

                    if author.email:
                        author_email = SubElement(entry_author, '{%s}email' % atom_ns)
                        author_email.text = author.email

        # 格式化XML
        rough_string = tostring(feed, encoding='unicode')
        reparsed = parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ", encoding='UTF-8')

        return pretty_xml.decode('utf-8')

    except Exception as e:
        print(f"生成Atom失败: {e}")
        import traceback
        traceback.print_exc()
        return ""


async def get_feed_metadata(db: AsyncSession) -> Dict[str, Any]:
    """
    获取Feed元数据（用于SEO和发现）
    
    Args:
        db: 数据库会话
        
    Returns:
        Feed元数据字典
    """
    try:
        # 统计文章总数
        from sqlalchemy import func
        count_query = select(func.count(Article.id)).where(Article.status == 1)
        count_result = await db.execute(count_query)
        total_articles = count_result.scalar() or 0

        # 获取最新文章时间
        latest_query = (
            select(Article.created_at)
            .where(Article.status == 1)
            .order_by(Article.created_at.desc())
            .limit(1)
        )
        latest_result = await db.execute(latest_query)
        latest_article = latest_result.scalar_one_or_none()

        return {
            "total_articles": total_articles,
            "latest_update": latest_article.isoformat() if latest_article else None,
            "rss_url": "/api/v1/feed/rss",
            "atom_url": "/api/v1/feed/atom",
            "formats": ["rss", "atom"]
        }

    except Exception as e:
        print(f"获取Feed元数据失败: {e}")
        return {
            "total_articles": 0,
            "latest_update": None,
            "rss_url": "/api/v1/feed/rss",
            "atom_url": "/api/v1/feed/atom",
            "formats": ["rss", "atom"]
        }
