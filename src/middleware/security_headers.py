"""
安全响应头中间件

纯 ASGI 实现（不经过 BaseHTTPMiddleware），避免给每个请求增加额外的
任务调度开销。已存在的同名响应头不会被覆盖，便于个别路由（如受限静态
文件服务）下发更严格的策略。
"""

from typing import Dict, Optional

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class SecurityHeadersMiddleware:
    """为所有 HTTP 响应补充安全相关响应头"""

    def __init__(
        self,
        app: ASGIApp,
        headers: Optional[Dict[str, str]] = None,
        hsts_max_age: int = 31536000,
    ):
        self.app = app
        self.headers = headers or {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            # 老浏览器兜底；现代浏览器以 CSP 为准
            "X-XSS-Protection": "1; mode=block",
        }
        self.hsts_max_age = hsts_max_age

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        is_https = scope.get("scheme") == "https" or any(
            name == b"x-forwarded-proto" and value == b"https"
            for name, value in scope.get("headers", [])
        )

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for key, value in self.headers.items():
                    if key not in headers:
                        headers[key] = value
                # HSTS 只在 HTTPS 下有意义，HTTP 下下发会被浏览器忽略
                if is_https and "strict-transport-security" not in headers:
                    headers["Strict-Transport-Security"] = (
                        f"max-age={self.hsts_max_age}; includeSubDomains"
                    )
            await send(message)

        await self.app(scope, receive, send_wrapper)


__all__ = ["SecurityHeadersMiddleware"]
