"""
支付网关 API

提供支付、退款、订单查询等功能
"""

from typing import Optional

from fastapi import APIRouter, Depends, Body

from shared.services.payment import unified_payment_service
from shared.services.payment.payment_gateway import (
    payment_manager,
    PaymentMethod,
)
from src.api.v1.core.responses import ApiResponse
from src.api.v1.users.user_management import jwt_required

router = APIRouter(prefix="/payment", tags=["Payment Gateway"])


@router.post("/create-order")
async def create_order(
        amount: float = Body(..., description="金额"),
        currency: str = Body("USD", description="货币"),
        description: str = Body("", description="描述"),
        payment_method: str = Body(..., description="支付方式 (stripe/paypal/alipay/wechat)"),
        current_user=Depends(jwt_required)
):
    """
    创建订单

    生成新的支付订单
    """
    try:
        method_enum = PaymentMethod(payment_method)

        order = payment_manager.create_order(
            user_id=current_user.id,
            amount=amount,
            currency=currency,
            description=description,
            payment_method=method_enum,
        )

        return ApiResponse(
            success=True,
            data=order.to_dict()
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e)
        )


@router.post("/pay/{order_id}")
async def process_payment(
        order_id: str,
        success_url: str = Body(..., description="成功跳转URL"),
        cancel_url: str = Body(..., description="取消跳转URL"),
        notify_url: str = Body("", description="通知URL"),
        current_user=Depends(jwt_required)
):
    """
    处理支付

    根据订单创建支付会话
    """
    order = payment_manager.get_order(order_id)

    if not order:
        return ApiResponse(
            success=False,
            error="Order not found"
        )

    try:
        result = await payment_manager.process_payment(
            order=order,
            success_url=success_url,
            cancel_url=cancel_url,
            notify_url=notify_url,
        )

        return ApiResponse(
            success=result.get("success", False),
            data=result
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e)
        )


@router.get("/order/{order_id}")
async def get_order(
        order_id: str,
        current_user=Depends(jwt_required)
):
    """
    查询订单

    获取订单详细信息
    """
    order = payment_manager.get_order(order_id)

    if not order:
        return ApiResponse(
            success=False,
            error="Order not found"
        )

    return ApiResponse(
        success=True,
        data=order.to_dict()
    )


@router.post("/refund/{order_id}")
async def refund_order(
        order_id: str,
        amount: Optional[float] = Body(None, description="退款金额（不填则全额退款）"),
        reason: str = Body("", description="退款原因"),
        current_user=Depends(jwt_required)
):
    """
    退款

    对已支付的订单进行退款
    """
    try:
        result = await payment_manager.refund_order(order_id, amount)

        return ApiResponse(
            success=result.get("success", False),
            data=result
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e)
        )


@router.post("/webhook/stripe")
async def stripe_webhook(
        payload: str = Body(...),
        signature: str = Body(..., description="Stripe签名")
):
    """
    Stripe Webhook

    接收 Stripe 支付事件通知
    """
    # 验证 webhook
    is_valid = await payment_manager.stripe.verify_webhook(payload, signature)

    if not is_valid:
        return ApiResponse(
            success=False,
            error="Invalid signature"
        )

    # 处理事件
    import json
    event = json.loads(payload)
    result = await payment_manager.stripe.handle_webhook_event(event)

    return ApiResponse(
        success=result.get("success", False),
        data=result
    )


@router.post("/webhook/paypal")
async def paypal_webhook(
        event_data: dict = Body(...)
):
    """
    PayPal Webhook

    接收 PayPal 支付事件通知
    """
    try:
        # 从 PayPal 事件中提取订单信息
        event_type = event_data.get("event_type", "")
        resource = event_data.get("resource", {})

        if event_type == "CHECKOUT.ORDER.APPROVED" or event_type == "PAYMENT.CAPTURE.COMPLETED":
            # 支付成功，获取 PayPal 订单ID
            paypal_order_id = resource.get("id", "")
            if paypal_order_id:
                # 通过 PayPal 捕获支付
                capture_result = await payment_manager.paypal.capture_payment(paypal_order_id)
                return ApiResponse(
                    success=True,
                    data={
                        "event_type": event_type,
                        "order_id": paypal_order_id,
                        "capture_result": capture_result,
                    }
                )
        elif event_type == "PAYMENT.CAPTURE.DENIED" or event_type == "PAYMENT.CAPTURE.REFUNDED":
            # 支付失败或退款
            return ApiResponse(
                success=True,
                data={
                    "event_type": event_type,
                    "resource_id": resource.get("id", ""),
                    "status": "handled",
                }
            )

        return ApiResponse(
            success=True,
            message="Webhook received",
            data={"event_type": event_type}
        )
    except Exception as e:
        from src.utils.logger import logger
        logger.error(f"PayPal webhook processing failed: {e}")
        return ApiResponse(
            success=False,
            error=f"Webhook processing failed: {str(e)}"
        )


@router.post("/webhook/alipay")
async def alipay_webhook(
        params: dict = Body(...)
):
    """
    支付宝异步通知

    接收支付宝支付结果通知
    """
    # 验证通知
    is_valid = await payment_manager.alipay.verify_notification(params)

    if not is_valid:
        return ApiResponse(
            success=False,
            error="Invalid notification"
        )

    # 从通知参数中提取订单信息并更新状态
    try:
        trade_no = params.get("trade_no", "") or params.get("out_trade_no", "")
        trade_status = params.get("trade_status", "")

        if trade_no and trade_status in ("TRADE_SUCCESS", "TRADE_FINISHED"):
            from shared.services.payment.order_management import OrderManager, OrderStatus
            order_manager = OrderManager()
            # 尝试通过交易号查找并更新订单
            for order_id, order in order_manager.orders.items():
                if getattr(order, 'transaction_id', '') == trade_no:
                    order_manager.update_order_status(order_id, OrderStatus.PAID)
                    break
    except Exception as e:
        from src.utils.logger import logger
        logger.error(f"Alipay order status update failed: {e}")

    return ApiResponse(
        success=True,
        message="Notification verified"
    )


@router.post("/webhook/wechat")
async def wechat_webhook(
        xml_data: str = Body(...)
):
    """
    微信支付通知

    接收微信支付结果通知
    """
    # 验证通知
    result = await payment_manager.wechat.verify_notification(xml_data)

    return ApiResponse(
        success=result.get("success", False),
        data=result
    )


@router.get("/methods")
async def get_payment_methods(current_user=Depends(jwt_required)):
    """
    获取支持的支付方式

    列出所有可用的支付网关
    """
    methods = [
        {
            "id": "stripe",
            "name": "Stripe",
            "description": "信用卡支付",
            "currencies": ["USD", "EUR", "GBP"],
            "icon": "credit-card",
        },
        {
            "id": "paypal",
            "name": "PayPal",
            "description": "PayPal 账户支付",
            "currencies": ["USD", "EUR", "GBP", "JPY"],
            "icon": "paypal",
        },
        {
            "id": "alipay",
            "name": "支付宝",
            "description": "支付宝扫码支付",
            "currencies": ["CNY"],
            "icon": "alipay",
        },
        {
            "id": "wechat",
            "name": "微信支付",
            "description": "微信扫码支付",
            "currencies": ["CNY"],
            "icon": "wechat",
        },
    ]

    return ApiResponse(
        success=True,
        data={
            "methods": methods,
            "total": len(methods)
        }
    )


@router.get("/guide")
async def get_payment_guide(current_user=Depends(jwt_required)):
    """
    获取支付集成指南
    """
    guide = {
        "overview": {
            "title": "支付网关集成",
            "description": "支持多种主流支付方式，提供安全便捷的支付体验。",
            "version": "1.0.0"
        },
        "supported_methods": [
            {
                "name": "Stripe",
                "description": "全球领先的在线支付平台",
                "features": ["信用卡", "借记卡", "Apple Pay", "Google Pay"],
                "setup": "需要注册 Stripe 账号并获取 API Key"
            },
            {
                "name": "PayPal",
                "description": "国际知名的电子钱包",
                "features": ["PayPal账户", "信用卡", "国际支付"],
                "setup": "需要注册 PayPal Business 账号"
            },
            {
                "name": "支付宝",
                "description": "中国最大的移动支付平台",
                "features": ["扫码支付", "APP支付", "网页支付"],
                "setup": "需要申请支付宝开放平台账号"
            },
            {
                "name": "微信支付",
                "description": "腾讯旗下的移动支付服务",
                "features": ["扫码支付", "公众号支付", "APP支付"],
                "setup": "需要注册微信商户平台"
            }
        ],
        "integration_steps": [
            "1. 配置支付网关的 API 密钥",
            "2. 创建订单: POST /payment/create-order",
            "3. 发起支付: POST /payment/pay/{order_id}",
            "4. 接收回调: 配置 Webhook URL",
            "5. 处理结果: 更新订单状态"
        ],
        "security": [
            "使用 HTTPS 传输",
            "验证 Webhook 签名",
            "不要在前端暴露私钥",
            "实施防重放攻击",
            "记录所有交易日志"
        ],
        "api_endpoints": {
            "create_order": "POST /payment/create-order - 创建订单",
            "process_payment": "POST /payment/pay/{order_id} - 处理支付",
            "get_order": "GET /payment/order/{order_id} - 查询订单",
            "refund": "POST /payment/refund/{order_id} - 退款",
            "webhooks": "POST /payment/webhook/{provider} - Webhook 回调"
        }
    }

    return ApiResponse(
        success=True,
        data=guide
    )


# ==================== 加密货币支付 API ====================

@router.post("/crypto/create")
async def create_crypto_payment(
        order_id: str = Body(..., description="订单ID"),
        blockchain: str = Body(..., description="区块链网络 (ethereum, bitcoin, polygon, bsc, solana)"),
        token_symbol: str = Body(..., description="代币符号 (ETH, BTC, USDT, USDC)"),
        current_user=Depends(jwt_required)
):
    """
    创建加密货币支付

    生成加密货币支付地址和二维码
    """
    try:
        result = await unified_payment_service.create_crypto_payment(
            order_id=order_id,
            blockchain=blockchain,
            token_symbol=token_symbol,
        )

        return ApiResponse(
            success=result.get("success", False),
            data=result,
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
        )


@router.get("/crypto/status/{order_id}")
async def check_crypto_payment_status(
        order_id: str,
        current_user=Depends(jwt_required)
):
    """
    检查加密货币支付状态

    查询支付确认数和状态
    """
    try:
        result = await unified_payment_service.check_crypto_payment_status(order_id)

        return ApiResponse(
            success=result.get("success", False),
            data=result,
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
        )


# ==================== x402微支付 API ====================

@router.post("/x402/channel/create")
async def create_x402_channel(
        sender_address: str = Body(..., description="发送方钱包地址"),
        receiver_address: str = Body(..., description="接收方钱包地址"),
        amount: float = Body(..., description="金额"),
        blockchain: str = Body(..., description="区块链网络"),
        current_user=Depends(jwt_required)
):
    """
    创建x402支付通道

    用于微支付场景
    """
    try:
        result = await unified_payment_service.create_payment_channel(
            sender_address=sender_address,
            receiver_address=receiver_address,
            amount=amount,
            blockchain=blockchain,
        )

        return ApiResponse(
            success=result.get("success", False),
            data=result,
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
        )


@router.post("/x402/payment")
async def process_x402_payment(
        channel_id: str = Body(..., description="通道ID"),
        amount: float = Body(..., description="支付金额"),
        signature: str = Body(..., description="签名"),
        current_user=Depends(jwt_required)
):
    """
    处理x402微支付

    通过支付通道进行微支付
    """
    try:
        result = await unified_payment_service.process_micro_payment(
            channel_id=channel_id,
            amount=amount,
            signature=signature,
        )

        return ApiResponse(
            success=result.get("success", False),
            data=result,
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
        )


# ==================== NFT验证 API ====================

@router.post("/nft/verify")
async def verify_nft_ownership(
        wallet_address: str = Body(..., description="钱包地址"),
        contract_address: str = Body(..., description="NFT合约地址"),
        token_id: int = Body(None, description="Token ID（可选）"),
        current_user=Depends(jwt_required)
):
    """
    验证NFT所有权

    用于NFT门票和内容解锁
    """
    try:
        result = await unified_payment_service.verify_nft_ownership(
            wallet_address=wallet_address,
            contract_address=contract_address,
            token_id=token_id,
        )

        return ApiResponse(
            success=result.get("success", False),
            data=result,
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
        )


# ==================== 税务计算 API ====================

@router.post("/tax/calculate")
async def calculate_tax(
        amount: float = Body(..., description="金额"),
        country_code: str = Body(..., description="国家代码"),
        region_code: str = Body(None, description="地区代码"),
        has_vat_number: bool = Body(False, description="是否有VAT号"),
        vat_number: str = Body(None, description="VAT号"),
        current_user=Depends(jwt_required)
):
    """
    计算税务

    根据地区和税种计算税额
    """
    try:
        result = unified_payment_service.calculate_tax(
            amount=amount,
            country_code=country_code,
            region_code=region_code,
            has_vat_number=has_vat_number,
            vat_number=vat_number,
        )

        return ApiResponse(
            success=True,
            data=result,
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
        )


@router.get("/compliance/check")
async def check_compliance(current_user=Depends(jwt_required)):
    """
    检查合规性

    检查GDPR和PCI DSS合规状态
    """
    try:
        result = unified_payment_service.check_compliance()

        return ApiResponse(
            success=True,
            data=result,
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
        )


@router.get("/privacy-policy")
async def get_privacy_policy(current_user=Depends(jwt_required)):
    """
    获取隐私政策模板
    """
    try:
        company_info = {
            "name": "FastBlog",
            "contact_email": "privacy@fastblog.com",
            "address": "123 Main St, City, Country",
        }

        policy = unified_payment_service.generate_privacy_policy(company_info)

        return ApiResponse(
            success=True,
            data={"policy": policy},
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
        )


@router.get("/cookie-consent")
async def get_cookie_consent(current_user=Depends(jwt_required)):
    """
    获取Cookie同意弹窗HTML
    """
    try:
        html = unified_payment_service.get_cookie_consent_html()

        return ApiResponse(
            success=True,
            data={"html": html},
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
        )


# ==================== 购物车 API ====================

@router.post("/cart/add")
async def add_to_cart(
        product_id: int = Body(..., description="产品ID"),
        product_name: str = Body(..., description="产品名称"),
        unit_price: float = Body(..., description="单价"),
        quantity: int = Body(1, description="数量"),
        current_user=Depends(jwt_required)
):
    """
    添加商品到购物车
    """
    try:
        result = unified_payment_service.add_to_cart(
            user_id=current_user.id,
            product_id=product_id,
            product_name=product_name,
            unit_price=unit_price,
            quantity=quantity,
        )

        return ApiResponse(
            success=result.get("success", False),
            data=result,
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
        )


@router.delete("/cart/remove/{product_id}")
async def remove_from_cart(
        product_id: int,
        current_user=Depends(jwt_required)
):
    """
    从购物车移除商品
    """
    try:
        result = unified_payment_service.remove_from_cart(
            user_id=current_user.id,
            product_id=product_id,
        )

        return ApiResponse(
            success=result.get("success", False),
            data=result,
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
        )


@router.put("/cart/update")
async def update_cart_quantity(
        product_id: int = Body(..., description="产品ID"),
        quantity: int = Body(..., description="数量"),
        current_user=Depends(jwt_required)
):
    """
    更新购物车商品数量
    """
    try:
        result = unified_payment_service.update_cart_quantity(
            user_id=current_user.id,
            product_id=product_id,
            quantity=quantity,
        )

        return ApiResponse(
            success=result.get("success", False),
            data=result,
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
        )


@router.get("/cart")
async def get_cart(current_user=Depends(jwt_required)):
    """
    获取购物车
    """
    try:
        result = unified_payment_service.get_cart(current_user.id)

        return ApiResponse(
            success=result.get("success", False),
            data=result,
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
        )


@router.post("/cart/checkout")
async def checkout_from_cart(
        currency: str = Body("USD", description="货币类型"),
        shipping_address: dict = Body(None, description="收货地址"),
        billing_address: dict = Body(None, description="账单地址"),
        notes: str = Body("", description="备注"),
        current_user=Depends(jwt_required)
):
    """
    从购物车结算

    创建订单并清空购物车
    """
    try:
        result = unified_payment_service.checkout_from_cart(
            user_id=current_user.id,
            currency=currency,
            shipping_address=shipping_address,
            billing_address=billing_address,
            notes=notes,
        )

        return ApiResponse(
            success=result.get("success", False),
            data=result,
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
        )


# ==================== 订单管理 API ====================

@router.post("/order/create")
async def create_order(
        items: list = Body(..., description="商品列表"),
        currency: str = Body("USD", description="货币类型"),
        shipping_address: dict = Body(None, description="收货地址"),
        billing_address: dict = Body(None, description="账单地址"),
        notes: str = Body("", description="备注"),
        current_user=Depends(jwt_required)
):
    """
    创建订单

    直接创建订单（不使用购物车）
    """
    try:
        result = unified_payment_service.create_order(
            user_id=current_user.id,
            items=items,
            currency=currency,
            shipping_address=shipping_address,
            billing_address=billing_address,
            notes=notes,
        )

        return ApiResponse(
            success=result.get("success", False),
            data=result,
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
        )


@router.get("/order/{order_id}")
async def get_order_detail(
        order_id: str,
        current_user=Depends(jwt_required)
):
    """
    获取订单详情
    """
    try:
        result = unified_payment_service.get_order(order_id)

        return ApiResponse(
            success=result.get("success", False),
            data=result,
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
        )


@router.get("/orders")
async def get_user_orders(
        status: str = Body(None, description="订单状态过滤"),
        current_user=Depends(jwt_required)
):
    """
    获取用户订单列表
    """
    try:
        result = unified_payment_service.get_user_orders(
            user_id=current_user.id,
            status=status,
        )

        return ApiResponse(
            success=result.get("success", False),
            data=result,
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
        )


@router.post("/order/{order_id}/cancel")
async def cancel_order(
        order_id: str,
        reason: str = Body("", description="取消原因"),
        current_user=Depends(jwt_required)
):
    """
    取消订单
    """
    try:
        result = unified_payment_service.cancel_order(
            order_id=order_id,
            reason=reason,
        )

        return ApiResponse(
            success=result.get("success", False),
            data=result,
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
        )


@router.post("/order/{order_id}/refund")
async def refund_order(
        order_id: str,
        amount: float = Body(None, description="退款金额（可选，默认全额）"),
        current_user=Depends(jwt_required)
):
    """
    退款
    """
    try:
        result = unified_payment_service.refund_order(
            order_id=order_id,
            amount=amount,
        )

        return ApiResponse(
            success=result.get("success", False),
            data=result,
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
        )


@router.get("/orders/statistics")
async def get_order_statistics(current_user=Depends(jwt_required)):
    """
    获取订单统计信息
    """
    try:
        result = unified_payment_service.get_order_statistics(
            user_id=current_user.id,
        )

        return ApiResponse(
            success=result.get("success", False),
            data=result,
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
        )
