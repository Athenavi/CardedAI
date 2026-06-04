"""
搜索与媒体管理扩展 API

提供搜索索引(SearchIndex)和媒体优化(MediaOptimization)的 CRUD 管理接口
"""
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import SearchIndex, MediaOptimization
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["search-media-management"])


# ==================== 搜索索引管理 ====================


@router.get("/search-index")
async def list_search_index(
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
    indexed: Optional[bool] = Query(None, description="是否已索引"),
    article_id: Optional[int] = Query(None, description="文章ID"),
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """
    获取搜索索引列表

    支持分页、按索引状态和文章ID筛选
    """
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(SearchIndex)

        if indexed is not None:
            query = query.where(SearchIndex.indexed == indexed)

        if article_id:
            query = query.where(SearchIndex.article_id == article_id)

        query = query.order_by(SearchIndex.updated_at.desc())

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        result = await db.execute(query)
        indexes = result.scalars().all()

        return ApiResponse(
            success=True,
            data={
                "search_indexes": [idx.to_dict() for idx in indexes],
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "total_pages": (total + per_page - 1) // per_page if total > 0 else 0,
                },
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/search-index/{index_id}")
async def get_search_index(
    index_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """获取搜索索引详情"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(SearchIndex).where(SearchIndex.id == index_id)
        result = await db.execute(query)
        index = result.scalar_one_or_none()

        if not index:
            return ApiResponse(success=False, error="搜索索引记录不存在")

        return ApiResponse(success=True, data=index.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/search-index")
async def create_search_index(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """创建搜索索引记录"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        data = await request.json()

        article_id = data.get("article_id")
        if not article_id:
            return ApiResponse(success=False, error="article_id 为必填字段")

        # 检查唯一性
        existing = await db.execute(
            select(SearchIndex).where(SearchIndex.article_id == article_id)
        )
        if existing.scalar_one_or_none():
            return ApiResponse(success=False, error=f"文章 ID={article_id} 的索引记录已存在")

        now = datetime.utcnow()
        index = SearchIndex(
            article_id=article_id,
            indexed=data.get("indexed", False),
            last_indexed_at=data.get("last_indexed_at"),
            index_hash=data.get("index_hash"),
            created_at=now,
            updated_at=now,
        )

        db.add(index)
        await db.commit()
        await db.refresh(index)

        return ApiResponse(success=True, data=index.to_dict(), message="搜索索引记录创建成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


@router.put("/search-index/{index_id}")
async def update_search_index(
    index_id: int,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """更新搜索索引记录"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(SearchIndex).where(SearchIndex.id == index_id)
        result = await db.execute(query)
        index = result.scalar_one_or_none()

        if not index:
            return ApiResponse(success=False, error="搜索索引记录不存在")

        data = await request.json()

        if "indexed" in data:
            index.indexed = data["indexed"]
        if "index_hash" in data:
            index.index_hash = data["index_hash"]
        if "last_indexed_at" in data:
            lia = data["last_indexed_at"]
            index.last_indexed_at = datetime.fromisoformat(lia.replace("Z", "+00:00")) if isinstance(lia, str) else lia

        # 标记索引时间
        if data.get("indexed") is True and index.last_indexed_at is None:
            index.last_indexed_at = datetime.utcnow()

        index.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(index)

        return ApiResponse(success=True, data=index.to_dict(), message="搜索索引记录更新成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


@router.delete("/search-index/{index_id}")
async def delete_search_index(
    index_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """删除搜索索引记录"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(SearchIndex).where(SearchIndex.id == index_id)
        result = await db.execute(query)
        index = result.scalar_one_or_none()

        if not index:
            return ApiResponse(success=False, error="搜索索引记录不存在")

        await db.delete(index)
        await db.commit()

        return ApiResponse(success=True, message="搜索索引记录删除成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


@router.post("/search-index/batch-reindex")
async def batch_reindex(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """
    批量标记需要重新索引

    将指定文章或所有文章的索引状态重置为待索引
    """
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        data = await request.json()
        article_ids = data.get("article_ids")  # 空列表或不传 = 全部重置

        if article_ids and isinstance(article_ids, list):
            # 重置指定文章
            count = 0
            for aid in article_ids:
                query = select(SearchIndex).where(SearchIndex.article_id == aid)
                result = await db.execute(query)
                index = result.scalar_one_or_none()
                if index:
                    index.indexed = False
                    index.index_hash = None
                    index.updated_at = datetime.utcnow()
                    count += 1
            await db.commit()
            return ApiResponse(success=True, data={"reset_count": count}, message=f"已重置 {count} 条索引记录")
        else:
            # 重置所有
            from sqlalchemy import update
            await db.execute(
                update(SearchIndex)
                .values(indexed=False, index_hash=None, updated_at=datetime.utcnow())
            )
            await db.commit()
            total = await db.execute(select(func.count()).select_from(SearchIndex))
            total_count = total.scalar()
            return ApiResponse(
                success=True,
                data={"reset_count": total_count},
                message=f"已重置全部 {total_count} 条索引记录",
            )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


# ==================== 媒体优化管理 ====================


@router.get("/media-optimizations")
async def list_media_optimizations(
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
    media_id: Optional[int] = Query(None, description="媒体ID"),
    optimization_status: Optional[str] = Query(None, description="优化状态"),
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """
    获取媒体优化配置列表

    支持分页、按媒体ID和优化状态筛选
    """
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(MediaOptimization)

        if media_id:
            query = query.where(MediaOptimization.media_id == media_id)

        if optimization_status:
            query = query.where(MediaOptimization.optimization_status == optimization_status)

        query = query.order_by(MediaOptimization.created_at.desc())

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        result = await db.execute(query)
        optimizations = result.scalars().all()

        return ApiResponse(
            success=True,
            data={
                "media_optimizations": [o.to_dict() for o in optimizations],
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "total_pages": (total + per_page - 1) // per_page if total > 0 else 0,
                },
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/media-optimizations/{opt_id}")
async def get_media_optimization(
    opt_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """获取媒体优化配置详情"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(MediaOptimization).where(MediaOptimization.id == opt_id)
        result = await db.execute(query)
        opt = result.scalar_one_or_none()

        if not opt:
            return ApiResponse(success=False, error="媒体优化配置不存在")

        return ApiResponse(success=True, data=opt.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/media-optimizations")
async def create_media_optimization(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """创建媒体优化配置"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        data = await request.json()

        media_id = data.get("media_id")
        if not media_id:
            return ApiResponse(success=False, error="media_id 为必填字段")

        # 检查该媒体是否已有优化配置
        existing = await db.execute(
            select(MediaOptimization).where(MediaOptimization.media_id == media_id)
        )
        if existing.scalar_one_or_none():
            return ApiResponse(success=False, error=f"媒体 ID={media_id} 的优化配置已存在")

        now = datetime.utcnow()
        opt = MediaOptimization(
            media_id=media_id,
            webp_url=data.get("webp_url"),
            sizes_json=json.dumps(data["sizes_json"], ensure_ascii=False)
            if "sizes_json" in data and isinstance(data["sizes_json"], dict)
            else data.get("sizes_json"),
            cdn_url=data.get("cdn_url"),
            optimization_status=data.get("optimization_status", "pending"),
            created_at=now,
            updated_at=now,
        )

        db.add(opt)
        await db.commit()
        await db.refresh(opt)

        return ApiResponse(success=True, data=opt.to_dict(), message="媒体优化配置创建成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


@router.put("/media-optimizations/{opt_id}")
async def update_media_optimization(
    opt_id: int,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """更新媒体优化配置"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(MediaOptimization).where(MediaOptimization.id == opt_id)
        result = await db.execute(query)
        opt = result.scalar_one_or_none()

        if not opt:
            return ApiResponse(success=False, error="媒体优化配置不存在")

        data = await request.json()

        if "webp_url" in data:
            opt.webp_url = data["webp_url"]
        if "cdn_url" in data:
            opt.cdn_url = data["cdn_url"]
        if "optimization_status" in data:
            opt.optimization_status = data["optimization_status"]
        if "sizes_json" in data:
            sj = data["sizes_json"]
            opt.sizes_json = json.dumps(sj, ensure_ascii=False) if isinstance(sj, dict) else sj

        opt.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(opt)

        return ApiResponse(success=True, data=opt.to_dict(), message="媒体优化配置更新成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


@router.delete("/media-optimizations/{opt_id}")
async def delete_media_optimization(
    opt_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """删除媒体优化配置"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(MediaOptimization).where(MediaOptimization.id == opt_id)
        result = await db.execute(query)
        opt = result.scalar_one_or_none()

        if not opt:
            return ApiResponse(success=False, error="媒体优化配置不存在")

        await db.delete(opt)
        await db.commit()

        return ApiResponse(success=True, message="媒体优化配置删除成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))
