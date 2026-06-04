"""
AMP (Accelerated Mobile Pages) API
提供AMP版本的文章页面
"""
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.article import Article
from shared.models.article_content import ArticleContent
from shared.models.user import User
from shared.services.advanced_features.amp_service import amp_service
from src.api.v1.core.responses import ApiResponse
from src.extensions import get_async_db_session as get_async_db

router = APIRouter()


@router.get("/{article_id}",
            summary="获取文章AMP版本",
            description="返回文章的AMP HTML页面,用于移动设备快速加载",
            response_description="返回AMP HTML或重定向")
async def get_article_amp_api(
        request: Request,
        article_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取文章AMP版本API
    
    返回符合AMP规范的HTML页面
    """
    try:
        # 查询文章
        article_query = select(Article).where(
            Article.id == article_id,
            Article.status == 1  # 只返回已发布的文章
        )
        article_result = await db.execute(article_query)
        article = article_result.scalar_one_or_none()
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # 获取文章内容
        content_query = select(ArticleContent).where(ArticleContent.aid == article_id)
        content_result = await db.execute(content_query)
        article_content = content_result.scalar_one_or_none()
        
        if not article_content:
            raise HTTPException(status_code=404, detail="Article content not found")
        
        # 获取作者信息
        author_query = select(User).where(User.id == article.user)
        author_result = await db.execute(author_query)
        author = author_result.scalar_one_or_none()
        
        # 构建文章数据
        from datetime import datetime
        article_data = {
            'title': article.title,
            'content': article_content.content,
            'author': {
                'name': author.username if author else 'Unknown',
                'id': author.id if author else None,
            },
            'published_at': article.created_at.isoformat() if article.created_at else datetime.now().isoformat(),
            'updated_at': article.updated_at.isoformat() if article.updated_at else datetime.now().isoformat(),
            'featured_image': article.cover_image,
            'canonical_url': f"{request.base_url}articles/{article.slug}" if article.slug else f"{request.base_url}articles/{article_id}",
        }
        
        # 生成AMP HTML
        amp_html = amp_service.generate_amp_html(article_data)
        
        # 验证AMP
        validation = amp_service.validate_amp(amp_html)
        
        if not validation['valid']:
            # 如果验证失败,记录错误但仍返回(开发阶段)
            print(f"AMP Validation Errors: {validation['errors']}")
        
        # 返回AMP HTML
        from fastapi.responses import HTMLResponse
        return HTMLResponse(
            content=amp_html,
            headers={
                'Content-Type': 'text/html; charset=utf-8',
                'X-AMP-Valid': str(validation['valid']).lower(),
                'Link': f'<{article_data["canonical_url"]}>; rel="canonical"',
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in get_article_amp_api: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{article_id}/validate",
            summary="验证文章AMP",
            description="验证文章的AMP版本是否符合规范",
            response_description="返回验证结果")
async def validate_article_amp_api(
        request: Request,
        article_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    """
    验证文章AMP API
    """
    try:
        # 查询文章
        article_query = select(Article).where(Article.id == article_id)
        article_result = await db.execute(article_query)
        article = article_result.scalar_one_or_none()
        
        if not article:
            return ApiResponse(success=False, error="Article not found")
        
        # 获取文章内容
        content_query = select(ArticleContent).where(ArticleContent.aid == article_id)
        content_result = await db.execute(content_query)
        article_content = content_result.scalar_one_or_none()
        
        if not article_content:
            return ApiResponse(success=False, error="Article content not found")
        
        # 获取作者信息
        author_query = select(User).where(User.id == article.user)
        author_result = await db.execute(author_query)
        author = author_result.scalar_one_or_none()
        
        # 构建文章数据
        from datetime import datetime
        article_data = {
            'title': article.title,
            'content': article_content.content,
            'author': {
                'name': author.username if author else 'Unknown',
            },
            'published_at': article.created_at.isoformat() if article.created_at else datetime.now().isoformat(),
            'updated_at': article.updated_at.isoformat() if article.updated_at else datetime.now().isoformat(),
            'featured_image': article.cover_image,
            'canonical_url': f"{request.base_url}articles/{article.slug}" if article.slug else f"{request.base_url}articles/{article_id}",
        }
        
        # 生成并验证AMP
        amp_html = amp_service.generate_amp_html(article_data)
        validation = amp_service.validate_amp(amp_html)
        
        return ApiResponse(
            success=True,
            data={
                'article_id': article_id,
                'validation': validation,
                'amp_url': f"{request.base_url}api/v1/amp/{article_id}/amp",
            }
        )
        
    except Exception as e:
        import traceback
        print(f"Error in validate_article_amp_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/info",
            summary="AMP信息",
            description="获取AMP配置和支持信息",
            response_description="返回AMP信息")
async def amp_info_api(request: Request):
    """
    AMP信息API
    """
    return ApiResponse(
        success=True,
        data={
            'enabled': True,
            'css_limit_kb': 50,
            'supported_components': [
                'amp-img',
                'amp-analytics',
                'amp-video',
                'amp-audio',
            ],
            'documentation': 'https://amp.dev/documentation/',
            'validator': 'https://validator.ampproject.org/',
        }
    )
