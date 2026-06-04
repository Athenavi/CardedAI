"""
API限流管理 API
提供限流配置、监控和管理功能
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body

from shared.services.security.rate_limiter import rate_limiter
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required

router = APIRouter(tags=["rate-limit"])


@router.get("/status", summary="获取限流状态")
async def get_rate_limit_status(
        user_id: Optional[int] = Query(None, description="用户ID"),
        ip_address: Optional[str] = Query(None, description="IP地址"),
        current_user=Depends(jwt_required)
):
    """
    获取当前限流状态
    
    Args:
        user_id: 用户ID（可选）
        ip_address: IP地址（可选）
        
    Returns:
        限流状态信息
    """
    try:
        result = {}

        # 获取用户配额信息
        if user_id:
            quota_info = await rate_limiter.get_quota_info(user_id)
            result['user_quota'] = quota_info

        # 获取IP限流信息
        if ip_address:
            limited, info = await rate_limiter.check_ip_limit(ip_address)
            result['ip_status'] = {
                'limited': limited,
                'info': info
            }

        return ApiResponse(
            success=True,
            data=result
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/config", summary="设置自定义限流配置")
async def set_custom_rate_limit(
        identifier: str = Body(..., description="标识符（IP或用户ID）"),
        limit_type: str = Body(..., description="限流类型 (ip/user/endpoint)"),
        requests: int = Body(..., description="最大请求数"),
        window: int = Body(..., description="时间窗口（秒）"),
        current_user=Depends(jwt_required)
):
    """
    设置自定义限流配置
    
    Args:
        identifier: 标识符
        limit_type: 限流类型
        requests: 最大请求数
        window: 时间窗口（秒）
        
    Returns:
        设置结果
    """
    try:
        # 验证参数
        if limit_type not in ['ip', 'user', 'endpoint']:
            return ApiResponse(success=False, error="Invalid limit_type. Must be 'ip', 'user', or 'endpoint'")

        if requests <= 0:
            return ApiResponse(success=False, error="requests must be positive")

        if window <= 0:
            return ApiResponse(success=False, error="window must be positive")

        # 设置自定义限流
        await rate_limiter.set_custom_limit(identifier, limit_type, requests, window)

        return ApiResponse(
            success=True,
            message=f"Rate limit configured for {identifier}",
            data={
                'identifier': identifier,
                'limit_type': limit_type,
                'requests': requests,
                'window': window
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/reset", summary="重置限流计数器")
async def reset_rate_limit(
        identifier: str = Body(..., description="标识符（IP或用户ID）"),
        limit_type: str = Body(..., description="限流类型 (ip/user)"),
        current_user=Depends(jwt_required)
):
    """
    重置限流计数器
    
    Args:
        identifier: 标识符
        limit_type: 限流类型
        
    Returns:
        重置结果
    """
    try:
        if limit_type not in ['ip', 'user']:
            return ApiResponse(success=False, error="Invalid limit_type. Must be 'ip' or 'user'")

        await rate_limiter.reset_limit(identifier, limit_type)

        return ApiResponse(
            success=True,
            message=f"Rate limit reset for {identifier}"
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/config/default", summary="获取默认限流配置")
async def get_default_config(current_user=Depends(jwt_required)):
    """
    获取默认限流配置
    
    Returns:
        默认配置
    """
    try:
        config = {
            'global': rate_limiter.default_limits['global'],
            'ip': rate_limiter.default_limits['ip'],
            'user': rate_limiter.default_limits['user'],
            'endpoints': rate_limiter.default_limits['endpoint']
        }

        return ApiResponse(
            success=True,
            data=config
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/config/update", summary="更新默认限流配置")
async def update_default_config(
        limit_type: str = Body(..., description="限流类型 (global/ip/user)"),
        requests: int = Body(..., description="最大请求数"),
        window: int = Body(..., description="时间窗口（秒）"),
        current_user=Depends(jwt_required)
):
    """
    更新默认限流配置
    
    Args:
        limit_type: 限流类型
        requests: 最大请求数
        window: 时间窗口（秒）
        
    Returns:
        更新结果
    """
    try:
        if limit_type not in ['global', 'ip', 'user']:
            return ApiResponse(success=False, error="Invalid limit_type. Must be 'global', 'ip', or 'user'")

        if requests <= 0:
            return ApiResponse(success=False, error="requests must be positive")

        if window <= 0:
            return ApiResponse(success=False, error="window must be positive")

        # 更新配置
        rate_limiter.default_limits[limit_type] = {
            'requests': requests,
            'window': window
        }

        return ApiResponse(
            success=True,
            message=f"Default rate limit updated for {limit_type}",
            data={
                'limit_type': limit_type,
                'requests': requests,
                'window': window
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/monitoring", summary="获取限流监控数据")
async def get_monitoring_data(
        period: str = Query("1h", description="统计周期 (1h/24h/7d)"),
        current_user=Depends(jwt_required)
):
    """
    获取限流监控数据
    
    Args:
        period: 统计周期
        
    Returns:
        监控数据
    """
    try:
        # 解析周期
        period_map = {
            '1h': {'hours': 1, 'label': '过去1小时'},
            '24h': {'hours': 24, 'label': '过去24小时'},
            '7d': {'hours': 168, 'label': '过去7天'}
        }

        period_config = period_map.get(period, period_map['1h'])

        # 这里可以返回更详细的监控数据
        # 在实际应用中，应该从数据库或Redis中获取统计数据
        monitoring_data = {
            'period': period_config['label'],
            'total_requests': 0,  # 需要从存储中获取
            'blocked_requests': 0,  # 被限流的请求数
            'top_blocked_ips': [],  # 被限流最多的IP
            'top_blocked_users': [],  # 被限流最多的用户
            'average_response_time': 0,  # 平均响应时间
        }

        return ApiResponse(
            success=True,
            data=monitoring_data
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/whitelist", summary="获取白名单")
async def get_whitelist(current_user=Depends(jwt_required)):
    """
    获取限流白名单
    
    Returns:
        白名单列表
    """
    try:
        # 白名单可以从配置文件或数据库中读取
        whitelist = {
            'ips': [
                # '127.0.0.1',
                # '192.168.1.1'
            ],
            'users': [
                # 管理员用户ID
            ]
        }

        return ApiResponse(
            success=True,
            data=whitelist
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/whitelist/add", summary="添加到白名单")
async def add_to_whitelist(
        item_type: str = Body(..., description="类型 (ip/user)"),
        value: str = Body(..., description="值（IP地址或用户ID）"),
        current_user=Depends(jwt_required)
):
    """
    添加IP或用户到白名单
    
    Args:
        item_type: 类型
        value: 值
        
    Returns:
        添加结果
    """
    try:
        if item_type not in ['ip', 'user']:
            return ApiResponse(success=False, error="Invalid type. Must be 'ip' or 'user'")

        # 在实际应用中，应该将白名单保存到数据库
        # 这里只是示例

        return ApiResponse(
            success=True,
            message=f"Added {value} to whitelist",
            data={
                'type': item_type,
                'value': value
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.delete("/whitelist/remove", summary="从白名单移除")
async def remove_from_whitelist(
        item_type: str = Body(..., description="类型 (ip/user)"),
        value: str = Body(..., description="值（IP地址或用户ID）"),
        current_user=Depends(jwt_required)
):
    """
    从白名单移除IP或用户
    
    Args:
        item_type: 类型
        value: 值
        
    Returns:
        移除结果
    """
    try:
        if item_type not in ['ip', 'user']:
            return ApiResponse(success=False, error="Invalid type. Must be 'ip' or 'user'")

        # 在实际应用中，应该从数据库中删除白名单记录

        return ApiResponse(
            success=True,
            message=f"Removed {value} from whitelist"
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))
