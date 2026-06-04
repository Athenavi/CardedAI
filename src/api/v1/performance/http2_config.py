"""
HTTP/2 和 HTTP/3 配置 API

提供HTTP/2和HTTP/3的配置管理和优化建议
"""

from fastapi import APIRouter, Depends, HTTPException, Body

from shared.services.performance.http2_service import http2_service
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required

router = APIRouter()


@router.get("/config", summary="获取HTTP/2配置", description="获取当前HTTP/2和HTTP/3配置")
async def get_http2_config(
        current_user=Depends(jwt_required),
):
    """获取HTTP/2配置"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    config = http2_service.get_configuration()

    return ApiResponse(
        success=True,
        data=config
    )


@router.post("/config", summary="更新HTTP/2配置", description="更新HTTP/2和HTTP/3配置")
async def update_http2_config(
        http2_enabled: bool = Body(None, description="是否启用HTTP/2"),
        http3_enabled: bool = Body(None, description="是否启用HTTP/3"),
        server_push_enabled: bool = Body(None, description="是否启用服务器推送"),
        max_concurrent_streams: int = Body(None, ge=1, le=1000, description="最大并发流数"),
        current_user=Depends(jwt_required),
):
    """更新HTTP/2配置"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    updates = {}
    if http2_enabled is not None:
        updates['http2_enabled'] = http2_enabled
    if http3_enabled is not None:
        updates['http3_enabled'] = http3_enabled
    if server_push_enabled is not None:
        updates['server_push_enabled'] = server_push_enabled
    if max_concurrent_streams is not None:
        updates['max_concurrent_streams'] = max_concurrent_streams

    config = http2_service.update_configuration(**updates)

    return ApiResponse(
        success=True,
        message="Configuration updated",
        data=config
    )


@router.get("/suggestions", summary="获取优化建议", description="获取HTTP/2和HTTP/3优化建议")
async def get_optimization_suggestions(
        current_user=Depends(jwt_required),
):
    """获取优化建议"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    suggestions = http2_service.get_optimization_suggestions()

    return ApiResponse(
        success=True,
        data={
            'suggestions': suggestions,
            'count': len(suggestions),
        }
    )


@router.get("/nginx-config", summary="获取Nginx配置", description="获取Nginx HTTP/2配置示例")
async def get_nginx_config(
        current_user=Depends(jwt_required),
):
    """获取Nginx配置"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    config = http2_service.generate_nginx_config()

    return ApiResponse(
        success=True,
        data={
            'config': config,
            'format': 'nginx',
        }
    )


@router.get("/apache-config", summary="获取Apache配置", description="获取Apache HTTP/2配置示例")
async def get_apache_config(
        current_user=Depends(jwt_required),
):
    """获取Apache配置"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    config = http2_service.generate_apache_config()

    return ApiResponse(
        success=True,
        data={
            'config': config,
            'format': 'apache',
        }
    )


@router.get("/best-practices", summary="获取最佳实践", description="获取HTTP/2和HTTP/3最佳实践")
async def get_best_practices():
    """获取最佳实践"""
    practices = http2_service.get_best_practices()

    return ApiResponse(
        success=True,
        data=practices
    )


@router.get("/check-support", summary="检查支持情况", description="检查服务器HTTP/2和HTTP/3支持情况")
async def check_support():
    """检查支持情况"""
    # 这里简化实现，实际应该检测服务器配置
    support = {
        'http2': {
            'supported': True,
            'note': '大多数现代Web服务器都支持HTTP/2',
        },
        'http3': {
            'supported': False,
            'note': 'HTTP/3需要较新的服务器版本和UDP支持',
        },
        'server_push': {
            'supported': True,
            'note': '服务器推送是HTTP/2的可选特性',
        },
    }

    return ApiResponse(
        success=True,
        data=support
    )
