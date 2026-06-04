"""
支付服务

支持多种支付网关：Stripe、PayPal、支付宝、微信支付
"""
import json

from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.order import Order

from src.unified_logger import default_logger as logger


class PaymentService:
    """支付服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_payment_intent(self, order_id: int, payment_method: str, amount: Decimal, currency: str = 'CNY',
                                    metadata: Dict = None) -> Dict:
        """
        创建支付意图
        
        Args:
            order_id: 订单ID
            payment_method: 支付方式 (stripe/paypal/alipay/wechat)
            amount: 支付金额
            currency: 货币类型 (USD/CNY等)
            metadata: 额外元数据
            
        Returns:
            支付意图信息
        """
        # 获取订单
        stmt = select(Order).where(Order.id == order_id)
        result = await self.db.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            raise ValueError(f"Order {order_id} not found")

        # 根据支付方式创建支付意图
        if payment_method == 'stripe':
            return await self._create_stripe_payment(order, amount, currency, metadata)
        elif payment_method == 'paypal':
            return await self._create_paypal_payment(order, amount, currency, metadata)
        elif payment_method == 'alipay':
            return await self._create_alipay_payment(order, amount, currency, metadata)
        elif payment_method == 'wechat':
            return await self._create_wechat_payment(order, amount, currency, metadata)
        else:
            raise ValueError(f"Unsupported payment method: {payment_method}")

    async def _create_stripe_payment(self, order: Order, amount: Decimal, currency: str, metadata: Dict = None) -> Dict:
        """创建 Stripe 支付意图"""
        try:
            import stripe

            # 从环境变量或配置获取密钥
            stripe.api_key = "sk_test_your_stripe_secret_key"

            # 创建 PaymentIntent
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Stripe 使用最小货币单位（分）
                currency=currency.lower(),
                metadata={
                    'order_id': order.id,
                    'user_id': order.user_id or '',
                    **(metadata or {})
                },
                description=f"Order #{order.id}"
            )

            logger.info(f"Stripe payment intent created: {payment_intent.id}")

            return {
                'success': True,
                'payment_method': 'stripe',
                'client_secret': payment_intent.client_secret,
                'payment_intent_id': payment_intent.id,
                'amount': amount,
                'currency': currency,
                'status': 'requires_payment_method'
            }
        except ImportError:
            logger.warning("Stripe library not installed. Using mock payment.")
            return self._mock_payment_response('stripe', order, amount, currency)
        except Exception as e:
            logger.error(f"Stripe payment creation failed: {e}")
            raise

    async def _create_paypal_payment(self, order: Order, amount: Decimal, currency: str, metadata: Dict = None) -> Dict:
        """创建 PayPal 支付"""
        try:
            import paypalrestsdk

            # 配置 PayPal
            paypalrestsdk.configure({
                "mode": "sandbox",  # sandbox or live
                "client_id": "your_paypal_client_id",
                "client_secret": "your_paypal_client_secret"
            })

            # 创建支付
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {"payment_method": "paypal"},
                "redirect_urls": {
                    "return_url": f"https://yourdomain.com/payment/success?order_id={order.id}",
                    "cancel_url": f"https://yourdomain.com/payment/cancel?order_id={order.id}"
                },
                "transactions": [{
                    "amount": {
                        "total": str(amount),
                        "currency": currency
                    },
                    "description": f"Order #{order.id}",
                    "custom": json.dumps({'order_id': order.id, **(metadata or {})})
                }]
            })

            if payment.create():
                approval_url = next(link.href for link in payment.links if link.rel == "approval_url")

                return {
                    'success': True,
                    'payment_method': 'paypal',
                    'payment_id': payment.id,
                    'approval_url': approval_url,
                    'amount': amount,
                    'currency': currency,
                    'status': 'pending'
                }
            else:
                raise Exception(payment.error)

        except ImportError:
            logger.warning("PayPal SDK not installed. Using mock payment.")
            return self._mock_payment_response('paypal', order, amount, currency)
        except Exception as e:
            logger.error(f"PayPal payment creation failed: {e}")
            raise

    async def _create_alipay_payment(self, order: Order, amount: Decimal, currency: str, metadata: Dict = None) -> Dict:
        """创建支付宝支付"""
        try:
            from alipay import AliPay

            # 初始化支付宝
            app_private_key_string = open("path/to/app_private_key.pem").read()
            alipay_public_key_string = open("path/to/alipay_public_key.pem").read()

            alipay = AliPay(
                appid="your_alipay_appid",
                app_notify_url=None,
                app_private_key_string=app_private_key_string,
                alipay_public_key_string=alipay_public_key_string,
                sign_type="RSA2",
                debug=True  # False for production
            )

            # 生成支付链接
            order_string = alipay.api_alipay_trade_page_pay(
                out_trade_no=f"ORDER_{order.id}_{int(datetime.now().timestamp())}",
                total_amount=str(amount),
                subject=f"Order #{order.id}",
                return_url=f"https://yourdomain.com/payment/success?order_id={order.id}",
                notify_url="https://yourdomain.com/api/v1/payment/webhook/alipay"
            )

            pay_url = f"https://openapi.alipay.com/gateway.do?{order_string}"

            return {
                'success': True,
                'payment_method': 'alipay',
                'pay_url': pay_url,
                'out_trade_no': f"ORDER_{order.id}_{int(datetime.now().timestamp())}",
                'amount': amount,
                'currency': currency,
                'status': 'pending'
            }
        except ImportError:
            logger.warning("Alipay library not installed. Using mock payment.")
            return self._mock_payment_response('alipay', order, amount, currency)
        except Exception as e:
            logger.error(f"Alipay payment creation failed: {e}")
            raise

    async def _create_wechat_payment(self, order: Order, amount: Decimal, currency: str, metadata: Dict = None) -> Dict:
        """创建微信支付"""
        try:
            from wechatpy.pay import WeChatPay

            # 初始化微信支付
            pay = WeChatPay(
                appid="your_wechat_appid",
                api_key="your_wechat_api_key",
                mch_id="your_wechat_mch_id",
                mch_cert="path/to/apiclient_cert.pem",
                mch_key="path/to/apiclient_key.pem"
            )

            # 创建统一下单
            result = pay.order.create(
                trade_type="NATIVE",  # NATIVE for QR code, JSAPI for in-app
                body=f"Order #{order.id}",
                total_fee=int(amount * 100),  # 微信使用分
                notify_url="https://yourdomain.com/api/v1/payment/webhook/wechat",
                out_trade_no=f"ORDER_{order.id}_{int(datetime.now().timestamp())}",
                spbill_create_ip="127.0.0.1"
            )

            return {
                'success': True,
                'payment_method': 'wechat',
                'code_url': result.get('code_url'),  # QR code URL for NATIVE payment
                'prepay_id': result.get('prepay_id'),
                'out_trade_no': f"ORDER_{order.id}_{int(datetime.now().timestamp())}",
                'amount': amount,
                'currency': currency,
                'status': 'pending'
            }
        except ImportError:
            logger.warning("WeChat Pay library not installed. Using mock payment.")
            return self._mock_payment_response('wechat', order, amount, currency)
        except Exception as e:
            logger.error(f"WeChat payment creation failed: {e}")
            raise

    async def verify_payment(self, payment_method: str, payment_data: Dict) -> Dict:
        """
        验证支付结果
        
        Args:
            payment_method: 支付方式
            payment_data: 支付回调数据
            
        Returns:
            验证结果
        """
        if payment_method == 'stripe':
            return await self._verify_stripe_payment(payment_data)
        elif payment_method == 'paypal':
            return await self._verify_paypal_payment(payment_data)
        elif payment_method == 'alipay':
            return await self._verify_alipay_payment(payment_data)
        elif payment_method == 'wechat':
            return await self._verify_wechat_payment(payment_data)
        else:
            raise ValueError(f"Unsupported payment method: {payment_method}")

    async def _verify_stripe_payment(self, payment_data: Dict) -> Dict:
        """验证 Stripe 支付"""
        try:
            import stripe
            stripe.api_key = "sk_test_your_stripe_secret_key"

            payment_intent_id = payment_data.get('payment_intent_id')
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            if payment_intent.status == 'succeeded':
                return {
                    'verified': True,
                    'status': 'completed',
                    'transaction_id': payment_intent.id,
                    'amount': Decimal(str(payment_intent.amount)) / 100,
                    'currency': payment_intent.currency.upper(),
                    'paid_at': datetime.fromtimestamp(payment_intent.created)
                }
            else:
                return {
                    'verified': False,
                    'status': payment_intent.status,
                    'message': f'Payment status: {payment_intent.status}'
                }
        except Exception as e:
            logger.error(f"Stripe payment verification failed: {e}")
            return {'verified': False, 'error': str(e)}

    async def _verify_paypal_payment(self, payment_data: Dict) -> Dict:
        """验证 PayPal 支付"""
        try:
            import paypalrestsdk
            paypalrestsdk.configure({
                "mode": "sandbox",
                "client_id": "your_paypal_client_id",
                "client_secret": "your_paypal_client_secret"
            })

            payment_id = payment_data.get('payment_id')
            payer_id = payment_data.get('PayerID')

            payment = paypalrestsdk.Payment.find(payment_id)

            if payment.execute({"payer_id": payer_id}):
                return {
                    'verified': True,
                    'status': 'completed',
                    'transaction_id': payment.id,
                    'amount': Decimal(payment.transactions[0].amount.total),
                    'currency': payment.transactions[0].amount.currency,
                    'paid_at': datetime.now()
                }
            else:
                return {
                    'verified': False,
                    'status': 'failed',
                    'message': payment.error
                }
        except Exception as e:
            logger.error(f"PayPal payment verification failed: {e}")
            return {'verified': False, 'error': str(e)}

    async def _verify_alipay_payment(self, payment_data: Dict) -> Dict:
        """验证支付宝支付"""
        try:
            from alipay import AliPay

            app_private_key_string = open("path/to/app_private_key.pem").read()
            alipay_public_key_string = open("path/to/alipay_public_key.pem").read()

            alipay = AliPay(
                appid="your_alipay_appid",
                app_notify_url=None,
                app_private_key_string=app_private_key_string,
                alipay_public_key_string=alipay_public_key_string,
                sign_type="RSA2",
                debug=True
            )

            # 验证签名
            signature = payment_data.pop('sign', '')
            is_verified = alipay.verify(payment_data, signature)

            if is_verified and payment_data.get('trade_status') == 'TRADE_SUCCESS':
                return {
                    'verified': True,
                    'status': 'completed',
                    'transaction_id': payment_data.get('trade_no'),
                    'out_trade_no': payment_data.get('out_trade_no'),
                    'amount': Decimal(payment_data.get('total_amount', '0')),
                    'currency': 'CNY',
                    'paid_at': datetime.strptime(payment_data.get('gmt_payment', ''), '%Y-%m-%d %H:%M:%S')
                }
            else:
                return {
                    'verified': False,
                    'status': 'failed',
                    'message': 'Verification failed or trade not successful'
                }
        except Exception as e:
            logger.error(f"Alipay payment verification failed: {e}")
            return {'verified': False, 'error': str(e)}

    async def _verify_wechat_payment(self, payment_data: Dict) -> Dict:
        """验证微信支付"""
        try:
            from wechatpy.pay import WeChatPay

            pay = WeChatPay(
                appid="your_wechat_appid",
                api_key="your_wechat_api_key",
                mch_id="your_wechat_mch_id",
                mch_cert="path/to/apiclient_cert.pem",
                mch_key="path/to/apiclient_key.pem"
            )

            # 验证签名
            if pay.check_signature(payment_data):
                if payment_data.get('result_code') == 'SUCCESS':
                    return {
                        'verified': True,
                        'status': 'completed',
                        'transaction_id': payment_data.get('transaction_id'),
                        'out_trade_no': payment_data.get('out_trade_no'),
                        'amount': Decimal(str(int(payment_data.get('total_fee', 0))) / 100),
                        'currency': 'CNY',
                        'paid_at': datetime.strptime(payment_data.get('time_end', ''), '%Y%m%d%H%M%S')
                    }
                else:
                    return {
                        'verified': False,
                        'status': 'failed',
                        'message': payment_data.get('err_code_des', 'Payment failed')
                    }
            else:
                return {
                    'verified': False,
                    'status': 'failed',
                    'message': 'Signature verification failed'
                }
        except Exception as e:
            logger.error(f"WeChat payment verification failed: {e}")
            return {'verified': False, 'error': str(e)}

    async def process_refund(self, order_id: int, payment_method: str, amount: Optional[Decimal] = None,
                             reason: str = '') -> Dict:
        """
        处理退款
        
        Args:
            order_id: 订单ID
            payment_method: 支付方式
            amount: 退款金额（None表示全额退款）
            reason: 退款原因
            
        Returns:
            退款结果
        """
        # 获取订单
        stmt = select(Order).where(Order.id == order_id)
        result = await self.db.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            raise ValueError(f"Order {order_id} not found")

        refund_amount = amount or order.total_amount

        if payment_method == 'stripe':
            return await self._refund_stripe(order, refund_amount, reason)
        elif payment_method == 'paypal':
            return await self._refund_paypal(order, refund_amount, reason)
        elif payment_method == 'alipay':
            return await self._refund_alipay(order, refund_amount, reason)
        elif payment_method == 'wechat':
            return await self._refund_wechat(order, refund_amount, reason)
        else:
            raise ValueError(f"Unsupported payment method: {payment_method}")

    async def _refund_stripe(self, order: Order, amount: Decimal, reason: str) -> Dict:
        """Stripe 退款"""
        try:
            import stripe
            stripe.api_key = "sk_test_your_stripe_secret_key"

            refund = stripe.Refund.create(
                payment_intent=order.transaction_id,
                amount=int(amount * 100),
                reason='requested_by_customer' if reason else 'duplicate'
            )

            return {
                'success': True,
                'refund_id': refund.id,
                'amount': amount,
                'status': refund.status,
                'message': 'Refund processed successfully'
            }
        except Exception as e:
            logger.error(f"Stripe refund failed: {e}")
            return {'success': False, 'error': str(e)}

    async def _refund_paypal(self, order: Order, amount: Decimal, reason: str) -> Dict:
        """PayPal 退款"""
        try:
            import paypalrestsdk
            paypalrestsdk.configure({
                "mode": "sandbox",
                "client_id": "your_paypal_client_id",
                "client_secret": "your_paypal_client_secret"
            })

            sale = paypalrestsdk.Sale.find(order.transaction_id)
            refund = sale.refund({
                "amount": {
                    "total": str(amount),
                    "currency": order.currency
                }
            })

            if refund.success():
                return {
                    'success': True,
                    'refund_id': refund.id,
                    'amount': amount,
                    'status': 'completed',
                    'message': 'Refund processed successfully'
                }
            else:
                return {'success': False, 'error': refund.error}
        except Exception as e:
            logger.error(f"PayPal refund failed: {e}")
            return {'success': False, 'error': str(e)}

    async def _refund_alipay(self, order: Order, amount: Decimal, reason: str) -> Dict:
        """支付宝退款"""
        try:
            from alipay import AliPay

            app_private_key_string = open("path/to/app_private_key.pem").read()
            alipay_public_key_string = open("path/to/alipay_public_key.pem").read()

            alipay = AliPay(
                appid="your_alipay_appid",
                app_notify_url=None,
                app_private_key_string=app_private_key_string,
                alipay_public_key_string=alipay_public_key_string,
                sign_type="RSA2",
                debug=True
            )

            result = alipay.api_alipay_trade_refund(
                out_trade_no=order.transaction_id,
                refund_amount=str(amount),
                refund_reason=reason or 'Customer request'
            )

            if result.get('code') == '10000':
                return {
                    'success': True,
                    'refund_id': result.get('trade_no'),
                    'amount': amount,
                    'status': 'completed',
                    'message': 'Refund processed successfully'
                }
            else:
                return {'success': False, 'error': result.get('msg')}
        except Exception as e:
            logger.error(f"Alipay refund failed: {e}")
            return {'success': False, 'error': str(e)}

    async def _refund_wechat(self, order: Order, amount: Decimal, reason: str) -> Dict:
        """微信退款"""
        try:
            from wechatpy.pay import WeChatPay

            pay = WeChatPay(
                appid="your_wechat_appid",
                api_key="your_wechat_api_key",
                mch_id="your_wechat_mch_id",
                mch_cert="path/to/apiclient_cert.pem",
                mch_key="path/to/apiclient_key.pem"
            )

            result = pay.refund.apply(
                total_fee=int(order.total_amount * 100),
                refund_fee=int(amount * 100),
                out_refund_no=f"REFUND_{order.id}_{int(datetime.now().timestamp())}",
                out_trade_no=order.transaction_id,
                op_user_id='admin'
            )

            if result.get('return_code') == 'SUCCESS' and result.get('result_code') == 'SUCCESS':
                return {
                    'success': True,
                    'refund_id': result.get('refund_id'),
                    'amount': amount,
                    'status': 'processing',
                    'message': 'Refund submitted successfully'
                }
            else:
                return {'success': False, 'error': result.get('return_msg')}
        except Exception as e:
            logger.error(f"WeChat refund failed: {e}")
            return {'success': False, 'error': str(e)}

    def _mock_payment_response(self, payment_method: str, order: Order, amount: Decimal, currency: str) -> Dict:
        """模拟支付响应（用于开发测试）"""
        logger.info(f"Using mock payment for {payment_method}")

        return {
            'success': True,
            'payment_method': payment_method,
            'mock': True,
            'order_id': order.id,
            'amount': amount,
            'currency': currency,
            'status': 'pending',
            'message': f'Mock {payment_method} payment created for testing'
        }


def create_payment_service(db: AsyncSession) -> PaymentService:
    """创建支付服务实例"""
    return PaymentService(db)
