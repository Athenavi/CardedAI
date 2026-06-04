"""
评论系统增强服务

功能：
1. 评论树形结构构建（嵌套回复）
2. 评论点赞/取消点赞
3. 评论排序（最新、最热、最早）
4. 评论通知
"""
from typing import List, Dict, Optional
from datetime import datetime

from sqlalchemy import select, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.comment import Comment
from shared.models.comment_vote import CommentVote
from shared.models.user import User


class CommentEnhancedService:
    """
    评论增强服务
    
    提供评论的树形结构、点赞、排序等功能
    """

    async def get_comments_tree(
            self,
            db: AsyncSession,
            article_id: int,
            sort_by: str = 'latest',
            page: int = 1,
            per_page: int = 20,
            include_unapproved: bool = False
    ) -> Dict:
        """
        获取文章的评论树（嵌套结构）
        
        Args:
            db: 数据库会话
            article_id: 文章ID
            sort_by: 排序方式 (latest, oldest, popular)
            page: 页码
            per_page: 每页数量
            include_unapproved: 是否包含未审核评论
            
        Returns:
            评论树和分页信息
        """
        # 构建查询
        query = select(Comment).where(Comment.article_id == article_id)

        if not include_unapproved:
            query = query.where(Comment.is_approved == True)

        # 排序
        if sort_by == 'latest':
            query = query.order_by(desc(Comment.created_at))
        elif sort_by == 'oldest':
            query = query.order_by(asc(Comment.created_at))
        elif sort_by == 'popular':
            query = query.order_by(desc(Comment.likes))
        else:
            query = query.order_by(desc(Comment.created_at))

        # 获取总数
        count_query = select(Comment.id).where(Comment.article_id == article_id)
        if not include_unapproved:
            count_query = count_query.where(Comment.is_approved == True)
        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())

        # 分页
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        result = await db.execute(query)
        comments = result.scalars().all()

        # 构建树形结构
        tree = self._build_comment_tree(comments)

        return {
            'comments': tree,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }

    def _build_comment_tree(self, comments: List[Comment]) -> List[Dict]:
        """
        构建评论树形结构
        
        Args:
            comments: 评论列表
            
        Returns:
            树形结构的评论列表
        """
        # 转换为字典并添加 children 字段
        comment_map = {}
        for comment in comments:
            comment_dict = comment.to_dict()
            comment_dict['children'] = []
            comment_dict['depth'] = 0
            comment_map[comment.id] = comment_dict

        # 构建树
        root_comments = []
        for comment in comments:
            comment_dict = comment_map[comment.id]

            if comment.parent_id is None or comment.parent_id not in comment_map:
                # 根评论
                root_comments.append(comment_dict)
            else:
                # 子评论，添加到父评论的 children
                parent = comment_map[comment.parent_id]
                comment_dict['depth'] = parent['depth'] + 1
                parent['children'].append(comment_dict)

        return root_comments

    async def like_comment(
            self,
            db: AsyncSession,
            comment_id: int,
            user_id: int
    ) -> Dict:
        """
        点赞评论
        
        Args:
            db: 数据库会话
            comment_id: 评论ID
            user_id: 用户ID
            
        Returns:
            操作结果
        """
        # 检查评论是否存在
        stmt = select(Comment).where(Comment.id == comment_id)
        result = await db.execute(stmt)
        comment = result.scalar_one_or_none()

        if not comment:
            raise ValueError("评论不存在")

        # 检查是否已经点赞
        stmt = select(CommentVote).where(
            CommentVote.comment_id == comment_id,
            CommentVote.user_id == user_id
        )
        result = await db.execute(stmt)
        existing_vote = result.scalar_one_or_none()

        if existing_vote:
            if existing_vote.vote_type == 'like':
                # 已经点赞，取消点赞
                await db.delete(existing_vote)
                comment.likes = max(0, comment.likes - 1)
                action = 'unliked'
            else:
                # 之前是反对，改为点赞
                existing_vote.vote_type = 'like'
                comment.likes += 1
                action = 'liked'
        else:
            # 新建点赞
            vote = CommentVote(
                comment_id=comment_id,
                user_id=user_id,
                vote_type='like'
            )
            db.add(vote)
            comment.likes += 1
            action = 'liked'

        await db.commit()

        return {
            'success': True,
            'action': action,
            'likes': comment.likes
        }

    async def dislike_comment(
            self,
            db: AsyncSession,
            comment_id: int,
            user_id: int
    ) -> Dict:
        """
        反对评论
        
        Args:
            db: 数据库会话
            comment_id: 评论ID
            user_id: 用户ID
            
        Returns:
            操作结果
        """
        # 检查评论是否存在
        stmt = select(Comment).where(Comment.id == comment_id)
        result = await db.execute(stmt)
        comment = result.scalar_one_or_none()

        if not comment:
            raise ValueError("评论不存在")

        # 检查是否已经投票
        stmt = select(CommentVote).where(
            CommentVote.comment_id == comment_id,
            CommentVote.user_id == user_id
        )
        result = await db.execute(stmt)
        existing_vote = result.scalar_one_or_none()

        if existing_vote:
            if existing_vote.vote_type == 'dislike':
                # 已经反对，取消反对
                await db.delete(existing_vote)
                action = 'undisliked'
            else:
                # 之前是点赞，改为反对
                existing_vote.vote_type = 'dislike'
                comment.likes = max(0, comment.likes - 1)
                action = 'disliked'
        else:
            # 新建反对
            vote = CommentVote(
                comment_id=comment_id,
                user_id=user_id,
                vote_type='dislike'
            )
            db.add(vote)
            comment.likes = max(0, comment.likes - 1)
            action = 'disliked'

        await db.commit()

        return {
            'success': True,
            'action': action,
            'likes': comment.likes
        }

    async def get_user_vote(
            self,
            db: AsyncSession,
            comment_id: int,
            user_id: int
    ) -> Optional[str]:
        """
        获取用户对评论的投票
        
        Args:
            db: 数据库会话
            comment_id: 评论ID
            user_id: 用户ID
            
        Returns:
            'like', 'dislike', 或 None
        """
        stmt = select(CommentVote).where(
            CommentVote.comment_id == comment_id,
            CommentVote.user_id == user_id
        )
        result = await db.execute(stmt)
        vote = result.scalar_one_or_none()

        return vote.vote_type if vote else None

    async def notify_comment_reply(
            self,
            db: AsyncSession,
            comment_id: int
    ) -> Dict:
        """
        通知评论被回复
        
        Args:
            db: 数据库会话
            comment_id: 新评论ID
            
        Returns:
            通知结果
        """
        from shared.models.notification import Notification

        # 获取新评论
        stmt = select(Comment).where(Comment.id == comment_id)
        result = await db.execute(stmt)
        new_comment = result.scalar_one_or_none()

        if not new_comment or not new_comment.parent_id:
            return {'success': False, 'message': '不是回复评论'}

        # 获取父评论
        stmt = select(Comment).where(Comment.id == new_comment.parent_id)
        result = await db.execute(stmt)
        parent_comment = result.scalar_one_or_none()

        if not parent_comment or not parent_comment.user_id:
            return {'success': False, 'message': '父评论没有用户'}

        # 如果是自己回复自己，不发送通知
        if parent_comment.user_id == new_comment.user_id:
            return {'success': False, 'message': '自己回复自己'}

        # 创建通知
        notification = Notification(
            user_id=parent_comment.user_id,
            type='comment_reply',
            title='有人回复了你的评论',
            content=f'{new_comment.author_name or "匿名用户"} 回复了你的评论',
            related_id=new_comment.id,
            related_type='comment',
            is_read=False
        )

        db.add(notification)
        await db.commit()

        return {
            'success': True,
            'notification_id': notification.id
        }


# 全局实例
comment_enhanced_service = CommentEnhancedService()
