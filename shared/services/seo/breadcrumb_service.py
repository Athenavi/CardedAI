"""
面包屑导航服务 - 生成SEO友好的面包屑导航
"""
from typing import List, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.article import Article
from shared.models.category import Category
from shared.models.pages import Pages


class BreadcrumbService:
    """面包屑导航服务"""
    
    @staticmethod
    async def get_article_breadcrumbs(
        db: AsyncSession,
        article_id: int
    ) -> List[Dict[str, str]]:
        """
        获取文章详情页的面包屑导航
        
        Args:
            db: 数据库会话
            article_id: 文章ID
            
        Returns:
            面包屑列表，每个元素包含 name 和 url
        """
        breadcrumbs = [
            {"name": "首页", "url": "/"}
        ]
        
        # 获取文章信息
        article_query = select(Article).where(Article.id == article_id)
        article_result = await db.execute(article_query)
        article = article_result.scalar_one_or_none()
        
        if not article:
            return breadcrumbs
        
        # 如果有分类，添加分类面包屑
        if article.category:
            category_query = select(Category).where(Category.id == article.category)
            category_result = await db.execute(category_query)
            category = category_result.scalar_one_or_none()
            
            if category:
                breadcrumbs.append({
                    "name": category.name,
                    "url": f"/category/{category.slug}" if category.slug else f"/category/{category.id}"
                })
        
        # 添加当前文章
        breadcrumbs.append({
            "name": article.title,
            "url": f"/article/{article.slug}" if article.slug else f"/article/{article.id}"
        })
        
        return breadcrumbs
    
    @staticmethod
    async def get_category_breadcrumbs(
        db: AsyncSession,
        category_id: int
    ) -> List[Dict[str, str]]:
        """
        获取分类页的面包屑导航
        
        Args:
            db: 数据库会话
            category_id: 分类ID
            
        Returns:
            面包屑列表
        """
        breadcrumbs = [
            {"name": "首页", "url": "/"}
        ]
        
        # 获取分类信息
        category_query = select(Category).where(Category.id == category_id)
        category_result = await db.execute(category_query)
        category = category_result.scalar_one_or_none()
        
        if not category:
            return breadcrumbs
        
        # 如果有父分类，递归添加父分类
        if category.parent_id:
            parent_breadcrumbs = await BreadcrumbService._get_category_parents(db, category.parent_id)
            breadcrumbs.extend(parent_breadcrumbs)
        
        # 添加当前分类
        breadcrumbs.append({
            "name": category.name,
            "url": f"/category/{category.slug}" if category.slug else f"/category/{category.id}"
        })
        
        return breadcrumbs
    
    @staticmethod
    async def _get_category_parents(
        db: AsyncSession,
        category_id: int
    ) -> List[Dict[str, str]]:
        """
        递归获取分类的父级分类
        
        Args:
            db: 数据库会话
            category_id: 分类ID
            
        Returns:
            父级分类面包屑列表
        """
        breadcrumbs = []
        
        category_query = select(Category).where(Category.id == category_id)
        category_result = await db.execute(category_query)
        category = category_result.scalar_one_or_none()
        
        if not category:
            return breadcrumbs
        
        # 如果还有父分类，继续递归
        if category.parent_id:
            parent_breadcrumbs = await BreadcrumbService._get_category_parents(db, category.parent_id)
            breadcrumbs.extend(parent_breadcrumbs)
        
        # 添加当前分类
        breadcrumbs.append({
            "name": category.name,
            "url": f"/category/{category.slug}" if category.slug else f"/category/{category.id}"
        })
        
        return breadcrumbs
    
    @staticmethod
    async def get_page_breadcrumbs(
        db: AsyncSession,
        page_id: int
    ) -> List[Dict[str, str]]:
        """
        获取页面详情页的面包屑导航
        
        Args:
            db: 数据库会话
            page_id: 页面ID
            
        Returns:
            面包屑列表
        """
        breadcrumbs = [
            {"name": "首页", "url": "/"}
        ]
        
        # 获取页面信息
        page_query = select(Pages).where(Pages.id == page_id)
        page_result = await db.execute(page_query)
        page = page_result.scalar_one_or_none()
        
        if not page:
            return breadcrumbs
        
        # 如果有父页面，递归添加父页面
        if page.parent_id:
            parent_breadcrumbs = await BreadcrumbService._get_page_parents(db, page.parent_id)
            breadcrumbs.extend(parent_breadcrumbs)
        
        # 添加当前页面
        breadcrumbs.append({
            "name": page.title,
            "url": f"/page/{page.slug}" if page.slug else f"/page/{page.id}"
        })
        
        return breadcrumbs
    
    @staticmethod
    async def _get_page_parents(
        db: AsyncSession,
        page_id: int
    ) -> List[Dict[str, str]]:
        """
        递归获取页面的父级页面
        
        Args:
            db: 数据库会话
            page_id: 页面ID
            
        Returns:
            父级页面面包屑列表
        """
        breadcrumbs = []
        
        page_query = select(Pages).where(Pages.id == page_id)
        page_result = await db.execute(page_query)
        page = page_result.scalar_one_or_none()
        
        if not page:
            return breadcrumbs
        
        # 如果还有父页面，继续递归
        if page.parent_id:
            parent_breadcrumbs = await BreadcrumbService._get_page_parents(db, page.parent_id)
            breadcrumbs.extend(parent_breadcrumbs)
        
        # 添加当前页面
        breadcrumbs.append({
            "name": page.title,
            "url": f"/page/{page.slug}" if page.slug else f"/page/{page.id}"
        })
        
        return breadcrumbs
    
    @staticmethod
    def get_search_breadcrumbs(search_query: str) -> List[Dict[str, str]]:
        """
        获取搜索结果页的面包屑导航
        
        Args:
            search_query: 搜索关键词
            
        Returns:
            面包屑列表
        """
        return [
            {"name": "首页", "url": "/"},
            {"name": f"搜索: {search_query}", "url": f"/search?q={search_query}"}
        ]
    
    @staticmethod
    def get_tag_breadcrumbs(tag_name: str) -> List[Dict[str, str]]:
        """
        获取标签页的面包屑导航
        
        Args:
            tag_name: 标签名称
            
        Returns:
            面包屑列表
        """
        return [
            {"name": "首页", "url": "/"},
            {"name": f"标签: {tag_name}", "url": f"/tag/{tag_name}"}
        ]
    
    @staticmethod
    def get_author_breadcrumbs(author_name: str) -> List[Dict[str, str]]:
        """
        获取作者页的面包屑导航
        
        Args:
            author_name: 作者用户名
            
        Returns:
            面包屑列表
        """
        return [
            {"name": "首页", "url": "/"},
            {"name": f"作者: {author_name}", "url": f"/author/{author_name}"}
        ]
    
    @staticmethod
    def generate_json_ld(breadcrumbs: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        生成JSON-LD结构化数据（用于SEO）
        
        Args:
            breadcrumbs: 面包屑列表
            
        Returns:
            JSON-LD结构化数据
        """
        items = []
        for index, crumb in enumerate(breadcrumbs, 1):
            items.append({
                "@type": "ListItem",
                "position": index,
                "name": crumb["name"],
                "item": crumb["url"]
            })
        
        return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": items
        }


# 全局实例
breadcrumb_service = BreadcrumbService()
