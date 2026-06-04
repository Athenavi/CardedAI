"""
团队评论和反馈 API

提供团队内部评论的管理功能
"""

from typing import Optional, List

from fastapi import APIRouter, Depends, Query, Body

from shared.services.comments.team_comments import team_comment_service
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required

router = APIRouter()


@router.post("/comment", summary="创建评论", description="创建团队评论")
async def create_comment(
        content_id: int = Body(..., description="内容ID"),
        content_type: str = Body(..., description="内容类型"),
        text: str = Body(..., description="评论内容"),
        parent_id: Optional[int] = Body(None, description="父评论ID（回复）"),
        mentions: Optional[List[int]] = Body(None, description="@提及的用户ID列表"),
        current_user=Depends(jwt_required),
):
    """创建评论"""
    comment = team_comment_service.create_comment(
        content_id=content_id,
        content_type=content_type,
        author_id=current_user.id,
        author_name=getattr(current_user, 'username', 'Unknown'),
        text=text,
        parent_id=parent_id,
        mentions=mentions,
    )

    return ApiResponse(
        success=True,
        message="Comment created",
        data=comment
    )


@router.put("/comment/{comment_id}", summary="更新评论", description="更新评论内容")
async def update_comment(
        comment_id: int,
        text: str = Body(..., description="新的评论内容"),
        current_user=Depends(jwt_required),
):
    """更新评论"""
    try:
        comment = team_comment_service.update_comment(
            comment_id=comment_id,
            author_id=current_user.id,
            text=text,
        )

        return ApiResponse(
            success=True,
            message="Comment updated",
            data=comment
        )
    except ValueError as e:
        return ApiResponse(success=False, error=str(e))


@router.delete("/comment/{comment_id}", summary="删除评论", description="删除评论")
async def delete_comment(
        comment_id: int,
        current_user=Depends(jwt_required),
):
    """删除评论"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)

        success = team_comment_service.delete_comment(
            comment_id=comment_id,
            user_id=current_user.id,
            is_admin=is_admin,
        )

        if success:
            return ApiResponse(
                success=True,
                message="Comment deleted"
            )
        else:
            return ApiResponse(
                success=False,
                error="Comment not found"
            )
    except ValueError as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/comment/{comment_id}/resolve", summary="标记为已解决", description="标记评论为已解决")
async def resolve_comment(
        comment_id: int,
        current_user=Depends(jwt_required),
):
    """标记为已解决"""
    try:
        comment = team_comment_service.resolve_comment(
            comment_id=comment_id,
            resolver_id=current_user.id,
            resolver_name=getattr(current_user, 'username', 'Unknown'),
        )

        return ApiResponse(
            success=True,
            message="Comment resolved",
            data=comment
        )
    except ValueError as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/content/{content_type}/{content_id}", summary="获取内容评论", description="获取指定内容的评论")
async def get_content_comments(
        content_type: str,
        content_id: int,
        include_resolved: bool = Query(True, description="是否包含已解决的评论"),
        current_user=Depends(jwt_required),
):
    """获取内容评论"""
    comments = team_comment_service.get_comments_for_content(
        content_id=content_id,
        content_type=content_type,
        include_resolved=include_resolved,
    )

    return ApiResponse(
        success=True,
        data={
            'comments': comments,
            'count': len(comments),
        }
    )


@router.get("/mentions", summary="获取@提及", description="获取@当前用户的评论")
async def get_mentions(
        unread_only: bool = Query(False, description="是否只返回未读的"),
        current_user=Depends(jwt_required),
):
    """获取@提及"""
    mentions = team_comment_service.get_user_mentions(
        user_id=current_user.id,
        unread_only=unread_only,
    )

    return ApiResponse(
        success=True,
        data={
            'mentions': mentions,
            'count': len(mentions),
        }
    )


@router.get("/statistics", summary="获取统计信息", description="获取评论统计信息")
async def get_statistics(
        content_id: Optional[int] = Query(None, description="内容ID过滤"),
        content_type: Optional[str] = Query(None, description="内容类型过滤"),
        current_user=Depends(jwt_required),
):
    """获取统计信息"""
    stats = team_comment_service.get_statistics(
        content_id=content_id,
        content_type=content_type,
    )

    return ApiResponse(
        success=True,
        data=stats
    )
