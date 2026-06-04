"""
SEO优化API端点
"""

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response

from shared.services.seo.seo_service import seo_service
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required

router = APIRouter(tags=["seo"])


# ==================== SEO分析 ====================

@router.post("/analyze")
async def analyze_seo(
        request: Request,
        current_user=Depends(jwt_required)
):
    """
    分析文章SEO质量
    
    请求体:
    - title: 文章标题
    - slug: URL Slug
    - excerpt: 文章摘要
    - content: 文章内容
    - cover_image: 封面图片URL
    - tags: 标签列表
    
    返回:
    - score: SEO评分 (0-100)
    - grade: 等级 (A/B/C/D/F)
    - checks: 检查项列表
    - suggestions: 改进建议
    """
    try:
        body = await request.json()

        # 提取文章数据
        article_data = {
            'title': body.get('title', ''),
            'slug': body.get('slug', ''),
            'excerpt': body.get('excerpt', ''),
            'content': body.get('content', ''),
            'cover_image': body.get('cover_image', ''),
            'tags': body.get('tags', [])
        }

        # 执行SEO分析
        result = seo_service.analyze_article_seo(article_data)

        return ApiResponse(
            success=True,
            data=result
        )
    except Exception as e:
        import traceback
        print(f"Error in analyze_seo: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


# ==================== 站点地图 ====================

@router.get("/sitemap.xml")
async def get_sitemap():
    """获取XML站点地图(公开访问)"""
    try:
        from shared.services.seo.seo_service import SEOService
        from shared.models.article import Article
        from shared.models.category import Category
        from sqlalchemy import select
        from src.extensions import get_async_db_session as get_async_db
        
        db = next(get_async_db())
        
        # 从数据库获取文章、分类、页面数据
        stmt = select(Article).where(Article.status == 'published')
        result = await db.execute(stmt)
        articles = result.scalars().all()
        
        article_list = [
            {
                'id': a.id,
                'slug': a.slug,
                'title': a.title,
                'excerpt': a.excerpt,
                'cover_image': a.cover_image,
                'created_at': a.created_at.isoformat() if a.created_at else None,
                'updated_at': a.updated_at.isoformat() if a.updated_at else None,
                'is_featured': a.is_featured
            }
            for a in articles
        ]
        
        stmt = select(Category)
        result = await db.execute(stmt)
        categories = result.scalars().all()
        
        category_list = [
            {'id': c.id, 'slug': c.slug, 'name': c.name}
            for c in categories
        ]

        result = await db.execute(stmt)
        pages = result.scalars().all()
        
        page_list = [
            {'id': p.id, 'slug': p.slug, 'title': p.title}
            for p in pages
        ]

        seo_service = SEOService()
        sitemap_xml = seo_service.generate_sitemap(article_list, category_list, page_list)

        return Response(
            content=sitemap_xml,
            media_type="application/xml"
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/sitemap/generate")
async def generate_sitemap(
        current_user=Depends(jwt_required)
):
    """手动生成站点地图"""
    try:
        from shared.services.seo.seo_service import SEOService
        from shared.models.article import Article
        from shared.models.category import Category
        from sqlalchemy import select
        from src.extensions import get_async_db_session as get_async_db
        
        db = next(get_async_db())
        
        # 获取所有已发布的文章
        stmt = select(Article).where(Article.status == 'published')
        result = await db.execute(stmt)
        articles = result.scalars().all()
        
        article_list = [
            {
                'id': a.id,
                'slug': a.slug,
                'title': a.title,
                'excerpt': a.excerpt,
                'cover_image': a.cover_image,
                'created_at': a.created_at.isoformat() if a.created_at else None,
                'updated_at': a.updated_at.isoformat() if a.updated_at else None,
                'is_featured': a.is_featured
            }
            for a in articles
        ]
        
        # 获取所有分类
        stmt = select(Category)
        result = await db.execute(stmt)
        categories = result.scalars().all()
        
        category_list = [
            {'id': c.id, 'slug': c.slug, 'name': c.name}
            for c in categories
        ]
        
        # 生成站点地图
        seo_service = SEOService(base_url="https://example.com")
        sitemap_xml = seo_service.generate_sitemap(
            articles=article_list,
            categories=category_list
        )
        
        # 保存到文件
        import os
        sitemap_path = os.path.join('static', 'sitemap.xml')
        os.makedirs(os.path.dirname(sitemap_path), exist_ok=True)
        with open(sitemap_path, 'w', encoding='utf-8') as f:
            f.write(sitemap_xml)
        
        return ApiResponse(success=True, data={"message": "站点地图已生成", "path": sitemap_path})
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# ==================== 结构化数据 ====================

@router.get("/schema/article/{article_id}")
async def get_article_schema(
        article_id: int,
        current_user=Depends(jwt_required)
):
    """获取文章结构化数据"""
    try:
        from shared.services.seo.seo_service import SEOService
        from shared.models.article import Article
        from sqlalchemy import select
        from src.extensions import get_async_db_session as get_async_db
        
        db = next(get_async_db())
        
        # 从数据库获取文章
        stmt = select(Article).where(Article.id == article_id)
        result = await db.execute(stmt)
        article = result.scalar_one_or_none()
        
        if not article:
            return ApiResponse(success=False, error="文章不存在")
        
        article_data = {
            'title': article.title,
            'excerpt': article.excerpt,
            'cover_image': article.cover_image,
            'created_at': article.created_at.isoformat() if article.created_at else None,
            'updated_at': article.updated_at.isoformat() if article.updated_at else None,
            'author_name': article.author.nickname if article.author else '',
            'slug': article.slug,
            'id': article.id
        }

        seo_service = SEOService(base_url="https://example.com")
        schema = seo_service.generate_article_schema(article_data)

        return ApiResponse(
            success=True,
            data={"schema": schema}
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/schema/breadcrumb")
async def get_breadcrumb_schema(
        request: Request,
        current_user=Depends(jwt_required)
):
    """获取面包屑结构化数据"""
    try:
        body = await request.json()
        breadcrumbs = body.get('breadcrumbs', [])

        schema = seo_service.generate_breadcrumb_schema(breadcrumbs)

        return ApiResponse(
            success=True,
            data={"schema": schema}
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# ==================== 面包屑导航 ====================

@router.get("/breadcrumbs/article/{article_id}")
async def get_article_breadcrumbs(
        article_id: int,
        current_user=Depends(jwt_required)
):
    """获取文章面包屑"""
    try:
        from shared.services.seo.seo_service import SEOService
        from shared.models.article import Article
        from shared.models.category import Category
        from sqlalchemy import select
        from src.extensions import get_async_db_session as get_async_db
        
        db = next(get_async_db())
        
        # 从数据库获取文章和分类
        stmt = select(Article).where(Article.id == article_id)
        result = await db.execute(stmt)
        article = result.scalar_one_or_none()
        
        if not article:
            return ApiResponse(success=False, error="文章不存在")
        
        category = None
        if article.category_id:
            stmt = select(Category).where(Category.id == article.category_id)
            result = await db.execute(stmt)
            category = result.scalar_one_or_none()
        
        article_data = {
            'title': article.title,
            'slug': article.slug,
            'id': article.id
        }
        
        category_data = {
            'name': category.name,
            'slug': category.slug,
            'id': category.id
        } if category else {}

        seo_service = SEOService(base_url="https://example.com")
        breadcrumbs = seo_service.generate_breadcrumbs(article=article_data, category=category_data)

        return ApiResponse(
            success=True,
            data={"breadcrumbs": breadcrumbs}
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/breadcrumbs/category/{category_id}")
async def get_category_breadcrumbs(
        category_id: int,
        current_user=Depends(jwt_required)
):
    """获取分类面包屑"""
    try:
        from shared.services.seo.seo_service import SEOService
        from shared.models.category import Category
        from sqlalchemy import select
        from src.extensions import get_async_db_session as get_async_db
        
        db = next(get_async_db())
        
        # 从数据库获取分类
        stmt = select(Category).where(Category.id == category_id)
        result = await db.execute(stmt)
        category = result.scalar_one_or_none()
        
        if not category:
            return ApiResponse(success=False, error="分类不存在")
        
        category_data = {
            'name': category.name,
            'slug': category.slug,
            'id': category.id
        }

        seo_service = SEOService(base_url="https://example.com")
        breadcrumbs = seo_service.generate_breadcrumbs(category=category_data)

        return ApiResponse(
            success=True,
            data={"breadcrumbs": breadcrumbs}
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# ==================== Canonical URL ====================

@router.get("/canonical")
async def get_canonical_url(
        path: str = Query(..., description="路径"),
        page: int = Query(None, description="页码"),
        current_user=Depends(jwt_required)
):
    """获取规范URL"""
    try:
        canonical_url = seo_service.get_canonical_url(path, page=page)
        canonical_tag = seo_service.generate_canonical_tag(path, page=page)

        return ApiResponse(
            success=True,
            data={
                "canonical_url": canonical_url,
                "canonical_tag": canonical_tag
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/canonical/normalize")
async def normalize_url(
        request: Request,
        current_user=Depends(jwt_required)
):
    """
    URL规范化 - 统一URL格式
    
    请求体:
    - url: 需要规范化的URL
    
    返回:
    - normalized_url: 规范化后的URL
    """
    try:
        body = await request.json()
        url = body.get('url', '')

        if not url:
            return ApiResponse(success=False, error="URL不能为空")

        normalized = seo_service.normalize_url(url)

        return ApiResponse(
            success=True,
            data={
                "original_url": url,
                "normalized_url": normalized
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/canonical/detect-duplicates")
async def detect_duplicate_content(
        request: Request,
        current_user=Depends(jwt_required)
):
    """
    检测重复内容
    
    请求体:
    - urls: URL列表
    - content_hash: 内容哈希值（可选）
    
    返回:
    - is_duplicate: 是否重复
    - canonical_url: 推荐的规范URL
    - duplicates: 重复的URL列表
    """
    try:
        body = await request.json()
        urls = body.get('urls', [])
        content_hash = body.get('content_hash')

        if not urls:
            return ApiResponse(success=False, error="URL列表不能为空")

        result = seo_service.detect_duplicate_content(urls, content_hash)

        return ApiResponse(
            success=True,
            data=result
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/canonical/pagination-tags")
async def get_pagination_tags(
        path: str = Query(..., description="基础路径"),
        current_page: int = Query(..., description="当前页码", ge=1),
        total_pages: int = Query(..., description="总页数", ge=1),
        current_user=Depends(jwt_required)
):
    """
    生成分页相关标签 (rel=prev/next)
    
    返回:
    - tags: HTML link标签列表
    """
    try:
        tags = seo_service.generate_pagination_tags(path, current_page, total_pages)

        return ApiResponse(
            success=True,
            data={
                "tags": tags,
                "current_page": current_page,
                "total_pages": total_pages
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/canonical/select-primary")
async def select_primary_url(
        request: Request,
        current_user=Depends(jwt_required)
):
    """
    主URL选择策略
    
    请求体:
    - urls: URL列表
    - strategy: 选择策略 ('shortest', 'first', 'https_preferred')
    
    返回:
    - primary_url: 选定的主URL
    """
    try:
        body = await request.json()
        urls = body.get('urls', [])
        strategy = body.get('strategy', 'shortest')

        if not urls:
            return ApiResponse(success=False, error="URL列表不能为空")

        primary_url = seo_service.select_primary_url(urls, strategy)

        return ApiResponse(
            success=True,
            data={
                "primary_url": primary_url,
                "strategy": strategy,
                "total_urls": len(urls)
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))
