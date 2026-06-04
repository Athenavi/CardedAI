"""
FastAPI 到 Django 的适配器层
允许在 Django 中直接使用 FastAPI 的路由和视图函数

使用方法:
1. 在 django_blog/urls.py 中包含 fastapi_urls.py
2. FastAPI 路由将自动注册到 /api/v1/... 路径
3. 无需修改任何 FastAPI 代码！

重要提示 - 生成器依赖清理:
----------------------------------
如果您的 FastAPI 代码使用 yield 定义依赖（如数据库会话），需要在 Django settings.py 中添加：

    MIDDLEWARE = [
        # ... 其他中间件
        'django_blog.fastapi_adapter.GeneratorDependencyCleanupMiddleware',  # 必须放在最后
    ]

注意：
- middlewares 参数已废弃，请改用 Django 的全局 MIDDLEWARE 配置
- CSRF 豁免路径可通过环境变量 FASTAPI_CSRF_EXEMPT_PATHS 自定义（默认：auth/login,auth/register）
- 请求体大小限制可通过 FASTAPI_ADAPTER_MAX_BODY_SIZE 调整（默认：10MB）
- 调试模式通过 DJANGO_DEBUG 控制（默认：False）

参考 Django Ninja 源码实现：
- ninja.Router: https://github.com/vitalik/django-ninja
- ninja.operation: Operation 类处理请求/响应
- ninja.params: Form, Query, Path 等参数解析
"""

import asyncio
import atexit
import os
import re
import sys
from functools import wraps, lru_cache
from threading import Thread, Lock
from typing import get_origin, get_args, Annotated

# 将 src 目录添加到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 使用统一的日志系统
from src.unified_logger import default_logger as logger

from django.http import JsonResponse, HttpResponse
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404 as DjangoHttp404

# 安全配置 - 请求体大小限制（10MB，可通过环境变量覆盖）
MAX_BODY_SIZE = int(os.getenv('FASTAPI_ADAPTER_MAX_BODY_SIZE', 10 * 1024 * 1024))

# 调试模式配置 - 控制错误详情是否返回给客户端
DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'

# 默认超时时间（秒，可通过环境变量覆盖）
DEFAULT_TIMEOUT = float(os.getenv('FASTAPI_ADAPTER_DEFAULT_TIMEOUT', 30.0))

# 事件循环关闭时的异步生成器清理超时（秒，可通过环境变量覆盖）
EVENT_LOOP_SHUTDOWN_TIMEOUT = float(os.getenv('FASTAPI_ADAPTER_EVENT_LOOP_SHUTDOWN_TIMEOUT', 5.0))

# 预编译正则表达式（性能优化）
PARAM_PATTERN = re.compile(r'\{(\w+)(?::(\w+))?\}')

# 类型映射常量
# 注意：float 需要 Django 的自定义转换器，见下方的 register_converter
PATH_TYPE_MAP = {
    'str': 'str',
    'int': 'int',
    'float': 'float',  # 使用自定义的 float 转换器
    'path': 'path',
    'uuid': 'uuid'
}


# 自动注册 Django float 路径转换器（如果尚未注册）
class FloatConverter:
    """
    Django 浮点数路径转换器
    匹配形如 3.14, 100, 0.5 等浮点数
    """
    regex = r'[0-9]+(?:\.[0-9]+)?'

    def to_python(self, value):
        return float(value)

    def to_url(self, value):
        return str(value)


try:
    from django.urls import register_converter

    register_converter(FloatConverter, 'float')
    logger.debug("Registered float path converter")
except Exception as e:
    logger.debug(f"Float converter may already be registered: {e}")


def _make_hashable(value):
    """
    将值转换为可哈希的形式，用于缓存键生成
    
    Args:
        value: 任意值
    
    Returns:
        可哈希的表示形式
    
    性能优化：
    - 快速识别请求对象（MockRequest、HttpRequest）并返回 None，避免深度遍历
    - 这些对象包含循环引用和大 __dict__，会导致严重的性能问题
    - 对于其他不可哈希对象（如 list/dict 嵌套），递归转换其内容
    
    注意：
    - 如果参数包含无法识别的不可哈希类型，缓存将被禁用（返回 None）
    - 这确保了依赖缓存系统的安全性，不会因哈希冲突导致错误
    """
    # 快速路径：特殊处理已知的不可哈希类型（如请求对象）
    if hasattr(value, 'django_request') or hasattr(value, 'META'):
        # MockRequest 或 Django HttpRequest，直接返回 None 禁用缓存
        logger.debug(f"Detected request object, disabling cache for this parameter")
        return None

    if value is None:
        return None
    elif isinstance(value, (str, int, float, bool, bytes)):
        return value
    elif isinstance(value, (list, tuple)):
        return tuple(_make_hashable(item) for item in value)
    elif isinstance(value, dict):
        return tuple(sorted((_make_hashable(k), _make_hashable(v)) for k, v in value.items()))
    elif hasattr(value, '__dict__'):
        # 直接哈希其 __dict__，不使用 repr
        # repr 可能包含内存地址导致每次返回值不同
        return _make_hashable(value.__dict__)
    else:
        # 其他不可哈希类型，返回 None 表示不缓存
        logger.debug(f"Cannot hash value of type {type(value).__name__}, will not cache")
        return None


def _make_cache_key(func, kwargs):
    """
    生成包含函数和参数值的缓存键
    解决 use_cache 未考虑参数的问题
    
    Args:
        func: 依赖函数
        kwargs: 参数字典
    
    Returns:
        可哈希的缓存键，如果参数不可哈希则返回 None
    """
    # 使用函数对象本身（而不是 id）避免 ID 重用导致的缓存冲突
    # 函数对象在 Python 中是可哈希的，且生命周期通常很长
    items = []
    for k, v in kwargs.items():
        h = _make_hashable(v)
        if h is None:
            # 存在不可哈希参数，禁用缓存
            logger.debug(f"Cannot cache dependency {func.__name__}: parameter '{k}' is not hashable")
            return None
        items.append((k, h))

    return (func, tuple(sorted(items)))


@lru_cache(maxsize=1024)
def _convert_fastapi_path_to_django(fastapi_path, view_func=None):
    """
    将 FastAPI 路径转换为 Django 路径（带缓存）
    
    Args:
        fastapi_path: FastAPI 风格路径，如 /users/{user_id:int}
        view_func: 视图函数，用于推断参数类型（可选）
    
    Returns:
        Django 风格路径，如 /users/<int:user_id>
    """

    def replace_param(match):
        param_name = match.group(1)
        param_type = match.group(2) or 'str'  # 默认使用 str
        django_type = PATH_TYPE_MAP.get(param_type, 'str')
        return f'<{django_type}:{param_name}>'

    # 首先尝试直接使用正则表达式转换
    result = PARAM_PATTERN.sub(replace_param, fastapi_path)

    # 如果没有显式类型声明，尝试从函数签名中推断类型
    if view_func and '{' in fastapi_path:
        import inspect
        from fastapi import params as fastapi_params

        try:
            sig = _get_function_signature(view_func)
            for param_match in PARAM_PATTERN.finditer(fastapi_path):
                param_name = param_match.group(1)
                param_type_in_path = param_match.group(2)

                # 如果路径中没有指定类型，尝试从函数签名推断
                if not param_type_in_path and param_name in sig.parameters:
                    func_param = sig.parameters[param_name]
                    param_annotation = func_param.annotation

                    # 根据类型注解推断 Django 类型
                    # 使用正则替换避免错误替换其他部分
                    if param_annotation == int:
                        # 精确替换 <str:param_name> 为 <int:param_name>
                        result = re.sub(
                            f'<str:{re.escape(param_name)}>',
                            f'<int:{param_name}>',
                            result
                        )
                        logger.debug(f"Inferred int type for parameter: {param_name}")
                    elif param_annotation == float:
                        # float 映射为 str，无需替换
                        pass
                    elif param_annotation == str:
                        # 已经是 str，无需替换
                        pass
                    elif hasattr(param_annotation, '__name__') and param_annotation.__name__ == 'UUID':
                        result = re.sub(
                            f'<str:{re.escape(param_name)}>',
                            f'<uuid:{param_name}>',
                            result
                        )
        except Exception as e:
            # 如果推断失败，使用默认的 str 类型
            logger.debug(f"Failed to infer parameter type for parameter in {fastapi_path}: {e}")

    logger.debug(f"Converted path: {fastapi_path} -> {result}")
    return result


@lru_cache(maxsize=1024)
def _get_function_signature(func):
    """
    获取函数签名（带缓存）
    避免反复调用 inspect.signature 的开销
    
    Args:
        func: 函数对象
    
    Returns:
        inspect.Signature 对象
    """
    import inspect
    return inspect.signature(func)


# 创建持久事件循环（在模块级别）
_loop = None
_loop_thread = None
_loop_lock = Lock()  # 保护事件循环创建的锁
_shutdown_lock = Lock()  # 保护关闭过程的锁
_shutdown_started = False  # 标记是否已开始关闭

# 全局后台任务集合，用于在进程退出前等待所有任务完成
_pending_background_tasks = set()
_pending_tasks_lock = Lock()  # 保护后台任务集合的线程安全
# 限制最大并发后台任务数，防止内存泄漏
MAX_PENDING_TASKS = int(os.getenv('FASTAPI_ADAPTER_MAX_PENDING_TASKS', 100))

# 请求体读取并发控制信号量（防止线程池耗尽）
# 可通过环境变量配置并发数（默认最多 10 个并发读取）
_BODY_SEMAPHORE_SIZE = int(os.getenv('FASTAPI_ADAPTER_BODY_SEMAPHORE_SIZE', 10))
# 在模块级别直接初始化信号量，避免延迟初始化的复杂性
# asyncio.Semaphore 可以在无事件循环时创建，会在首次使用时绑定到当前循环
_body_semaphore = asyncio.Semaphore(_BODY_SEMAPHORE_SIZE)


def _shutdown_event_loop():
    """
    在进程退出时关闭事件循环线程
    使用 atexit 注册
    
    改进：
    - 将线程设为非 daemon，并在 atexit 中优雅停止循环并 join 线程
    - 增加超时机制，防止阻塞进程退出
    - 确保生成器依赖的 finally 块执行
    - 调用 shutdown_asyncgens() 清理残留的异步生成器
    - 取消所有待处理的后台任务
    """
    global _loop, _loop_thread, _shutdown_started

    # 使用锁保护避免重复关闭
    with _shutdown_lock:
        if _shutdown_started:
            return
        _shutdown_started = True

    if _loop and not _loop.is_closed():
        try:
            logger.info("Shutting down async event loop...")

            # 先取消所有待处理的后台任务
            if _pending_background_tasks:
                # 使用锁保护避免竞态条件
                with _pending_tasks_lock:
                    tasks_to_cancel = list(_pending_background_tasks)

                logger.info(f"Cancelling {len(tasks_to_cancel)} pending background task(s)")
                for task in tasks_to_cancel:
                    task.cancel()
                # 等待取消完成
                if tasks_to_cancel:
                    try:
                        asyncio.run_coroutine_threadsafe(
                            asyncio.gather(*tasks_to_cancel, return_exceptions=True),
                            _loop
                        ).result(timeout=2.0)
                    except Exception:
                        pass
                with _pending_tasks_lock:
                    _pending_background_tasks.clear()

            # 先清理异步生成器
            try:
                async def cleanup_async_gens():
                    await _loop.shutdown_asyncgens()

                # 在事件循环中执行清理（超时可配置）
                future = asyncio.run_coroutine_threadsafe(cleanup_async_gens(), _loop)
                future.result(timeout=EVENT_LOOP_SHUTDOWN_TIMEOUT)
                logger.debug("Async generators cleaned up")
            except Exception as e:
                logger.debug(f"Async generator cleanup during shutdown: {e}")

            # 取消所有未完成的任务
            try:
                pending = asyncio.all_tasks(_loop)
                if pending:
                    logger.info(f"Cancelling {len(pending)} pending task(s)")
                    for task in pending:
                        task.cancel()
                    # 等待取消完成
                    asyncio.run_coroutine_threadsafe(
                        asyncio.gather(*pending, return_exceptions=True),
                        _loop
                    ).result(timeout=2.0)
            except Exception as e:
                logger.debug(f"Task cancellation during shutdown: {e}")

            # 安全地停止事件循环
            _loop.call_soon_threadsafe(_loop.stop)

            # 等待线程结束（最多 5 秒）
            if _loop_thread and _loop_thread.is_alive():
                _loop_thread.join(timeout=5.0)
                if _loop_thread.is_alive():
                    logger.warning("Event loop thread did not terminate gracefully, forcing shutdown")

            # 关闭事件循环
            if not _loop.is_closed():
                _loop.close()

            logger.info("Async event loop shut down complete")
        except Exception as e:
            logger.error(f"Error shutting down event loop: {e}")
        finally:
            # 重置全局变量
            _loop = None
            _loop_thread = None


# 注册退出钩子
atexit.register(_shutdown_event_loop)


def get_or_create_event_loop():
    """
    获取或创建持久事件循环
    避免反复创建/销毁事件循环的开销
    自动处理循环关闭并重建
    使用线程锁保护防止多线程竞态条件
    """
    global _loop, _loop_thread

    # 检测循环是否已关闭，需要重建
    if _loop is None or _loop.is_closed():
        # 使用锁保护防止多线程同时创建
        with _loop_lock:
            # 双重检查锁定（避免在等待锁时已被其他线程创建）
            if _loop is None or _loop.is_closed():
                # 创建新的事件循环
                _loop = asyncio.new_event_loop()

                # 在后台线程中运行事件循环
                def run_loop():
                    asyncio.set_event_loop(_loop)
                    _loop.run_forever()

                _loop_thread = Thread(target=run_loop, daemon=False)  # 改为非 daemon 线程
                _loop_thread.start()

    return _loop


def run_async_coroutine(coroutine, timeout=DEFAULT_TIMEOUT):
    """
    在持久事件循环中运行异步协程
    使用 asyncio.run_coroutine_threadsafe 确保线程安全
    支持超时控制
    自动检测事件循环健康状态，必要时重建
    
    Args:
        coroutine: 要执行的协程
        timeout: 超时时间（秒），默认使用 DEFAULT_TIMEOUT
    """
    # 每次调用都获取最新的事件循环（可能已重建）
    loop = get_or_create_event_loop()

    # 检测事件循环是否健康
    if loop.is_closed():
        # 循环已关闭，需要重建
        logger.warning("Event loop is closed, recreating...")
        # 直接调用 get_or_create_event_loop() 会内部加锁重建，无需手动重置
        loop = get_or_create_event_loop()

    future = asyncio.run_coroutine_threadsafe(coroutine, loop)
    try:
        return future.result(timeout=timeout)
    except asyncio.TimeoutError:
        # 超时时取消协程，避免资源泄漏
        future.cancel()
        logger.error(f"Coroutine timed out after {timeout}s and was cancelled")
        raise
    except Exception as e:
        logger.error(f"Error running coroutine: {e}")
        raise


class FastAPIToDjangoAdapter:
    """
    FastAPI 到 Django 适配器
    
    将 FastAPI 的 Request 对象转换为 Django 的 HttpRequest
    将 FastAPI 的响应转换为 Django 的 HttpResponse
    """

    # 中间件列表（可在注册时自定义）
    middlewares = []

    @staticmethod
    class MockBackgroundTasks:
        """
        模拟 FastAPI 的 BackgroundTasks 接口
        收集后台任务并在请求结束后执行
        """

        def __init__(self):
            self.tasks = []

        def add_task(self, func, *args, **kwargs):
            """添加后台任务"""
            self.tasks.append((func, args, kwargs))

        async def __call__(self):
            """异步执行所有后台任务"""
            for func, args, kwargs in self.tasks:
                try:
                    if asyncio.iscoroutinefunction(func):
                        await func(*args, **kwargs)
                    else:
                        # 同步函数在线程池中执行
                        await asyncio.to_thread(func, *args, **kwargs)
                except Exception as e:
                    logger.error(f"Background task error: {e}")

    @classmethod
    def set_middlewares(cls, middleware_list):
        """
        设置 Django 中间件列表
        中间件将在调用视图前后执行
        """
        cls.middlewares = middleware_list

    @staticmethod
    class MockUploadFile:
        """
        模拟 FastAPI 的 UploadFile 接口
        包装 Django 的 UploadedFile 对象
        使用 asyncio.to_thread 避免阻塞事件循环
        
        注意：
        - read() 方法支持分块读取，建议用户使用 chunk_size（如 8KB）避免内存溢出
        - 提供 __aiter__() 方法支持异步迭代
        - 单次读取大小受 MAX_BODY_SIZE 限制
        """

        def __init__(self, django_file):
            self.file = django_file
            self.filename = getattr(django_file, 'name', 'unknown')
            self.content_type = getattr(django_file, 'content_type', 'application/octet-stream')
            self._file_obj = django_file

        async def read(self, size=-1):
            """
            读取文件内容
            
            Args:
                size: 读取字节数，-1 表示读取全部（默认）
            
            Returns:
                文件内容（bytes）
            
            ⚠️ 注意：
            - size=-1 时会尝试一次性读取整个文件到内存
            - 大文件建议使用异步迭代：async for chunk in file
            - 文件大小超过 MAX_BODY_SIZE 会抛出 413 错误
            """
            # 检查文件大小（如果可用）
            if size == -1 and hasattr(self._file_obj, 'size') and self._file_obj.size is not None:
                if self._file_obj.size > MAX_BODY_SIZE:
                    from fastapi import HTTPException
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large (max {MAX_BODY_SIZE // 1024 // 1024}MB)"
                    )
                # 小文件可以直接读取全部
                return await asyncio.to_thread(self._file_obj.read)
            elif size == -1:
                # 文件大小未知，使用分块读取避免 OOM
                chunks = []
                total_size = 0
                while True:
                    chunk = await asyncio.to_thread(self._file_obj.read, 8192)
                    if not chunk:
                        break
                    total_size += len(chunk)
                    if total_size > MAX_BODY_SIZE:
                        from fastapi import HTTPException
                        raise HTTPException(
                            status_code=413,
                            detail=f"File too large (max {MAX_BODY_SIZE // 1024 // 1024}MB)"
                        )
                    chunks.append(chunk)
                return b''.join(chunks)
            else:
                # 分块读取模式
                # 限制单次读取大小，避免大文件占用过多内存
                size = min(size, MAX_BODY_SIZE)  # 不超过最大限制
                return await asyncio.to_thread(self._file_obj.read, size)

        async def write(self, data):
            # Django 的 UploadedFile 不支持写入操作
            raise NotImplementedError("UploadFile.write() is not supported for Django UploadedFile")

        async def close(self):
            await asyncio.to_thread(self._file_obj.close)

        async def seek(self, pos):
            await asyncio.to_thread(self._file_obj.seek, pos)

        async def __aiter__(self):
            """
            异步迭代器支持，用于分块读取文件
            每次迭代返回 8KB 的数据块
            """
            while True:
                chunk = await self.read(8192)
                if not chunk:
                    break
                yield chunk

    @staticmethod
    def convert_django_request_to_fastapi(django_request, path_params=None):
        """
        将 Django 的 HttpRequest 转换为类似 FastAPI 的 Request 对象
        
        由于 FastAPI 基于 Starlette，我们需要模拟其接口
        
        Args:
            django_request: Django 请求对象
            path_params: 路径参数 dict
        """

        class MockRequest:
            def __init__(self, django_req, path_params=None):
                self.method = django_req.method
                self.headers = dict(django_req.headers)
                self.query_params = django_req.GET
                self.cookies = django_req.COOKIES
                self._body = None
                self._json = None
                self.django_request = django_req
                self.state = type('State', (), {})()  # 用于存储中间件添加的状态
                self.client = type('Client', (), {'host': django_req.META.get('REMOTE_ADDR', '127.0.0.1')})()
                self.url = type('URL', (), {'path': django_req.path, 'scheme': 'http'})()
                self.path_params = path_params or {}  # 路径参数

                # 先创建后台任务对象，再赋值给 self 和原始请求
                self.background_tasks = FastAPIToDjangoAdapter.MockBackgroundTasks()

                # 将后台任务对象也挂载到原始 Django request 上
                original_request = django_req
                original_request._fastapi_background_tasks = self.background_tasks

                # 添加 FastAPI/Starlette 兼容的 scope
                self.scope = {
                    "type": "http",
                    "method": django_req.method,
                    "path": django_req.path,
                    "headers": [[k.encode(), v.encode()] for k, v in django_req.headers.items()],
                    "query_string": django_req.GET.urlencode().encode() if django_req.GET else b"",
                    "client": (self.client.host, 0),
                    "server": (django_req.META.get('SERVER_NAME', 'localhost'),
                               django_req.META.get('SERVER_PORT', '80')),
                }

                # 添加 app 属性（可选）
                self.app = None

                # receive 和 send 对于普通 HTTP 请求不是必需的
                self.receive = None
                self.send = None

            async def body(self):
                if self._body is None:
                    # 提前检查 Content-Length header，避免大请求占用内存
                    content_length = self.django_request.META.get('CONTENT_LENGTH')
                    if content_length and int(content_length) > MAX_BODY_SIZE:
                        from fastapi import HTTPException
                        raise HTTPException(
                            status_code=413,
                            detail=f"Request body too large (max {MAX_BODY_SIZE // 1024 // 1024}MB)"
                        )

                    # 优化：使用 asyncio.to_thread 避免阻塞事件循环
                    # Django 的 request.body 是同步属性，会触发整个请求体的读取
                    # 必须在线程池中执行，防止阻塞其他并发请求
                    # 使用信号量限制并发读取数量，防止线程池耗尽
                    try:
                        async with _body_semaphore:
                            self._body = await asyncio.to_thread(lambda: self.django_request.body)
                    except Exception as e:
                        # Django 抛出 RequestDataTooBig 时的处理
                        logger.warning(f"Request body too large, using streaming: {e}")
                        # 回退到流式读取（同样使用 to_thread，但不受信号量限制）
                        chunks = []
                        total_size = 0
                        while True:
                            chunk = await asyncio.to_thread(lambda: self.django_request.read(8192))
                            if not chunk:
                                break
                            total_size += len(chunk)
                            if total_size > MAX_BODY_SIZE:
                                from fastapi import HTTPException
                                raise HTTPException(
                                    status_code=413,
                                    detail=f"Request body too large (max {MAX_BODY_SIZE // 1024 // 1024}MB)"
                                )
                            chunks.append(chunk)
                        self._body = b''.join(chunks)
                return self._body

            async def json(self):
                if self._json is None:
                    import json
                    try:
                        # 使用已实现流式读取的 body() 方法
                        body_data = await self.body()
                        self._json = json.loads(body_data.decode('utf-8'))
                    except json.JSONDecodeError:
                        self._json = {}
                return self._json

            async def stream(self, chunk_size=8192):
                """
                流式读取请求体，避免大文件占用过多内存
                        
                Args:
                    chunk_size: 每次读取的字节数，默认 8KB
                        
                Yields:
                    数据块（bytes）
                """
                # 真正的流式读取，不预先加载整个 body
                total_size = 0
                while True:
                    chunk = await asyncio.to_thread(lambda: self.django_request.read(chunk_size))
                    if not chunk:
                        break
                    total_size += len(chunk)
                    if total_size > MAX_BODY_SIZE:
                        from fastapi import HTTPException
                        raise HTTPException(
                            status_code=413,
                            detail=f"Request body too large (max {MAX_BODY_SIZE // 1024 // 1024}MB)"
                        )
                    yield chunk

        return MockRequest(django_request, path_params)

    @staticmethod
    def convert_fastapi_response_to_django(fastapi_response):
        """
        将 FastAPI/Starlette 的 Response 转换为 Django 的 HttpResponse
        
        参考 Django Ninja 的响应处理逻辑：
        - 处理 JSONResponse（包括 Pydantic 模型）
        - 处理普通 Response
        - 处理字典和自定义响应对象
        - 自动设置状态码和 headers
        - 支持 StreamingResponse 流式响应
        """
        from starlette.responses import JSONResponse as StarletteJSONResponse
        from starlette.responses import Response as StarletteResponse
        from starlette.responses import StreamingResponse
        from fastapi.responses import JSONResponse as FastAPIJSONResponse
        from django.http import StreamingHttpResponse
        import json

        # 如果是 Starlette/FastAPI 的 StreamingResponse
        if isinstance(fastapi_response, StreamingResponse):
            logger.debug("Converting StreamingResponse to StreamingHttpResponse")
            # 将异步迭代器转换为同步生成器，解决 Django 无法消费异步迭代器的问题
            # 改进：使用独立线程运行生产者，避免阻塞事件循环
            import queue
            import threading

            def sync_wrapper(async_iter):
                """将异步迭代器转换为同步生成器
                
                使用独立线程运行生产者协程，避免阻塞事件循环：
                - 创建独立线程运行生产者协程（不占用事件循环线程）
                - 事件循环线程负责从 async_iter 获取数据
                - 请求线程作为消费者，从队列中取出数据 yield 给客户端
                
                ⚠️ 性能警告：
                - 每个 chunk 都会阻塞请求线程，降低并发能力
                - 对于大文件，建议使用 Django 原生的 FileResponse
                - 仅推荐用于小数据量的流式传输（如 SSE 事件）
                """
                # 创建一个有界队列（最多缓冲 10 个 chunk）
                q = queue.Queue(maxsize=10)
                sentinel = object()  # 结束标记
                loop = get_or_create_event_loop()
                stop_event = threading.Event()
                producer_error = [None]  # 使用列表存储异常，便于内部函数修改

                # 生产者函数：在独立线程中运行，不阻塞事件循环
                def producer_thread():
                    """在线程中运行生产者协程"""

                    async def run_producer():
                        try:
                            while not stop_event.is_set():
                                try:
                                    # 每次获取一个 chunk（带超时保护）
                                    future = asyncio.run_coroutine_threadsafe(
                                        async_iter.__anext__(), loop
                                    )
                                    chunk = future.result(timeout=DEFAULT_TIMEOUT)
                                    # 使用超时 put，避免队列满时永久阻塞
                                    while not stop_event.is_set():
                                        try:
                                            q.put(chunk, timeout=0.5)
                                            break
                                        except queue.Full:
                                            continue
                                except StopAsyncIteration:
                                    break
                                except asyncio.TimeoutError:
                                    logger.warning("StreamingResponse chunk timeout")
                                    break
                                except Exception as e:
                                    logger.error(f"StreamingResponse producer error: {e}")
                                    producer_error[0] = e
                                    break
                        finally:
                            # 确保 sentinel 被放入，即使队列已满
                            while not stop_event.is_set():
                                try:
                                    q.put(sentinel, timeout=0.5)
                                    break
                                except queue.Full:
                                    continue

                    # 在线程中运行协程
                    try:
                        # 如果当前没有运行的事件循环，创建一个新的
                        try:
                            asyncio.get_running_loop()
                            # 已有事件循环，直接运行
                            loop.call_soon_threadsafe(asyncio.create_task, run_producer())
                        except RuntimeError:
                            # 没有事件循环，在当前线程创建一个并运行
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            new_loop.run_until_complete(run_producer())
                            new_loop.close()
                    except Exception as e:
                        logger.error(f"Producer thread error: {e}")
                        producer_error[0] = e

                # 启动生产者线程（非 daemon 线程，确保能完成清理）
                producer_thread = threading.Thread(target=producer_thread, daemon=False)
                producer_thread.start()

                try:
                    # 消费者：从队列中取出数据并 yield
                    while True:
                        try:
                            item = q.get(timeout=5.0)  # 减小超时时间至 5 秒
                            if item is sentinel:
                                # 检查是否有生产者错误
                                if producer_error[0]:
                                    raise producer_error[0]
                                break
                            yield item
                        except queue.Empty:
                            logger.warning("StreamingResponse consumer timeout (5s)")
                            # 继续等待，直到遇到 sentinel 或停止事件
                            if stop_event.is_set():
                                break
                finally:
                    # 设置停止标志并等待生产者线程结束
                    stop_event.set()
                    producer_thread.join(timeout=2.0)  # 增加等待时间
                    # 清空队列中剩余的数据
                    while not q.empty():
                        try:
                            q.get_nowait()
                        except queue.Empty:
                            break

            return StreamingHttpResponse(
                streaming_content=sync_wrapper(fastapi_response.body_iterator),
                status=fastapi_response.status_code,
                content_type=fastapi_response.headers.get('content-type', 'application/octet-stream')
            )

        # 如果是 Starlette/FastAPI 的 JSONResponse
        if isinstance(fastapi_response, (StarletteJSONResponse, FastAPIJSONResponse)):
            # 解析 body 内容为 Python 对象
            try:
                content = fastapi_response.body.decode('utf-8') if isinstance(fastapi_response.body, bytes) else str(
                    fastapi_response.body)
                data = json.loads(content)

                # 使用解析后的数据创建 JsonResponse
                django_response = JsonResponse(
                    data=data,
                    status=fastapi_response.status_code,
                    safe=False
                )
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                # 如果解析失败，回退到原始内容
                django_response = HttpResponse(
                    content=fastapi_response.body if isinstance(fastapi_response.body,
                                                                bytes) else fastapi_response.body.encode('utf-8'),
                    status=fastapi_response.status_code,
                    content_type='application/json'
                )
            # 复制 headers
            for header, value in fastapi_response.headers.items():
                if header.lower() == 'set-cookie':
                    # 使用 append_header 支持多个 Set-Cookie
                    django_response.headers.append_header('Set-Cookie', value)
                else:
                    django_response[header] = value
            return django_response

        # 如果是 Starlette 的普通 Response
        elif isinstance(fastapi_response, StarletteResponse):
            # 处理状态码 204 且 body 为 None 的情况
            if fastapi_response.status_code == 204 and fastapi_response.body is None:
                django_response = HttpResponse(status=204)
            else:
                # 通用处理：body=None 时转换为空字节串
                content = fastapi_response.body if fastapi_response.body is not None else b''
                if isinstance(content, bytes):
                    django_response = HttpResponse(
                        content=content,
                        status=fastapi_response.status_code
                    )
                else:
                    django_response = HttpResponse(
                        content=content.encode('utf-8'),
                        status=fastapi_response.status_code
                    )
            for header, value in fastapi_response.headers.items():
                django_response[header] = value
            return django_response

        # 如果是字典或 ApiResponse 对象
        elif isinstance(fastapi_response, dict):
            return JsonResponse(fastapi_response)

        # 如果是 ApiResponse 对象（来自 src.api.v1.responses）
        elif hasattr(fastapi_response, '__dict__'):
            # 检查是否有 model_dump 或 dict 方法
            if hasattr(fastapi_response, 'model_dump'):
                data = fastapi_response.model_dump(mode='json')
            elif hasattr(fastapi_response, 'dict'):
                data = fastapi_response.dict()
            else:
                # 否则使用 __dict__
                data = fastapi_response.__dict__

            # 提取 status_code（如果存在）
            status_code = getattr(fastapi_response, 'status_code', 200)

            return JsonResponse(data, status=status_code)

        # 如果是其他类型，尝试直接返回
        else:
            return HttpResponse(str(fastapi_response))

    @staticmethod
    def _get_depends_obj(param_annotation, param_default):
        """
        统一获取 Depends 对象
        优先从 param_default 获取，其次从 Annotated 元数据获取
        
        Args:
            param_annotation: 参数注解
            param_default: 参数默认值
        
        Returns:
            Depends 对象或 None
        """
        from fastapi import params as fastapi_params

        # 优先从 default 获取
        if isinstance(param_default, fastapi_params.Depends):
            return param_default

        # 从 Annotated 元数据获取
        if param_annotation and get_origin(param_annotation) is Annotated:
            annotated_args = get_args(param_annotation)
            for arg in annotated_args:
                if isinstance(arg, fastapi_params.Depends):
                    return arg

        return None

    @staticmethod
    def _parse_common_parameters(sig, request, mock_request, base_kwargs, is_dependency=False):
        """
        通用参数解析函数（支持 Path、Query、Header、Cookie、Body、Form、File 等）
        
        Args:
            sig: 函数签名对象
            request: Django 请求对象
            mock_request: MockRequest 对象
            base_kwargs: 基础参数字典（路径参数等）
            is_dependency: 是否为依赖函数参数解析（默认 False）
        
        Returns:
            parsed_kwargs: 解析后的参数字典
        """
        import inspect
        from fastapi import params as fastapi_params, HTTPException
        from pydantic import BaseModel
        from pydantic.error_wrappers import ValidationError

        parsed_kwargs = {}

        # 分析每个参数
        for param_name, param in sig.parameters.items():
            # 已经在 base_kwargs 中的参数（路径参数等）
            if param_name in base_kwargs:
                parsed_kwargs[param_name] = base_kwargs[param_name]
                continue

            # request 参数
            if param_name == 'request':
                parsed_kwargs['request'] = mock_request
                continue

            # 检查是否是 Depends 注入
            param_annotation = param.annotation if param.annotation != inspect.Parameter.empty else None
            param_default = param.default if param.default is not inspect.Parameter.empty else None

            # 使用统一函数获取 Depends 对象
            depends_obj = FastAPIToDjangoAdapter._get_depends_obj(param_annotation, param_default)

            # 调试日志：打印参数信息
            if param_name in ['db', 'request']:
                print(f"\n[ADAPTER DEBUG] Parameter '{param_name}':")
                print(f"  - annotation: {param_annotation}")
                print(f"  - default_type: {type(param_default).__name__}")
                print(f"  - depends_obj: {depends_obj}")
                print(f"  - is_Depends: {isinstance(param_default, fastapi_params.Depends)}")

            # 优先处理具体的参数类型（Form、Query 等）
            if isinstance(param_default, fastapi_params.Form):
                # Form 参数 - 从 POST 数据中获取
                default_value = param_default.default
                is_required = default_value is ...
                form_value = request.POST.get(param_name)
                if form_value is None:
                    if is_required:
                        raise HTTPException(status_code=422, detail=f"Missing required parameter: {param_name}")
                    form_value = default_value
                param_type = param.annotation if param.annotation != inspect.Parameter.empty else str
                parsed_kwargs[param_name] = FastAPIToDjangoAdapter._convert_param_type(form_value, param_type,
                                                                                       param_name)
                continue

            elif isinstance(param_default, fastapi_params.Query):
                # Query 参数 - 从 request 中获取
                default_value = param_default.default
                is_required = default_value is ...
                param_type = param.annotation if param.annotation != inspect.Parameter.empty else str

                if param_type in (list, tuple) or get_origin(param_type) in (list, tuple):
                    # 支持多值查询参数
                    query_value = mock_request.query_params.getlist(param_name)
                    if not query_value:
                        if is_required:
                            raise HTTPException(status_code=422, detail=f"Missing required parameter: {param_name}")
                        # 使用默认值（如果有），否则为空列表
                        query_value = default_value if default_value is not ... else []
                else:
                    query_value = mock_request.query_params.get(param_name)
                    if query_value is None:
                        if is_required:
                            raise HTTPException(status_code=422, detail=f"Missing required parameter: {param_name}")
                        query_value = default_value
                parsed_kwargs[param_name] = FastAPIToDjangoAdapter._convert_param_type(query_value, param_type,
                                                                                       param_name)
                continue

            elif isinstance(param_default, fastapi_params.Path):
                # Path 参数 - 从 base_kwargs 获取（应该已经存在）
                path_value = base_kwargs.get(param_name)
                if path_value is None:
                    raise HTTPException(status_code=422, detail=f"Missing path parameter: {param_name}")
                param_type = param.annotation if param.annotation != inspect.Parameter.empty else str
                parsed_kwargs[param_name] = FastAPIToDjangoAdapter._convert_param_type(path_value, param_type,
                                                                                       param_name)
                continue

            elif isinstance(param_default, fastapi_params.Cookie):
                # Cookie 参数 - 从 cookies 中获取
                default_value = param_default.default
                is_required = default_value is ...

                # 使用 alias（如果指定）
                cookie_key = getattr(param_default, 'alias', param_name)
                cookie_value = mock_request.cookies.get(cookie_key)

                # 必填参数校验
                if cookie_value is None:
                    if is_required:
                        raise HTTPException(status_code=422, detail=f"Missing required cookie: {param_name}")
                    cookie_value = default_value
                param_type = param.annotation if param.annotation != inspect.Parameter.empty else str
                parsed_kwargs[param_name] = FastAPIToDjangoAdapter._convert_param_type(cookie_value, param_type,
                                                                                       param_name)
                continue

            elif isinstance(param_default, fastapi_params.Header):
                # Header 参数 - 从 headers 中获取（注意连字符转换）
                default_value = param_default.default
                is_required = default_value is ...

                # 检查 convert_underscores 属性（默认 True）
                convert_underscores = getattr(param_default, 'convert_underscores', True)
                if convert_underscores:
                    header_key = param_name.replace('_', '-').lower()
                else:
                    header_key = param_name.lower()

                # 使用大小写不敏感的查找方式
                header_value = None
                for key, value in request.headers.items():
                    if key.lower() == header_key.lower():
                        header_value = value
                        break

                # 必填参数校验
                if header_value is None:
                    if is_required:
                        raise HTTPException(status_code=422, detail=f"Missing required header: {param_name}")
                    header_value = default_value
                param_type = param.annotation if param.annotation != inspect.Parameter.empty else str
                parsed_kwargs[param_name] = FastAPIToDjangoAdapter._convert_param_type(header_value, param_type,
                                                                                       param_name)
                continue

            elif isinstance(param_default, fastapi_params.Body):
                # Body 参数 - 从 request body 中获取
                # ⚠️ 性能警告：同步 I/O 操作可能阻塞事件循环
                # 建议：避免在依赖函数中使用 Body 参数，应在视图函数中处理
                content_type = request.content_type
                if not content_type or not content_type.startswith('application/json'):
                    raise HTTPException(
                        status_code=415,
                        detail=f"Expected Content-Type: application/json, got: {content_type or 'None'}"
                    )

                try:
                    import json
                    body_data = request.body.decode('utf-8')
                    parsed_body = json.loads(body_data) if body_data else {}

                    # 检查 embed 属性
                    embed = getattr(param_default, 'embed', False)

                    if param.annotation and issubclass(param.annotation, BaseModel):
                        # Pydantic 模型：根据 embed 决定如何解析
                        if embed:
                            # Body(embed=True) 期望 body 为 {param_name: actual_value}
                            # 如果请求体不是字典，直接使用整个请求体作为值
                            if isinstance(parsed_body, dict):
                                model_data = parsed_body.get(param_name,
                                                             parsed_body if param_name not in parsed_body else {})
                            else:
                                # 请求体是数组或原始类型，直接使用
                                model_data = parsed_body

                            # 类型检查：确保 model_data 是字典或可以转换为模型
                            if not isinstance(model_data, dict):
                                raise HTTPException(
                                    status_code=422,
                                    detail=f"Expected object for '{param_name}', got {type(model_data).__name__}"
                                )
                            try:
                                parsed_kwargs[param_name] = param.annotation(**model_data)
                            except ValidationError as ve:
                                raise HTTPException(status_code=422, detail=ve.errors())
                        else:
                            # 整个 body 作为模型数据
                            try:
                                parsed_kwargs[param_name] = param.annotation(**parsed_body)
                            except ValidationError as ve:
                                raise HTTPException(status_code=422, detail=ve.errors())
                    elif param.annotation and hasattr(param.annotation, '__fields__'):
                        # 其他有 __fields__ 的类
                        if embed and isinstance(parsed_body, dict):
                            parsed_kwargs[param_name] = parsed_body.get(param_name, parsed_body)
                        else:
                            parsed_kwargs[param_name] = parsed_body
                    else:
                        # 普通类型（dict、list 等）
                        if embed:
                            # Body(embed=True) 期望 body 为 {param_name: actual_value}
                            # 如果请求体不是字典，直接使用整个请求体作为值
                            if isinstance(parsed_body, dict):
                                parsed_kwargs[param_name] = parsed_body.get(param_name, parsed_body)
                            else:
                                parsed_kwargs[param_name] = parsed_body
                        else:
                            # 整个 body 作为参数值
                            parsed_kwargs[param_name] = parsed_body
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    # 生产环境脱敏处理
                    detail = str(e) if DEBUG else "Invalid JSON body"
                    raise HTTPException(status_code=422, detail=detail)
                continue

            elif isinstance(param_default, fastapi_params.File):
                # File 参数 - 从 request.FILES 中获取
                # ⚠️ 性能警告：同步 I/O 操作可能阻塞事件循环
                # 建议：避免在依赖函数中使用 File 参数，应在视图函数中处理
                default_value = param_default.default
                is_required = default_value is ...
                django_file = request.FILES.get(param_name)
                if django_file is None:
                    if is_required:
                        raise HTTPException(status_code=422, detail=f"Missing required file: {param_name}")
                    parsed_kwargs[param_name] = default_value
                else:
                    parsed_kwargs[param_name] = FastAPIToDjangoAdapter.MockUploadFile(django_file)
                continue

            # 检查是否是 BackgroundTasks 类型（仅视图函数需要）
            elif not is_dependency and hasattr(param.annotation,
                                               '__name__') and param.annotation.__name__ == 'BackgroundTasks':
                # 注入后台任务对象
                parsed_kwargs[param_name] = mock_request.background_tasks
                continue

            # Depends 嵌套依赖 - 递归解析（仅依赖函数需要）
            elif is_dependency and depends_obj:
                dependency = depends_obj.dependency
                use_cache = getattr(depends_obj, 'use_cache', True)
                if dependency:
                    dep_value = FastAPIToDjangoAdapter._resolve_dependency(
                        dependency, mock_request, parsed_kwargs, set(), use_cache
                    )
                    parsed_kwargs[param_name] = dep_value
                else:
                    logger.warning(f"Depends object has no dependency attribute for {param_name}")
                    parsed_kwargs[param_name] = None
                continue

            # 普通 Depends 注入（视图函数模式）
            elif not is_dependency and depends_obj:
                # 视图函数中的 Depends 参数（如 db: AsyncSession = Depends(get_async_session)）
                dependency = depends_obj.dependency
                use_cache = getattr(depends_obj, 'use_cache', True)
                if dependency:
                    dep_value = FastAPIToDjangoAdapter._resolve_dependency(
                        dependency, mock_request, parsed_kwargs, set(), use_cache
                    )
                    parsed_kwargs[param_name] = dep_value
                else:
                    logger.warning(f"Depends object has no dependency attribute for {param_name}")
                    parsed_kwargs[param_name] = None
                continue

            # 普通参数 - 尝试从 query string 获取
            if hasattr(mock_request, 'query_params') and param_name in mock_request.query_params:
                value = mock_request.query_params.get(param_name)
                param_type = param.annotation if param.annotation != inspect.Parameter.empty else str
                parsed_kwargs[param_name] = FastAPIToDjangoAdapter._convert_param_type(value, param_type, param_name)
            elif param.default != inspect.Parameter.empty:
                # 使用默认值（区分是否为 Param 对象）
                default_value = param.default
                if hasattr(default_value, 'default'):
                    default_value = default_value.default
                if default_value is ...:
                    raise HTTPException(status_code=422, detail=f"Missing required parameter: {param_name}")
                parsed_kwargs[param_name] = default_value

        return parsed_kwargs

    @staticmethod
    def _parse_parameters(sig, request, mock_request, kwargs):
        """
        解析 FastAPI 视图函数的参数
        
        Args:
            sig: 函数签名对象
            request: Django 请求对象
            mock_request: MockRequest 对象
            kwargs: 路径参数
        
        Returns:
            view_kwargs: 解析后的参数字典
        """
        # 复用通用参数解析函数
        return FastAPIToDjangoAdapter._parse_common_parameters(sig, request, mock_request, kwargs, is_dependency=False)

    @staticmethod
    def _convert_param_type(value, param_type, param_name: str):
        """
        转换参数类型，支持更多类型
        
        Args:
            value: 要转换的值
            param_type: 目标类型
            param_name: 参数名称
        
        Returns:
            转换后的值
        """
        if value is None:
            return None

        try:
            if param_type == int:
                return int(value)
            elif param_type == float:
                return float(value)
            elif param_type == bool:
                # 完善 bool 转换逻辑，正确处理 "false", "0" 等字符串
                if isinstance(value, str):
                    val_lower = value.lower()
                    if val_lower in ('true', '1', 'yes', 'on', 'y'):
                        return True
                    if val_lower in ('false', '0', 'no', 'off', 'n'):
                        return False
                    # 默认按字符串非空判断（兼容旧行为）
                    return bool(value)
                return bool(value)
            elif param_type == str:
                return str(value)
            elif hasattr(param_type, '__name__') and param_type.__name__ == 'UUID':
                import uuid
                return uuid.UUID(str(value)) if value else None
            elif hasattr(param_type, '__name__') and param_type.__name__ == 'datetime':
                from datetime import datetime
                if isinstance(value, str):
                    # 尝试 ISO 格式
                    try:
                        return datetime.fromisoformat(value)
                    except ValueError:
                        pass
                return value  # 保持原值
            else:
                # 对于其他类型，尝试直接返回
                return value
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not convert {param_name} to {param_type}: {e}")
            return value

    @staticmethod
    def wrap_fastapi_view(fastapi_view_func, middlewares=None, response_model=None,
                          response_model_exclude_unset=False, response_model_include=None,
                          response_model_exclude=None, response_model_by_alias=True,
                          global_deps=None, timeout=None):
        """
        装饰器：将 FastAPI 视图函数包装为 Django 视图函数
        完整支持 FastAPI 的依赖注入系统
        
        参考 Django Ninja 的实现方式：
        - Ninja 使用 Operation.run() 方法执行视图函数
        - 支持异步和同步视图
        - 自动解析 Form、Query、Path、Cookie、Header、File 等参数
        - 支持路由级全局依赖（router.dependencies）
        - 支持请求级别的超时配置
        
        Args:
            fastapi_view_func: FastAPI 视图函数
            middlewares: Django 中间件列表（可选），现已废弃，改用 Django 全局中间件
            response_model: Pydantic 响应模型（可选）
            response_model_exclude_unset: 是否排除未设置的字段
            response_model_include: 只包含的字段集合
            response_model_exclude: 排除的字段集合
            response_model_by_alias: 是否使用别名
            global_deps: 路由级全局依赖列表（可选）
            timeout: 请求超时时间（秒），None 使用默认值
        """
        import inspect
        from fastapi import HTTPException
        from pydantic import BaseModel
        from pydantic.error_wrappers import ValidationError

        # 获取函数签名用于分析（使用 lru_cache 优化）
        sig = _get_function_signature(fastapi_view_func)
        return_annotation = sig.return_annotation

        # 检测是否有 Pydantic 模型作为返回类型（优先使用 response_model）
        is_pydantic_return = False
        actual_response_model = response_model
        if actual_response_model:
            is_pydantic_return = isinstance(actual_response_model, type) and issubclass(actual_response_model,
                                                                                        BaseModel)
        else:
            if return_annotation != inspect.Parameter.empty:
                if isinstance(return_annotation, type) and issubclass(return_annotation, BaseModel):
                    is_pydantic_return = True
                    actual_response_model = return_annotation
                elif hasattr(return_annotation, '__origin__'):  # 处理 Union 等泛型
                    origin = return_annotation.__origin__
                    if hasattr(origin, '__args__'):
                        for arg in origin.__args__:
                            if isinstance(arg, type) and issubclass(arg, BaseModel):
                                is_pydantic_return = True
                                actual_response_model = arg
                                break

        @wraps(fastapi_view_func)
        def wrapper(request, *args, **kwargs):
            # 中间件功能已废弃，改用 Django 全局中间件
            # 保留此代码仅为向后兼容，实际不再使用
            if middlewares:
                logger.warning(
                    "The 'middlewares' parameter is deprecated. "
                    "Please use Django's global MIDDLEWARE setting instead."
                )

            # 转换请求对象，传入路径参数
            mock_request = FastAPIToDjangoAdapter.convert_django_request_to_fastapi(request, path_params=kwargs)

            # 1. 先解析路由级全局依赖（router.dependencies）并注入到视图函数参数
            #    全局依赖可能依赖于路径参数，所以需要先传入 kwargs
            resolved_global_deps = {}
            if global_deps:
                for dep in global_deps:
                    dependency_func = dep.dependency if hasattr(dep, 'dependency') else dep
                    resolved_value = FastAPIToDjangoAdapter._resolve_dependency(
                        dependency_func,
                        mock_request,
                        kwargs  # 传入路径参数，供依赖函数使用
                    )
                    # 尝试获取依赖函数名
                    dep_name = getattr(dep, '__name__', None)
                    if not dep_name and hasattr(dependency_func, '__name__'):
                        dep_name = dependency_func.__name__

                    # 如果依赖函数有返回值且视图函数有同名参数，注入到 view_kwargs
                    if resolved_value is not None and dep_name and dep_name in sig.parameters:
                        resolved_global_deps[dep_name] = resolved_value
                        logger.debug(f"Injected global dependency {dep_name} into view kwargs")

                    # 同时存储到 request.state 中让开发者可以自行获取
                    if not hasattr(mock_request.state, 'global_deps'):
                        mock_request.state.global_deps = {}
                    if dep_name:
                        mock_request.state.global_deps[dep_name] = resolved_value

            # 2. 解析视图函数普通参数（包括 Depends、Query、Path 等）
            #    此时 _parse_parameters 可以访问 mock_request.state.global_deps
            view_kwargs = FastAPIToDjangoAdapter._parse_parameters(sig, request, mock_request, kwargs)

            # 3. 将全局依赖合并到视图参数中（如果视图有同名参数，以全局依赖为准）
            view_kwargs.update(resolved_global_deps)

            # 运行异步的 FastAPI 视图函数（使用持久事件循环）
            try:
                # 性能监控：记录执行时间
                import time
                start_time = time.perf_counter()

                # 调用 FastAPI 视图函数，传入 mock_request 和路径参数
                fastapi_response = run_async_coroutine(
                    fastapi_view_func(**view_kwargs),
                    timeout=timeout if timeout is not None else DEFAULT_TIMEOUT
                )

                elapsed = time.perf_counter() - start_time
                if elapsed > 1.0:  # 超过 1 秒记录警告
                    logger.warning(f"Slow view {fastapi_view_func.__name__}: {elapsed:.2f}s")

                # 如果是 Pydantic 模型，应用 response_model 序列化
                if is_pydantic_return and actual_response_model:
                    # 构建 model_dump 的参数
                    dump_kwargs = {
                        'mode': 'json',
                        'exclude_unset': response_model_exclude_unset,
                        'by_alias': response_model_by_alias
                    }
                    if response_model_include:
                        dump_kwargs['include'] = response_model_include
                    if response_model_exclude:
                        dump_kwargs['exclude'] = response_model_exclude

                    if isinstance(fastapi_response, BaseModel):
                        # 已经是 Pydantic 模型，直接序列化
                        fastapi_response = fastapi_response.model_dump(**dump_kwargs)
                    elif isinstance(fastapi_response, dict):
                        # 是字典，用 response_model 验证
                        validated = actual_response_model(**fastapi_response)
                        fastapi_response = validated.model_dump(**dump_kwargs)

                # 转换响应（参考 Ninja 的 Response 渲染逻辑）
                django_response = FastAPIToDjangoAdapter.convert_fastapi_response_to_django(fastapi_response)

                return django_response

            except HTTPException as e:
                # FastAPI HTTPException - 返回对应的状态码
                logger.warning(f"[HTTPException] {e.status_code}: {e.detail}")
                response = JsonResponse({
                    'success': False,
                    'error': e.detail if isinstance(e.detail, str) else str(e.detail),
                    'status_code': e.status_code
                }, status=e.status_code)
                # 复制 HTTPException 的 headers（如 WWW-Authenticate）
                if hasattr(e, 'headers') and e.headers:
                    for key, value in e.headers.items():
                        response[key] = value
                return response

            except ValidationError as ve:
                # Pydantic 验证错误 - 返回 422
                logger.error(f"[Validation Error] {ve}")
                # 构建标准化的错误响应格式（兼容 FastAPI）
                if DEBUG:
                    # 开发环境：返回完整错误详情
                    details = ve.errors()
                else:
                    # 生产环境：脱敏处理，但保留错误结构
                    details = []
                    for error in ve.errors():
                        # 只保留基本错误信息，隐藏敏感数据
                        details.append({
                            'loc': error.get('loc', []),
                            'msg': 'Validation failed',
                            'type': error.get('type', 'value_error')
                        })

                return JsonResponse({
                    'success': False,
                    'error': 'Validation Error',
                    'detail': details
                }, status=422)

            except DjangoHttp404 as e:
                # Django 404 错误 - 返回 404
                logger.warning(f"[404 Error] {e}")
                return JsonResponse({
                    'success': False,
                    'error': 'Not Found'
                }, status=404)

            except DjangoValidationError as e:
                # Django 验证错误 - 返回 422
                logger.error(f"[Django Validation Error] {e}")
                # 生产环境脱敏处理
                if DEBUG:
                    details = str(e)
                else:
                    details = "Validation failed"
                return JsonResponse({
                    'success': False,
                    'error': 'Validation Error',
                    'details': details
                }, status=422)

            except Exception as e:
                import traceback
                logger.error(f"FastAPI view error: {e}")
                logger.error(traceback.format_exc())

                # 特殊处理超时错误 - 返回 504
                if isinstance(e, asyncio.TimeoutError):
                    return JsonResponse({
                        'success': False,
                        'error': 'Gateway Timeout',
                        'type': 'TimeoutError'
                    }, status=504)

                # 生产环境错误脱敏
                if DEBUG:
                    error_detail = str(e)
                    error_type = type(e).__name__
                else:
                    error_detail = "Internal server error"
                    error_type = "ServerError"

                return JsonResponse({
                    'success': False,
                    'error': error_detail,
                    'type': error_type
                }, status=500)
            # 注意：生成器清理已移至中间件，避免重复清理

        return wrapper

    @staticmethod
    def _parse_dependency_parameters(sig, request, mock_request, view_kwargs):
        """
        解析依赖函数的参数（支持 Path、Query、Header、Cookie、Body 等）
        复用 _parse_common_parameters 方法
        
        Args:
            sig: 函数签名对象
            request: Django 请求对象
            mock_request: MockRequest 对象
            view_kwargs: 视图已解析的参数（用于填充路径参数等）
        
        Returns:
            dep_kwargs: 解析后的参数字典
        """
        # 复用通用参数解析函数，标记为依赖函数模式
        return FastAPIToDjangoAdapter._parse_common_parameters(sig, request, mock_request, view_kwargs,
                                                               is_dependency=True)

    @staticmethod
    def _resolve_dependency(dependency, request, view_kwargs, _stack=None, use_cache=True):
        """
        递归解析 FastAPI 的 Depends 注入
        支持生成器依赖（yield）的生命周期管理
        支持 use_cache 参数缓存依赖结果
        
        Args:
            dependency: 依赖函数
            request: Mock 请求对象
            view_kwargs: 视图函数参数
            _stack: 调用栈集合（用于检测循环依赖，内部使用）
            use_cache: 是否缓存依赖结果（默认 True）
        
        Returns:
            解析后的依赖值
        
        Raises:
            HTTPException: 当依赖解析失败时抛出 500 错误
        
        ⚠️ 性能提示:
        - 依赖函数中应避免使用 Body、Form、File 等会触发同步 I/O 的参数
        - 这些操作会阻塞事件循环线程，降低并发能力
        - 如需处理请求体或文件，建议在视图函数中进行而非依赖函数
        """
        import inspect
        from fastapi import HTTPException

        # 初始化调用栈（用于检测循环依赖）
        if _stack is None:
            _stack = set()

        if not callable(dependency):
            return None

        # 获取依赖函数的签名（使用缓存）
        dep_sig = _get_function_signature(dependency)

        # 使用新的参数解析方法（支持 Path、Query、Header 等）
        dep_kwargs = FastAPIToDjangoAdapter._parse_dependency_parameters(
            dep_sig, request.django_request, request, view_kwargs
        )

        # 使用调用栈检测循环依赖（而非全局已访问集合）
        # 这样允许同一依赖函数在不同路径中被调用（只要不在同一调用链中）
        dep_id = id(dependency)
        if dep_id in _stack:
            logger.warning(f"Circular dependency detected: {dependency.__name__}")
            return None

        # 标记为当前调用栈
        _stack.add(dep_id)

        try:
            # 初始化缓存键（避免 UnboundLocalError）
            cache_key = None
            
            # 检查依赖缓存（use_cache 功能）
            if use_cache and hasattr(request.state, 'dependencies_cache'):
                # 使用参数化缓存键，解决相同依赖函数不同参数的问题
                cache_key = _make_cache_key(dependency, dep_kwargs)
                if cache_key is not None and cache_key in request.state.dependencies_cache:
                    logger.debug(f"Cache hit for dependency: {dependency.__name__}")
                    return request.state.dependencies_cache[cache_key]

            # 执行依赖函数 (支持生成器依赖)
            # 检测同步生成器
            if inspect.isgeneratorfunction(dependency):
                gen = dependency(**dep_kwargs)
                value = next(gen)  # 执行到第一个 yield
                # 存储生成器到原始 Django request 对象，确保中间件可以访问
                original_request = request.django_request
                if not hasattr(original_request, '_fastapi_generator_deps'):
                    original_request._fastapi_generator_deps = []
                original_request._fastapi_generator_deps.append(gen)
                result = value

            # 检测异步生成器
            elif inspect.isasyncgenfunction(dependency):
                agen = dependency(**dep_kwargs)
                value = run_async_coroutine(agen.__anext__())  # 执行到第一个 yield
                # 存储异步生成器到原始 Django request 对象
                original_request = request.django_request
                if not hasattr(original_request, '_fastapi_async_generator_deps'):
                    original_request._fastapi_async_generator_deps = []
                original_request._fastapi_async_generator_deps.append(agen)
                result = value

            # 普通协程函数
            elif inspect.iscoroutinefunction(dependency):
                result = run_async_coroutine(dependency(**dep_kwargs))

            # 同步函数
            else:
                result = dependency(**dep_kwargs)

            # 缓存依赖结果 (use_cache 功能)
            if use_cache and cache_key is not None:
                if not hasattr(request.state, 'dependencies_cache'):
                    request.state.dependencies_cache = {}
                request.state.dependencies_cache[cache_key] = result
                logger.debug(f"Cached dependency result: {dependency.__name__}")

            return result
        except HTTPException:
            # 重新抛出 HTTPException，保持原有的错误处理
            raise
        except Exception as e:
            # 依赖解析失败应抛出明确异常，而不是返回 None
            import traceback
            dep_name = getattr(dependency, '__name__', f'<anonymous_dep_{id(dependency)}>')
            error_msg = f"[Dependency Resolution Error] {dep_name}: {e}"
            logger.error(error_msg)
            logger.error(f"  Parameters: {dep_kwargs.keys() if dep_kwargs else 'none'}")
            logger.error(f"  Traceback:\n{traceback.format_exc()}")
            # 抛出 500 错误，让调用者知道依赖解析失败
            raise HTTPException(status_code=500, detail=f"Dependency '{dep_name}' failed: {str(e)}")
        finally:
            # 从调用栈中移除，允许同一函数在不同路径中被调用
            _stack.discard(dep_id)


def register_fastapi_router(router, prefix='', tags=None, middlewares=None):
    """
    将 FastAPI Router 注册到 Django URL 配置
    
    参考 Django Ninja 的 Router.register() 方法实现：
    - 遍历 router.routes 获取所有注册的路由
    - 将 FastAPI 路径参数转换为 Django 路径参数
    - 使用 wrap_fastapi_view 包装视图函数
    - 支持嵌套路由器
    - 自动处理路由级全局依赖（router.dependencies）
    - 自动添加 GeneratorDependencyCleanupMiddleware（如果未提供，已废弃）
    
    Args:
        router: FastAPI 的 APIRouter 实例
        prefix: URL 前缀
        tags: 标签列表（用于文档）
        middlewares: Django 中间件列表（可选），已废弃，请使用 Django 全局 MIDDLEWARE 配置
    
    Returns:
        Django URL patterns
    """
    from django.urls import path

    urlpatterns = []

    # middlewares 参数已废弃警告
    if middlewares:
        logger.warning(
            "The 'middlewares' parameter in register_fastapi_router is deprecated. "
            "Please use Django's global MIDDLEWARE setting in settings.py instead. "
            "Make sure to add 'django_blog.fastapi_adapter.GeneratorDependencyCleanupMiddleware' "
            "to your MIDDLEWARE list (should be the last one)."
        )

    # 获取路由级全局依赖（APIRouter(dependencies=[...])）
    global_deps = getattr(router, 'dependencies', [])

    # 获取 router 中注册的所有路由（参考 Ninja 的 urls.py 生成逻辑）
    if hasattr(router, 'routes'):
        for route in router.routes:
            # 处理嵌套路由器（递归注册）
            if hasattr(route, 'routes'):  # 是另一个 APIRouter
                # 使用更安全的前缀拼接方式，避免双斜杠
                nested_prefix = '/'.join(p for p in [prefix, route.prefix] if p).strip('/')
                urlpatterns.extend(register_fastapi_router(
                    route,
                    prefix=nested_prefix,
                    tags=tags,
                    middlewares=middlewares
                ))
                continue

            if hasattr(route, 'methods') and hasattr(route, 'path'):
                # 检测 WebSocket 路由（不支持）
                if 'WEBSOCKET' in route.methods:
                    logger.warning(f"WebSocket route {route.path} is not supported, skipping")
                    continue

                # 获取视图函数（endpoint）
                view_func = route.endpoint

                logger.debug(f"Registering route: {route.path} -> endpoint: {view_func.__name__}")

                # 从路由对象读取 response_model（如果存在）
                response_model = getattr(route, 'response_model', None)
                response_model_exclude_unset = getattr(route, 'response_model_exclude_unset', False)
                response_model_include = getattr(route, 'response_model_include', None)
                response_model_exclude = getattr(route, 'response_model_exclude', None)
                response_model_by_alias = getattr(route, 'response_model_by_alias', True)

                # 读取路由级别的超时配置（如果存在）
                route_timeout = getattr(route, 'timeout', None)

                # 转换 FastAPI 路径为 Django 路径（使用缓存函数，传入视图函数用于类型推断）
                django_path = _convert_fastapi_path_to_django(route.path, view_func)

                # 添加前缀
                if prefix:
                    full_path = f"{prefix.strip('/')}/{django_path}"
                else:
                    full_path = django_path.lstrip('/')

                # 移除开头的 /（Django path 不应该以 / 开头）
                full_path = full_path.lstrip('/').rstrip('/')

                # 空路径处理（不要变成 '.'）
                if not full_path:
                    full_path = ''  # 使用空字符串而不是 '.'

                # 包装视图函数（使用 Ninja 风格的包装器，支持 response_model 和全局依赖）
                # middlewares 参数已废弃，不再传递
                wrapped_view = FastAPIToDjangoAdapter.wrap_fastapi_view(
                    view_func,
                    middlewares=None,  # 已废弃，改用 Django 全局中间件
                    response_model=response_model,
                    response_model_exclude_unset=response_model_exclude_unset,
                    response_model_include=response_model_include,
                    response_model_exclude=response_model_exclude,
                    response_model_by_alias=response_model_by_alias,
                    global_deps=global_deps,
                    timeout=route_timeout
                )

                # 对于认证相关的路由，豁免 CSRF 检查
                from django.views.decorators.csrf import csrf_exempt
                # 使用后缀匹配，确保匹配到完整的路径段
                # 如：/api/v1/auth/login 应该匹配 auth/login
                # 如：/auth/register 应该匹配 auth/register
                csrf_exempt_paths_env = os.getenv('FASTAPI_CSRF_EXEMPT_PATHS', 'auth/login,auth/register')
                csrf_exempt_paths = [p.strip() for p in csrf_exempt_paths_env.split(',') if p.strip()]

                def matches_csrf_exempt_path(full_path, exempt_path):
                    """
                    检查 full_path 是否以 exempt_path 结尾（作为完整路径段）
                    例如：
                    - 'api/v1/auth/login' 匹配 'auth/login' ✓
                    - 'api/v1/auth/login_extra' 不匹配 'auth/login' ✗
                    - 'auth/login' 匹配 'auth/login' ✓
                    """
                    # 精确匹配
                    if full_path == exempt_path:
                        return True
                    # 后缀匹配：full_path 以 '/' + exempt_path 结尾
                    if full_path.endswith('/' + exempt_path):
                        return True
                    return False
                
                should_exempt = any(
                    matches_csrf_exempt_path(full_path, path)
                    for path in csrf_exempt_paths
                )
                if should_exempt:
                    wrapped_view = csrf_exempt(wrapped_view)

                # 添加到 URL patterns - 不要自动添加尾部斜杠
                url_name = route.name if hasattr(route, 'name') else view_func.__name__
                if full_path:
                    urlpatterns.append(path(full_path, wrapped_view, name=url_name))
                else:
                    # 空路径特殊情况
                    urlpatterns.append(path('', wrapped_view, name=url_name))

    return urlpatterns


class GeneratorDependencyCleanupMiddleware:
    """
    Django 中间件：在请求结束时清理生成器依赖
    
    用法：在 Django settings.py 的 MIDDLEWARE 中添加：
    'django_blog.fastapi_adapter.GeneratorDependencyCleanupMiddleware'
    
    此中间件必须放在所有中间件之后（列表底部），确保在响应返回前执行清理
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 执行视图函数
        response = self.get_response(request)

        # 请求后清理生成器（从原始 Django request 对象读取）
        # 注意：视图函数的 finally 块已经处理了大部分清理工作
        # 这里作为双重保障，确保中间件级别的清理也能执行
        generators = getattr(request, '_fastapi_generator_deps', [])
        for gen in generators:
            try:
                # 无条件调用 close()，即使生成器已结束也无害
                gen.close()
            except Exception as e:
                logger.debug(f"Generator close error in middleware: {e}")

        # 清理异步生成器 - 使用后台线程等待，不阻塞响应返回
        async_generators = getattr(request, '_fastapi_async_generator_deps', [])
        for agen in async_generators:
            try:
                # 在后台线程中执行清理并记录异常
                def cleanup_async_gen(agen):
                    try:
                        loop = get_or_create_event_loop()
                        future = asyncio.run_coroutine_threadsafe(agen.aclose(), loop)

                        # 添加异常回调记录日志
                        def log_cleanup_result(fut):
                            exc = fut.exception()
                            if exc:
                                logger.warning(f"Async generator cleanup failed with exception: {exc}")
                            else:
                                logger.debug(f"Async generator closed successfully: {agen}")

                        future.add_done_callback(log_cleanup_result)
                    except Exception as e:
                        logger.warning(f"Failed to schedule async generator close: {e}")

                # 启动后台线程进行清理（daemon 线程，不会阻塞进程退出）
                import threading
                threading.Thread(target=cleanup_async_gen, args=(agen,), daemon=True).start()
            except Exception as e:
                # 记录警告而不是 debug，因为异步生成器清理失败可能导致资源泄漏
                logger.warning(f"Failed to schedule async generator close: {e}")

        # 执行后台任务（FastAPI BackgroundTasks）- 不阻塞响应返回
        if hasattr(request, '_fastapi_background_tasks') and request._fastapi_background_tasks.tasks:
            try:
                # 提交到事件循环异步执行，不等待结果
                background_tasks = request._fastapi_background_tasks
                loop = get_or_create_event_loop()
                future = asyncio.run_coroutine_threadsafe(background_tasks(), loop)

                # 限制后台任务数量，防止集合无限增长
                with _pending_tasks_lock:
                    if len(_pending_background_tasks) >= MAX_PENDING_TASKS:
                        logger.warning(
                            f"Too many pending background tasks ({len(_pending_background_tasks)}), "
                            f"discarding oldest task"
                        )
                        # 取消并移除最老的任务
                        if _pending_background_tasks:
                            oldest = next(iter(_pending_background_tasks))
                            oldest.cancel()
                            _pending_background_tasks.discard(oldest)

                    _pending_background_tasks.add(future)

                # 添加异常处理回调
                def log_background_exception(fut):
                    exc = fut.exception()
                    if exc:
                        logger.error(f"Background task failed with exception: {exc}")
                        import traceback
                        # 使用异常对象的 __traceback__ 属性获取原始堆栈
                        tb = ''.join(traceback.format_tb(exc.__traceback__))
                        logger.error(f"Background task traceback:\n{tb}")
                    # 从待处理集合中移除（使用锁保护）
                    with _pending_tasks_lock:
                        _pending_background_tasks.discard(fut)

                future.add_done_callback(log_background_exception)
                logger.debug(f"Scheduled {len(background_tasks.tasks)} background task(s) for execution")
            except Exception as e:
                logger.error(f"Background tasks scheduling error: {e}")

        return response
