"""
HTTP 缓存中间件 - 支持 ETag、Last-Modified 和条件请求

功能:
- 自动生成 ETag（基于响应内容哈希）
- 支持 Last-Modified 头
- 处理 If-None-Match 条件请求（返回 304）
- 处理 If-Modified-Since 条件请求（返回 304）
- 自动添加 Cache-Control 头
- 可配置跳过特定路径和方法
"""

import hashlib
import time
from datetime import datetime, timezone
from typing import Callable, List, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class HttpCacheMiddleware(BaseHTTPMiddleware):
    """
    HTTP 缓存中间件

    实现 RFC 7232 条件请求规范
    支持 ETag 和 Last-Modified 验证
    """

    def __init__(
            self,
            app,
            enable_etag: bool = True,
            enable_last_modified: bool = True,
            default_cache_ttl: int = 300,
            skip_paths: Optional[List[str]] = None,
            skip_methods: Optional[List[str]] = None,
            cache_public_only: bool = True,
    ):
        """
        初始化 HTTP 缓存中间件

        Args:
            app: FastAPI 应用
            enable_etag: 是否启用 ETag
            enable_last_modified: 是否启用 Last-Modified
            default_cache_ttl: 默认缓存 TTL（秒）
            skip_paths: 跳过缓存的路径列表
            skip_methods: 跳过缓存的 HTTP 方法列表
            cache_public_only: 只缓存公开响应（非认证请求）
        """
        super().__init__(app)
        self.enable_etag = enable_etag
        self.enable_last_modified = enable_last_modified
        self.default_cache_ttl = default_cache_ttl
        self.skip_paths = skip_paths or [
            '/admin',
            '/api/v1/auth',
            '/api/v2/auth',
            '/api/v1/user',
            '/login',
            '/register',
            '/api/v1/installation',
        ]
        self.skip_methods = skip_methods or ['POST', 'PUT', 'DELETE', 'PATCH']
        self.cache_public_only = cache_public_only

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 检查是否应该跳过缓存
        if self._should_skip_cache(request):
            return await call_next(request)

        # 只处理 GET 和 HEAD 请求
        if request.method not in ['GET', 'HEAD']:
            return await call_next(request)

        # 调用下一个处理程序获取响应
        response = await call_next(request)

        # 对于 HEAD 请求，直接返回（不计算 ETag）
        if request.method == 'HEAD':
            return self._add_cache_headers(response, request, is_head=True)

        # 读取响应体以计算 ETag
        response_body = b''
        async for chunk in response.body_iterator:
            response_body += chunk

        # 计算 ETag
        etag = None
        if self.enable_etag and response_body:
            etag = self._generate_etag(response_body)

        # 获取或设置 Last-Modified
        last_modified = None
        if self.enable_last_modified:
            last_modified = response.headers.get('last-modified')
            if not last_modified:
                # 使用当前时间作为 Last-Modified
                last_modified = self._format_http_datetime(time.time())

        # 检查条件请求
        conditional_response = self._check_conditional_request(
            request, etag, last_modified
        )

        if conditional_response:
            # 返回 304 Not Modified
            return conditional_response

        # 添加缓存头到正常响应
        response = self._add_cache_headers(
            response, request, etag, last_modified, response_body
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

        # 如果只缓存公开响应，检查是否有认证
        if self.cache_public_only:
            auth_header = request.headers.get('authorization')
            if auth_header:
                return True

        # 检查查询参数中的 no-cache
        if 'no-cache' in request.query_params:
            return True

        # 检查 Cache-Control 请求头
        cache_control = request.headers.get('cache-control', '')
        if 'no-cache' in cache_control or 'no-store' in cache_control:
            return True

        return False

    def _generate_etag(self, content: bytes) -> str:
        """
        生成 ETag

        Args:
            content: 响应内容

        Returns:
            ETag 字符串（强验证器）
        """
        hash_value = hashlib.md5(content).hexdigest()
        return f'"{hash_value}"'

    def _format_http_datetime(self, timestamp: float) -> str:
        """
        格式化时间为 HTTP 日期格式

        Args:
            timestamp: Unix 时间戳

        Returns:
            HTTP 日期字符串 (RFC 7231)
        """
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return dt.strftime('%a, %d %b %Y %H:%M:%S GMT')

    def _parse_http_datetime(self, date_string: str) -> Optional[float]:
        """
        解析 HTTP 日期字符串

        Args:
            date_string: HTTP 日期字符串

        Returns:
            Unix 时间戳，解析失败返回 None
        """
        try:
            # 尝试解析多种格式
            formats = [
                '%a, %d %b %Y %H:%M:%S GMT',
                '%A, %d-%b-%y %H:%M:%S GMT',
                '%a %b %d %H:%M:%S %Y',
            ]

            for fmt in formats:
                try:
                    dt = datetime.strptime(date_string, fmt)
                    dt = dt.replace(tzinfo=timezone.utc)
                    return dt.timestamp()
                except ValueError:
                    continue

            return None
        except Exception:
            return None

    def _check_conditional_request(
            self,
            request: Request,
            etag: Optional[str],
            last_modified: Optional[str]
    ) -> Optional[Response]:
        """
        检查条件请求

        Args:
            request: FastAPI 请求
            etag: 响应的 ETag
            last_modified: 响应的 Last-Modified

        Returns:
            如果满足条件返回 304 响应，否则返回 None
        """
        # 检查 If-None-Match
        if_none_match = request.headers.get('if-none-match')
        if if_none_match and etag:
            # 支持多个 ETag 和通配符 *
            if if_none_match == '*' or if_none_match == etag:
                return Response(status_code=304, headers={
                    'ETag': etag,
                    'Cache-Control': f'public, max-age={self.default_cache_ttl}',
                })

            # 处理逗号分隔的多个 ETag
            etags = [e.strip() for e in if_none_match.split(',')]
            if etag in etags:
                return Response(status_code=304, headers={
                    'ETag': etag,
                    'Cache-Control': f'public, max-age={self.default_cache_ttl}',
                })

        # 检查 If-Modified-Since
        if_modified_since = request.headers.get('if-modified-since')
        if if_modified_since and last_modified:
            client_time = self._parse_http_datetime(if_modified_since)
            server_time = self._parse_http_datetime(last_modified)

            if client_time is not None and server_time is not None:
                # 如果资源未修改（服务器时间 <= 客户端时间），返回 304
                if server_time <= client_time:
                    return Response(status_code=304, headers={
                        'Last-Modified': last_modified,
                        'Cache-Control': f'public, max-age={self.default_cache_ttl}',
                    })

        return None

    def _add_cache_headers(
            self,
            response: Response,
            request: Request,
            etag: Optional[str] = None,
            last_modified: Optional[str] = None,
            response_body: bytes = b'',
            is_head: bool = False,
    ) -> Response:
        """
        添加缓存头到响应

        Args:
            response: FastAPI 响应
            request: FastAPI 请求
            etag: ETag 值
            last_modified: Last-Modified 值
            response_body: 响应体
            is_head: 是否为 HEAD 请求

        Returns:
            添加了缓存头的响应
        """
        # 添加 ETag
        if etag:
            response.headers['ETag'] = etag

        # 添加 Last-Modified
        if last_modified:
            response.headers['Last-Modified'] = last_modified

        # 添加 Cache-Control
        if 'cache-control' not in response.headers:
            # 根据响应状态码设置不同的缓存策略
            if response.status_code == 200:
                response.headers['Cache-Control'] = f'public, max-age={self.default_cache_ttl}'
            elif response.status_code in [301, 302]:
                # 重定向缓存较长时间
                response.headers['Cache-Control'] = 'public, max-age=3600'
            elif response.status_code >= 400:
                # 错误响应不缓存或短时间缓存
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'

        # 添加 Vary 头（指示缓存键包含哪些请求头）
        if 'vary' not in response.headers:
            vary_headers = []
            if 'accept-encoding' in request.headers:
                vary_headers.append('Accept-Encoding')
            if 'authorization' in request.headers:
                vary_headers.append('Authorization')

            if vary_headers:
                response.headers['Vary'] = ', '.join(vary_headers)

        # 对于 HEAD 请求，不需要重新设置 body
        if is_head:
            return response

        # 重新设置响应体（因为之前已经读取了）

        async def body_iterator():
            yield response_body

        response.body_iterator = body_iterator()
        response.headers['Content-Length'] = str(len(response_body))

        # 添加自定义缓存头用于调试
        response.headers['X-Cache-Status'] = 'MISS'
        response.headers['X-Cache-TTL'] = str(self.default_cache_ttl)

        return response


# 导出中间件
__all__ = ['HttpCacheMiddleware']
