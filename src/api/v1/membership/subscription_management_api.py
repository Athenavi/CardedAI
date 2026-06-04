"""
订阅管理优化 API

提供多层级VIP计划、试用期、自动续费、会员权益等功能
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Body

from shared.services.membership.subscription_management import subscription_service
from src.api.v1.core.responses import ApiResponse
from src.api.v1.users.user_management import jwt_required

router = APIRouter(prefix="/subscription-management", tags=["Subscription Management"])


@router.post("/trial/activate")
async def activate_trial(
        plan_id: int = Body(..., description="套餐ID"),
        trial_days: Optional[int] = Body(7, description="试用天数"),
        current_user=Depends(jwt_required)
):
    """
    激活试用订阅
    
    为新用户提供免费试用机会
    """
    # 检查试用资格
    eligibility = subscription_service.check_trial_eligibility(current_user.id)

    if not eligibility["eligible"]:
        return ApiResponse(
            success=False,
            error=eligibility["reason"]
        )

    # 创建试用订阅
    result = subscription_service.create_trial_subscription(
        user_id=current_user.id,
        plan_id=plan_id,
        trial_days=trial_days or 7,
        level=1
    )

    return ApiResponse(
        success=True,
        data=result,
        message=result["message"]
    )


@router.get("/trial/eligibility")
async def check_trial_eligibility(current_user=Depends(jwt_required)):
    """
    检查试用资格
    
    查看用户是否符合试用条件
    """
    eligibility = subscription_service.check_trial_eligibility(current_user.id)

    return ApiResponse(
        success=True,
        data=eligibility
    )


@router.post("/upgrade")
async def upgrade_subscription(
        new_plan_id: int = Body(..., description="新套餐ID"),
        new_level: int = Body(..., description="新等级"),
        payment_amount: float = Body(..., description="支付金额"),
        current_user=Depends(jwt_required)
):
    """
    升级订阅
    
    升级到更高等级的VIP套餐
    """
    result = subscription_service.upgrade_subscription(
        user_id=current_user.id,
        new_plan_id=new_plan_id,
        new_level=new_level,
        payment_amount=payment_amount
    )

    if result["success"]:
        return ApiResponse(
            success=True,
            data=result,
            message=result["message"]
        )
    else:
        return ApiResponse(
            success=False,
            error=result["error"]
        )


@router.post("/downgrade")
async def downgrade_subscription(
        new_level: int = Body(..., description="新等级"),
        effective_date: Optional[str] = Body(None, description="生效日期"),
        current_user=Depends(jwt_required)
):
    """
    降级订阅
    
    降级到较低等级，在当前周期结束后生效
    """
    result = subscription_service.downgrade_subscription(
        user_id=current_user.id,
        new_level=new_level,
        effective_date=effective_date
    )

    if result["success"]:
        return ApiResponse(
            success=True,
            data=result,
            message=result["message"]
        )
    else:
        return ApiResponse(
            success=False,
            error=result["error"]
        )


@router.post("/auto-renewal/setup")
async def setup_auto_renewal(
        enabled: bool = Body(True, description="是否启用"),
        payment_method: Optional[str] = Body(None, description="支付方式"),
        current_user=Depends(jwt_required)
):
    """
    设置自动续费
    
    配置订阅到期后自动续费
    """
    result = subscription_service.setup_auto_renewal(
        user_id=current_user.id,
        enabled=enabled,
        payment_method=payment_method
    )

    return ApiResponse(
        success=True,
        data=result,
        message=result["message"]
    )


@router.post("/auto-renewal/process")
async def process_auto_renewal(current_user=Depends(jwt_required)):
    """
    处理自动续费
    
    手动触发自动续费流程（通常由定时任务调用）
    """
    result = subscription_service.process_auto_renewal(current_user.id)

    if result["success"]:
        return ApiResponse(
            success=True,
            data=result,
            message=result["message"]
        )
    else:
        return ApiResponse(
            success=False,
            error=result["error"]
        )


@router.get("/benefits/{level}")
async def get_member_benefits(
        level: int,
        current_user=Depends(jwt_required)
):
    """
    获取会员权益
    
    查看指定VIP等级的所有权益
    """
    benefits = subscription_service.get_member_benefits(level)

    return ApiResponse(
        success=True,
        data={
            "level": level,
            "benefits": benefits,
            "total": len(benefits)
        }
    )


@router.get("/points/calculate")
async def calculate_points(
        action: str = Query(..., description="行为类型"),
        amount: Optional[float] = Query(0, description="金额"),
        current_user=Depends(jwt_required)
):
    """
    计算积分获取
    
    预览执行某个行为可获得的积分
    """
    points = subscription_service.calculate_points_earning(
        user_id=current_user.id,
        action=action,
        amount=amount or 0
    )

    return ApiResponse(
        success=True,
        data={
            "action": action,
            "points_earned": points
        }
    )


@router.post("/referral/generate")
async def generate_referral_code(current_user=Depends(jwt_required)):
    """
    生成推荐码
    
    为用户生成专属推荐码
    """
    code = subscription_service.generate_referral_code(current_user.id)

    return ApiResponse(
        success=True,
        data={
            "referral_code": code,
            "share_url": f"https://example.com/ref/{code}"
        },
        message="推荐码生成成功"
    )


@router.post("/referral/reward")
async def process_referral_reward(
        referrer_id: int = Body(..., description="推荐人ID"),
        referred_user_id: int = Body(..., description="被推荐人ID"),
        reward_type: str = Body("points", description="奖励类型"),
        current_user=Depends(jwt_required)
):
    """
    处理推荐奖励
    
    当被推荐人完成注册或购买时发放奖励
    """
    result = subscription_service.process_referral_reward(
        referrer_id=referrer_id,
        referred_user_id=referred_user_id,
        reward_type=reward_type
    )

    if result["success"]:
        return ApiResponse(
            success=True,
            data=result,
            message=result["description"]
        )
    else:
        return ApiResponse(
            success=False,
            error=result["error"]
        )


@router.get("/comparison")
async def get_plan_comparison(current_user=Depends(jwt_required)):
    """
    获取套餐对比
    
    对比不同VIP等级的功能和价格
    """
    plans = [
        {
            "level": 0,
            "name": "免费版",
            "price": 0,
            "duration": "永久",
            "features": [
                "基础内容访问",
                "标准客服支持",
                "有限存储空间"
            ],
            "limitations": [
                "有广告",
                "无法访问专属内容",
                "无API访问权限"
            ]
        },
        {
            "level": 1,
            "name": "基础版",
            "price": 29.9,
            "duration": "30天",
            "features": [
                "专属内容访问",
                "无广告体验",
                "优先技术支持",
                "20%积分加成"
            ],
            "popular": True
        },
        {
            "level": 2,
            "name": "进阶版",
            "price": 79.9,
            "duration": "90天",
            "features": [
                "包含基础版所有功能",
                "高级数据分析",
                "自定义域名",
                "API访问权限",
                "50%积分加成"
            ],
            "savings": "节省11%"
        },
        {
            "level": 3,
            "name": "专业版",
            "price": 299.9,
            "duration": "365天",
            "features": [
                "包含进阶版所有功能",
                "白标服务",
                "团队协作",
                "无限存储空间",
                "100%积分加成",
                "专属客户经理"
            ],
            "savings": "节省17%",
            "best_value": True
        }
    ]

    return ApiResponse(
        success=True,
        data={
            "plans": plans,
            "currency": "CNY"
        }
    )


@router.get("/guide")
async def get_subscription_guide(current_user=Depends(jwt_required)):
    """
    获取订阅使用指南
    """
    guide = {
        "overview": {
            "title": "订阅管理系统",
            "description": "灵活管理您的VIP订阅，享受更多特权和功能。"
        },
        "features": [
            "多层级VIP计划 - 从基础版到专业版，满足不同需求",
            "免费试用 - 新用户可享受7天免费试用",
            "灵活升级 - 随时升级到更高等级，立即生效",
            "平滑降级 - 当前周期结束后自动降级，不浪费剩余时间",
            "自动续费 - 设置后无需担心订阅过期",
            "积分系统 - VIP用户享受更高积分加成",
            "推荐奖励 - 邀请好友获得额外奖励"
        ],
        "faq": [
            {
                "question": "如何开始试用？",
                "answer": "点击'激活试用'按钮，即可享受7天免费试用。每个用户只能试用一次。"
            },
            {
                "question": "升级后立即生效吗？",
                "answer": "是的，升级后立即生效，您会立即获得新等级的所有权益。"
            },
            {
                "question": "降级什么时候生效？",
                "answer": "降级会在当前订阅周期结束后生效，确保您充分利用已付费的时间。"
            },
            {
                "question": "如何取消自动续费？",
                "answer": "在'我的订阅'页面可以隨時关闭自动续费功能。"
            },
            {
                "question": "退款政策是什么？",
                "answer": "升级时会按比例退还旧订阅的剩余价值，用于抵扣新订阅费用。"
            }
        ],
        "tips": [
            "年费套餐最划算，平均每天不到1元",
            "开启自动续费避免服务中断",
            "邀请好友可获得额外积分或VIP时长",
            "定期检查会员权益，充分利用VIP特权"
        ]
    }

    return ApiResponse(
        success=True,
        data=guide
    )
