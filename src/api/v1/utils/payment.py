"""
支付相关API
"""
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import VIPPlan, VIPSubscription
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["payment"])


@router.post("")
async def create_payment(
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    创建支付订单
    """
    try:
        # 获取请求数据
        data = await request.json()
        user_id = data.get('user_id')
        plan_id = data.get('plan_id')
        payment_method = data.get('payment_method')  # 'alipay' 或 'wechat'

        # 验证用户ID
        if not user_id or user_id != current_user.id:
            return ApiResponse(success=False, error="无效的用户ID", data=None)

        # 获取VIP套餐信息
        from sqlalchemy import select
        plan_query = select(VIPPlan).where(VIPPlan.id == plan_id, VIPPlan.is_active == True)
        plan_result = await db.execute(plan_query)
        plan = plan_result.scalar_one_or_none()
        if not plan:
            return ApiResponse(success=False, error="无效的套餐ID", data=None)

        # 检查用户是否已有有效订阅
        from sqlalchemy import select
        existing_subscription_query = select(VIPSubscription).where(
            VIPSubscription.user_id == current_user.id,
            VIPSubscription.status == 1
        )
        existing_subscription_result = await db.execute(existing_subscription_query)
        existing_subscription = existing_subscription_result.scalar_one_or_none()

        if existing_subscription:
            return ApiResponse(success=False, error="您已有有效的VIP订阅，无法重复购买", data=None)

        # 创建支付订单记录（这里简化处理，实际应根据支付方式调用对应支付网关）
        if payment_method == 'alipay':
            # 模拟支付宝支付URL生成
            pay_url = f"https://openapi.alipay.com/gateway.do?biz_content={{'out_trade_no':'VIP_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}', 'total_amount':'{plan.price}', 'subject':'VIP_{plan.name}'}}"
            return ApiResponse(
                success=True,
                data={
                    "payment_data": {
                        "pay_url": pay_url,
                        "order_id": f"VIP_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        "amount": float(plan.price),
                        "description": f"购买VIP {plan.name}套餐"
                    }
                }
            )
        elif payment_method == 'wechat':
            # 模拟微信支付处理
            return ApiResponse(
                success=True,
                data={
                    "payment_data": {
                        "qr_code": "mock_wechat_qr_code_data",
                        "order_id": f"VIP_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        "amount": float(plan.price),
                        "description": f"购买VIP {plan.name}套餐"
                    }
                }
            )
        else:
            return ApiResponse(success=False, error="不支持的支付方式", data=None)

    except Exception as e:
        import traceback
        print(f"Error in create_payment: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/alipay/notify")
async def alipay_notify(
        request: Request,
        db: AsyncSession = Depends(get_async_db)
):
    """
    支付宝异步通知处理
    """
    try:
        # 这里应该验证支付宝签名和处理通知数据
        # 为了简化，这里只做模拟处理
        data = await request.form()

        # 模拟处理支付成功逻辑
        # 1. 验证订单号是否存在
        # 2. 验证金额是否正确
        # 3. 更新订单状态
        # 4. 创建VIP订阅记录

        return {"success": True}
    except Exception as e:
        import traceback
        print(f"Error in alipay_notify: {str(e)}")
        print(traceback.format_exc())
        return {"success": False}


@router.post("/wechat/notify")
async def wechat_notify(
        request: Request,
        db: AsyncSession = Depends(get_async_db)
):
    """
    微信异步通知处理
    """
    try:
        # 这里应该验证微信支付签名和处理通知数据
        # 为了简化，这里只做模拟处理
        data = await request.json()

        # 模拟处理支付成功逻辑
        # 1. 验证订单号是否存在
        # 2. 验证金额是否正确
        # 3. 更新订单状态
        # 4. 创建VIP订阅记录

        return {"success": True}
    except Exception as e:
        import traceback
        print(f"Error in wechat_notify: {str(e)}")
        print(traceback.format_exc())
        return {"success": False}
