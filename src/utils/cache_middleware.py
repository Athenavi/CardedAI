"""
缓存中间件 - 自动缓存HTTP响应
"""

from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from shared.services.core.cache_service import cache_service


class CacheMiddleware(BaseHTTPMiddleware):
    """
    HTTP缓存中间件
    
    功能:
    - 自动缓存GET请求的响应
    - 支持自定义TTL
    - 支持跳过特定路径
    """

    def __init__(
            self,
            app,
            default_ttl: int = 300,
            skip_paths: list = None,
            skip_methods: list = None
    ):
        super().__init__(app)
        self.default_ttl = default_ttl
        self.skip_paths = skip_paths or [
            '/admin',
            '/api/v1/auth',
            '/api/v1/user',
            '/login',
            '/register'
        ]
        self.skip_methods = skip_methods or ['POST', 'PUT', 'DELETE', 'PATCH']

    async def dispatch(self, request: Request, call_next: Callable):
        # 检查是否应该跳过缓存
        if self._should_skip_cache(request):
            return await call_next(request)

        # 只缓存GET请求
        if request.method != 'GET':
            return await call_next(request)

        # 生成缓存键
        cache_key = f"{request.url.path}:{request.url.query}"

        # 尝试从缓存获取
        cached_page = cache_service.get_page(cache_key)
        if cached_page:
            # 返回缓存的响应
            response = Response(
                content=cached_page['content'],
                status_code=cached_page['status_code'],
                headers={
                    **cached_page['headers'],
                    'X-Cache': 'HIT',
                    'X-Cache-Age': self._calculate_age(cached_page['cached_at'])
                }
            )
            return response

        # 执行请求
        response = await call_next(request)

        # 只缓存成功的响应
        if response.status_code == 200:
            # 读取响应内容
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk

            # 尝试解码为字符串
            try:
                content_str = response_body.decode('utf-8')

                # 存入缓存
                cache_service.set_page(
                    cache_key,
                    content_str,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    ttl=self.default_ttl
                )

                # 重新构建响应
                response = Response(
                    content=content_str,
                    status_code=response.status_code,
                    headers={
                        **dict(response.headers),
                        'X-Cache': 'MISS',
                        'X-Cache-TTL': str(self.default_ttl)
                    }
                )
            except Exception as e:
                # 如果无法解码(可能是二进制内容),不缓存
                print(f"Cache middleware error: {e}")
                response = Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers={
                        **dict(response.headers),
                        'X-Cache': 'BYPASS'
                    }
                )

        return response

    def _should_skip_cache(self, request: Request) -> bool:
        """检查是否应该跳过缓存"""
        # 检查请求方法
        if request.method in self.skip_methods:
            return True

        # 检查路径
        path = request.url.path
        for skip_path in self.skip_paths:
            if path.startswith(skip_path):
                return True

        # 检查查询参数中的no-cache
        if 'no-cache' in request.query_params:
            return True

        # 检查用户认证状态(可选)
        # 如果有认证token,可能不应该缓存
        auth_header = request.headers.get('Authorization')
        if auth_header:
            return True

        return False

    def _calculate_age(self, cached_at: str) -> str:
        """计算缓存年龄"""
        try:
            from datetime import datetime
            cached_time = datetime.fromisoformat(cached_at)
            age_seconds = (datetime.now() - cached_time).total_seconds()
            return f"{int(age_seconds)}s"
        except:
            return "unknown"


# 便捷函数: 手动清除相关缓存
async def invalidate_article_cache(article_id: int):
    """文章更新时清除相关缓存"""
    try:
        # 清除文章详情页缓存
        cache_service.invalidate_pattern(f"/p/")

        # 清除首页缓存
        cache_service.invalidate_pattern("/")

        # 清除分类页缓存
        cache_service.invalidate_pattern("/category/")

        # 清除对象缓存
        cache_service.delete_object(f"article:{article_id}")

        print(f"✓ Invalidated cache for article {article_id}")
    except Exception as e:
        print(f"✗ Cache invalidation failed: {e}")


async def invalidate_category_cache(category_id: int):
    """分类更新时清除相关缓存"""
    try:
        cache_service.invalidate_pattern("/category/")
        cache_service.delete_object(f"category:{category_id}")
        print(f"✓ Invalidated cache for category {category_id}")
    except Exception as e:
        print(f"✗ Cache invalidation failed: {e}")
