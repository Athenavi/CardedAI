"""
文章密码保护API
"""
from typing import Optional

from fastapi import APIRouter, Depends, Path, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession

from shared.services.articles.article_manager import password_protection_service
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required
from src.utils.database.main import get_async_session

router = APIRouter()


@router.post("/{article_id}/password",
             summary="设置文章密码",
             description="为文章设置访问密码或清除密码，需要管理员或作者权限",
             response_description="返回操作结果")
async def set_article_password_api(
        article_id: int = Path(..., description="文章ID"),
        password: Optional[str] = Body(None, embed=True, description="密码，传null清除密码"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    """设置文章密码"""
    try:
        from sqlalchemy import select
        from shared.models.article import Article
        
        # 检查权限
        article_query = select(Article).where(Article.id == article_id)
        article_result = await db.execute(article_query)
        article = article_result.scalar_one_or_none()
        
        if not article:
            return ApiResponse(success=False, error="Article not found")
        
        # 仅管理员或作者可设置密码（不限制必须是隐藏文章）
        if (not getattr(current_user, 'is_staff', False) and 
            not getattr(current_user, 'is_superuser', False) and
            article.user != current_user.id):
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Permission denied")
        
        result = await password_protection_service.set_article_password(db, article_id, password)
        
        return ApiResponse(
            success=True,
            data=result
        )
    except Exception as e:
        import traceback
        print(f"Error in set_article_password_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/{article_id}/verify",
             summary="验证文章密码",
             description="验证用户输入的文章访问密码",
             response_description="返回验证结果和访问token")
async def verify_article_password_api(
        article_id: int = Path(..., description="文章ID"),
        password: str = Body(..., embed=True, description="用户输入的密码"),
        db: AsyncSession = Depends(get_async_session)
):
    """验证文章密码"""
    try:
        result = await password_protection_service.verify_article_password(db, article_id, password)
        
        if result['success']:
            # 生成访问token
            access_token = password_protection_service.generate_access_token(article_id)
            result['access_token'] = access_token
        
        return ApiResponse(
            success=result['success'],
            data=result
        )
    except Exception as e:
        import traceback
        print(f"Error in verify_article_password_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/{article_id}/access",
            summary="检查文章访问权限",
            description="检查当前用户是否有权限访问受密码保护的文章",
            response_description="返回访问权限信息")
async def check_article_access_api(
        request: Request,
        article_id: int = Path(..., description="文章ID"),
        db: AsyncSession = Depends(get_async_session)
):
    """检查文章访问权限"""
    try:
        # 从cookie或query参数获取access_token
        access_token = request.query_params.get('access_token') or request.cookies.get(f'article_access_{article_id}')
        
        result = await password_protection_service.check_article_access(db, article_id, access_token)
        
        return ApiResponse(
            success=True,
            data=result
        )
    except Exception as e:
        import traceback
        print(f"Error in check_article_access_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))
