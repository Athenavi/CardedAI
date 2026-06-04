"""
插件公开API服务
提供插件可以安全调用的公开接口，避免插件直接操作数据库
"""
import re
from typing import Dict, List, Any, Optional

from sqlalchemy import select

from shared.models.article import Article
from src.extensions import get_async_session_context


class PluginPublicAPI:
    """
    插件公开API

    所有插件应该通过此类提供的接口来访问系统数据，
    而不是直接操作数据库。这样可以保证：
    1. 数据一致性
    2. 权限控制
    3. 缓存机制
    4. 业务逻辑完整性
    """

    @staticmethod
    async def get_published_articles(
            limit: int = 100,
            offset: int = 0,
            category_id: Optional[int] = None,
            include_hidden: bool = False
    ) -> List[Dict[str, Any]]:
        """
        获取已发布文章列表（异步版本）

        Args:
            limit: 返回数量限制
            offset: 偏移量
            category_id: 分类ID筛选
            include_hidden: 是否包含隐藏文章

        Returns:
            文章列表，每个文章包含:
            - id: 文章ID
            - title: 标题
            - slug: URL别名
            - excerpt: 摘要
            - cover_image: 封面图
            - created_at: 创建时间
            - updated_at: 更新时间
            - tags: 标签列表
            - category: 分类名称
            - views: 浏览量
        """
        try:
            # 构建查询条件
            filters = [
                Article.status == 1,  # 已发布状态
            ]

            if not include_hidden:
                filters.append(Article.hidden == False)

            if category_id:
                filters.append(Article.category == category_id)

            # 执行异步查询
            async with get_async_session_context() as db_session:
                stmt = select(Article).where(*filters).order_by(Article.created_at.desc())

                # 应用分页
                if limit > 0:
                    stmt = stmt.offset(offset).limit(limit)

                result = await db_session.execute(stmt)
                articles_data = result.scalars().all()

                articles = []
                for article in articles_data:
                    # 解析标签
                    tags_list = []
                    if article.tags_list:
                        try:
                            tags_list = [tag.strip() for tag in re.split(r'[,;]', article.tags_list) if tag.strip()]
                        except:
                            tags_list = []

                    articles.append({
                        'id': article.id,
                        'title': article.title,
                        'slug': article.slug,
                        'excerpt': article.excerpt or '',
                        'cover_image': article.cover_image or '',
                        'created_at': article.created_at,
                        'updated_at': article.updated_at or article.created_at,
                        'tags': tags_list,
                        'category': article.category or '',
                        'views': article.views or 0,
                    })

                return articles

            return []

        except Exception as e:
            print(f"[PluginPublicAPI] Failed to get published articles: {e}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    async def get_article_by_slug(slug: str) -> Optional[Dict[str, Any]]:
        """
        根据slug获取文章详情（异步版本）

        Args:
            slug: 文章URL别名

        Returns:
            文章详情字典，如果不存在返回None
        """
        try:
            # 执行异步查询
            async with get_async_session_context() as db_session:
                stmt = select(Article).where(
                    Article.slug == slug,
                    Article.status == 1,
                    Article.hidden == False
                )
                result = await db_session.execute(stmt)
                article = result.scalar_one_or_none()

                if article:
                    tags_list = []
                    if article.tags_list:
                        try:
                            tags_list = [tag.strip() for tag in re.split(r'[,;]', article.tags_list) if tag.strip()]
                        except:
                            tags_list = []

                    return {
                        'id': article.id,
                        'title': article.title,
                        'slug': article.slug,
                        'excerpt': article.excerpt or '',
                        'cover_image': article.cover_image or '',
                        'created_at': article.created_at,
                        'updated_at': article.updated_at or article.created_at,
                        'tags': tags_list,
                        'category': article.category or '',
                        'views': article.views or 0,
                    }
                else:
                    return None

        except Exception as e:
            print(f"[PluginPublicAPI] Failed to get article by slug: {e}")
            return None

    @staticmethod
    async def get_all_pages(include_draft: bool = False) -> List[Dict[str, Any]]:
        """
        获取所有页面列表（异步版本）

        Args:
            include_draft: 是否包含草稿

        Returns:
            页面列表
        """
        # Pages feature is not yet implemented in the current system
        # When pages table is available, implement like this:
        # from shared.models.page import Page
        # from sqlalchemy import select
        #
        # stmt = select(Page)
        # if not include_draft:
        #     stmt = stmt.where(Page.status == 'published')
        # result = await db.execute(stmt)
        # pages = result.scalars().all()
        #
        # return [{
        #     'id': page.id,
        #     'title': page.title,
        #     'slug': page.slug,
        #     'content': page.content,
        #     'status': page.status,
        # } for page in pages]

        print("[PluginPublicAPI] Pages feature not yet implemented, returning empty list")
        return []

    @staticmethod
    async def get_site_settings() -> Dict[str, Any]:
        """
        获取网站设置（异步版本）

        Returns:
            网站设置字典
        """
        try:
            from shared.models import SiteSettings

            # 执行异步查询
            async with get_async_session_context() as db_session:
                stmt = select(SiteSettings).limit(1)
                result = await db_session.execute(stmt)
                site_settings = result.scalar_one_or_none()

                if site_settings:
                    return {
                        'site_name': site_settings.site_name or 'FastBlog',
                        'site_description': site_settings.site_description or '',
                        'site_url': site_settings.site_url or '',
                        'canonical_url_base': site_settings.site_url or '',
                    }
                else:
                    return {
                        'site_name': 'FastBlog',
                        'site_description': '',
                        'site_url': '',
                        'canonical_url_base': '',
                    }

        except Exception as e:
            print(f"[PluginPublicAPI] Failed to get site settings: {e}")
            return {
                'site_name': 'FastBlog',
                'site_description': '',
                'site_url': '',
                'canonical_url_base': '',
            }


# 全局实例
plugin_api = PluginPublicAPI()
