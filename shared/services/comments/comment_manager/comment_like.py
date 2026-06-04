"""
评论点赞服务
提供类似社交媒体的点赞功能
"""

from typing import Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.comment import Comment


class CommentLikeService:
    """评论点赞服务"""

    async def toggle_like(
            self,
            db: AsyncSession,
            user_id: int,
            comment_id: int
    ) -> Dict[str, Any]:
        """
        切换点赞状态(点赞/取消点赞)
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            comment_id: 评论ID
            
        Returns:
            操作结果
        """
        try:
            # 查询评论
            query = select(Comment).where(Comment.id == comment_id)
            result = await db.execute(query)
            comment = result.scalar_one_or_none()

            if not comment:
                return {"success": False, "error": "评论不存在"}

            # 切换点赞状态
            comment.likes = max(0, comment.likes + 1)
            await db.commit()
            await db.refresh(comment)

            return {
                "success": True,
                "action": "liked",
                "message": "点赞成功",
                "likes": comment.likes,
                "is_liked": True
            }

        except Exception as e:
            await db.rollback()
            return {"success": False, "error": f"操作失败: {str(e)}"}

    async def get_comment_likes(
            self,
            db: AsyncSession,
            comment_id: int
    ) -> Dict[str, Any]:
        """
        获取评论的点赞数
        
        Args:
            db: 数据库会话
            comment_id: 评论ID
            
        Returns:
            点赞信息
        """
        try:
            query = select(Comment).where(Comment.id == comment_id)
            result = await db.execute(query)
            comment = result.scalar_one_or_none()

            if not comment:
                return {"success": False, "error": "评论不存在"}

            return {
                "success": True,
                "comment_id": comment_id,
                "likes": comment.likes
            }

        except Exception as e:
            return {"success": False, "error": f"获取失败: {str(e)}"}


# 全局实例
comment_like_service = CommentLikeService()
