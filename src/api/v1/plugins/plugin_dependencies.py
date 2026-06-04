"""
插件依赖管理 API 端点
"""

from fastapi import APIRouter, Depends, Query

from shared.services.plugins.plugin_manager.dependency import plugin_dependency_manager
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required

router = APIRouter(prefix="/plugin-dependencies", tags=["plugin-dependencies"])


@router.get("/{plugin_slug}/check")
async def check_plugin_dependencies(
    plugin_slug: str,
    installed_plugins: str = Query(..., description="已安装插件列表（逗号分隔）"),
    current_user=Depends(jwt_required)
):
    """检查插件依赖"""
    try:
        installed_list = [p.strip() for p in installed_plugins.split(',') if p.strip()]
        
        # 检查依赖
        dep_result = plugin_dependency_manager.check_dependencies(plugin_slug, installed_list)
        
        # 检查冲突
        conflict_result = plugin_dependency_manager.detect_conflicts(plugin_slug, installed_list)
        
        return ApiResponse(
            success=True,
            data={
                "dependencies": dep_result,
                "conflicts": conflict_result,
                "can_install": dep_result["success"] and conflict_result["can_install"]
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/{plugin_slug}/install-order")
async def get_install_order(
    plugin_slug: str,
    installed_plugins: str = Query(..., description="已安装插件列表（逗号分隔）"),
    current_user=Depends(jwt_required)
):
    """获取插件安装顺序"""
    try:
        installed_list = [p.strip() for p in installed_plugins.split(',') if p.strip()]
        
        order = plugin_dependency_manager.get_install_order(plugin_slug, installed_list)
        
        return ApiResponse(
            success=order["success"],
            data=order
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/{plugin_slug}/lock-versions")
async def lock_dependency_versions(
    plugin_slug: str,
    current_user=Depends(jwt_required)
):
    """锁定插件依赖版本"""
    try:
        result = plugin_dependency_manager.lock_dependency_versions(plugin_slug)
        
        if result["success"]:
            return ApiResponse(
                success=True,
                message="依赖版本已锁定",
                data=result
            )
        else:
            return ApiResponse(
                success=False,
                error=result["error"]
            )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/{plugin_slug}/compatibility")
async def check_compatibility(
    plugin_slug: str,
    platform_version: str = Query(..., description="平台版本"),
    current_user=Depends(jwt_required)
):
    """检查插件兼容性"""
    try:
        result = plugin_dependency_manager.validate_compatibility(plugin_slug, platform_version)
        
        return ApiResponse(
            success=True,
            data=result
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))
