"""
内部链接建议API
分析文章内容,推荐相关内部链接
"""
from typing import Dict, Any

from fastapi import APIRouter, Depends, Request, Body
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.article import Article
from shared.models.article_content import ArticleContent
from shared.models.user import User
from shared.services.seo.internal_link_service import internal_link_service
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import admin_required as admin_required_api
from src.extensions import get_async_db_session as get_async_db

router = APIRouter()


@router.post("/suggest",
             summary="获取内部链接建议",
             description="基于文章内容分析,推荐相关的内部链接(仅管理员)",
             response_description="返回建议列表")
async def get_internal_link_suggestions_api(
        request: Request,
        data: Dict[str, Any] = Body(...),
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(admin_required_api)
):
    """
    获取内部链接建议API
    
    Request Body:
    {
        "article_id": 123
    }
    """
    try:
        article_id = data.get('article_id')
        
        if not article_id:
            return ApiResponse(success=False, error='缺少文章ID')
        
        # 查询当前文章
        article_query = select(Article).where(Article.id == article_id)
        article_result = await db.execute(article_query)
        article = article_result.scalar_one_or_none()
        
        if not article:
            return ApiResponse(success=False, error='文章不存在')
        
        # 获取文章内容
        content_query = select(ArticleContent).where(ArticleContent.article == article_id)
        content_result = await db.execute(content_query)
        article_content = content_result.scalar_one_or_none()
        
        if not article_content:
            return ApiResponse(success=False, error='文章内容不存在')
        
        # 获取所有已发布文章(简化版:实际应分页)
        all_articles_query = select(Article).where(Article.status == 1)
        all_articles_result = await db.execute(all_articles_query)
        all_articles = all_articles_result.scalars().all()
        
        # 构建文章数据
        articles_data = [
            {
                'id': a.id,
                'title': a.title,
                'slug': a.slug,
                'content': '',  # 简化版:不加载所有内容
            }
            for a in all_articles
        ]
        
        # 为当前文章添加内容
        current_article_data = {
            'id': article.id,
            'title': article.title,
            'slug': article.slug,
            'content': article_content.content,
        }
        
        # 获取建议
        suggestions = internal_link_service.suggest_internal_links(
            current_article_data,
            articles_data
        )
        
        return ApiResponse(
            success=True,
            data=suggestions
        )
    except Exception as e:
        import traceback
        print(f"Error in get_internal_link_suggestions_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/orphan-articles",
            summary="检测孤立文章",
            description="查找没有被其他文章链接的文章(仅管理员)",
            response_description="返回孤立文章列表")
async def detect_orphan_articles_api(
        request: Request,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(admin_required_api)
):
    """
    检测孤立文章API
    """
    try:
        # 获取所有已发布文章
        articles_query = select(Article).where(Article.status == 1)
        articles_result = await db.execute(articles_query)
        all_articles = articles_result.scalars().all()
        
        articles_data = [
            {
                'id': a.id,
                'title': a.title,
                'slug': a.slug,
            }
            for a in all_articles
        ]
        
        # 简化版:假设没有链接记录
        orphan_articles = internal_link_service.detect_orphan_articles(
            articles_data,
            []  # 实际应从数据库查询链接记录
        )
        
        return ApiResponse(
            success=True,
            data={
                'orphan_count': len(orphan_articles),
                'orphan_articles': orphan_articles[:20],  # 返回前20个
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in detect_orphan_articles_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/analysis",
            summary="内链分析报告",
            description="生成内部链接分布分析报告(仅管理员)",
            response_description="返回分析结果")
async def internal_link_analysis_api(
        request: Request,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(admin_required_api)
):
    """
    内链分析报告API
    """
    try:
        # 获取所有已发布文章
        articles_query = select(Article).where(Article.status == 1)
        articles_result = await db.execute(articles_query)
        all_articles = articles_result.scalars().all()
        
        articles_data = [
            {
                'id': a.id,
                'title': a.title,
                'slug': a.slug,
            }
            for a in all_articles
        ]
        
        # 简化版:假设没有链接记录
        analysis = internal_link_service.analyze_link_distribution(
            articles_data,
            []  # 实际应从数据库查询链接记录
        )
        
        return ApiResponse(
            success=True,
            data=analysis
        )
    except Exception as e:
        import traceback
        print(f"Error in internal_link_analysis_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/info",
            summary="内部链接系统信息",
            description="获取内部链接建议系统信息",
            response_description="返回系统信息")
async def internal_link_info_api(request: Request):
    """
    内部链接系统信息API
    """
    return ApiResponse(
        success=True,
        data={
            'enabled': True,
            'features': [
                '关键词提取',
                '相关文章推荐',
                '孤立文章检测',
                '链接密度分析',
                '锚文本建议',
            ],
            'algorithms': [
                '词频统计(TF)',
                '关键词匹配',
                '相关度评分',
            ],
            'recommendations': [
                '每篇文章保持2-5个内部链接',
                '使用描述性锚文本',
                '避免过度链接(链接密度<5%)',
                '定期修复断裂链接',
            ],
        }
    )
