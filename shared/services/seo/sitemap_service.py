"""
站点地图(Sitemap)生成服务
自动生成符合SEO标准的sitemap.xml文件
"""

from datetime import datetime
from typing import Optional, List
from xml.dom.minidom import parseString
from xml.etree.ElementTree import Element, SubElement, tostring

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.article import Article
from shared.models.category import Category


async def generate_sitemap_xml(
        db: AsyncSession,
        base_url: str = "http://localhost:8000",
        include_articles: bool = True,
        include_categories: bool = True,
        articles_limit: Optional[int] = None
) -> str:
    """
    生成站点地图XML
    
    Args:
        db: 数据库会话
        base_url: 网站基础URL
        include_articles: 是否包含文章页面
        include_categories: 是否包含分类页面
        articles_limit: 文章数量限制(None表示全部)
        
    Returns:
        sitemap XML字符串
    """
    try:
        # 创建sitemap根元素
        urlset = Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')

        # 1. 添加首页
        _add_url(urlset, base_url, priority='1.0', changefreq='daily')

        # 2. 添加分类页面
        if include_categories:
            categories = await _get_categories(db)
            for category in categories:
                category_url = f"{base_url}/category/{category.slug}"
                _add_url(
                    urlset,
                    category_url,
                    lastmod=category.updated_at,
                    priority='0.8',
                    changefreq='weekly'
                )

        # 3. 添加文章页面
        if include_articles:
            articles = await _get_articles(db, limit=articles_limit)
            for article in articles:
                article_url = f"{base_url}/p/{article.slug}"
                _add_url(
                    urlset,
                    article_url,
                    lastmod=article.updated_at or article.created_at,
                    priority='0.7',
                    changefreq='monthly'
                )

        # 格式化XML
        rough_string = tostring(urlset, encoding='unicode')
        reparsed = parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ", encoding='UTF-8')

        return pretty_xml.decode('utf-8')

    except Exception as e:
        print(f"生成sitemap失败: {e}")
        import traceback
        traceback.print_exc()
        return ""


async def generate_robots_txt(
        base_url: str = "http://localhost:8000",
        sitemap_url: Optional[str] = None
) -> str:
    """
    生成robots.txt文件内容
    
    Args:
        base_url: 网站基础URL
        sitemap_url: sitemap.xml的完整URL
        
    Returns:
        robots.txt文本内容
    """
    if not sitemap_url:
        sitemap_url = f"{base_url}/sitemap.xml"

    robots_content = f"""# robots.txt for Fast Blog
# Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

User-agent: *
Allow: /
Allow: /p/
Allow: /category/
Allow: /tag/
Allow: /search

# 禁止访问管理后台
Disallow: /admin/
Disallow: /api/v1/admin/

# 禁止访问API端点(可选)
Disallow: /api/v1/auth/
Disallow: /api/v1/user/

# Sitemap位置
Sitemap: {sitemap_url}
"""
    return robots_content


async def _get_categories(db: AsyncSession) -> List[Category]:
    """获取所有可见的分类"""
    query = (
        select(Category)
        .where(Category.is_visible == True)
        .order_by(Category.sort_order.asc())
    )
    result = await db.execute(query)
    return result.scalars().all()


async def _get_articles(db: AsyncSession, limit: Optional[int] = None) -> List[Article]:
    """获取已发布的文章"""
    query = (
        select(Article)
        .where(Article.status == 1)  # status=1表示已发布
        .where(Article.hidden == False)  # 未隐藏的文章
        .order_by(Article.created_at.desc())
    )

    if limit:
        query = query.limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


def _add_url(
        urlset: Element,
        loc: str,
        lastmod: Optional[datetime] = None,
        changefreq: str = 'monthly',
        priority: str = '0.5'
):
    """
    向sitemap添加URL条目
    
    Args:
        urlset: sitemap根元素
        loc: URL地址
        lastmod: 最后修改时间
        changefreq: 更新频率(always/hourly/daily/weekly/monthly/yearly/never)
        priority: 优先级(0.0-1.0)
    """
    url_elem = SubElement(urlset, 'url')

    # URL地址(必需)
    loc_elem = SubElement(url_elem, 'loc')
    loc_elem.text = loc

    # 最后修改时间(可选)
    if lastmod:
        lastmod_elem = SubElement(url_elem, 'lastmod')
        if isinstance(lastmod, datetime):
            lastmod_elem.text = lastmod.strftime('%Y-%m-%dT%H:%M:%S+00:00')
        else:
            lastmod_elem.text = str(lastmod)

    # 更新频率(可选)
    changefreq_elem = SubElement(url_elem, 'changefreq')
    changefreq_elem.text = changefreq

    # 优先级(可选)
    priority_elem = SubElement(url_elem, 'priority')
    priority_elem.text = priority
