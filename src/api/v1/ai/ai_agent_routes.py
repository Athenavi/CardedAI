"""
AI Agent 推荐 API
提供自动标签推荐、SEO 优化建议、相关文章推荐等功能
"""
import asyncio
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared.services.ai.ai_agent_recommendations import ai_agent_service
from src.auth.auth_deps import jwt_required_dependency as jwt_required
from shared.models.user import User
from src.utils.database.main import get_async_session

router = APIRouter(prefix="/ai-agent", tags=["AI Agent Recommendations"])


@router.post("/recommend-tags")
async def recommend_tags(
        title: str,
        content: str,
        existing_tags: Optional[List[str]] = None,
        max_tags: int = Query(5, ge=1, le=10),
        current_user: User = Depends(jwt_required)
):
    """
    P11-1: 基于文章内容自动推荐标签
    
    Args:
        title: 文章标题
        content: 文章内容
        existing_tags: 已有标签列表
        max_tags: 最大推荐数量
        
    Returns:
        推荐的标签列表及置信度
    """
    result = await ai_agent_service.recommend_tags(
        title=title,
        content=content,
        existing_tags=existing_tags,
        max_tags=max_tags
    )

    if not result['success']:
        raise HTTPException(status_code=500, detail=result.get('error', '推荐失败'))

    return result


@router.post("/seo-suggestions")
async def suggest_seo_optimizations(
        title: str,
        content: str,
        excerpt: Optional[str] = None,
        slug: Optional[str] = None,
        current_user: User = Depends(jwt_required)
):
    """
    P11-1: SEO 优化建议主动提示
    
    Args:
        title: 文章标题
        content: 文章内容
        excerpt: 摘要
        slug: URL 路径
        
    Returns:
        SEO 优化建议列表和评分
    """
    result = await ai_agent_service.suggest_seo_optimizations(
        title=title,
        content=content,
        excerpt=excerpt,
        slug=slug
    )

    return result


@router.get("/related-articles/{article_id}")
async def recommend_related_articles(
        article_id: int,
        limit: int = Query(5, ge=1, le=10),
        current_user: User = Depends(jwt_required)
):
    """
    P11-1: 相关文章智能推荐
    
    Args:
        article_id: 当前文章 ID
        limit: 推荐数量
        
    Returns:
        相关文章列表（按相关度排序）
    """
    async for db in get_async_session():
        related_articles = await ai_agent_service.recommend_related_articles(
            article_id=article_id,
            db_session=db,
            limit=limit
        )

        return {
            "success": True,
            "article_id": article_id,
            "related_articles": related_articles,
            "total_found": len(related_articles)
        }


@router.post("/analyze-article")
async def analyze_article_complete(
        title: str,
        content: str,
        excerpt: Optional[str] = None,
        slug: Optional[str] = None,
        existing_tags: Optional[List[str]] = None,
        current_user: User = Depends(jwt_required)
):
    """
    P11-1: 完整文章分析（标签推荐 + SEO 建议）
    
    Args:
        title: 文章标题
        content: 文章内容
        excerpt: 摘要
        slug: URL 路径
        existing_tags: 已有标签
        
    Returns:
        综合分析结果
    """
    # 并行执行标签推荐和 SEO 分析
    tags_result, seo_result = await asyncio.gather(
        ai_agent_service.recommend_tags(title, content, existing_tags),
        ai_agent_service.suggest_seo_optimizations(title, content, excerpt, slug)
    )

    return {
        "success": True,
        "tag_recommendations": tags_result,
        "seo_analysis": seo_result,
        "analyzed_at": datetime.utcnow().isoformat()
    }
