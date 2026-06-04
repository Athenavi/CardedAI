"""
移动端评论API
提供适合移动端的评论相关接口，包括查看、发表、回复、点赞等功能
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.comment import Comment
from shared.models.user import User
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required
from src.utils.database.main import get_async_session

router = APIRouter(tags=["mobile-comments"])


@router.get("/article/{article_id}")
async def get_mobile_article_comments(
        request: Request,
        article_id: int,
        page: int = Query(1, ge=1, description="页码"),
        per_page: int = Query(20, ge=1, le=50, description="每页数量"),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取文章评论列表（移动端优化）
    """
    try:
        # 查询已审核的评论
        query = (
            select(Comment)
            .where(
                Comment.article_id == article_id,
                Comment.is_approved == True
            )
            .order_by(Comment.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )

        result = await db.execute(query)
        comments = result.scalars().all()

        # 统计总数
        count_query = (
            select(func.count(Comment.id))
            .where(
                Comment.article_id == article_id,
                Comment.is_approved == True
            )
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 批量加载用户信息
        user_ids = list({c.user_id for c in comments if c.user_id})
        users_dict = {}

        if user_ids:
            users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
            users_dict = {u.id: u for u in users_result.scalars().all()}

        # 构建响应数据
        comments_data = []
        for comment in comments:
            user = users_dict.get(comment.user_id)

            comments_data.append({
                "id": comment.id,
                "content": comment.content,
                "author": {
                    "id": user.id if user else None,
                    "username": user.username if user else (comment.author_name or "访客"),
                    "avatar": user.profile_picture if user else None
                },
                "created_at": comment.created_at.isoformat() if comment.created_at else None,
                "likes": comment.likes or 0,
                "parent_id": comment.parent_id
            })

        return ApiResponse(
            success=True,
            data={
                "comments": comments_data,
                "pagination": {
                    "current_page": page,
                    "per_page": per_page,
                    "total": total,
                    "total_pages": (total + per_page - 1) // per_page,
                    "has_next": page < (total + per_page - 1) // per_page,
                    "has_prev": page > 1
                }
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_mobile_article_comments: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))


@router.post("/")
async def create_mobile_comment(
        request: Request,
        article_id: int = Query(..., description="文章ID"),
        content: str = Query(..., min_length=1, description="评论内容"),
        parent_id: Optional[int] = Query(None, description="父评论ID（回复时使用）"),
        db: AsyncSession = Depends(get_async_session),
        current_user=Depends(jwt_required)
):
    """
    创建评论（移动端）
    """
    try:
        from datetime import datetime

        # 检查文章是否存在
        from shared.models.article import Article
        article_query = select(Article).where(Article.id == article_id)
        article_result = await db.execute(article_query)
        article = article_result.scalar_one_or_none()

        if not article:
            return ApiResponse(success=False, error="文章不存在")

        # 创建评论
        new_comment = Comment(
            article_id=article_id,
            user_id=current_user.id,
            parent_id=parent_id,
            content=content,
            is_approved=True,  # 登录用户直接通过
            likes=0,
            author_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent", "")
        )

        db.add(new_comment)
        await db.commit()
        await db.refresh(new_comment)

        return ApiResponse(
            success=True,
            data={
                "id": new_comment.id,
                "content": new_comment.content,
                "created_at": new_comment.created_at.isoformat() if new_comment.created_at else None,
                "message": "评论发表成功"
            }
        )
    except Exception as e:
        await db.rollback()
        import traceback
        print(f"Error in create_mobile_comment: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))


@router.post("/{comment_id}/like")
async def like_mobile_comment(
        request: Request,
        comment_id: int,
        db: AsyncSession = Depends(get_async_session),
        current_user=Depends(jwt_required)
):
    """
    点赞/取消点赞评论（移动端）
    """
    try:
        from shared.models.comment_like import CommentLike

        # 检查是否已点赞
        like_query = select(CommentLike).where(
            CommentLike.user_id == current_user.id,
            CommentLike.comment_id == comment_id
        )
        like_result = await db.execute(like_query)
        existing_like = like_result.scalar_one_or_none()

        if existing_like:
            # 取消点赞
            await db.delete(existing_like)

            # 减少评论点赞数
            comment_query = select(Comment).where(Comment.id == comment_id)
            comment_result = await db.execute(comment_query)
            comment = comment_result.scalar_one_or_none()

            if comment and comment.likes > 0:
                comment.likes -= 1

            action = "unliked"
            message = "已取消点赞"
        else:
            # 添加点赞
            new_like = CommentLike(
                user_id=current_user.id,
                comment_id=comment_id
            )
            db.add(new_like)

            # 增加评论点赞数
            comment_query = select(Comment).where(Comment.id == comment_id)
            comment_result = await db.execute(comment_query)
            comment = comment_result.scalar_one_or_none()

            if comment:
                comment.likes = (comment.likes or 0) + 1

            action = "liked"
            message = "点赞成功"

        await db.commit()

        return ApiResponse(
            success=True,
            data={
                "action": action,
                "message": message
            }
        )
    except Exception as e:
        await db.rollback()
        import traceback
        print(f"Error in like_mobile_comment: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))
