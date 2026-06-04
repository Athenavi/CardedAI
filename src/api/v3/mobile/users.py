"""
移动端用户API
提供适合移动端的用户相关接口，包括登录、注册、个人资料等功能
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required
from src.utils.database.main import get_async_session

router = APIRouter(tags=["mobile-users"])


@router.get("/profile")
async def get_mobile_user_profile(
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取用户资料（移动端）
    """
    try:
        # 构建头像URL
        avatar_url = None
        if current_user.profile_picture:
            safe_filename = current_user.profile_picture.replace('\\', '/').split('/')[-1]
            safe_filename = safe_filename.replace('"', '').replace("'", "").strip()
            if safe_filename:
                base_url = str(request.url).split('/users/profile')[0].rsplit('/', 1)[0]
                avatar_url = f"{base_url}/api/v2/static/avatar/{safe_filename}.webp"

        return ApiResponse(
            success=True,
            data={
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email,
                "avatar": avatar_url,
                "bio": getattr(current_user, 'bio', ''),
                "created_at": current_user.date_joined.isoformat() if hasattr(current_user,
                                                                              'date_joined') and current_user.date_joined else None,
                "is_active": current_user.is_active,
                "vip_level": getattr(current_user, 'vip_level', 0)
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_mobile_user_profile: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))


@router.put("/profile")
async def update_mobile_user_profile(
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    """
    更新用户资料（移动端）
    """
    try:
        data = await request.json()

        # 允许更新的字段
        allowed_fields = ['username', 'email', 'bio']

        for field in allowed_fields:
            if field in data:
                setattr(current_user, field, data[field])

        await db.commit()
        await db.refresh(current_user)

        return ApiResponse(
            success=True,
            data={
                "message": "资料更新成功",
                "user": {
                    "id": current_user.id,
                    "username": current_user.username,
                    "email": current_user.email,
                    "bio": getattr(current_user, 'bio', '')
                }
            }
        )
    except Exception as e:
        await db.rollback()
        import traceback
        print(f"Error in update_mobile_user_profile: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))


@router.get("/stats")
async def get_mobile_user_stats(
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取用户统计信息（移动端）
    """
    try:
        from shared.models.article import Article
        from sqlalchemy import func

        # 统计文章数量
        articles_count = await db.scalar(
            select(func.count(Article.id)).where(Article.user == current_user.id)
        )

        # 统计评论数量
        from shared.models.comment import Comment
        comments_count = await db.scalar(
            select(func.count(Comment.id)).where(Comment.user_id == current_user.id)
        )

        return ApiResponse(
            success=True,
            data={
                "articles_count": articles_count or 0,
                "comments_count": comments_count or 0,
                "likes_received": 0,  # 可以后续实现
                "views_received": 0  # 可以后续实现
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_mobile_user_stats: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))
