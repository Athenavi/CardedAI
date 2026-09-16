"""
性能监控中间件
自动拦截并记录所有HTTP请求的性能指标
"""


import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from shared.services.performance.performance_monitor import performance_monitor
from src.unified_logger import default_logger as logger


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    性能监控中间件

    功能:
    1. 自动记录每个请求的响应时间
    2. 跟踪请求大小和响应大小
    3. 捕获状态码和错误
    4. 支持排除特定路径(如健康检查、静态文件)
    """

    def __init__(self, app, excluded_paths: list = None):
        """
        初始化中间件

        Args:
            app: FastAPI应用实例
            excluded_paths: 需要排除的路径列表 (不监控这些路径)
        """
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            '/api/v2/health',
            '/metrics',
            '/favicon.ico',
            '/api/v2/static/',
            '/api/v2/docs',
            '/api/v2/openapi.json',
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并记录性能指标

        Args:
            request: FastAPI请求对象
            call_next: 下一个处理函数

        Returns:
            HTTP响应
        """
        # 检查是否需要排除
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.excluded_paths):
            return await call_next(request)

        # 记录开始时间
        start_time = time.perf_counter()

        try:
            # 获取请求大小
            request_size = 0
            content_length = request.headers.get('content-length')
            if content_length:
                try:
                    request_size = int(content_length)
                except ValueError:
                    pass

            # 处理请求
            response = await call_next(request)

            # 计算响应时间
            elapsed_time = time.perf_counter() - start_time

            # 获取响应大小
            response_size = int(response.headers.get('content-length', 0))

            # 记录性能指标
            performance_monitor.record_request(
                endpoint=path,
                method=request.method,
                status_code=response.status_code,
                response_time=elapsed_time,
                request_size=request_size,
                response_size=response_size,
            )

            # 添加响应头 (用于调试)
            response.headers['X-Response-Time'] = f"{elapsed_time:.4f}s"

            # 如果响应时间过长，记录警告
            if elapsed_time > 1.0:
                logger.warning(
                    f"慢请求检测: {request.method} {path}, "
                    f"耗时: {elapsed_time:.3f}s, "
                    f"状态码: {response.status_code}"
                )

            return response

        except Exception as e:
            # 即使出错也记录性能
            elapsed_time = time.perf_counter() - start_time

            performance_monitor.record_request(
                endpoint=path,
                method=request.method,
                status_code=500,
                response_time=elapsed_time,
            )

            logger.error(f"请求处理失败: {path}, 错误: {str(e)}")
            raise


# ==================== 数据库查询监控装饰器 ====================

def monitor_db_query(table_name: str = None):
    """
    数据库查询性能监控装饰器

    用法:
        @monitor_db_query(table_name='articles')
        async def get_articles():
            # 数据库查询代码
            pass

    Args:
        table_name: 表名 (可选，如果不提供则从函数名推断)

    Returns:
        装饰器函数
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.perf_counter()

            try:
                result = await func(*args, **kwargs)

                # 计算执行时间
                elapsed_time = time.perf_counter() - start_time

                # 推断表名
                table = table_name or func.__name__.replace('get_', '').replace('list_', '')

                # 记录数据库查询性能
                performance_monitor.record_db_query(
                    query=func.__name__,
                    table=table,
                    execution_time=elapsed_time,
                )

                return result

            except Exception as e:
                elapsed_time = time.perf_counter() - start_time
                table = table_name or func.__name__.replace('get_', '').replace('list_', '')

                performance_monitor.record_db_query(
                    query=func.__name__,
                    table=table,
                    execution_time=elapsed_time,
                )

                raise

        return wrapper

    return decorator


# ==================== 系统资源监控定时任务 ====================

def start_system_monitoring(interval: int = 30):
    """
    启动系统资源监控定时任务

    Args:
        interval: 采样间隔 (秒)
    """
    import threading
    import time

    def monitor_loop():
        while True:
            try:
                performance_monitor.record_system_metrics()
            except Exception as e:
                logger.error(f"系统资源监控失败: {e}")

            time.sleep(interval)

    # 启动后台线程
    thread = threading.Thread(target=monitor_loop, daemon=True)
    thread.start()

    logger.info(f"系统资源监控已启动，采样间隔: {interval}秒")
    return thread
