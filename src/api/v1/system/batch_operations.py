"""
批量操作 API
提供文章、评论、商品等资源的批量操作功能
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.user import User
from shared.services.system.batch_operations import create_batch_service
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session

router = APIRouter(tags=["batch"])


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    ids: List[int]


class BatchUpdateStatusRequest(BaseModel):
    """批量更新状态请求"""
    ids: List[int]
    status: str


class BatchMoveCategoryRequest(BaseModel):
    """批量移动分类请求"""
    ids: List[int]
    category_id: int


class BatchAddTagsRequest(BaseModel):
    """批量添加标签请求"""
    ids: List[int]
    tags: List[str]


class BatchUpdatePriceRequest(BaseModel):
    """批量更新价格请求"""
    ids: List[int]
    price: float
    original_price: Optional[float] = None


class BatchUpdateStockRequest(BaseModel):
    """批量更新库存请求"""
    ids: List[int]
    stock: int
    operation: str = "set"  # set, add, subtract


class BatchUpdateSortRequest(BaseModel):
    """批量更新排序请求"""
    orders: List[dict]  # [{id: int, sort_order: int}, ...]


@router.post("/articles/delete", summary="批量删除文章")
async def batch_delete_articles(
        request: BatchDeleteRequest,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db_session)
):
    """
    批量删除文章
    
    **权限要求**: 需要登录，只能删除自己的文章或管理员可删除任意文章
    
    Args:
        request: 删除请求，包含文章ID列表
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        操作结果，包含成功数量和消息
    """
    try:
        service = create_batch_service(db)
        result = await service.batch_delete_articles(
            article_ids=request.ids,
            operator_id=current_user.id,
            user=current_user
        )

        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/articles/update-status", summary="批量更新文章状态")
async def batch_update_article_status(
        request: BatchUpdateStatusRequest,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db_session)
):
    """
    批量更新文章状态
    
    **权限要求**: 需要登录，只能更新自己的文章或管理员可更新任意文章
    
    Args:
        request: 更新请求，包含文章ID列表和目标状态
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        操作结果，包含更新数量和消息
    """
    try:
        service = create_batch_service(db)
        result = await service.batch_update_article_status(
            article_ids=request.ids,
            status=request.status,
            operator_id=current_user.id,
            user=current_user
        )

        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/articles/move-category", summary="批量移动文章到分类")
async def batch_move_to_category(
        request: BatchMoveCategoryRequest,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db_session)
):
    """
    批量移动文章到指定分类
    
    **权限要求**: 需要登录，只能移动自己的文章或管理员可移动任意文章
    
    Args:
        request: 移动请求，包含文章ID列表和目标分类ID
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        操作结果，包含移动数量和消息
    """
    try:
        service = create_batch_service(db)
        result = await service.batch_move_to_category(
            article_ids=request.ids,
            category_id=request.category_id,
            operator_id=current_user.id,
            user=current_user
        )

        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/articles/add-tags", summary="批量添加标签")
async def batch_add_tags(
        request: BatchAddTagsRequest,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db_session)
):
    """
    批量添加标签
    
    **权限要求**: 需要登录，只能为自己的文章添加标签或管理员可为任意文章添加
    
    Args:
        request: 添加标签请求，包含文章ID列表和标签列表
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        操作结果，包含更新数量和消息
    """
    try:
        service = create_batch_service(db)
        result = await service.batch_add_tags(
            article_ids=request.ids,
            tags=request.tags,
            operator_id=current_user.id,
            user=current_user
        )

        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comments/delete", summary="批量删除评论")
async def batch_delete_comments(
        request: BatchDeleteRequest,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db_session)
):
    """
    批量删除评论
    
    **权限要求**: 需要登录，管理员或文章作者可删除评论
    
    Args:
        request: 删除请求，包含评论ID列表
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        操作结果，包含删除数量和消息
    """
    try:
        service = create_batch_service(db)
        result = await service.batch_delete_comments(
            comment_ids=request.ids,
            operator_id=current_user.id,
            user=current_user
        )

        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comments/update-status", summary="批量更新评论状态")
async def batch_update_comment_status(
        request: BatchUpdateStatusRequest,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db_session)
):
    """
    批量更新评论状态
    
    **权限要求**: 需要登录，管理员或文章作者可更新评论状态
    
    Args:
        request: 更新请求，包含评论ID列表和目标状态
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        操作结果，包含更新数量和消息
    """
    try:
        service = create_batch_service(db)
        result = await service.batch_update_comment_status(
            comment_ids=request.ids,
            status=request.status,
            operator_id=current_user.id,
            user=current_user
        )

        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 商品批量操作
# ============================================================================

@router.post("/products/delete", summary="批量删除商品")
async def batch_delete_products(
        request: BatchDeleteRequest,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db_session)
):
    """
    批量删除商品
    
    **权限要求**: 需要登录，管理员可删除任意商品
    
    Args:
        request: 删除请求，包含商品ID列表
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        操作结果，包含删除数量和消息
    """
    try:
        service = create_batch_service(db)
        result = await service.batch_delete_products(
            product_ids=request.ids,
            operator_id=current_user.id,
            user=current_user
        )

        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/products/update-price", summary="批量更新商品价格")
async def batch_update_product_price(
        request: BatchUpdatePriceRequest,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db_session)
):
    """
    批量更新商品价格
    
    **权限要求**: 需要登录，管理员可更新任意商品价格
    
    Args:
        request: 更新请求，包含商品ID列表、新价格和可选的原价
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        操作结果，包含更新数量和消息
    """
    try:
        service = create_batch_service(db)
        result = await service.batch_update_product_price(
            product_ids=request.ids,
            price=request.price,
            original_price=request.original_price,
            operator_id=current_user.id,
            user=current_user
        )

        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/products/update-stock", summary="批量更新商品库存")
async def batch_update_product_stock(
        request: BatchUpdateStockRequest,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db_session)
):
    """
    批量更新商品库存
    
    **权限要求**: 需要登录，管理员可更新任意商品库存
    
    Args:
        request: 更新请求，包含商品ID列表、库存数量和操作类型(set/add/subtract)
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        操作结果，包含更新数量和消息
    """
    try:
        service = create_batch_service(db)
        result = await service.batch_update_product_stock(
            product_ids=request.ids,
            stock=request.stock,
            operation=request.operation,
            operator_id=current_user.id,
            user=current_user
        )

        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/products/update-status", summary="批量更新商品状态")
async def batch_update_product_status(
        request: BatchUpdateStatusRequest,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db_session)
):
    """
    批量更新商品状态
    
    **权限要求**: 需要登录，管理员可更新任意商品状态
    
    Args:
        request: 更新请求，包含商品ID列表和目标状态(active/inactive)
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        操作结果，包含更新数量和消息
    """
    try:
        service = create_batch_service(db)
        result = await service.batch_update_product_status(
            product_ids=request.ids,
            status=request.status,
            operator_id=current_user.id,
            user=current_user
        )

        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/articles/update-sort", summary="批量更新文章排序")
async def batch_update_articles_sort(
        request: BatchUpdateSortRequest,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db_session)
):
    """
    批量更新文章排序（用于拖拽排序）
    
    **权限要求**: 需要登录
    
    Args:
        request: 更新请求，包含文章排序列表 [{id: 文章ID, sort_order: 排序值}, ...]
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        操作结果，包含更新数量和消息
    """
    try:
        service = create_batch_service(db)
        result = await service.batch_update_articles_sort(
            article_orders=request.orders,
            operator_id=current_user.id
        )

        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/categories/update-sort", summary="批量更新分类排序")
async def batch_update_categories_sort(
        request: BatchUpdateSortRequest,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db_session)
):
    """
    批量更新分类排序（用于拖拽排序）
    
    **权限要求**: 需要登录，管理员权限
    
    Args:
        request: 更新请求，包含分类排序列表 [{id: 分类ID, sort_order: 排序值}, ...]
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        操作结果，包含更新数量和消息
    """
    try:
        service = create_batch_service(db)
        result = await service.batch_update_categories_sort(
            category_orders=request.orders,
            operator_id=current_user.id
        )

        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
