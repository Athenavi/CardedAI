"""
安全中间件

提供 XSS 过滤、CSRF 保护、速率限制等安全功能
"""

import re
import time
from collections import defaultdict
from typing import Dict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.unified_logger import default_logger as logger


class XSSFilterMiddleware(BaseHTTPMiddleware):
    """
    XSS 过滤中间件

    检查请求体中的内容，防止 XSS 攻击
    支持多种检测模式和智能排除
    """

    # 危险的 HTML 模式（增强版）
    DANGEROUS_PATTERNS = [
        # Script 标签
        r'<script[^>]*>.*?</script>',
        r'<script[^>]*/>',
        # JavaScript 协议
        r'javascript\s*:',
        r'vbscript\s*:',
        r'data\s*:',
        # 事件处理器
        r'on\w+\s*=\s*["\']',
        r'on\w+\s*=\s*[^\s>]',
        # 危险标签
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
        r'<applet[^>]*>',
        r'<meta[^>]*>',
        r'<link[^>]*>',
        r'<base[^>]*>',
        r'<form[^>]*>',
        r'<input[^>]*type\s*=\s*["\']?file["\']?',
        # SVG XSS
        r'<svg[^>]*on\w+',
        r'<svg[^>]*>.*?<script',
        # MathML XSS
        r'<math[^>]*>.*?<maction',
        # CSS 表达式
        r'expression\s*\(',
        r'url\s*\(\s*["\']?\s*javascript',
        # 编码绕过
        r'&#x?[0-9a-f]+;',
        r'%3[Cc]script',
        r'&lt;script',
    ]

    # 需要记录日志的严重模式
    CRITICAL_PATTERNS = [
        r'<script[^>]*>.*?(document\.cookie|localStorage|sessionStorage)',
        r'<script[^>]*>.*?(window\.location|document\.write)',
        r'on(error|load)\s*=.*?fetch\(',
    ]

    # 排除的路径（如富文本编辑器、登录接口、文件上传等）
    EXCLUDED_PATHS = [
        '/api/v1/articles/content',  # 文章内容可能包含 HTML
        '/api/v1/pages/content',  # 页面内容可能包含 HTML
        '/api/v1/auth/login',  # 登录接口（避免消耗请求体）
        '/api/v1/auth/register',  # 注册接口（避免消耗请求体）
        '/api/v1/users/auth/login',  # 用户管理模块的登录接口
        '/api/v1/users/auth/register',  # 用户管理模块的注册接口
        '/api/v1/user-settings/profile/avatar',  # 头像上传（避免消耗 multipart/form-data）
        '/api/v1/media/upload',  # 媒体文件上传（避免消耗 multipart/form-data）
    ]

    # 允许的 HTML 标签（白名单）
    ALLOWED_TAGS = {
        'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'a', 'img',
        'table', 'thead', 'tbody', 'tr', 'th', 'td',
        'div', 'span', 'section', 'article', 'header', 'footer'
    }

    # 允许的属性
    ALLOWED_ATTRIBUTES = {
        'href', 'src', 'alt', 'title', 'class', 'id',
        'width', 'height', 'target', 'rel'
    }

    def __init__(self, app, enable_logging: bool = True, strict_mode: bool = False):
        """
        初始化 XSS 过滤器

        Args:
            app: FastAPI 应用
            enable_logging: 是否启用日志记录
            strict_mode: 严格模式（拦截所有 HTML）
        """
        super().__init__(app)
        self.enable_logging = enable_logging
        self.strict_mode = strict_mode
        if enable_logging:
            logger.info("XSSFilterMiddleware initialized")

    async def dispatch(self, request: Request, call_next):
        # 检查是否在排除列表中
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS):
            return await call_next(request)

        # 只检查 POST/PUT/PATCH 请求
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.headers.get('content-type', '')

            # 检查 JSON 请求
            if 'application/json' in content_type:
                try:
                    body = await request.json()
                    xss_result = self._check_for_xss(body)
                    if xss_result['detected']:
                        self._log_attempt(request, 'json_body', xss_result)
                        return JSONResponse(
                            status_code=400,
                            content={
                                "success": False,
                                "error": "Request contains potentially dangerous content (XSS detected)",
                                "pattern_matched": xss_result.get('pattern', ''),
                                "severity": xss_result.get('severity', 'medium')
                            }
                        )
                except Exception:
                    pass

            # 检查表单数据
            elif 'application/x-www-form-urlencoded' in content_type or 'multipart/form-data' in content_type:
                try:
                    form_data = await request.form()
                    for key, value in form_data.items():
                        if isinstance(value, str):
                            xss_result = self._check_for_xss(value)
                            if xss_result['detected']:
                                self._log_attempt(request, f'form_field:{key}', xss_result)
                                return JSONResponse(
                                    status_code=400,
                                    content={
                                        "success": False,
                                        "error": f"Form field '{key}' contains dangerous content (XSS detected)",
                                        "pattern_matched": xss_result.get('pattern', ''),
                                        "severity": xss_result.get('severity', 'medium')
                                    }
                                )
                except Exception:
                    pass

        response = await call_next(request)

        # 添加安全响应头
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://fonts.gstatic.com; "
            "frame-ancestors 'self'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        return response

    def _check_for_xss(self, data) -> dict:
        """
        递归检查数据中是否包含 XSS

        Args:
            data: 要检查的数据（字符串、字典或列表）

        Returns:
            dict: {
                'detected': bool,  # 是否检测到 XSS
                'pattern': str,    # 匹配的模式
                'severity': str    # 严重程度 ('low', 'medium', 'high', 'critical')
            }
        """
        if isinstance(data, str):
            for pattern in self.DANGEROUS_PATTERNS:
                if re.search(pattern, data, re.IGNORECASE | re.DOTALL):
                    # 检查是否为严重模式
                    severity = 'medium'
                    is_critical = any(
                        re.search(critical_pattern, data, re.IGNORECASE | re.DOTALL)
                        for critical_pattern in self.CRITICAL_PATTERNS
                    )
                    if is_critical:
                        severity = 'critical'
                    elif any(p in pattern.lower() for p in ['script', 'iframe', 'object', 'embed']):
                        severity = 'high'

                    return {
                        'detected': True,
                        'pattern': pattern,
                        'severity': severity
                    }
        elif isinstance(data, dict):
            for value in data.values():
                result = self._check_for_xss(value)
                if result['detected']:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = self._check_for_xss(item)
                if result['detected']:
                    return result

        return {
            'detected': False,
            'pattern': '',
            'severity': 'none'
        }

    def _log_attempt(self, request: Request, source: str, result: dict):
        """
        记录 XSS 尝试

        Args:
            request: FastAPI 请求对象
            source: 检测来源
            result: 检测结果
        """
        if not self.enable_logging:
            return

        client_ip = request.client.host if request.client else 'unknown'
        pattern = result.get('pattern', 'unknown')
        severity = result.get('severity', 'medium')

        log_level = logger.WARNING if severity in ['high', 'critical'] else logger.INFO
        message = (
            f"XSS attempt detected from {client_ip}\n"
            f"  Method: {request.method}\n"
            f"  Path: {request.url.path}\n"
            f"  Source: {source}\n"
            f"  Pattern: {pattern}\n"
            f"  Severity: {severity}"
        )

        logger.log(log_level, message)


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    CSRF 保护中间件

    验证 CSRF token，防止跨站请求伪造
    """

    # 不需要 CSRF 验证的方法
    SAFE_METHODS = {'GET', 'HEAD', 'OPTIONS'}

    # 排除的路径（如 API 端点使用 JWT 认证）
    EXCLUDED_PATHS = ['/api/', '/auth/', '/api/v2/health']

    async def dispatch(self, request: Request, call_next):
        # GET/HEAD/OPTIONS 请求不需要 CSRF 验证
        if request.method in self.SAFE_METHODS:
            return await call_next(request)

        # 检查是否在排除列表中
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS):
            return await call_next(request)

        # 验证 CSRF token
        csrf_token = request.headers.get('X-CSRF-Token') or request.headers.get('X-XSRF-TOKEN')

        if not csrf_token:
            # 对于 API 请求，如果没有 CSRF token 但有 Authorization header，跳过检查
            auth_header = request.headers.get('Authorization')
            if auth_header:
                return await call_next(request)

            return JSONResponse(
                status_code=403,
                content={
                    "success": False,
                    "error": "CSRF token missing"
                }
            )

        # 实现实际的 CSRF token 验证逻辑
        from src.extensions import cache

        stored_token = await cache.get(f"csrf_token:{csrf_token}")
        if not stored_token:
            return JSONResponse(
                status_code=403,
                content={
                    "success": False,
                    "error": "CSRF token invalid or expired"
                }
            )

        # 验证后删除token(一次性使用)
        await cache.delete(f"csrf_token:{csrf_token}")

        response = await call_next(request)
        return response


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    速率限制中间件

    限制单个 IP 的请求频率，防止滥用和 DDoS 攻击
    支持不同端点的差异化限流策略
    """

    # 不需要速率限制的路径
    EXCLUDED_PATHS = [
        '/api/v1/thumbnail',  # 缩略图接口（频繁访问，需要豁免）
        '/api/v1/media/',  # 媒体文件接口（图片加载需要豁免）
        '/api/v2/health',  # 健康检查接口
        '/api/v2/static/',  # 静态文件
    ]

    # 敏感端点的更严格限制 {path_prefix: (max_requests, window_seconds)}
    STRICT_LIMITS = {
        '/api/v1/auth/login': (5, 60),  # 登录：5次/分钟
        '/api/v1/auth/register': (3, 300),  # 注册：3次/5分钟
        '/api/v1/users/password': (3, 300),  # 密码重置：3次/5分钟
    }

    # 默认限制
    DEFAULT_MAX_REQUESTS = 100
    DEFAULT_WINDOW_SECONDS = 60

    def __init__(self, app, max_requests: int = None, window_seconds: int = None):
        """
        初始化速率限制器

        Args:
            app: FastAPI 应用
            max_requests: 时间窗口内的最大请求数（已废弃，使用类常量）
            window_seconds: 时间窗口（秒）（已废弃，使用类常量）
        """
        super().__init__(app)
        # 使用类常量，忽略传入参数以保持向后兼容
        self.max_requests = max_requests or self.DEFAULT_MAX_REQUESTS
        self.window_seconds = window_seconds or self.DEFAULT_WINDOW_SECONDS

        # 存储每个 IP 的请求记录 {ip: [timestamp1, timestamp2, ...]}
        self.request_log: Dict[str, list] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # 检查是否在排除列表中（缩略图等频繁访问的接口）
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS):
            return await call_next(request)

        # 获取客户端 IP
        client_ip = self._get_client_ip(request)

        # 获取当前路径的速率限制配置
        max_requests, window_seconds = self._get_rate_limit_for_path(path)

        # 检查速率限制
        if not self._check_rate_limit(client_ip, path, max_requests, window_seconds):
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": "Too many requests. Please try again later.",
                    "retry_after": window_seconds
                },
                headers={
                    "Retry-After": str(window_seconds),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + window_seconds),
                }
            )

        response = await call_next(request)

        # 添加速率限制头
        remaining = self._get_remaining_requests(client_ip, path, max_requests, window_seconds)
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + window_seconds)

        return response

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实 IP"""
        # 检查代理头
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()

        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _get_rate_limit_for_path(self, path: str) -> tuple:
        """
        根据路径获取速率限制配置

        Args:
            path: 请求路径

        Returns:
            (max_requests, window_seconds) 元组
        """
        # 检查是否有针对该路径的严格限制
        for prefix, limits in self.STRICT_LIMITS.items():
            if path.startswith(prefix):
                return limits

        # 返回默认限制
        return (self.DEFAULT_MAX_REQUESTS, self.DEFAULT_WINDOW_SECONDS)

    def _check_rate_limit(self, client_ip: str, path: str, max_requests: int, window_seconds: int) -> bool:
        """检查是否超过速率限制"""
        now = time.time()
        window_start = now - window_seconds

        # 使用 IP + 路径组合作为 key，实现更细粒度的控制
        rate_key = f"{client_ip}:{path}"

        # 清理过期的请求记录
        self.request_log[rate_key] = [
            ts for ts in self.request_log[rate_key]
            if ts > window_start
        ]

        # 检查是否超过限制
        if len(self.request_log[rate_key]) >= max_requests:
            return False

        # 记录当前请求
        self.request_log[rate_key].append(now)
        return True

    def _get_remaining_requests(self, client_ip: str, path: str, max_requests: int, window_seconds: int) -> int:
        """获取剩余请求数"""
        now = time.time()
        window_start = now - window_seconds

        rate_key = f"{client_ip}:{path}"

        current_requests = len([
            ts for ts in self.request_log[rate_key]
            if ts > window_start
        ])

        return max(0, max_requests - current_requests)


class SQLInjectionFilterMiddleware(BaseHTTPMiddleware):
    """
    SQL 注入过滤中间件

    检查请求参数中的 SQL 注入模式
    支持日志记录和审计功能
    """

    # SQL 注入危险模式（增强版）
    SQL_INJECTION_PATTERNS = [
        # SQL 关键字
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|EXEC|EXECUTE)\b)",
        # SQL 注释
        r"(--|#|/\*|\*/)",
        # SQL 逻辑注入
        r"(\bOR\b\s+\d+\s*=\s*\d+)",
        r"(\bAND\b\s+\d+\s*=\s*\d+)",
        r"(\bOR\b\s+['\"][^'\"]*['\"]\s*=\s*['\"])",
        # SQL 命令分隔符
        r"(;\s*(DROP|DELETE|UPDATE|INSERT|ALTER))",
        # SQL 函数调用
        r"(\b(CONCAT|CHAR|CHR|ASCII|SUBSTRING|MID|LOAD_FILE|INTO OUTFILE|INTO DUMPFILE)\b)",
        # SQL 时间盲注
        r"(\b(SLEEP|BENCHMARK|WAITFOR DELAY)\b)",
        # SQL 错误注入
        r"(\b(EXTRACTVALUE|UPDATEXML|XMLTYPE)\b)",
    ]

    # 需要记录日志的严重模式
    CRITICAL_PATTERNS = [
        r"(\b(DROP|TRUNCATE|ALTER)\b)",
        r"(\b(INTO OUTFILE|INTO DUMPFILE)\b)",
        r"(\b(LOAD_FILE|SLEEP|BENCHMARK)\b)",
    ]

    # 排除的路径（如搜索接口可能包含 SQL 关键字、文件上传等）
    EXCLUDED_PATHS = [
        '/api/v1/search',  # 搜索接口
        '/api/v1/auth/login',  # 登录接口（避免消耗请求体）
        '/api/v1/auth/register',  # 注册接口（避免消耗请求体）
        '/api/v1/users/auth/login',  # 用户管理模块的登录接口
        '/api/v1/users/auth/register',  # 用户管理模块的注册接口
        '/api/v1/user-settings/profile/avatar',  # 头像上传（避免消耗请求体）
        '/api/v1/media/upload',  # 媒体文件上传（避免消耗请求体）
    ]

    def __init__(self, app, enable_logging: bool = True):
        """
        初始化 SQL 注入过滤器

        Args:
            app: FastAPI 应用
            enable_logging: 是否启用日志记录
        """
        super().__init__(app)
        self.enable_logging = enable_logging
        if enable_logging:
            logger.info("SQL注入过滤器已启动")

    async def dispatch(self, request: Request, call_next):
        # 检查是否在排除列表中
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS):
            return await call_next(request)

        # 检查查询参数
        query_params = dict(request.query_params)
        injection_result = self._check_sql_injection(query_params)
        if injection_result['detected']:
            self._log_attempt(request, 'query_params', injection_result)
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Invalid request parameters (SQL injection detected)",
                    "pattern_matched": injection_result.get('pattern', '')
                }
            )

        # 检查 POST/PUT/PATCH 请求体
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.headers.get('content-type', '')

            if 'application/json' in content_type:
                try:
                    body = await request.json()
                    injection_result = self._check_sql_injection(body)
                    if injection_result['detected']:
                        self._log_attempt(request, 'request_body', injection_result)
                        return JSONResponse(
                            status_code=400,
                            content={
                                "success": False,
                                "error": "Request body contains invalid content (SQL injection detected)",
                                "pattern_matched": injection_result.get('pattern', '')
                            }
                        )
                except Exception:
                    pass

        response = await call_next(request)
        return response

    def _log_attempt(self, request: Request, source: str, result: dict):
        """
        记录 SQL 注入尝试

        Args:
            request: FastAPI 请求对象
            source: 检测来源 ('query_params' 或 'request_body')
            result: 检测结果
        """
        if not self.enable_logging:
            return

        client_ip = request.client.host if request.client else 'unknown'
        pattern = result.get('pattern', 'unknown')
        is_critical = result.get('is_critical', False)

        log_level = logger.WARNING if is_critical else logger.INFO
        message = (
            f"SQL Injection attempt detected from {client_ip}\n"
            f"  Method: {request.method}\n"
            f"  Path: {request.url.path}\n"
            f"  Source: {source}\n"
            f"  Pattern: {pattern}\n"
            f"  Critical: {is_critical}"
        )

        logger.log(log_level, message)

    def _check_sql_injection(self, data) -> dict:
        """
        递归检查 SQL 注入

        Args:
            data: 要检查的数据（字符串、字典或列表）

        Returns:
            dict: {
                'detected': bool,  # 是否检测到 SQL 注入
                'pattern': str,    # 匹配的模式
                'is_critical': bool  # 是否为严重威胁
            }
        """
        if isinstance(data, str):
            for pattern in self.SQL_INJECTION_PATTERNS:
                if re.search(pattern, data, re.IGNORECASE):
                    # 检查是否为严重模式
                    is_critical = any(
                        re.search(critical_pattern, data, re.IGNORECASE)
                        for critical_pattern in self.CRITICAL_PATTERNS
                    )
                    return {
                        'detected': True,
                        'pattern': pattern,
                        'is_critical': is_critical
                    }
        elif isinstance(data, dict):
            for value in data.values():
                result = self._check_sql_injection(value)
                if result['detected']:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = self._check_sql_injection(item)
                if result['detected']:
                    return result

        return {
            'detected': False,
            'pattern': '',
            'is_critical': False
        }


def create_security_middleware_stack(app):
    """
    创建安全中间件栈（不包含速率限制）

    Args:
        app: FastAPI 应用

    Returns:
        添加了安全中间件的应用
    """
    # 按顺序添加中间件（后添加的先执行）
    # 已经注释1 2 它们可能影响绝大多数路由的正确执行
    # 1. SQL 注入过滤（最外层）
    # app.add_middleware(SQLInjectionFilterMiddleware)

    # 2. XSS 过滤
    # app.add_middleware(XSSFilterMiddleware)

    # 3. CSRF 保护
    app.add_middleware(CSRFProtectionMiddleware)

    # 注意：速率限制已移除，改为在特定路由上使用装饰器方式

    return app
