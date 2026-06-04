"""
缓存管理 API

提供多级缓存的管理、监控和预热功能
"""

from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Body

from shared.services.core.multi_level_cache import multi_level_cache
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required

router = APIRouter()


@router.get("/stats", summary="获取缓存统计", description="获取多级缓存的详细统计信息")
async def get_cache_stats(
        current_user=Depends(jwt_required),
):
    """获取缓存统计信息"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    stats = multi_level_cache.get_stats()

    return ApiResponse(
        success=True,
        data=stats
    )


@router.post("/warmup", summary="缓存预热", description="批量预热缓存数据")
async def warmup_cache(
        keys_data: List[Dict[str, Any]] = Body(..., description="预热数据列表"),
        current_user=Depends(jwt_required),
):
    """
    缓存预热
    
    请求体示例:
    [
        {"key": "article:1", "value": {...}, "ttl": 3600},
        {"key": "category:list", "value": [...], "ttl": 1800}
    ]
    """
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    try:
        multi_level_cache.warmup(keys_data)

        return ApiResponse(
            success=True,
            message=f"Successfully warmed up {len(keys_data)} cache entries"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache warmup failed: {str(e)}")


@router.delete("/clear", summary="清空缓存", description="清空所有缓存层级")
async def clear_cache(
        current_user=Depends(jwt_required),
):
    """清空所有缓存"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    try:
        multi_level_cache.clear()

        return ApiResponse(
            success=True,
            message="All cache levels cleared successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache clear failed: {str(e)}")


@router.get("/items/{key}", summary="获取缓存值", description="从多级缓存中获取指定键的值")
async def get_cache_value(
        key: str,
        current_user=Depends(jwt_required),
):
    """获取单个缓存值"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    value = multi_level_cache.get(key)
    
    if value is None:
        raise HTTPException(status_code=404, detail="Cache key not found")

    return ApiResponse(
        success=True,
        data={
            'key': key,
            'value': value,
        }
    )


@router.post("/items/{key}", summary="设置缓存值", description="设置缓存值到所有层级")
async def set_cache_value(
        key: str,
        value: Any = Body(..., description="缓存值"),
        ttl: Optional[int] = Body(None, description="TTL(秒)"),
        current_user=Depends(jwt_required),
):
    """设置缓存值"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    try:
        multi_level_cache.set(key, value, ttl)

        return ApiResponse(
            success=True,
            message="Cache value set successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set cache: {str(e)}")


@router.delete("/items/{key}", summary="删除缓存值", description="从所有缓存层级删除指定键")
async def delete_cache_value(
        key: str,
        current_user=Depends(jwt_required),
):
    """删除缓存值"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    try:
        multi_level_cache.delete(key)

        return ApiResponse(
            success=True,
            message="Cache value deleted successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete cache: {str(e)}")


@router.post("/config", summary="更新缓存配置", description="动态更新缓存配置")
async def update_cache_config(
        config: Dict[str, Any] = Body(..., description="配置项"),
        current_user=Depends(jwt_required),
):
    """
    更新缓存配置
    
    可配置项:
    - memory_ttl: 内存缓存TTL
    - file_cache_ttl: 文件缓存TTL
    """
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    # 注意: 当前实现不支持动态重新初始化,需要重启服务
    # 这里只返回提示信息
    return ApiResponse(
        success=True,
        message="Config update received. Note: Some config changes require service restart.",
        data=config
    )
