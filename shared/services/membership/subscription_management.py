"""
订阅管理优化服务

提供多层级VIP计划、试用期设置、自动续费、会员权益等功能
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional


class SubscriptionManagementService:
    """
    订阅管理服务
    
    功能:
    1. 多层级VIP计划管理
    2. 试用期设置和管理
    3. 自动续费逻辑
    4. 降级/升级处理
    5. 会员权益控制
    6. 积分系统集成
    7. 推荐奖励机制
    8. 账单和发票生成
    """

    def __init__(self):
        # 订阅配置目录
        self.config_dir = Path("storage/subscriptions")
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def create_trial_subscription(
            self,
            user_id: int,
            plan_id: int,
            trial_days: int = 7,
            level: int = 1
    ) -> Dict[str, Any]:
        """
        创建试用订阅
        
        Args:
            user_id: 用户ID
            plan_id: 套餐ID
            trial_days: 试用天数
            level: VIP等级
            
        Returns:
            试用订阅信息
        """
        now = datetime.now()
        expires_at = now + timedelta(days=trial_days)

        subscription = {
            "user_id": user_id,
            "plan_id": plan_id,
            "starts_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "status": "trial",
            "level": level,
            "is_trial": True,
            "trial_days": trial_days,
            "payment_amount": 0,
            "created_at": now.isoformat()
        }

        # 保存试用记录
        self._save_subscription(subscription)

        return {
            "success": True,
            "subscription": subscription,
            "message": f"已开通{trial_days}天试用"
        }

    def check_trial_eligibility(self, user_id: int) -> Dict[str, Any]:
        """
        检查用户是否符合试用资格
        
        Args:
            user_id: 用户ID
            
        Returns:
            试用资格信息
        """
        # 检查用户是否已经使用过试用
        user_subs = self._get_user_subscriptions(user_id)

        has_used_trial = any(
            sub.get("is_trial", False)
            for sub in user_subs
        )

        if has_used_trial:
            return {
                "eligible": False,
                "reason": "您已经使用过试用资格"
            }

        return {
            "eligible": True,
            "available_trials": [
                {
                    "plan_id": 1,
                    "name": "基础版试用",
                    "days": 7,
                    "level": 1
                },
                {
                    "plan_id": 2,
                    "name": "进阶版试用",
                    "days": 3,
                    "level": 2
                }
            ]
        }

    def upgrade_subscription(
            self,
            user_id: int,
            new_plan_id: int,
            new_level: int,
            payment_amount: float
    ) -> Dict[str, Any]:
        """
        升级订阅
        
        Args:
            user_id: 用户ID
            new_plan_id: 新套餐ID
            new_level: 新等级
            payment_amount: 支付金额
            
        Returns:
            升级结果
        """
        # 获取当前订阅
        current_sub = self._get_active_subscription(user_id)

        if not current_sub:
            return {
                "success": False,
                "error": "没有活跃的订阅"
            }

        current_level = current_sub.get("level", 0)

        if new_level <= current_level:
            return {
                "success": False,
                "error": f"新等级({new_level})不高于当前等级({current_level})"
            }

        # 计算剩余价值
        remaining_days = self._calculate_remaining_days(current_sub)
        remaining_value = self._prorate_refund(current_sub, remaining_days)

        # 创建新订阅
        now = datetime.now()
        new_plan_duration = self._get_plan_duration(new_plan_id)
        expires_at = now + timedelta(days=new_plan_duration)

        new_subscription = {
            "user_id": user_id,
            "plan_id": new_plan_id,
            "starts_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "status": "active",
            "level": new_level,
            "is_trial": False,
            "payment_amount": payment_amount,
            "previous_subscription_id": current_sub.get("id"),
            "upgrade_from_level": current_level,
            "remaining_credit": remaining_value,
            "created_at": now.isoformat()
        }

        # 停用旧订阅
        current_sub["status"] = "upgraded"
        self._update_subscription(current_sub)

        # 保存新订阅
        self._save_subscription(new_subscription)

        return {
            "success": True,
            "subscription": new_subscription,
            "remaining_credit": remaining_value,
            "message": f"已成功升级到等级 {new_level}"
        }

    def downgrade_subscription(
            self,
            user_id: int,
            new_level: int,
            effective_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        降级订阅（在当前周期结束后生效）
        
        Args:
            user_id: 用户ID
            new_level: 新等级
            effective_date: 生效日期（可选，默认为当前订阅结束）
            
        Returns:
            降级结果
        """
        current_sub = self._get_active_subscription(user_id)

        if not current_sub:
            return {
                "success": False,
                "error": "没有活跃的订阅"
            }

        current_level = current_sub.get("level", 0)

        if new_level >= current_level:
            return {
                "success": False,
                "error": f"新等级({new_level})不低于当前等级({current_level})"
            }

        # 设置生效日期
        if effective_date is None:
            effective_date = current_sub.get("expires_at")

        # 创建降级计划
        downgrade_plan = {
            "user_id": user_id,
            "type": "downgrade",
            "from_level": current_level,
            "to_level": new_level,
            "effective_date": effective_date,
            "current_subscription_id": current_sub.get("id"),
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }

        # 保存降级计划
        self._save_downgrade_plan(downgrade_plan)

        return {
            "success": True,
            "downgrade_plan": downgrade_plan,
            "message": f"降级已安排，将在 {effective_date} 生效"
        }

    def setup_auto_renewal(
            self,
            user_id: int,
            enabled: bool = True,
            payment_method: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        设置自动续费
        
        Args:
            user_id: 用户ID
            enabled: 是否启用
            payment_method: 支付方式
            
        Returns:
            设置结果
        """
        auto_renewal_config = {
            "user_id": user_id,
            "enabled": enabled,
            "payment_method": payment_method,
            "updated_at": datetime.now().isoformat()
        }

        # 保存配置
        config_file = self.config_dir / f"auto_renewal_{user_id}.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(auto_renewal_config, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "config": auto_renewal_config,
            "message": "自动续费已" + ("启用" if enabled else "禁用")
        }

    def process_auto_renewal(self, user_id: int) -> Dict[str, Any]:
        """
        处理自动续费
        
        Args:
            user_id: 用户ID
            
        Returns:
            续费结果
        """
        # 检查自动续费配置
        config_file = self.config_dir / f"auto_renewal_{user_id}.json"

        if not config_file.exists():
            return {
                "success": False,
                "error": "未配置自动续费"
            }

        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        if not config.get("enabled", False):
            return {
                "success": False,
                "error": "自动续费已禁用"
            }

        # 获取当前订阅
        current_sub = self._get_active_subscription(user_id)

        if not current_sub:
            return {
                "success": False,
                "error": "没有活跃的订阅"
            }

        # 检查是否需要续费（到期前7天）
        expires_at = datetime.fromisoformat(current_sub["expires_at"])
        days_until_expiry = (expires_at - datetime.now()).days

        if days_until_expiry > 7:
            return {
                "success": False,
                "error": "距离到期还有较长时间，暂不需要续费"
            }

        # 执行续费
        plan_id = current_sub.get("plan_id")
        plan_duration = self._get_plan_duration(plan_id)
        payment_amount = self._get_plan_price(plan_id)

        # 创建新订阅
        now = datetime.now()
        new_expires_at = expires_at + timedelta(days=plan_duration)

        new_subscription = {
            "user_id": user_id,
            "plan_id": plan_id,
            "starts_at": now.isoformat(),
            "expires_at": new_expires_at.isoformat(),
            "status": "active",
            "level": current_sub.get("level"),
            "is_trial": False,
            "payment_amount": payment_amount,
            "renewal_from": current_sub.get("id"),
            "is_auto_renewal": True,
            "created_at": now.isoformat()
        }

        # 保存新订阅
        self._save_subscription(new_subscription)

        # 更新旧订阅状态
        current_sub["status"] = "renewed"
        self._update_subscription(current_sub)

        return {
            "success": True,
            "subscription": new_subscription,
            "message": "自动续费成功"
        }

    def get_member_benefits(self, level: int) -> List[Dict[str, Any]]:
        """
        获取会员权益列表
        
        Args:
            level: VIP等级
            
        Returns:
            权益列表
        """
        all_benefits = [
            {
                "id": "premium_content",
                "name": "专属内容访问",
                "description": "访问VIP专属文章和资源",
                "min_level": 1,
                "icon": "lock-open"
            },
            {
                "id": "no_ads",
                "name": "无广告体验",
                "description": "浏览网站时不显示广告",
                "min_level": 1,
                "icon": "ban"
            },
            {
                "id": "priority_support",
                "name": "优先技术支持",
                "description": "获得更快的客服响应",
                "min_level": 1,
                "icon": "headset"
            },
            {
                "id": "advanced_analytics",
                "name": "高级数据分析",
                "description": "查看详细的数据统计和分析报告",
                "min_level": 2,
                "icon": "chart-bar"
            },
            {
                "id": "custom_domain",
                "name": "自定义域名",
                "description": "绑定自己的域名",
                "min_level": 2,
                "icon": "globe"
            },
            {
                "id": "api_access",
                "name": "API访问权限",
                "description": "使用完整的API接口",
                "min_level": 2,
                "icon": "code"
            },
            {
                "id": "white_label",
                "name": "白标服务",
                "description": "移除品牌标识",
                "min_level": 3,
                "icon": "paint-brush"
            },
            {
                "id": "team_collaboration",
                "name": "团队协作",
                "description": "邀请团队成员共同管理",
                "min_level": 3,
                "icon": "users"
            },
            {
                "id": "unlimited_storage",
                "name": "无限存储空间",
                "description": "不受存储容量限制",
                "min_level": 3,
                "icon": "database"
            }
        ]

        # 过滤出该等级可用的权益
        available_benefits = [
            benefit for benefit in all_benefits
            if benefit["min_level"] <= level
        ]

        return available_benefits

    def calculate_points_earning(
            self,
            user_id: int,
            action: str,
            amount: float = 0
    ) -> int:
        """
        计算积分获取
        
        Args:
            user_id: 用户ID
            action: 行为类型
            amount: 金额（如适用）
            
        Returns:
            获得的积分
        """
        # 获取用户VIP等级
        current_sub = self._get_active_subscription(user_id)
        level = current_sub.get("level", 0) if current_sub else 0

        # 基础积分规则
        base_points = {
            "daily_login": 5,
            "article_read": 2,
            "comment_post": 10,
            "content_share": 15,
            "purchase": 1,  # 每元1积分
        }

        # VIP等级加成
        level_multiplier = {
            0: 1.0,  # 普通用户
            1: 1.2,  # VIP1: 20%加成
            2: 1.5,  # VIP2: 50%加成
            3: 2.0,  # VIP3: 100%加成
        }

        multiplier = level_multiplier.get(level, 1.0)
        base = base_points.get(action, 0)

        if action == "purchase":
            points = int(amount * base * multiplier)
        else:
            points = int(base * multiplier)

        return points

    def generate_referral_code(self, user_id: int) -> str:
        """
        生成推荐码
        
        Args:
            user_id: 用户ID
            
        Returns:
            推荐码
        """
        import hashlib
        import time

        # 基于用户ID和时间戳生成唯一推荐码
        raw = f"{user_id}_{int(time.time())}"
        code = hashlib.md5(raw.encode()).hexdigest()[:8].upper()

        # 保存推荐码
        referral_data = {
            "user_id": user_id,
            "code": code,
            "created_at": datetime.now().isoformat(),
            "usage_count": 0,
            "total_rewards": 0
        }

        referral_file = self.config_dir / f"referral_{user_id}.json"
        with open(referral_file, 'w', encoding='utf-8') as f:
            json.dump(referral_data, f, ensure_ascii=False, indent=2)

        return code

    def process_referral_reward(
            self,
            referrer_id: int,
            referred_user_id: int,
            reward_type: str = "points"
    ) -> Dict[str, Any]:
        """
        处理推荐奖励
        
        Args:
            referrer_id: 推荐人ID
            referred_user_id: 被推荐人ID
            reward_type: 奖励类型（points/subscription_days）
            
        Returns:
            奖励结果
        """
        # 获取推荐码信息
        referral_file = self.config_dir / f"referral_{referrer_id}.json"

        if not referral_file.exists():
            return {
                "success": False,
                "error": "推荐码不存在"
            }

        with open(referral_file, 'r', encoding='utf-8') as f:
            referral_data = json.load(f)

        # 更新使用次数
        referral_data["usage_count"] += 1

        # 计算奖励
        if reward_type == "points":
            reward_amount = 100  # 100积分
            referral_data["total_rewards"] += reward_amount
            reward_description = f"获得 {reward_amount} 积分"
        elif reward_type == "subscription_days":
            reward_amount = 3  # 3天订阅
            referral_data["total_rewards"] += reward_amount
            reward_description = f"获得 {reward_amount} 天VIP时长"
        else:
            return {
                "success": False,
                "error": "无效的奖励类型"
            }

        # 保存更新后的数据
        with open(referral_file, 'w', encoding='utf-8') as f:
            json.dump(referral_data, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "reward_type": reward_type,
            "reward_amount": reward_amount,
            "description": reward_description,
            "total_referrals": referral_data["usage_count"]
        }

    def _get_active_subscription(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户的活跃订阅"""
        user_subs = self._get_user_subscriptions(user_id)

        for sub in user_subs:
            if sub.get("status") == "active":
                expires_at = datetime.fromisoformat(sub["expires_at"])
                if expires_at > datetime.now():
                    return sub

        return None

    def _get_user_subscriptions(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户的所有订阅"""
        subs_file = self.config_dir / f"subscriptions_{user_id}.json"

        if not subs_file.exists():
            return []

        with open(subs_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_subscription(self, subscription: Dict[str, Any]):
        """保存订阅"""
        user_id = subscription["user_id"]
        subs_file = self.config_dir / f"subscriptions_{user_id}.json"

        subs = []
        if subs_file.exists():
            with open(subs_file, 'r', encoding='utf-8') as f:
                subs = json.load(f)

        subs.append(subscription)

        with open(subs_file, 'w', encoding='utf-8') as f:
            json.dump(subs, f, ensure_ascii=False, indent=2)

    def _update_subscription(self, subscription: Dict[str, Any]):
        """更新订阅"""
        user_id = subscription["user_id"]
        subs_file = self.config_dir / f"subscriptions_{user_id}.json"

        if not subs_file.exists():
            return

        with open(subs_file, 'r', encoding='utf-8') as f:
            subs = json.load(f)

        # 找到并更新订阅
        for i, sub in enumerate(subs):
            if sub.get("id") == subscription.get("id"):
                subs[i] = subscription
                break

        with open(subs_file, 'w', encoding='utf-8') as f:
            json.dump(subs, f, ensure_ascii=False, indent=2)

    def _save_downgrade_plan(self, plan: Dict[str, Any]):
        """保存降级计划"""
        user_id = plan["user_id"]
        plans_file = self.config_dir / f"downgrade_plans_{user_id}.json"

        plans = []
        if plans_file.exists():
            with open(plans_file, 'r', encoding='utf-8') as f:
                plans = json.load(f)

        plans.append(plan)

        with open(plans_file, 'w', encoding='utf-8') as f:
            json.dump(plans, f, ensure_ascii=False, indent=2)

    def _calculate_remaining_days(self, subscription: Dict[str, Any]) -> int:
        """计算剩余天数"""
        expires_at = datetime.fromisoformat(subscription["expires_at"])
        remaining = (expires_at - datetime.now()).days
        return max(0, remaining)

    def _prorate_refund(
            self,
            subscription: Dict[str, Any],
            remaining_days: int
    ) -> float:
        """计算按比例退款金额"""
        payment_amount = subscription.get("payment_amount", 0)
        total_days = self._get_plan_duration(subscription.get("plan_id"))

        if total_days == 0:
            return 0

        daily_rate = payment_amount / total_days
        refund_amount = daily_rate * remaining_days

        return round(refund_amount, 2)

    def _get_plan_duration(self, plan_id: int) -> int:
        """获取套餐有效期"""
        # 模拟套餐数据
        plans = {
            1: 30,  # 月卡
            2: 90,  # 季卡
            3: 365,  # 年卡
        }
        return plans.get(plan_id, 30)

    def _get_plan_price(self, plan_id: int) -> float:
        """获取套餐价格"""
        # 模拟套餐价格
        prices = {
            1: 29.9,
            2: 79.9,
            3: 299.9,
        }
        return prices.get(plan_id, 29.9)


# 全局实例
subscription_service = SubscriptionManagementService()
