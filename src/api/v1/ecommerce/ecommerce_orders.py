"""
电子商务 API - 订单管理
从 ecommerce_cart.py 中分离出来，使购物车和订单职责更清晰
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import Order, OrderItem, Product
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["ecommerce-orders"])


@router.get("/")
async def list_orders(
        page: int = Query(1, ge=1, description="页码"),
        per_page: int = Query(10, ge=1, le=100, description="每页数量"),
        status: Optional[str] = Query(None, description="订单状态"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取用户订单列表
    """
    try:
        query = select(Order).where(Order.user_id == current_user.id)

        if status:
            query = query.where(Order.status == status)

        query = query.order_by(Order.created_at.desc())

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # 分页
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        result = await db.execute(query)
        orders = result.scalars().all()

        orders_data = [order.to_dict() for order in orders]

        return ApiResponse(
            success=True,
            data={
                "orders": orders_data,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "total_pages": (total + per_page - 1) // per_page
                }
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{order_id}")
async def get_order(
        order_id: int,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取订单详情
    """
    try:
        query = select(Order).where(
            Order.id == order_id,
            Order.user_id == current_user.id
        )
        result = await db.execute(query)
        order = result.scalar_one_or_none()

        if not order:
            return ApiResponse(success=False, error="订单不存在", data=None)

        # 获取订单项
        items_query = (
            select(OrderItem, Product)
            .outerjoin(Product, OrderItem.product_id == Product.id)
            .where(OrderItem.order_id == order.id)
        )
        items_result = await db.execute(items_query)
        items = items_result.all()

        order_items = []
        for order_item, product in items:
            item_data = order_item.to_dict()
            if product:
                item_data["product"] = product.to_dict()
            order_items.append(item_data)

        order_data = order.to_dict()
        order_data["items"] = order_items

        return ApiResponse(success=True, data=order_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
