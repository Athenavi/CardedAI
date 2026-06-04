"""
电子商务 API - 商品管理
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import Product
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["products"])


@router.get("/")
async def list_products(
        page: int = Query(1, ge=1, description="页码"),
        per_page: int = Query(10, ge=1, le=100, description="每页数量"),
        category_id: Optional[int] = Query(None, description="分类ID"),
        search: Optional[str] = Query(None, description="搜索关键词"),
        is_featured: Optional[bool] = Query(None, description="是否推荐"),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取商品列表
    
    支持分页、分类筛选、搜索和推荐筛选
    """
    try:
        # 构建查询
        query = select(Product).where(Product.is_active == True)

        # 分类筛选
        if category_id:
            query = query.where(Product.category_id == category_id)

        # 搜索
        if search:
            query = query.where(
                (Product.name.ilike(f"%{search}%")) |
                (Product.description.ilike(f"%{search}%"))
            )

        # 推荐筛选
        if is_featured is not None:
            query = query.where(Product.is_featured == is_featured)

        # 排序(推荐商品优先,然后按创建时间降序)
        query = query.order_by(Product.is_featured.desc(), Product.created_at.desc())

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # 分页
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        result = await db.execute(query)
        products = result.scalars().all()

        # 转换为字典
        products_data = [product.to_dict() for product in products]

        return ApiResponse(
            success=True,
            data={
                "products": products_data,
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


@router.get("/{product_id}")
async def get_product(
        product_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取商品详情
    """
    try:
        query = select(Product).where(Product.id == product_id)
        result = await db.execute(query)
        product = result.scalar_one_or_none()

        if not product:
            return ApiResponse(success=False, error="商品不存在", data=None)

        return ApiResponse(success=True, data=product.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_product(
        product_data: dict,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    创建商品(需要管理员权限)
    """
    try:
        # 检查管理员权限
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="Permission denied. Admin access required.")

        # 创建商品实例
        product = Product(**product_data)

        db.add(product)
        await db.commit()
        await db.refresh(product)

        return ApiResponse(
            success=True,
            data=product.to_dict(),
            message="商品创建成功"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{product_id}")
async def update_product(
        product_id: int,
        product_data: dict,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    更新商品(需要管理员权限)
    """
    try:
        query = select(Product).where(Product.id == product_id)
        result = await db.execute(query)
        product = result.scalar_one_or_none()

        if not product:
            return ApiResponse(success=False, error="商品不存在", data=None)

        # 更新字段
        for key, value in product_data.items():
            if hasattr(product, key):
                setattr(product, key, value)

        await db.commit()
        await db.refresh(product)

        return ApiResponse(
            success=True,
            data=product.to_dict(),
            message="商品更新成功"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{product_id}")
async def delete_product(
        product_id: int,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    删除商品(需要管理员权限)
    """
    try:
        query = select(Product).where(Product.id == product_id)
        result = await db.execute(query)
        product = result.scalar_one_or_none()

        if not product:
            return ApiResponse(success=False, error="商品不存在", data=None)

        await db.delete(product)
        await db.commit()

        return ApiResponse(
            success=True,
            message="商品删除成功"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
