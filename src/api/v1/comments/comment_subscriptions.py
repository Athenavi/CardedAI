"""
评论订阅API
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from shared.services.comments.comment_manager import comment_subscription_service
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required, jwt_optional_dependency
from src.utils.database.main import get_async_session

router = APIRouter()


@router.post("/subscribe",
             summary="订阅文章评论",
             description="订阅指定文章的评论通知，支持用户和访客",
             response_description="返回订阅结果")
async def subscribe_to_article_api(
        article_id: int = Body(..., embed=True, description="文章ID"),
        email: str = Body(..., embed=True, description="订阅邮箱"),
        notify_type: str = Body('new_comment', embed=True, description="通知类型"),
        current_user=Depends(jwt_optional_dependency),
        db: AsyncSession = Depends(get_async_session)
):
    """订阅文章评论"""
    try:
        user_id = current_user.id if current_user else None
        
        result = await comment_subscription_service.subscribe_to_article(
            db=db,
            article_id=article_id,
            email=email,
            user_id=user_id,
            notify_type=notify_type
        )
        
        return ApiResponse(
            success=result['success'],
            data=result
        )
    except Exception as e:
        import traceback
        print(f"Error in subscribe_to_article_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/unsubscribe",
             summary="取消订阅文章评论",
             description="取消对指定文章的评论订阅",
             response_description="返回操作结果")
async def unsubscribe_from_article_api(
        article_id: int = Body(..., embed=True, description="文章ID"),
        email: str = Body(..., embed=True, description="订阅邮箱"),
        db: AsyncSession = Depends(get_async_session)
):
    """取消订阅文章评论"""
    try:
        result = await comment_subscription_service.unsubscribe_from_article(db, article_id, email)
        
        return ApiResponse(
            success=result['success'],
            data=result
        )
    except Exception as e:
        import traceback
        print(f"Error in unsubscribe_from_article_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/confirm/{token}",
            summary="确认订阅",
            description="通过token确认订阅（访客）",
            response_description="返回确认结果")
async def confirm_subscription_api(
        token: str,
        db: AsyncSession = Depends(get_async_session)
):
    """确认订阅"""
    try:
        result = await comment_subscription_service.confirm_subscription(db, token)
        
        return ApiResponse(
            success=result['success'],
            data=result
        )
    except Exception as e:
        import traceback
        print(f"Error in confirm_subscription_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/my-subscriptions",
            summary="获取我的订阅列表",
            description="获取当前用户的所有评论订阅",
            response_description="返回订阅列表")
async def get_my_subscriptions_api(
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    """获取我的订阅列表"""
    try:
        subscriptions = await comment_subscription_service.get_user_subscriptions(db, current_user.id)
        
        return ApiResponse(
            success=True,
            data={
                "subscriptions": subscriptions,
                "total": len(subscriptions)
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_my_subscriptions_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/article/{article_id}/subscribers",
            summary="获取文章订阅者",
            description="获取指定文章的订阅者列表（用于发送通知）",
            response_description="返回订阅者列表")
async def get_article_subscribers_api(
        article_id: int,
        notify_type: Optional[str] = Query(None, description="通知类型筛选"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    """获取文章订阅者"""
    try:
        # 检查权限：仅管理员或文章作者可查看
        from sqlalchemy import select
        from shared.models.article import Article
        
        article_query = select(Article).where(Article.id == article_id)
        article_result = await db.execute(article_query)
        article = article_result.scalar_one_or_none()
        
        if not article:
            return ApiResponse(success=False, error="Article not found")
        
        if (not getattr(current_user, 'is_staff', False) and 
            not getattr(current_user, 'is_superuser', False) and
            article.user != current_user.id):
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Permission denied")
        
        subscribers = await comment_subscription_service.get_article_subscribers(db, article_id, notify_type)
        
        return ApiResponse(
            success=True,
            data={
                "subscribers": subscribers,
                "total": len(subscribers)
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_article_subscribers_api: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))
