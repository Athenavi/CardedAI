"""
页面缓存管理 API

提供页面缓存的管理、监控和清除功能
"""

from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Body

from shared.services.performance.cache_manager import page_cache_service
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required

router = APIRouter()


@router.get("/stats", summary="获取页面缓存统计", description="获取页面缓存的统计信息")
async def get_page_cache_stats(
        current_user=Depends(jwt_required),
):
    """获取页面缓存统计"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    # 获取多级缓存统计
    cache_stats = page_cache_service.cache.get_stats()

    return ApiResponse(
        success=True,
        data={
            "page_cache": {
                "prefix": page_cache_service.cache_prefix,
                "default_ttl": page_cache_service.default_ttl,
            },
            "underlying_cache": cache_stats,
        }
    )


@router.post("/invalidate", summary="清除页面缓存", description="使指定页面的缓存失效")
async def invalidate_page_cache(
        url: str = Body(..., description="页面URL"),
        user_role: str = Body("anonymous", description="用户角色"),
        params: Optional[Dict[str, Any]] = Body(None, description="查询参数"),
        current_user=Depends(jwt_required),
):
    """清除指定页面的缓存"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    try:
        await page_cache_service.invalidate_page(url, user_role, params)

        return ApiResponse(
            success=True,
            message=f"Page cache invalidated for: {url}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to invalidate cache: {str(e)}")


@router.post("/invalidate-pattern", summary="批量清除缓存", description="使匹配模式的页面缓存失效")
async def invalidate_pattern_cache(
        pattern: str = Body(..., description="URL模式（支持通配符）"),
        current_user=Depends(jwt_required),
):
    """批量清除匹配模式的页面缓存"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    try:
        count = await page_cache_service.invalidate_pattern(pattern)

        return ApiResponse(
            success=True,
            message=f"Invalidated {count} cached pages matching pattern: {pattern}",
            data={"count": count}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to invalidate pattern: {str(e)}")


@router.post("/clear-all", summary="清空所有页面缓存", description="清空所有页面缓存")
async def clear_all_page_cache(
        current_user=Depends(jwt_required),
):
    """清空所有页面缓存"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    try:
        await page_cache_service.clear_all()

        return ApiResponse(
            success=True,
            message="All page cache cleared successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.get("/info", summary="获取缓存信息", description="获取指定页面的缓存状态")
async def get_cache_info(
        url: str = Query(..., description="页面URL"),
        user_role: str = Query("anonymous", description="用户角色"),
        current_user=Depends(jwt_required),
):
    """获取页面缓存信息"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    info = page_cache_service.get_cache_info(url, user_role)

    return ApiResponse(
        success=True,
        data=info
    )


@router.post("/config", summary="更新缓存配置", description="更新页面缓存配置")
async def update_cache_config(
        ttl: int = Body(None, ge=1, le=86400, description="默认TTL(秒)"),
        enabled: bool = Body(None, description="是否启用缓存"),
        current_user=Depends(jwt_required),
):
    """更新页面缓存配置"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    if ttl is not None:
        page_cache_service.default_ttl = ttl

    return ApiResponse(
        success=True,
        message="Cache configuration updated",
        data={
            "default_ttl": page_cache_service.default_ttl,
        }
    )


@router.get("/examples", summary="缓存使用示例", description="获取页面缓存使用示例")
async def get_cache_examples():
    """获取页面缓存使用示例"""
    examples = {
        "basic_usage": {
            "description": "基本用法 - 在路由中使用装饰器",
            "code": '''
from shared.services.page_cache import page_cache

@app.get("/articles")
@page_cache(ttl=300)
async def get_articles():
    # 这个响应会被缓存5分钟
    return {"articles": [...]}
            '''.strip()
        },
        "manual_cache": {
            "description": "手动缓存 - 在服务层控制缓存",
            "code": '''
from shared.services.page_cache import page_cache_service

async def get_article_detail(article_id: int):
    url = f"/articles/{article_id}"
    
    # 尝试从缓存获取
    cached = await page_cache_service.get_page(url)
    if cached:
        return cached
    
    # 生成内容
    content = generate_article_html(article_id)
    
    # 存入缓存
    await page_cache_service.set_page(url, content, ttl=600)
    
    return content
            '''.strip()
        },
        "invalidate_cache": {
            "description": "清除缓存 - 内容更新时清除缓存",
            "code": '''
from shared.services.page_cache import page_cache_service

async def update_article(article_id: int, data: dict):
    # 更新文章
    await db.update(...)
    
    # 清除相关缓存
    await page_cache_service.invalidate_page(f"/articles/{article_id}")
    await page_cache_service.invalidate_page("/articles")  # 列表页
            '''.strip()
        },
        "cache_strategy": {
            "description": "缓存策略建议",
            "recommendations": [
                "首页: TTL 60-120秒（高频访问，内容变化快）",
                "文章列表: TTL 300秒（中等频率）",
                "文章详情: TTL 600-3600秒（低频变化）",
                "分类/标签页: TTL 600秒",
                "用户个人页面: 不缓存或短TTL",
                "管理后台: 不缓存",
            ]
        }
    }

    return ApiResponse(
        success=True,
        data=examples
    )
