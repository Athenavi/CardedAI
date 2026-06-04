"""
电子商务 API - 购物车和订单管理
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import Cart, CartItem, Product
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["ecommerce"])


# ==================== 购物车 API ====================

@router.get("")
async def get_cart(
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取用户购物车
    """
    try:
        # 查找或创建购物车
        query = select(Cart).where(Cart.user_id == current_user.id)
        result = await db.execute(query)
        cart = result.scalar_one_or_none()

        if not cart:
            # 创建新购物车
            cart = Cart(user_id=current_user.id)
            db.add(cart)
            await db.commit()
            await db.refresh(cart)

        # 获取购物车项
        items_query = (
            select(CartItem, Product)
            .join(Product, CartItem.product_id == Product.id)
            .where(CartItem.cart_id == cart.id)
        )
        items_result = await db.execute(items_query)
        items = items_result.all()

        cart_items = []
        total_amount = 0

        for cart_item, product in items:
            item_total = float(product.price) * cart_item.quantity
            total_amount += item_total

            cart_items.append({
                "id": cart_item.id,
                "product": product.to_dict(),
                "quantity": cart_item.quantity,
                "price": float(product.price),
                "total": item_total
            })

        return ApiResponse(
            success=True,
            data={
                "cart_id": cart.id,
                "items": cart_items,
                "total_amount": total_amount,
                "item_count": len(cart_items)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/items")
async def add_to_cart(
        item_data: dict,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    添加商品到购物车
    
    Args:
        item_data: {"product_id": 1, "quantity": 2}
    """
    try:
        product_id = item_data.get("product_id")
        quantity = item_data.get("quantity", 1)

        # 验证商品
        product_query = select(Product).where(
            Product.id == product_id,
            Product.is_active == True
        )
        product_result = await db.execute(product_query)
        product = product_result.scalar_one_or_none()

        if not product:
            return ApiResponse(success=False, error="商品不存在或已下架", data=None)

        # 检查库存
        if product.stock < quantity:
            return ApiResponse(success=False, error=f"库存不足,当前库存: {product.stock}", data=None)

        # 查找或创建购物车
        cart_query = select(Cart).where(Cart.user_id == current_user.id)
        cart_result = await db.execute(cart_query)
        cart = cart_result.scalar_one_or_none()

        if not cart:
            cart = Cart(user_id=current_user.id)
            db.add(cart)
            await db.flush()

        # 检查是否已存在该商品
        existing_query = select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == product_id
        )
        existing_result = await db.execute(existing_query)
        existing_item = existing_result.scalar_one_or_none()

        if existing_item:
            # 更新数量
            existing_item.quantity += quantity
            existing_item.updated_at = datetime.now()
        else:
            # 创建新购物车项
            new_item = CartItem(
                cart_id=cart.id,
                product_id=product_id,
                quantity=quantity,
                price=float(product.price)
            )
            db.add(new_item)

        await db.commit()

        return ApiResponse(
            success=True,
            message="已添加到购物车"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/items/{item_id}")
async def update_cart_item(
        item_id: int,
        item_data: dict,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    更新购物车项数量
    """
    try:
        quantity = item_data.get("quantity")

        if quantity is None or quantity < 1:
            return ApiResponse(success=False, error="无效的数量", data=None)

        # 查找购物车项
        query = (
            select(CartItem)
            .join(Cart, CartItem.cart_id == Cart.id)
            .where(
                CartItem.id == item_id,
                Cart.user_id == current_user.id
            )
        )
        result = await db.execute(query)
        cart_item = result.scalar_one_or_none()

        if not cart_item:
            return ApiResponse(success=False, error="购物车项不存在", data=None)

        # 检查库存
        product_query = select(Product).where(Product.id == cart_item.product_id)
        product_result = await db.execute(product_query)
        product = product_result.scalar_one_or_none()

        if product and product.stock < quantity:
            return ApiResponse(success=False, error=f"库存不足,当前库存: {product.stock}", data=None)

        cart_item.quantity = quantity
        cart_item.updated_at = datetime.now()

        await db.commit()

        return ApiResponse(success=True, message="购物车项已更新")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/items/{item_id}")
async def remove_from_cart(
        item_id: int,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    从购物车移除商品
    """
    try:
        query = (
            select(CartItem)
            .join(Cart, CartItem.cart_id == Cart.id)
            .where(
                CartItem.id == item_id,
                Cart.user_id == current_user.id
            )
        )
        result = await db.execute(query)
        cart_item = result.scalar_one_or_none()

        if not cart_item:
            return ApiResponse(success=False, error="购物车项不存在", data=None)

        await db.delete(cart_item)
        await db.commit()

        return ApiResponse(success=True, message="已从购物车移除")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 订单 API ====================
# 注意：订单相关端点已移至 ecommerce_orders.py
# 通过 /api/v2/shop/orders 访问
