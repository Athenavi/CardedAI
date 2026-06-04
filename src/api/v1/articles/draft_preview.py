"""
草稿预览链接API端点
"""

from typing import Optional

from fastapi import APIRouter, Depends, Body
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from shared.services.articles.draft_preview_service import draft_preview_service
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["draft-preview"])


class CreatePreviewRequest(BaseModel):
    """创建预览链接请求"""
    article_id: int
    expires_hours: int = 24
    password: Optional[str] = None
    max_views: Optional[int] = None


class ValidatePreviewRequest(BaseModel):
    """验证预览链接请求"""
    token: str
    password: Optional[str] = None


@router.post("/generate")
async def generate_preview_link(
        request: CreatePreviewRequest,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    生成草稿预览链接
    
    Args:
        request: 创建预览请求
    """
    try:
        # 验证文章是否存在且属于当前用户
        from shared.models.article import Article
        from sqlalchemy import select

        article_query = select(Article).where(
            Article.id == request.article_id,
            Article.user == current_user.id
        )
        result = await db.execute(article_query)
        article = result.scalar_one_or_none()

        if not article:
            return ApiResponse(
                success=False,
                error="文章不存在或无权访问"
            )

        # 生成预览令牌
        token = draft_preview_service.generate_preview_token(
            article_id=request.article_id,
            expires_hours=request.expires_hours,
            password=request.password,
            max_views=request.max_views
        )

        # 生成完整URL
        preview_url = draft_preview_service.get_preview_url(token)

        return ApiResponse(
            success=True,
            data={
                'token': token,
                'preview_url': preview_url,
                'expires_hours': request.expires_hours,
                'has_password': request.password is not None,
                'max_views': request.max_views,
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/validate")
async def validate_preview_link(
        request: ValidatePreviewRequest
):
    """
    验证预览链接并获取文章数据
    
    Args:
        request: 验证请求
    """
    try:
        # 验证令牌
        token_info = draft_preview_service.validate_preview_token(
            token=request.token,
            password=request.password
        )

        if not token_info:
            return ApiResponse(
                success=False,
                error="预览链接无效、已过期或密码错误"
            )

        # 获取文章内容
        from shared.models.article import Article
        from shared.models.article_content import ArticleContent
        from sqlalchemy import select

        query = (
            select(Article, ArticleContent)
            .outerjoin(ArticleContent, Article.id == ArticleContent.article)
            .where(Article.id == token_info['article_id'])
        )
        result = await get_async_db().execute(query)
        row = result.first()

        if not row:
            return ApiResponse(
                success=False,
                error="文章不存在"
            )

        article, content_obj = row

        return ApiResponse(
            success=True,
            data={
                'article': {
                    'id': article.id,
                    'title': article.title,
                    'excerpt': article.excerpt,
                    'cover_image': article.cover_image,
                    'created_at': article.created_at.isoformat() if article.created_at else None,
                    'updated_at': article.updated_at.isoformat() if article.updated_at else None,
                },
                'content': content_obj.content if content_obj else "",
                'view_count': token_info['view_count'],
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/revoke")
async def revoke_preview_link(
        token: str = Body(..., embed=True),
        current_user=Depends(jwt_required)
):
    """
    撤销预览链接
    
    Args:
        token: 预览令牌
    """
    try:
        success = draft_preview_service.revoke_token(token)

        if success:
            return ApiResponse(
                success=True,
                data={'message': '预览链接已撤销'}
            )
        else:
            return ApiResponse(
                success=False,
                error="预览链接不存在"
            )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/stats/{token}")
async def get_preview_stats(
        token: str,
        current_user=Depends(jwt_required)
):
    """
    获取预览链接统计信息
    
    Args:
        token: 预览令牌
    """
    try:
        stats = draft_preview_service.get_token_stats(token)

        if not stats:
            return ApiResponse(
                success=False,
                error="预览链接不存在"
            )

        return ApiResponse(
            success=True,
            data=stats
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/cleanup")
async def cleanup_expired_tokens(
        current_user=Depends(jwt_required)
):
    """
    清理过期的预览令牌
    
    Args:
        current_user: 当前用户(需要管理员权限)
    """
    try:
        # 检查管理员权限
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            return ApiResponse(success=False, error="Permission denied. Admin access required.")

        count = draft_preview_service.cleanup_expired_tokens()

        return ApiResponse(
            success=True,
            data={
                'message': f'清理了 {count} 个过期令牌',
                'cleaned_count': count
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))
