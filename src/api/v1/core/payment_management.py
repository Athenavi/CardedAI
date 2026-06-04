"""
支付管理 API

提供支付创建、验证、退款等功能
"""
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.user import User
from shared.services.core.payment_service import create_payment_service
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["payment"])


@router.post("/create")
async def create_payment(
        order_id: int = Body(..., embed=True, description="订单ID"),
        payment_method: str = Body(..., embed=True, description="支付方式: stripe/paypal/alipay/wechat"),
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    创建支付
    
    Args:
        order_id: 订单ID
        payment_method: 支付方式
        
    Returns:
        支付意图信息
    """
    try:
        from shared.models.order import Order
        from sqlalchemy import select

        # 获取订单
        stmt = select(Order).where(Order.id == order_id)
        result = await db.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            return ApiResponse(success=False, error="Order not found")

        # 检查订单所有权
        if order.user_id != current_user.id:
            return ApiResponse(success=False, error="Permission denied")

        # 检查订单状态
        if order.status != 'pending':
            return ApiResponse(success=False, error=f"Order status is {order.status}, cannot create payment")

        service = create_payment_service(db)
        result = await service.create_payment_intent(
            order_id=order_id,
            payment_method=payment_method,
            amount=order.total_amount,
            currency=order.currency or 'CNY'
        )

        return ApiResponse(
            success=True,
            data=result
        )
    except Exception as e:
        import traceback
        print(f"Error creating payment: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/verify/{payment_method}")
async def verify_payment(
        payment_method: str,
        payment_data: dict = Body(..., description="支付回调数据"),
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    验证支付结果
    
    Args:
        payment_method: 支付方式
        payment_data: 支付回调数据
        
    Returns:
        验证结果
    """
    try:
        service = create_payment_service(db)
        result = await service.verify_payment(payment_method, payment_data)

        if result.get('verified'):
            # 更新订单状态
            from shared.models.order import Order
            from sqlalchemy import select, update

            order_id = payment_data.get('order_id')
            if order_id:
                stmt = select(Order).where(Order.id == order_id)
                order_result = await db.execute(stmt)
                order = order_result.scalar_one_or_none()

                if order:
                    await db.execute(
                        update(Order)
                        .where(Order.id == order_id)
                        .values(
                            status='paid',
                            transaction_id=result.get('transaction_id'),
                            paid_at=result.get('paid_at')
                        )
                    )
                    await db.commit()

        return ApiResponse(
            success=True,
            data=result
        )
    except Exception as e:
        import traceback
        print(f"Error verifying payment: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/refund")
async def process_refund(
        order_id: int = Body(..., embed=True, description="订单ID"),
        payment_method: str = Body(..., embed=True, description="支付方式"),
        amount: Optional[float] = Body(None, description="退款金额（None表示全额退款）"),
        reason: str = Body('', description="退款原因"),
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    处理退款（需要管理员权限）
    
    Args:
        order_id: 订单ID
        payment_method: 支付方式
        amount: 退款金额
        reason: 退款原因
        
    Returns:
        退款结果
    """
    try:
        # 检查管理员权限
        if not getattr(current_user, 'is_superuser', False):
            return ApiResponse(success=False, error="Permission denied. Admin required.")

        service = create_payment_service(db)
        refund_amount = Decimal(str(amount)) if amount else None

        result = await service.process_refund(
            order_id=order_id,
            payment_method=payment_method,
            amount=refund_amount,
            reason=reason
        )

        if result.get('success'):
            # 更新订单状态
            from shared.models.order import Order
            from sqlalchemy import select, update

            stmt = select(Order).where(Order.id == order_id)
            order_result = await db.execute(stmt)
            order = order_result.scalar_one_or_none()

            if order:
                new_status = 'refunded' if not amount else 'partially_refunded'
                await db.execute(
                    update(Order)
                    .where(Order.id == order_id)
                    .values(status=new_status)
                )
                await db.commit()

        return ApiResponse(
            success=result.get('success', False),
            data=result if result.get('success') else None,
            error=result.get('error') if not result.get('success') else None
        )
    except Exception as e:
        import traceback
        print(f"Error processing refund: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/webhook/{payment_method}")
async def payment_webhook(
        payment_method: str,
        request: Request,
        db: AsyncSession = Depends(get_async_db)
):
    """
    支付网关 Webhook 回调
    
    Args:
        payment_method: 支付方式
        
    Returns:
        Webhook 响应
    """
    try:
        # 获取回调数据
        if payment_method in ['stripe', 'paypal']:
            data = await request.json()
        else:
            # 支付宝和微信使用 form data
            form_data = await request.form()
            data = dict(form_data)

        service = create_payment_service(db)
        result = await service.verify_payment(payment_method, data)

        if result.get('verified'):
            # 更新订单状态
            from shared.models.order import Order
            from sqlalchemy import select, update

            order_id = data.get('order_id') or data.get('out_trade_no', '').replace('ORDER_', '').split('_')[0]

            if order_id:
                try:
                    order_id = int(order_id)
                    stmt = select(Order).where(Order.id == order_id)
                    order_result = await db.execute(stmt)
                    order = order_result.scalar_one_or_none()

                    if order:
                        await db.execute(
                            update(Order)
                            .where(Order.id == order_id)
                            .values(
                                status='paid',
                                transaction_id=result.get('transaction_id'),
                                paid_at=result.get('paid_at')
                            )
                        )
                        await db.commit()

                        # 触发 webhook 事件
                        try:
                            from shared.services.webhook_service import webhook_service
                            webhook_data = {
                                'order_id': order_id,
                                'status': 'paid',
                                'transaction_id': result.get('transaction_id'),
                                'paid_at': result.get('paid_at'),
                                'amount': float(order.total_amount) if hasattr(order, 'total_amount') else 0,
                                'currency': order.currency if hasattr(order, 'currency') else 'CNY'
                            }
                            webhook_service.trigger_event('order.paid', webhook_data)
                        except Exception as webhook_error:
                            print(f"Failed to trigger webhook: {webhook_error}")
                except (ValueError, TypeError):
                    pass

        # 返回成功响应给支付网关
        if payment_method == 'stripe':
            return {'received': True}
        elif payment_method == 'paypal':
            return {'status': 'success'}
        elif payment_method == 'alipay':
            return 'success'
        elif payment_method == 'wechat':
            return '<xml><return_code><![CDATA[SUCCESS]]></return_code><return_msg><![CDATA[OK]]></return_msg></xml>'
        else:
            return {'status': 'ok'}

    except Exception as e:
        import traceback
        print(f"Error processing webhook: {str(e)}")
        print(traceback.format_exc())
        return {'error': str(e)}


@router.get("/methods")
async def get_payment_methods():
    """
    获取支持的支付方式列表
    
    Returns:
        支付方式列表
    """
    return ApiResponse(
        success=True,
        data={
            'methods': [
                {
                    'id': 'stripe',
                    'name': 'Stripe',
                    'description': 'Credit/Debit Card',
                    'currencies': ['USD', 'EUR', 'GBP'],
                    'icon': 'stripe'
                },
                {
                    'id': 'paypal',
                    'name': 'PayPal',
                    'description': 'PayPal Account',
                    'currencies': ['USD', 'EUR', 'GBP', 'CNY'],
                    'icon': 'paypal'
                },
                {
                    'id': 'alipay',
                    'name': '支付宝',
                    'description': 'Alipay',
                    'currencies': ['CNY'],
                    'icon': 'alipay'
                },
                {
                    'id': 'wechat',
                    'name': '微信支付',
                    'description': 'WeChat Pay',
                    'currencies': ['CNY'],
                    'icon': 'wechat'
                }
            ]
        }
    )
