"""
资源优化管理 API

提供静态资源的压缩、优化和版本化管理功能
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Body

from shared.services.performance.resource_optimizer import resource_optimizer
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required

router = APIRouter()


@router.get("/stats", summary="获取资源优化统计", description="获取资源优化的统计信息")
async def get_resource_stats(
        current_user=Depends(jwt_required),
):
    """获取资源优化统计"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    # 生成清单获取统计
    manifest = resource_optimizer.generate_resource_manifest()

    return ApiResponse(
        success=True,
        data={
            "total_resources": len(manifest['resources']),
            "version_map_size": len(manifest['version_map']),
            "generated_at": manifest['generated_at'],
        }
    )


@router.post("/optimize", summary="批量优化资源", description="批量优化CSS、JS和图片资源")
async def batch_optimize_resources(
        file_types: List[str] = Body(["css", "js"], description="要优化的文件类型"),
        minify: bool = Body(True, description="是否压缩文本文件"),
        image_quality: int = Body(85, ge=1, le=100, description="图片压缩质量"),
        current_user=Depends(jwt_required),
):
    """批量优化资源"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    try:
        stats = resource_optimizer.batch_optimize(
            file_types=file_types,
            minify=minify,
            image_quality=image_quality
        )

        return ApiResponse(
            success=True,
            message="Resource optimization completed",
            data=stats
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.post("/clear-cache", summary="清空优化缓存", description="清空所有优化后的资源")
async def clear_optimization_cache(
        current_user=Depends(jwt_required),
):
    """清空优化缓存"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    try:
        resource_optimizer.clear_cache()

        return ApiResponse(
            success=True,
            message="Optimization cache cleared successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.get("/versioned-url", summary="获取带版本的URL", description="获取资源的带版本号URL")
async def get_versioned_url(
        url: str = Query(..., description="原始资源URL"),
):
    """获取带版本号的URL"""
    versioned_url = resource_optimizer.get_versioned_url(url)

    return ApiResponse(
        success=True,
        data={
            "original_url": url,
            "versioned_url": versioned_url,
        }
    )


@router.get("/manifest", summary="获取资源清单", description="获取所有优化资源的清单")
async def get_resource_manifest(
        current_user=Depends(jwt_required),
):
    """获取资源清单"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    manifest = resource_optimizer.generate_resource_manifest()

    return ApiResponse(
        success=True,
        data=manifest
    )


@router.post("/optimize-css", summary="优化CSS", description="优化单个CSS文件")
async def optimize_css(
        css_content: str = Body(..., description="CSS内容"),
        minify: bool = Body(True, description="是否压缩"),
):
    """优化CSS内容"""
    optimized_css = resource_optimizer.optimize_css(css_content, minify)

    return ApiResponse(
        success=True,
        data={
            "original_size": len(css_content),
            "optimized_size": len(optimized_css),
            "compression_ratio": f"{(1 - len(optimized_css) / len(css_content)) * 100:.2f}%",
            "optimized_content": optimized_css,
        }
    )


@router.post("/optimize-js", summary="优化JavaScript", description="优化单个JS文件")
async def optimize_js(
        js_content: str = Body(..., description="JavaScript内容"),
        minify: bool = Body(True, description="是否压缩"),
):
    """优化JavaScript内容"""
    optimized_js = resource_optimizer.optimize_js(js_content, minify)

    return ApiResponse(
        success=True,
        data={
            "original_size": len(js_content),
            "optimized_size": len(optimized_js),
            "compression_ratio": f"{(1 - len(optimized_js) / len(js_content)) * 100:.2f}%",
            "optimized_content": optimized_js,
        }
    )


@router.get("/best-practices", summary="最佳实践", description="获取资源优化最佳实践")
async def get_best_practices():
    """获取最佳实践"""
    practices = {
        "caching_strategy": {
            "title": "缓存策略",
            "items": [
                "静态资源设置长期缓存（1年）",
                "使用版本号URL实现缓存失效",
                "HTML页面设置短缓存或无缓存",
                "API响应使用ETag和Last-Modified",
            ]
        },
        "compression": {
            "title": "压缩策略",
            "items": [
                "启用Gzip压缩（兼容性好）",
                "启用Brotli压缩（压缩率更高）",
                "图片使用WebP格式（比JPEG小30%）",
                "SVG图标内联到HTML",
            ]
        },
        "loading_optimization": {
            "title": "加载优化",
            "items": [
                "关键CSS内联到<head>",
                "非关键CSS异步加载",
                "JavaScript使用defer或async",
                "图片实现懒加载",
                "字体使用preload预加载",
            ]
        },
        "cdn_configuration": {
            "title": "CDN配置",
            "items": [
                "启用HTTP/2或HTTP/3",
                "配置合适的TTL",
                "启用边缘缓存",
                "设置防盗链",
                "监控CDN命中率",
            ]
        }
    }

    return ApiResponse(
        success=True,
        data=practices
    )
