"""
统一支付服务

整合所有支付相关功能，提供统一的API接口

功能:
1. 传统支付网关（Stripe, PayPal, 支付宝, 微信）
2. 加密货币支付（BTC, ETH, USDT, USDC等）
3. x402微支付协议
4. NFT门票验证
5. 税务计算和合规性
6. 订单管理
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from .payment_gateway import PaymentManager, PaymentMethod, Order as GatewayOrder
from .crypto_payment import (
    CryptoPaymentManager,
    Blockchain,
    TokenSymbol,
)
from .tax_compliance import TaxComplianceService
from .order_management import OrderManager, OrderItem, OrderStatus

# 导出全局实例
from .payment_gateway import payment_manager
from .crypto_payment import crypto_payment_manager
from .tax_compliance import tax_compliance_service
from .order_management import order_manager

__all__ = [
    'UnifiedPaymentService',
    'unified_payment_service',
    'payment_manager',
    'crypto_payment_manager',
    'tax_compliance_service',
    'order_manager',
    'PaymentMethod',
    'Blockchain',
    'TokenSymbol',
    'OrderStatus',
    'OrderItem',
]


class UnifiedPaymentService:
    """
    统一支付服务
    
    整合所有支付相关功能
    """

    def __init__(self):
        self.payment_manager = PaymentManager()
        self.crypto_payment_manager = CryptoPaymentManager()
        self.tax_service = TaxComplianceService()
        self.order_manager = OrderManager()

    # ==================== 订单管理 ====================

    def create_order(
            self,
            user_id: int,
            items: List[Dict[str, Any]],
            currency: str = "USD",
            shipping_address: Dict[str, Any] = None,
            billing_address: Dict[str, Any] = None,
            notes: str = ""
    ) -> Dict[str, Any]:
        """
        创建订单
        
        Args:
            user_id: 用户ID
            items: 商品列表，每项包含 product_id, product_name, quantity, unit_price
            currency: 货币类型
            shipping_address: 收货地址
            billing_address: 账单地址
            notes: 备注
            
        Returns:
            订单信息
        """
        order_items = [
            OrderItem(
                product_id=item["product_id"],
                product_name=item["product_name"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                metadata=item.get("metadata"),
            )
            for item in items
        ]

        order = self.order_manager.create_order(
            user_id=user_id,
            items=order_items,
            currency=currency,
            shipping_address=shipping_address,
            billing_address=billing_address,
            notes=notes,
        )

        return {
            "success": True,
            "order": order.to_dict(),
        }

    def get_order(self, order_id: str) -> Dict[str, Any]:
        """获取订单详情"""
        order = self.order_manager.get_order(order_id)

        if not order:
            return {"success": False, "error": "Order not found"}

        return {"success": True, "order": order.to_dict()}

    def get_user_orders(
            self,
            user_id: int,
            status: str = None
    ) -> Dict[str, Any]:
        """获取用户订单列表"""
        order_status = OrderStatus(status) if status else None
        orders = self.order_manager.get_user_orders(user_id, order_status)

        return {
            "success": True,
            "orders": [order.to_dict() for order in orders],
            "total": len(orders),
        }

    # ==================== 传统支付 ====================

    async def process_traditional_payment(
            self,
            order_id: str,
            payment_method: str,
            **kwargs
    ) -> Dict[str, Any]:
        """
        处理传统支付
        
        Args:
            order_id: 订单ID
            payment_method: 支付方式 (stripe, paypal, alipay, wechat)
            **kwargs: 支付参数
            
        Returns:
            支付结果
        """
        order = self.order_manager.get_order(order_id)

        if not order:
            return {"success": False, "error": "Order not found"}

        # 映射支付方式
        method_map = {
            "stripe": PaymentMethod.STRIPE,
            "paypal": PaymentMethod.PAYPAL,
            "alipay": PaymentMethod.ALIPAY,
            "wechat": PaymentMethod.WECHAT,
        }

        if payment_method not in method_map:
            return {"success": False, "error": f"Unsupported payment method: {payment_method}"}

        # 创建网关订单
        gateway_order = GatewayOrder(
            order_id=order_id,
            user_id=order.user_id,
            amount=order.total_amount,
            currency=order.currency,
            description=f"Order {order_id}",
            payment_method=method_map[payment_method],
        )

        # 处理支付
        result = await self.payment_manager.process_payment(gateway_order, **kwargs)

        if result.get("success"):
            # 更新订单状态
            transaction_id = result.get("transaction_id", "")
            self.order_manager.process_payment(order_id, transaction_id, payment_method)

        return result

    # ==================== 加密货币支付 ====================

    async def create_crypto_payment(
            self,
            order_id: str,
            blockchain: str,
            token_symbol: str
    ) -> Dict[str, Any]:
        """
        创建加密货币支付
        
        Args:
            order_id: 订单ID
            blockchain: 区块链网络 (ethereum, bitcoin, polygon, bsc, solana)
            token_symbol: 代币符号 (ETH, BTC, USDT, USDC, etc.)
            
        Returns:
            支付请求信息
        """
        order = self.order_manager.get_order(order_id)

        if not order:
            return {"success": False, "error": "Order not found"}

        try:
            blockchain_enum = Blockchain(blockchain.lower())
            token_enum = TokenSymbol(token_symbol.upper())
        except ValueError as e:
            return {"success": False, "error": f"Invalid blockchain or token: {str(e)}"}

        result = await self.crypto_payment_manager.create_crypto_payment(
            order_id=order_id,
            user_id=order.user_id,
            amount_usd=order.total_amount,
            blockchain=blockchain_enum,
            token_symbol=token_enum,
        )

        return result

    async def check_crypto_payment_status(self, order_id: str) -> Dict[str, Any]:
        """检查加密货币支付状态"""
        return await self.crypto_payment_manager.check_payment_status(order_id)

    # ==================== x402微支付 ====================

    async def create_payment_channel(
            self,
            sender_address: str,
            receiver_address: str,
            amount: float,
            blockchain: str
    ) -> Dict[str, Any]:
        """创建x402支付通道"""
        try:
            blockchain_enum = Blockchain(blockchain.lower())
        except ValueError:
            return {"success": False, "error": "Invalid blockchain"}

        return await self.crypto_payment_manager.x402_handler.create_payment_channel(
            sender_address=sender_address,
            receiver_address=receiver_address,
            amount=amount,
            blockchain=blockchain_enum,
        )

    async def process_micro_payment(
            self,
            channel_id: str,
            amount: float,
            signature: str
    ) -> Dict[str, Any]:
        """处理x402微支付"""
        return await self.crypto_payment_manager.x402_handler.process_micro_payment(
            channel_id=channel_id,
            amount=amount,
            signature=signature,
        )

    # ==================== NFT验证 ====================

    def register_nft_contract(
            self,
            contract_address: str,
            blockchain: str,
            name: str,
            required_token_ids: List[int] = None
    ) -> Dict[str, Any]:
        """注册NFT合约"""
        try:
            blockchain_enum = Blockchain(blockchain.lower())
        except ValueError:
            return {"success": False, "error": "Invalid blockchain"}

        self.crypto_payment_manager.nft_verifier.register_nft_contract(
            contract_address=contract_address,
            blockchain=blockchain_enum,
            name=name,
            required_token_ids=required_token_ids,
        )

        return {"success": True, "message": "NFT contract registered"}

    async def verify_nft_ownership(
            self,
            wallet_address: str,
            contract_address: str,
            token_id: int = None
    ) -> Dict[str, Any]:
        """验证NFT所有权"""
        is_owner = await self.crypto_payment_manager.nft_verifier.verify_nft_ownership(
            wallet_address=wallet_address,
            contract_address=contract_address,
            token_id=token_id,
        )

        return {
            "success": True,
            "is_owner": is_owner,
            "wallet_address": wallet_address,
            "contract_address": contract_address,
        }

    # ==================== 税务计算 ====================

    def calculate_tax(
            self,
            amount: float,
            country_code: str,
            region_code: str = None,
            has_vat_number: bool = False,
            vat_number: str = None
    ) -> Dict[str, Any]:
        """
        计算税务
        
        Args:
            amount: 金额
            country_code: 国家代码
            region_code: 地区代码
            has_vat_number: 是否有VAT号
            vat_number: VAT号
            
        Returns:
            税务计算结果
        """
        customer_info = {
            "country_code": country_code,
            "region_code": region_code,
            "has_vat_number": has_vat_number,
            "vat_number": vat_number,
        }

        return self.tax_service.process_transaction_with_tax(amount, customer_info)

    def generate_privacy_policy(self, company_info: Dict[str, Any]) -> str:
        """生成隐私政策"""
        return self.tax_service.compliance_manager.generate_privacy_policy(company_info)

    def get_cookie_consent_html(self) -> str:
        """获取Cookie同意弹窗HTML"""
        return self.tax_service.compliance_manager.generate_cookie_consent_html()

    def check_compliance(self) -> Dict[str, Any]:
        """检查合规性"""
        gdpr_check = self.tax_service.compliance_manager.check_gdpr_compliance({})
        pci_check = self.tax_service.compliance_manager.check_pci_dss_compliance()

        return {
            "gdpr": gdpr_check,
            "pci_dss": pci_check,
        }

    # ==================== 购物车管理 ====================

    def add_to_cart(
            self,
            user_id: int,
            product_id: int,
            product_name: str,
            unit_price: float,
            quantity: int = 1,
            metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """添加商品到购物车"""
        cart = self.order_manager.get_cart(user_id)
        cart.add_item(product_id, product_name, unit_price, quantity, metadata)

        return {
            "success": True,
            "cart": cart.to_dict(),
        }

    def remove_from_cart(self, user_id: int, product_id: int) -> Dict[str, Any]:
        """从购物车移除商品"""
        cart = self.order_manager.get_cart(user_id)
        cart.remove_item(product_id)

        return {
            "success": True,
            "cart": cart.to_dict(),
        }

    def update_cart_quantity(
            self,
            user_id: int,
            product_id: int,
            quantity: int
    ) -> Dict[str, Any]:
        """更新购物车商品数量"""
        cart = self.order_manager.get_cart(user_id)
        cart.update_quantity(product_id, quantity)

        return {
            "success": True,
            "cart": cart.to_dict(),
        }

    def get_cart(self, user_id: int) -> Dict[str, Any]:
        """获取购物车"""
        cart = self.order_manager.get_cart(user_id)

        return {
            "success": True,
            "cart": cart.to_dict(),
        }

    def checkout_from_cart(
            self,
            user_id: int,
            currency: str = "USD",
            shipping_address: Dict[str, Any] = None,
            billing_address: Dict[str, Any] = None,
            notes: str = ""
    ) -> Dict[str, Any]:
        """从购物车结算"""
        order = self.order_manager.create_order_from_cart(
            user_id=user_id,
            currency=currency,
            shipping_address=shipping_address,
            billing_address=billing_address,
            notes=notes,
        )

        if not order:
            return {"success": False, "error": "Cart is empty"}

        return {
            "success": True,
            "order": order.to_dict(),
        }

    # ==================== 订单操作 ====================

    def cancel_order(self, order_id: str, reason: str = "") -> Dict[str, Any]:
        """取消订单"""
        success = self.order_manager.cancel_order(order_id, reason)

        if not success:
            return {"success": False, "error": "Failed to cancel order"}

        return {"success": True, "message": "Order cancelled"}

    def refund_order(
            self,
            order_id: str,
            amount: float = None
    ) -> Dict[str, Any]:
        """退款"""
        result = self.order_manager.refund_order(order_id, amount)

        if not result:
            return {"success": False, "error": "Failed to refund order"}

        return {"success": True, "refund": result}

    def get_order_statistics(self, user_id: int = None) -> Dict[str, Any]:
        """获取订单统计"""
        stats = self.order_manager.get_order_statistics(user_id)

        return {
            "success": True,
            "statistics": stats,
        }


# 全局实例
unified_payment_service = UnifiedPaymentService()
