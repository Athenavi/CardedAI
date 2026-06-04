"""
会员订阅服务

功能：
1. 会员等级管理
2. 内容访问控制
3. 订阅管理
4. 权限检查
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


class MembershipService:
    """
    会员订阅服务
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_vip_status(self, user_id: int) -> Dict:
        """
        获取用户 VIP 状态
        
        Args:
            user_id: 用户ID
            
        Returns:
            VIP 状态信息
        """
        from shared.models.vip_subscription import VIPSubscription
        from shared.models.vip_plan import VIPPlan

        # 查询当前有效的订阅
        now = datetime.now()
        stmt = select(VIPSubscription).join(
            VIPPlan, VIPSubscription.plan_id == VIPPlan.id
        ).where(
            VIPSubscription.user_id == user_id,
            VIPSubscription.status == 1,
            VIPSubscription.expires_at > now
        ).order_by(
            VIPSubscription.expires_at.desc()
        ).limit(1)

        result = await self.db.execute(stmt)
        subscription = result.scalar_one_or_none()

        if not subscription:
            return {
                'is_vip': False,
                'level': 0,
                'expires_at': None,
                'plan_name': None,
            }

        return {
            'is_vip': True,
            'level': subscription.plan.level,
            'expires_at': subscription.expires_at.isoformat(),
            'plan_name': subscription.plan.name,
            'subscription_id': subscription.id,
        }

    async def check_content_access(
            self,
            user_id: int,
            article_id: int,
            required_level: int = 0
    ) -> Dict:
        """
        检查用户是否有权限访问内容
        
        Args:
            user_id: 用户ID
            article_id: 文章ID
            required_level: 所需VIP等级（0表示无需VIP）
            
        Returns:
            访问权限结果
        """
        if required_level == 0:
            return {
                'has_access': True,
                'reason': '公开内容',
            }

        vip_status = await self.get_user_vip_status(user_id)

        if not vip_status['is_vip']:
            return {
                'has_access': False,
                'reason': '需要VIP会员',
                'required_level': required_level,
            }

        if vip_status['level'] < required_level:
            return {
                'has_access': False,
                'reason': f'需要VIP等级{required_level}',
                'current_level': vip_status['level'],
                'required_level': required_level,
            }

        return {
            'has_access': True,
            'reason': '权限验证通过',
            'level': vip_status['level'],
        }

    async def create_subscription(
            self,
            user_id: int,
            plan_id: int,
            payment_amount: float,
            transaction_id: Optional[str] = None
    ) -> Dict:
        """
        创建订阅
        
        Args:
            user_id: 用户ID
            plan_id: 套餐ID
            payment_amount: 支付金额
            transaction_id: 交易ID
            
        Returns:
            订阅结果
        """
        from shared.models.vip_subscription import VIPSubscription
        from shared.models.vip_plan import VIPPlan

        # 获取套餐信息
        plan = await self.db.get(VIPPlan, plan_id)
        if not plan:
            return {'success': False, 'message': '套餐不存在'}

        if not plan.is_active:
            return {'success': False, 'message': '套餐已停用'}

        # 创建订阅
        now = datetime.now()
        expires_at = now + timedelta(days=plan.duration_days)

        subscription = VIPSubscription(
            user_id=user_id,
            plan_id=plan_id,
            starts_at=now,
            expires_at=expires_at,
            status=1,
            payment_amount=payment_amount,
            transaction_id=transaction_id,
            created_at=now,
        )

        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)

        return {
            'success': True,
            'subscription_id': subscription.id,
            'expires_at': expires_at.isoformat(),
            'plan_name': plan.name,
            'level': plan.level,
        }

    async def cancel_subscription(self, subscription_id: int, user_id: int) -> Dict:
        """
        取消订阅
        
        Args:
            subscription_id: 订阅ID
            user_id: 用户ID
            
        Returns:
            操作结果
        """
        from shared.models.vip_subscription import VIPSubscription

        subscription = await self.db.get(VIPSubscription, subscription_id)

        if not subscription:
            return {'success': False, 'message': '订阅不存在'}

        if subscription.user_id != user_id:
            return {'success': False, 'message': '无权操作此订阅'}

        subscription.status = 0
        await self.db.commit()

        return {
            'success': True,
            'message': '订阅已取消',
        }

    async def get_available_plans(self) -> List[Dict]:
        """
        获取可用套餐列表
        
        Returns:
            套餐列表
        """
        from shared.models.vip_plan import VIPPlan
        from sqlalchemy import select

        stmt = select(VIPPlan).where(
            VIPPlan.is_active == True
        ).order_by(
            VIPPlan.level.asc(),
            VIPPlan.price.asc()
        )

        result = await self.db.execute(stmt)
        plans = result.scalars().all()

        return [
            {
                'id': plan.id,
                'name': plan.name,
                'description': plan.description,
                'price': plan.price,
                'original_price': plan.original_price,
                'duration_days': plan.duration_days,
                'level': plan.level,
                'features': plan.features,
            }
            for plan in plans
        ]

    async def get_user_subscriptions(self, user_id: int) -> List[Dict]:
        """
        获取用户订阅历史
        
        Args:
            user_id: 用户ID
            
        Returns:
            订阅列表
        """
        from shared.models.vip_subscription import VIPSubscription
        from shared.models.vip_plan import VIPPlan
        from sqlalchemy import select

        stmt = select(VIPSubscription).join(
            VIPPlan, VIPSubscription.plan_id == VIPPlan.id
        ).where(
            VIPSubscription.user_id == user_id
        ).order_by(
            VIPSubscription.created_at.desc()
        )

        result = await self.db.execute(stmt)
        subscriptions = result.scalars().all()

        return [
            {
                'id': sub.id,
                'plan_name': sub.plan.name,
                'level': sub.plan.level,
                'starts_at': sub.starts_at.isoformat(),
                'expires_at': sub.expires_at.isoformat(),
                'status': sub.status,
                'payment_amount': sub.payment_amount,
                'created_at': sub.created_at.isoformat(),
            }
            for sub in subscriptions
        ]


def create_membership_service(db: AsyncSession) -> MembershipService:
    return MembershipService(db)
