"""
评论订阅服务 - 管理文章评论订阅和通知
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.comment_subscription import CommentSubscription


class CommentSubscriptionService:
    """评论订阅服务"""
    
    @staticmethod
    async def subscribe_to_article(
        db: AsyncSession,
        article_id: int,
        email: str,
        user_id: Optional[int] = None,
        notify_type: str = 'new_comment'
    ) -> Dict[str, Any]:
        """订阅文章评论"""
        # 检查是否已存在订阅
        query = select(CommentSubscription).where(
            CommentSubscription.article_id == article_id,
            CommentSubscription.email == email
        )
        result = await db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.is_active = True
            existing.notify_type = notify_type
            existing.user_id = user_id
            await db.commit()
            
            return {
                "success": True,
                "message": "Subscription updated successfully",
                "subscription_id": existing.id,
                "needs_confirmation": not existing.confirmed_at and not user_id
            }
        
        # 创建新订阅
        confirm_token = None if user_id else uuid.uuid4().hex
        
        subscription = CommentSubscription(
            article_id=article_id,
            email=email,
            user_id=user_id,
            notify_type=notify_type,
            confirm_token=confirm_token,
            confirmed_at=datetime.now(timezone.utc) if user_id else None
        )
        
        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)
        
        return {
            "success": True,
            "message": "Subscription created successfully",
            "subscription_id": subscription.id,
            "confirm_token": confirm_token,
            "needs_confirmation": not user_id
        }
    
    @staticmethod
    async def unsubscribe_from_article(
        db: AsyncSession,
        article_id: int,
        email: str
    ) -> Dict[str, Any]:
        """取消订阅文章评论"""
        query = select(CommentSubscription).where(
            CommentSubscription.article_id == article_id,
            CommentSubscription.email == email
        )
        result = await db.execute(query)
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            return {"success": False, "error": "Subscription not found"}
        
        subscription.is_active = False
        await db.commit()

        return {"success": True, "message": "Unsubscribed successfully"}
    
    @staticmethod
    async def confirm_subscription(
        db: AsyncSession,
        token: str
    ) -> Dict[str, Any]:
        """确认订阅（访客）"""
        query = select(CommentSubscription).where(
            CommentSubscription.confirm_token == token
        )
        result = await db.execute(query)
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            return {"success": False, "error": "Invalid confirmation token"}
        
        subscription.confirmed_at = datetime.now(timezone.utc)
        subscription.confirm_token = None
        await db.commit()

        return {"success": True, "message": "Subscription confirmed successfully"}
    
    @staticmethod
    async def get_user_subscriptions(
        db: AsyncSession,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """获取用户的订阅列表"""
        query = select(CommentSubscription).where(
            CommentSubscription.user_id == user_id,
            CommentSubscription.is_active == True
        ).order_by(CommentSubscription.created_at.desc())

        result = await db.execute(query)
        subscriptions = result.scalars().all()
        
        return [
            {
                "id": sub.id,
                "article_id": sub.article_id,
                "notify_type": sub.notify_type,
                "created_at": sub.created_at.isoformat() if sub.created_at else None
            }
            for sub in subscriptions
        ]
    
    @staticmethod
    async def get_article_subscribers(
        db: AsyncSession,
        article_id: int,
        notify_type: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """获取文章的订阅者列表（用于发送通知）"""
        query = select(CommentSubscription).where(
            CommentSubscription.article_id == article_id,
            CommentSubscription.is_active == True,
            CommentSubscription.confirmed_at != None
        )
        
        if notify_type:
            query = query.where(
                (CommentSubscription.notify_type == notify_type) |
                (CommentSubscription.notify_type == 'all_replies')
            )
        
        result = await db.execute(query)
        subscriptions = result.scalars().all()
        
        return [
            {
                "email": sub.email,
                "user_id": sub.user_id,
                "notify_type": sub.notify_type
            }
            for sub in subscriptions
        ]


# 全局实例
comment_subscription_service = CommentSubscriptionService()
