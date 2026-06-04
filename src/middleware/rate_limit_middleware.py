"""
API速率限制中间件

自动为API请求应用速率限制
返回429状态码和限制头信息
"""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from shared.services.security.rate_limiter import rate_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    速率限制中间件
    
    为所有API请求应用速率限制
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求
        
        Args:
            request: HTTP请求
            call_next: 下一个处理器
        
        Returns:
            HTTP响应
        """
        # 只限制API请求
        if not request.url.path.startswith('/api/'):
            return await call_next(request)

        # 获取用户ID（如果已认证）
        user_id = None
        if hasattr(request.state, 'user') and request.state.user:
            user_id = getattr(request.state.user, 'id', None)

        # 获取IP地址
        ip_address = request.client.host if request.client else None

        # 获取端点路径
        endpoint = request.url.path

        # 检查速率限制
        allowed, info = await rate_limiter.check_rate_limit(
            user_id=user_id,
            ip_address=ip_address,
            endpoint=endpoint,
        )

        if not allowed:
            # 返回429 Too Many Requests
            response = JSONResponse(
                status_code=429,
                content={
                    'success': False,
                    'error': 'Rate limit exceeded',
                    'retry_after': info['retry_after'],
                    'limit': info['limit'],
                },
                headers={
                    'Retry-After': str(int(info['retry_after']) + 1),
                    'X-RateLimit-Limit': str(info['limit'].get('user', {}).get('limit',
                                                                               info['limit'].get('ip', {}).get('limit',
                                                                                                               0))),
                    'X-RateLimit-Remaining': str(info['limit'].get('user', {}).get('remaining',
                                                                                   info['limit'].get('ip', {}).get(
                                                                                       'remaining', 0))),
                    'X-RateLimit-Reset': str(int(info['limit'].get('user', {}).get('reset',
                                                                                   info['limit'].get('ip', {}).get(
                                                                                       'reset', time.time())))),
                }
            )
            return response

        # 继续处理请求
        response = await call_next(request)

        # 添加速率限制头到响应
        if 'user' in info['limit']:
            limit_info = info['limit']['user']
        elif 'ip' in info['limit']:
            limit_info = info['limit']['ip']
        else:
            limit_info = {}

        if limit_info:
            response.headers['X-RateLimit-Limit'] = str(limit_info.get('limit', 0))
            response.headers['X-RateLimit-Remaining'] = str(limit_info.get('remaining', 0))
            response.headers['X-RateLimit-Reset'] = str(int(limit_info.get('reset', time.time())))

        return response


# 导出
__all__ = ['RateLimitMiddleware']
