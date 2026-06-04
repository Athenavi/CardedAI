"""
对象缓存管理 API

提供对象缓存的管理、监控和清除功能
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Body

from shared.services.core.object_cache import object_cache_service
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required

router = APIRouter()


@router.get("/stats", summary="获取对象缓存统计", description="获取对象缓存的统计信息")
async def get_object_cache_stats(
        current_user=Depends(jwt_required),
):
    """获取对象缓存统计"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    stats = await object_cache_service.get_stats()

    return ApiResponse(
        success=True,
        data=stats
    )


@router.post("/invalidate-tag", summary="按标签清除缓存", description="使指定标签的所有缓存失效")
async def invalidate_by_tag(
        tag: str = Body(..., description="缓存标签"),
        current_user=Depends(jwt_required),
):
    """按标签清除缓存"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    try:
        count = await object_cache_service.invalidate_by_tag(tag)

        return ApiResponse(
            success=True,
            message=f"Invalidated {count} cached objects with tag: {tag}",
            data={"count": count}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to invalidate by tag: {str(e)}")


@router.post("/invalidate-tags", summary="批量按标签清除", description="使多个标签的缓存失效")
async def invalidate_by_tags(
        tags: List[str] = Body(..., description="缓存标签列表"),
        current_user=Depends(jwt_required),
):
    """批量按标签清除缓存"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    try:
        count = await object_cache_service.invalidate_by_tags(tags)

        return ApiResponse(
            success=True,
            message=f"Invalidated {count} cached objects",
            data={"count": count, "tags": tags}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to invalidate by tags: {str(e)}")


@router.post("/config", summary="更新缓存配置", description="更新对象缓存配置")
async def update_cache_config(
        ttl: int = Body(None, ge=1, le=86400, description="默认TTL(秒)"),
        current_user=Depends(jwt_required),
):
    """更新对象缓存配置"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    if ttl is not None:
        object_cache_service.default_ttl = ttl

    return ApiResponse(
        success=True,
        message="Cache configuration updated",
        data={
            "default_ttl": object_cache_service.default_ttl,
        }
    )
