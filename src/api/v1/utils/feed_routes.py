"""
多端分发服务
提供标准化的 RSS/JSON Feed 及第三方平台发布接口
"""
from fastapi import APIRouter, Response, Depends
from typing import List

from shared.models.article import Article
from sqlalchemy import select, desc
from src.utils.database.main import get_async_session
from datetime import datetime

router = APIRouter(tags=["Multi-platform Distribution"])


@router.get("/feed/rss")
async def rss_feed():
    """P5-2: 生成标准 RSS 2.0 Feed"""
    async for db in get_async_session():
        query = select(Article).where(Article.status == 1).order_by(desc(Article.created_at)).limit(20)
        result = await db.execute(query)
        articles = result.scalars().all()

        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>FastBlog</title>
<link>https://example.com</link>
<description>Latest posts from FastBlog</description>
<lastBuildDate>{datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")}</lastBuildDate>
"""
        for article in articles:
            xml_content += f"""
<item>
<title>{article.title}</title>
<link>https://example.com/article/{article.slug}</link>
<description>{article.excerpt or ''}</description>
<pubDate>{article.created_at.strftime("%a, %d %b %Y %H:%M:%S GMT") if article.created_at else ''}</pubDate>
</item>
"""
        xml_content += "</channel></rss>"

        return Response(content=xml_content, media_type="application/xml")


@router.get("/feed/json")
async def json_feed():
    """P5-2: 生成 JSON Feed 1.1"""
    async for db in get_async_session():
        query = select(Article).where(Article.status == 1).order_by(desc(Article.created_at)).limit(20)
        result = await db.execute(query)
        articles = result.scalars().all()

        feed_data = {
            "version": "https://jsonfeed.org/version/1.1",
            "title": "FastBlog",
            "home_page_url": "https://example.com",
            "items": [
                {
                    "id": str(a.id),
                    "url": f"https://example.com/article/{a.slug}",
                    "title": a.title,
                    "content_html": a.excerpt,
                    "date_published": a.created_at.isoformat() if a.created_at else None
                } for a in articles
            ]
        }
        return feed_data
