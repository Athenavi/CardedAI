"""
订单管理服务

处理订单创建、管理、状态跟踪等功能

功能:
1. 订单创建和管理
2. 订单状态跟踪
3. 购物车集成
4. 支付集成
5. 订单历史查询
6. 订单统计和分析
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    FAILED = "failed"


class PaymentStatus(Enum):
    """支付状态"""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class ShippingStatus(Enum):
    """物流状态"""
    NOT_SHIPPED = "not_shipped"
    SHIPPED = "shipped"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    RETURNED = "returned"


class OrderItem:
    """订单项"""

    def __init__(
            self,
            product_id: int,
            product_name: str,
            quantity: int,
            unit_price: float,
            metadata: Dict[str, Any] = None
    ):
        self.product_id = product_id
        self.product_name = product_name
        self.quantity = quantity
        self.unit_price = unit_price
        self.total_price = quantity * unit_price
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total_price": self.total_price,
            "metadata": self.metadata,
        }


class Order:
    """订单"""

    def __init__(
            self,
            user_id: int,
            items: List[OrderItem],
            currency: str = "USD",
            shipping_address: Dict[str, Any] = None,
            billing_address: Dict[str, Any] = None,
            notes: str = ""
    ):
        self.order_id = f"ORD-{uuid.uuid4().hex[:12].upper()}"
        self.user_id = user_id
        self.items = items
        self.currency = currency
        self.shipping_address = shipping_address
        self.billing_address = billing_address
        self.notes = notes

        # 计算总额
        self.subtotal = sum(item.total_price for item in items)
        self.tax_amount = 0.0
        self.shipping_cost = 0.0
        self.discount = 0.0
        self.total_amount = self.subtotal

        # 状态
        self.status = OrderStatus.PENDING
        self.payment_status = PaymentStatus.PENDING
        self.shipping_status = ShippingStatus.NOT_SHIPPED

        # 时间戳
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.paid_at = None
        self.shipped_at = None
        self.delivered_at = None
        self.cancelled_at = None

        # 支付信息
        self.payment_method = None
        self.payment_transaction_id = None
        self.payment_gateway_id = None

    def calculate_total(self, tax_rate: float = 0.0, shipping_cost: float = 0.0, discount: float = 0.0):
        """计算订单总额"""
        self.tax_amount = round(self.subtotal * (tax_rate / 100), 2)
        self.shipping_cost = shipping_cost
        self.discount = discount
        self.total_amount = round(self.subtotal + self.tax_amount + self.shipping_cost - self.discount, 2)

    def add_item(self, item: OrderItem):
        """添加订单项"""
        self.items.append(item)
        self.subtotal = sum(item.total_price for item in self.items)
        self.calculate_total()

    def remove_item(self, product_id: int):
        """移除订单项"""
        self.items = [item for item in self.items if item.product_id != product_id]
        self.subtotal = sum(item.total_price for item in self.items)
        self.calculate_total()

    def update_status(self, status: OrderStatus):
        """更新订单状态"""
        self.status = status
        self.updated_at = datetime.now()

        if status == OrderStatus.CANCELLED:
            self.cancelled_at = datetime.now()

    def mark_as_paid(self, transaction_id: str, payment_method: str):
        """标记为已支付"""
        self.payment_status = PaymentStatus.PAID
        self.payment_transaction_id = transaction_id
        self.payment_method = payment_method
        self.paid_at = datetime.now()
        self.status = OrderStatus.PROCESSING
        self.updated_at = datetime.now()

    def mark_as_shipped(self):
        """标记为已发货"""
        self.shipping_status = ShippingStatus.SHIPPED
        self.shipped_at = datetime.now()
        self.updated_at = datetime.now()

    def mark_as_delivered(self):
        """标记为已送达"""
        self.shipping_status = ShippingStatus.DELIVERED
        self.delivered_at = datetime.now()
        self.status = OrderStatus.COMPLETED
        self.updated_at = datetime.now()

    def cancel(self, reason: str = ""):
        """取消订单"""
        if self.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
            raise ValueError("Cannot cancel order in current status")

        self.status = OrderStatus.CANCELLED
        self.cancelled_at = datetime.now()
        self.updated_at = datetime.now()

        if reason:
            self.notes = f"{self.notes}\nCancellation reason: {reason}" if self.notes else f"Cancellation reason: {reason}"

    def refund(self, amount: float = None):
        """退款"""
        if self.payment_status != PaymentStatus.PAID:
            raise ValueError("Can only refund paid orders")

        refund_amount = amount if amount else self.total_amount

        if amount and amount < self.total_amount:
            self.payment_status = PaymentStatus.PARTIALLY_REFUNDED
        else:
            self.payment_status = PaymentStatus.REFUNDED
            self.status = OrderStatus.REFUNDED

        self.updated_at = datetime.now()

        return {
            "refund_amount": refund_amount,
            "original_amount": self.total_amount,
            "payment_status": self.payment_status.value,
            "order_status": self.status.value,
        }

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "items": [item.to_dict() for item in self.items],
            "currency": self.currency,
            "subtotal": self.subtotal,
            "tax_amount": self.tax_amount,
            "shipping_cost": self.shipping_cost,
            "discount": self.discount,
            "total_amount": self.total_amount,
            "status": self.status.value,
            "payment_status": self.payment_status.value,
            "shipping_status": self.shipping_status.value,
            "shipping_address": self.shipping_address,
            "billing_address": self.billing_address,
            "notes": self.notes,
            "payment_method": self.payment_method,
            "payment_transaction_id": self.payment_transaction_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "shipped_at": self.shipped_at.isoformat() if self.shipped_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
        }


class ShoppingCart:
    """购物车"""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.items: Dict[int, Dict[str, Any]] = {}
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def add_item(
            self,
            product_id: int,
            product_name: str,
            unit_price: float,
            quantity: int = 1,
            metadata: Dict[str, Any] = None
    ):
        """添加商品到购物车"""
        if product_id in self.items:
            self.items[product_id]["quantity"] += quantity
        else:
            self.items[product_id] = {
                "product_id": product_id,
                "product_name": product_name,
                "unit_price": unit_price,
                "quantity": quantity,
                "metadata": metadata or {},
            }

        self.updated_at = datetime.now()

    def remove_item(self, product_id: int):
        """从购物车移除商品"""
        if product_id in self.items:
            del self.items[product_id]
            self.updated_at = datetime.now()

    def update_quantity(self, product_id: int, quantity: int):
        """更新商品数量"""
        if product_id in self.items:
            if quantity <= 0:
                self.remove_item(product_id)
            else:
                self.items[product_id]["quantity"] = quantity
                self.updated_at = datetime.now()

    def clear(self):
        """清空购物车"""
        self.items.clear()
        self.updated_at = datetime.now()

    def get_total(self) -> float:
        """获取购物车总额"""
        return sum(
            item["unit_price"] * item["quantity"]
            for item in self.items.values()
        )

    def get_item_count(self) -> int:
        """获取商品总数"""
        return sum(item["quantity"] for item in self.items.values())

    def is_empty(self) -> bool:
        """检查购物车是否为空"""
        return len(self.items) == 0

    def to_order_items(self) -> List[OrderItem]:
        """转换为订单项列表"""
        return [
            OrderItem(
                product_id=item["product_id"],
                product_name=item["product_name"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                metadata=item.get("metadata"),
            )
            for item in self.items.values()
        ]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "items": list(self.items.values()),
            "total": self.get_total(),
            "item_count": self.get_item_count(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class OrderManager:
    """
    订单管理器
    
    统一管理订单和购物车
    """

    def __init__(self):
        self.orders: Dict[str, Order] = {}
        self.carts: Dict[int, ShoppingCart] = {}

    def get_cart(self, user_id: int) -> ShoppingCart:
        """获取用户购物车"""
        if user_id not in self.carts:
            self.carts[user_id] = ShoppingCart(user_id)
        return self.carts[user_id]

    def create_order_from_cart(
            self,
            user_id: int,
            currency: str = "USD",
            shipping_address: Dict[str, Any] = None,
            billing_address: Dict[str, Any] = None,
            notes: str = ""
    ) -> Optional[Order]:
        """
        从购物车创建订单
        
        Args:
            user_id: 用户ID
            currency: 货币类型
            shipping_address: 收货地址
            billing_address: 账单地址
            notes: 备注
            
        Returns:
            创建的订单，如果购物车为空则返回None
        """
        cart = self.get_cart(user_id)

        if cart.is_empty():
            return None

        # 创建订单项
        items = cart.to_order_items()

        # 创建订单
        order = Order(
            user_id=user_id,
            items=items,
            currency=currency,
            shipping_address=shipping_address,
            billing_address=billing_address,
            notes=notes,
        )

        # 保存订单
        self.orders[order.order_id] = order

        # 清空购物车
        cart.clear()

        return order

    def create_order(
            self,
            user_id: int,
            items: List[OrderItem],
            currency: str = "USD",
            shipping_address: Dict[str, Any] = None,
            billing_address: Dict[str, Any] = None,
            notes: str = ""
    ) -> Order:
        """
        直接创建订单
        
        Args:
            user_id: 用户ID
            items: 订单项列表
            currency: 货币类型
            shipping_address: 收货地址
            billing_address: 账单地址
            notes: 备注
            
        Returns:
            创建的订单
        """
        order = Order(
            user_id=user_id,
            items=items,
            currency=currency,
            shipping_address=shipping_address,
            billing_address=billing_address,
            notes=notes,
        )

        self.orders[order.order_id] = order

        return order

    def get_order(self, order_id: str) -> Optional[Order]:
        """获取订单"""
        return self.orders.get(order_id)

    def get_user_orders(self, user_id: int, status: OrderStatus = None) -> List[Order]:
        """
        获取用户订单列表
        
        Args:
            user_id: 用户ID
            status: 订单状态过滤（可选）
            
        Returns:
            订单列表
        """
        user_orders = [
            order for order in self.orders.values()
            if order.user_id == user_id
        ]

        if status:
            user_orders = [order for order in user_orders if order.status == status]

        # 按创建时间倒序排序
        user_orders.sort(key=lambda x: x.created_at, reverse=True)

        return user_orders

    def update_order_status(self, order_id: str, status: OrderStatus) -> bool:
        """
        更新订单状态
        
        Args:
            order_id: 订单ID
            status: 新状态
            
        Returns:
            是否成功更新
        """
        order = self.get_order(order_id)
        if not order:
            return False

        order.update_status(status)
        return True

    def process_payment(
            self,
            order_id: str,
            transaction_id: str,
            payment_method: str
    ) -> bool:
        """
        处理支付
        
        Args:
            order_id: 订单ID
            transaction_id: 交易ID
            payment_method: 支付方式
            
        Returns:
            是否成功处理
        """
        order = self.get_order(order_id)
        if not order:
            return False

        order.mark_as_paid(transaction_id, payment_method)
        return True

    def ship_order(self, order_id: str) -> bool:
        """
        发货
        
        Args:
            order_id: 订单ID
            
        Returns:
            是否成功发货
        """
        order = self.get_order(order_id)
        if not order:
            return False

        if order.status not in [OrderStatus.PROCESSING]:
            return False

        order.mark_as_shipped()
        return True

    def deliver_order(self, order_id: str) -> bool:
        """
        标记为已送达
        
        Args:
            order_id: 订单ID
            
        Returns:
            是否成功标记
        """
        order = self.get_order(order_id)
        if not order:
            return False

        if order.shipping_status != ShippingStatus.SHIPPED:
            return False

        order.mark_as_delivered()
        return True

    def cancel_order(self, order_id: str, reason: str = "") -> bool:
        """
        取消订单
        
        Args:
            order_id: 订单ID
            reason: 取消原因
            
        Returns:
            是否成功取消
        """
        order = self.get_order(order_id)
        if not order:
            return False

        try:
            order.cancel(reason)
            return True
        except ValueError:
            return False

    def refund_order(
            self,
            order_id: str,
            amount: float = None
    ) -> Optional[Dict[str, Any]]:
        """
        退款
        
        Args:
            order_id: 订单ID
            amount: 退款金额（可选，默认为全额）
            
        Returns:
            退款结果
        """
        order = self.get_order(order_id)
        if not order:
            return None

        try:
            return order.refund(amount)
        except ValueError:
            return None

    def get_order_statistics(self, user_id: int = None) -> Dict[str, Any]:
        """
        获取订单统计信息
        
        Args:
            user_id: 用户ID（可选，不提供则统计所有订单）
            
        Returns:
            统计信息
        """
        orders = self.orders.values()

        if user_id:
            orders = [order for order in orders if order.user_id == user_id]

        total_orders = len(orders)
        total_revenue = sum(order.total_amount for order in orders)

        status_counts = {}
        for order in orders:
            status = order.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_orders": total_orders,
            "total_revenue": round(total_revenue, 2),
            "average_order_value": round(total_revenue / total_orders, 2) if total_orders > 0 else 0,
            "status_breakdown": status_counts,
        }

    def search_orders(
            self,
            user_id: int = None,
            status: OrderStatus = None,
            date_from: datetime = None,
            date_to: datetime = None,
            min_amount: float = None,
            max_amount: float = None
    ) -> List[Order]:
        """
        搜索订单
        
        Args:
            user_id: 用户ID
            status: 订单状态
            date_from: 开始日期
            date_to: 结束日期
            min_amount: 最小金额
            max_amount: 最大金额
            
        Returns:
            匹配的订单列表
        """
        results = list(self.orders.values())

        if user_id:
            results = [order for order in results if order.user_id == user_id]

        if status:
            results = [order for order in results if order.status == status]

        if date_from:
            results = [order for order in results if order.created_at >= date_from]

        if date_to:
            results = [order for order in results if order.created_at <= date_to]

        if min_amount is not None:
            results = [order for order in results if order.total_amount >= min_amount]

        if max_amount is not None:
            results = [order for order in results if order.total_amount <= max_amount]

        # 按创建时间倒序排序
        results.sort(key=lambda x: x.created_at, reverse=True)

        return results


# 全局实例
order_manager = OrderManager()
