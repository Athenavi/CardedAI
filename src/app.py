"""
FastBlog 应用入口
"""
import importlib
import os
import time as _time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.staticfiles import StaticFiles

from src.unified_logger import default_logger as logger


# ---------- 工具函数 ----------
def safe_run(func_name: str, func, *args, **kwargs):
    """安全执行同步/异步初始化，统一日志输出"""
    logger.info(f"[{func_name}] 开始初始化...")
    try:
        result = func(*args, **kwargs)
        logger.info(f"[{func_name}] 完成")
        return result
    except Exception as e:
        logger.error(f"[{func_name}] 失败: {e}", exc_info=True)
        return None


async def safe_run_async(func_name: str, func, *args, **kwargs):
    """安全执行异步初始化"""
    logger.info(f"[{func_name}] 开始初始化...")
    try:
        # 直接调用函数，如果是协程函数会自动返回协程对象
        result = func(*args, **kwargs)
        # 如果结果是协程，则等待它
        if hasattr(result, '__await__'):
            await result
        logger.info(f"[{func_name}] 完成")
        return result
    except Exception as e:
        logger.error(f"[{func_name}] 失败: {e}", exc_info=True)
        return None


def check_installation() -> bool:
    """检查系统是否已安装"""
    try:
        from shared.services.install.install_manager import installation_wizard_service
        installed = installation_wizard_service.is_installed()
        if not installed:
            logger.warning("系统尚未安装 - 请启动前端进程后访问 http://localhost:4321/install 完成安装向导")
        return installed
    except Exception as e:
        logger.warning(f"Failed to check installation status: {e}")
        return False


# 使用 src/api/v2/__init__.py 中的 ROUTE_REGISTRY_V2


def _load_single_module(module_path: str, required: bool):
    """并行加载单个模块并获取其 router（线程安全）"""
    mod_start = _time.monotonic()
    mod = importlib.import_module(module_path)
    router = getattr(mod, "router", None)
    mod_elapsed = _time.monotonic() - mod_start
    return module_path, router, mod_elapsed, required, None


def _load_single_module_safe(module_path: str, required: bool):
    """安全版本：捕获异常并返回错误信息"""
    try:
        return _load_single_module(module_path, required, )
    except Exception as e:
        return module_path, None, 0.0, required, e


def register_all_routes(app: FastAPI, worker_info: str):
    """注册 API v2 和 v3 路由（已移除 v1）"""

    # 注册 v2 路由（新规范）— 并行加载 + 顺序注册
    logger.info(f"{worker_info} 开始注册 API v2 路由...")
    routes_start = _time.monotonic()
    try:
        from src.api.v2 import ROUTE_REGISTRY_V2
        loaded_count = 0
        failed_count = 0

        # Phase 1: 并行加载所有模块和路由器（ThreadPoolExecutor）
        # importlib + getattr(mod, "router") 触发 _build_router() 是 CPU/IO 密集操作，可并行
        load_start = _time.monotonic()
        load_results = []

        # 根据核心数自适应线程池大小，最少 4 最多 16
        max_workers = min(max(4, (os.cpu_count() or 4)), 16, len(ROUTE_REGISTRY_V2))

        with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="route_loader") as executor:
            future_map = {
                executor.submit(_load_single_module_safe, module_path, required): module_path
                for module_path, prefix, tags, required in ROUTE_REGISTRY_V2
            }
            # 保持结果顺序与 ROUTE_REGISTRY_V2 一致
            result_by_path = {}
            for future in as_completed(future_map):
                result = future.result()
                result_by_path[result[0]] = result

            for module_path, prefix, tags, required in ROUTE_REGISTRY_V2:
                load_results.append((module_path, prefix, tags, result_by_path.get(module_path)))

        load_elapsed = _time.monotonic() - load_start
        logger.info(f"{worker_info} 模块并行加载完成 (线程池: {max_workers}, 耗时: {load_elapsed:.2f}s)")

        # Phase 2: 顺序注册路由器到 app（FastAPI include_router 非线程安全）
        register_start = _time.monotonic()
        for module_path, prefix, tags, result in load_results:
            if result is None:
                failed_count += 1
                logger.warning(f"{worker_info} v2/{module_path} 未找到加载结果")
                continue

            _, router, mod_elapsed, req, error = result

            if error is not None:
                if req:
                    logger.error(f"{worker_info} v2 必需模块加载失败: {module_path} - {error}")
                    raise error
                else:
                    failed_count += 1
                    logger.warning(f"{worker_info} v2/{module_path} 未能加载: {error}")
                    continue

            if router is None:
                failed_count += 1
                logger.warning(f"{worker_info} v2/{module_path} 未找到 router 属性")
                continue

            try:
                if prefix:
                    app.include_router(router, prefix=prefix, tags=tags if tags else [])
                else:
                    app.include_router(router)
                loaded_count += 1
                short_name = module_path.split('.')[-1]
                if mod_elapsed > 1.0:
                    logger.warning(f"{worker_info} v2/{short_name} 已加载 (慢: {mod_elapsed:.2f}s)")
                else:
                    logger.debug(f"{worker_info} v2/{short_name} 已加载 ({mod_elapsed:.2f}s)")
            except Exception as e:
                if req:
                    raise
                failed_count += 1
                logger.warning(f"{worker_info} v2/{module_path} 注册异常: {e}")

        routes_elapsed = _time.monotonic() - routes_start
        register_elapsed = _time.monotonic() - register_start
        logger.info(f"{worker_info} API v2 路由注册完成 (成功: {loaded_count}, 失败: {failed_count}, "
              f"加载: {load_elapsed:.2f}s, 注册: {register_elapsed:.2f}s, 总耗时: {routes_elapsed:.2f}s)")
    except ImportError as e:
        logger.error(f"{worker_info} API v2 模块未找到: {e}")
        raise


# ---------- 生命周期 ----------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理（结构化）"""
    lifespan_start = _time.monotonic()

    # 1. 安装状态检查
    step_start = _time.monotonic()
    is_installed = check_installation()
    logger.debug(f"[lifespan] 安装检查耗时: {_time.monotonic() - step_start:.2f}s")

    # 2. 数据库管理器（仅安装后）
    if is_installed:
        step_start = _time.monotonic()
        await safe_run_async("数据库管理器", _init_database)
        logger.debug(f"[lifespan] 数据库初始化耗时: {_time.monotonic() - step_start:.2f}s")

    # 2.5 懒加载系统初始化
    try:
        from src.utils.lazy_loader import init_lazy_loading
        step_start = _time.monotonic()
        safe_run("懒加载系统", init_lazy_loading)
        logger.debug(f"[lifespan] 懒加载系统耗时: {_time.monotonic() - step_start:.2f}s")
    except ImportError as e:
        logger.debug(f"[懒加载系统] 跳过: {e}")

    # 3. 扩展、调度器
    try:
        from src.extensions import init_extensions
        step_start = _time.monotonic()
        safe_run("扩展初始化", lambda: init_extensions(app))
        logger.debug(f"[lifespan] 扩展初始化耗时: {_time.monotonic() - step_start:.2f}s")
    except ImportError as e:
        logger.debug(f"[扩展初始化] 跳过: {e}")

    try:
        from src.scheduler import init_scheduler
        step_start = _time.monotonic()
        safe_run("调度器初始化", lambda: init_scheduler(app))
        logger.debug(f"[lifespan] 调度器初始化耗时: {_time.monotonic() - step_start:.2f}s")
    except ImportError as e:
        logger.debug(f"[调度器初始化] 跳过: {e}")

    # 3.5 工作流引擎节点执行器注册
    try:
        from shared.services.workflow.dag_engine import DAGEngine
        step_start = _time.monotonic()
        safe_run("工作流引擎执行器注册", DAGEngine.init_executors)
        logger.debug(f"[lifespan] 执行器注册耗时: {_time.monotonic() - step_start:.2f}s")
    except ImportError as e:
        logger.debug(f"[执行器注册] 跳过: {e}")

    if is_installed:
        step_start = _time.monotonic()
        await safe_run_async("定时发布调度器", _start_scheduled_publisher)
        logger.debug(f"[lifespan] 定时发布调度器耗时: {_time.monotonic() - step_start:.2f}s")

    # 5. 下载队列处理器
    if is_installed:
        step_start = _time.monotonic()
        await safe_run_async("下载队列处理器", _init_download_processor)
        logger.debug(f"[lifespan] 下载队列处理器耗时: {_time.monotonic() - step_start:.2f}s")

    total_elapsed = _time.monotonic() - lifespan_start
    logger.info(f"[lifespan] 应用启动完成，总耗时: {total_elapsed:.2f}s")

    yield

    # ---------- 关闭清理 ----------
    await safe_run_async("调度器停止", _stop_scheduler)

    if is_installed:
        await safe_run_async("下载队列停止", _shutdown_download_processor)
        await safe_run_async("数据库连接关闭", _close_database)


async def _init_database():
    from src.utils.database.unified_manager import db_manager
    db_manager.initialize()
    # 确保所有模型表已创建（首次部署/空库时建表；已有表时 checkfirst 跳过，不重复）
    try:
        from shared.models import Base
        from src.utils.database.main import _import_models_once
        _import_models_once()
        async with db_manager.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("[lifespan] 数据库表已确保存在（create_all）")
    except Exception as e:
        logger.warning(f"[lifespan] 建表跳过/失败: {e}")


async def _start_scheduled_publisher():
    from src.utils.database.unified_manager import db_manager
    from shared.services.core.scheduler import start_scheduler, init_scheduler
    init_scheduler(db_manager.async_session_factory, check_interval=60)
    await start_scheduler()


async def _stop_scheduler():
    try:
        from src.scheduler import session_scheduler
        session_scheduler.scheduler.stop()
    except (ImportError, AttributeError):
        pass


async def _init_download_processor():
    from shared.services.media.download_queue_processor import init_download_processor
    await init_download_processor()


async def _shutdown_download_processor():
    from shared.services.media.download_queue_processor import shutdown_download_processor
    await shutdown_download_processor()


async def _close_database():
    from src.utils.database.unified_manager import db_manager
    await db_manager.close()


# ---------- 中间件注册 ----------
def _make_lazy_middleware(module_path: str, class_name: str):
    """创建惰性中间件代理类：首次实例化时才导入目标模块（避免启动时加载 psutil 等重依赖）"""
    _cache = {}

    class _LazyProxy:
        def __init__(self, app, **kwargs):
            self._app = app
            if 'cls' not in _cache:
                import importlib
                try:
                    mod = importlib.import_module(module_path)
                    _cache['cls'] = getattr(mod, class_name)
                except (ImportError, AttributeError) as e:
                    # 中间件模块缺失（如精简模式下未安装对应依赖）：跳过该中间件
                    logger.warning(f"[Middleware] 中间件 {module_path}.{class_name} 不可用，已跳过: {e}")
                    _cache['cls'] = None
            if _cache['cls'] is not None:
                self._impl = _cache['cls'](app=app, **kwargs)
            else:
                self._impl = None

        async def __call__(self, scope, receive, send):
            if self._impl is None:
                await self._app(scope, receive, send)
                return
            await self._impl(scope, receive, send)

    _LazyProxy.__name__ = f"Lazy_{class_name}"
    _LazyProxy.__qualname__ = f"_make_lazy_middleware.<locals>.Lazy_{class_name}"
    return _LazyProxy


def register_middleware(app: FastAPI):
    """统一注册所有中间件（调试、安全、缓存等）"""
    # 获取 worker 信息（用于日志）
    from src.setting import _get_worker_info
    worker_info = _get_worker_info()

    # CORS（从环境变量或默认值）
    from fastapi.middleware.cors import CORSMiddleware
    origins_env = os.environ.get('CORS_ORIGINS', '')
    if origins_env:
        allow_origins = [o.strip() for o in origins_env.replace(';', ',').split(',') if o.strip()]
    else:
        allow_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:4321",
            "http://127.0.0.1:4321",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
            "http://localhost:9421",
            "http://127.0.0.1:9421",
            "http://localhost"  # Capacitor Android 模拟器
        ]
    if "*" in allow_origins:
        allow_origins = [o for o in allow_origins if o != "*"] or ["http://localhost:3000"]

    logger.info(f"[CORS] 允许源: {allow_origins}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["Authorization", "Content-Type", "Cookie", "X-Requested-With"],
        expose_headers=["Content-Length", "X-Total-Count"],
    )

    # 统一调试中间件（仅开发环境加载）
    if os.environ.get('ENVIRONMENT', 'development').lower() != 'production':
        class DebugMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request, call_next):
                url = str(request.url)
                if "/sensitive-words" in url:
                    logger.debug(f"[DEBUG] 请求: {request.method} {url}")
                    logger.debug(f"[DEBUG] Headers: {dict(request.headers)}")
                    if request.method == "POST":
                        try:
                            body = await request.body()
                            logger.debug(f"[DEBUG] Body: {body.decode('utf-8')}")

                            async def receive():
                                return {"type": "http.request", "body": body}

                            request._receive = receive
                        except Exception as e:
                            logger.debug(f"[DEBUG] 无法读取 body: {e}")
                response = await call_next(request)
                if "/sensitive-words" in url and response.status_code == 422:
                    logger.debug(f"[DEBUG] 422 响应: {response.status_code}")
                return response

        app.add_middleware(DebugMiddleware)

        # WebSocket 调试（仅开发环境）
        class WSDebugMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request, call_next):
                if request.headers.get("upgrade", "").lower() == "websocket" and "/collaboration/ws/" in str(request.url):
                    logger.debug(f"[WS DEBUG] 连接尝试: {request.url}")
                return await call_next(request)

        app.add_middleware(WSDebugMiddleware)
    else:
        logger.info(f"{worker_info} [Middleware] 生产环境，调试中间件已跳过")

    # HTTP 缓存
    try:
        from src.middleware.http_cache_middleware import HttpCacheMiddleware
        app.add_middleware(HttpCacheMiddleware, enable_etag=True, enable_last_modified=True,
                           default_cache_ttl=300, skip_methods=['POST', 'PUT', 'DELETE', 'PATCH'])
        logger.info("[HTTP Cache] 已添加")
    except ImportError:
        pass

    # 安全中间件（惰性加载：首次请求时才导入 security_middleware 模块）
    try:
        app.add_middleware(
            _make_lazy_middleware("src.auth.security_middleware", "CSRFProtectionMiddleware")
        )
    except Exception:
        pass

    # 速率限制已移除全局中间件，改为在特定路由上使用装饰器

    # API 版本响应头
    class APIVersionMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            response.headers["API-Version"] = "v2"
            return response

    app.add_middleware(APIVersionMiddleware)
    logger.info("[API Version] 已添加版本响应头中间件")

    # 性能监控中间件（惰性加载：避免启动时 import psutil）
    try:
        app.add_middleware(
            _make_lazy_middleware("src.middleware.performance_monitor", "PerformanceMonitoringMiddleware")
        )
        logger.info("[Performance Monitor] 已添加性能监控中间件（惰性加载）")
    except Exception as e:
        logger.warning(f"[Performance Monitor] 加载失败: {e}")


# ---------- 错误处理与静态文件 ----------
def register_error_handlers(app: FastAPI):
    """注册全局错误处理器和 SPA 回退"""

    @app.get("/api/v2/health", tags=["system"])
    async def health_check():
        # 原逻辑简化
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}

    @app.get("/api/v2/mobile-login", tags=["qr-login"])
    async def mobile_login_page(request: Request):
        """手机扫码确认页面（注册在应用顶层，绕过 API 中间件和认证）"""
        from src.api.v2.qr_login import _MOBILE_LOGIN_HTML
        from fastapi.responses import HTMLResponse

        # 动态计算前端登录页地址
        host = request.headers.get("host", "localhost:9421")
        scheme = request.url.scheme or "http"
        # 开发环境：后端 :9421 → 前端 :4321（Astro 默认端口）
        # 生产环境：同源部署时 host 不含 :9421，保持原样
        frontend_host = host.replace(":9421", ":4321")
        frontend_origin = f"{scheme}://{frontend_host}"

        html = _MOBILE_LOGIN_HTML.replace("{{FRONTEND_ORIGIN}}", frontend_origin)
        return HTMLResponse(content=html)

    # 注意：不再注册 catch-all 路由（如 @app.get('/{full_path:path}')），
    # 因为它会拦截所有请求（包括 API 请求），导致 API 路由（如 /api/v2/articles）
    # 在缺少尾部斜杠时返回 404 而非正确匹配。
    # SPA 回退逻辑已移至 404 异常处理器中处理。

    @app.exception_handler(401)
    async def unauthorized_handler(request: Request, exc: HTTPException):
        if request.url.path.startswith('/api/') or 'application/json' in request.headers.get('accept', ''):
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=401, content={"detail": exc.detail})
        return RedirectResponse(url=f"/login?next={request.url}")

    @app.exception_handler(404)
    async def custom_404_handler(request: Request, exc: HTTPException):
        # [插件系统已移除] 直接处理
        # API 路径直接返回 JSON 404
        path = request.url.path
        if path.startswith('/api/') or 'application/json' in request.headers.get('accept', ''):
            from src.error import error
            return error(404, "Page Not Found")

        # 3. 非 API 路径尝试返回前端 SPA 页面
        excluded_prefixes = ['api/v2/static/', 'api/v2/assets/', 'api/v2/docs', 'api/v2/redoc', 'api/v2/openapi.json',
                             'api/v2/health']
        if not any(path.lstrip('/').startswith(prefix) for prefix in excluded_prefixes):
            try:
                frontend_index = os.path.join(os.path.dirname(__file__), "..", "frontend-astro", "dist", "index.html")
                if os.path.exists(frontend_index):
                    with open(frontend_index, "r", encoding="utf-8") as f:
                        return HTMLResponse(content=f.read())
            except Exception:
                pass
            # 默认返回一个简单的SPA模板
            return HTMLResponse(
                content="<!DOCTYPE html><html><head><title>Blog</title></head><body><div id='app'></div></body></html>")

        from src.error import error
        return error(404, "Page Not Found")

    @app.exception_handler(500)
    async def custom_500_handler(request: Request, exc: HTTPException):
        from src.error import error
        return error(500, "Internal Server Error")

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        from src.unified_logger import default_logger as logger
        logger.error(f"General error: {exc}")
        if any(kw in str(exc).lower() for kw in ["not found", "no result", "does not exist"]):
            from src.error import error
            return error(404, "Page Not Found")
        from src.error import error
        return error(500, "Internal Server Error")


# ---------- 应用工厂 ----------
def create_app(config=None):
    """创建 FastAPI 应用实例"""
    app_start = _time.monotonic()

    if config is None:
        from src.setting import ProductionConfig
        config = ProductionConfig()

    # 获取 worker 信息（用于日志）
    from src.setting import _get_worker_info
    worker_info = _get_worker_info()

    # OpenAPI 元数据（精简但保留核心内容）
    app = FastAPI(
        title="FastBlog API",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/v2/docs",
        redoc_url="/api/v2/redoc",
        openapi_url="/api/v2/openapi.json",
        swagger_ui_oauth2_redirect_url="/api/v2/docs/oauth2-redirect",
    )

    # 注册中间件
    step_start = _time.monotonic()
    register_middleware(app)
    logger.info(f"{worker_info} [create_app] 中间件注册耗时: {_time.monotonic() - step_start:.2f}s")

    # 注册所有 API 路由
    step_start = _time.monotonic()
    register_all_routes(app, worker_info)
    logger.info(f"{worker_info} [create_app] 路由注册耗时: {_time.monotonic() - step_start:.2f}s")

    # 错误处理和 SPA 回退
    register_error_handlers(app)

    # 静态文件挂载 - 确保在所有路由注册之后挂载，避免被catch-all路由拦截
    static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
    os.makedirs(static_dir, exist_ok=True)
    app.mount("/api/v2/static", StaticFiles(directory=static_dir), name="static")

    # 本地存储 - 使用统一前缀 /api/v2/assets/storage 避免与业务路由冲突
    try:
        from src.setting import app_config
        local_storage = getattr(app_config, 'LOCAL_STORAGE_PATH', 'storage')
    except Exception:
        local_storage = 'storage'
    os.makedirs(local_storage, exist_ok=True)
    app.mount("/api/v2/assets/storage", StaticFiles(directory=local_storage), name="local-storage")

    objects_dir = os.path.join(local_storage, 'objects')
    os.makedirs(objects_dir, exist_ok=True)
    app.mount("/api/v2/assets/storage/objects", StaticFiles(directory=objects_dir), name="storage-objects")

    themes_dir = os.path.join(os.path.dirname(__file__), "..", "themes")
    if os.path.exists(themes_dir):
        app.mount("/api/v2/assets/themes", StaticFiles(directory=themes_dir), name="themes")

    # 前端静态资源（同源部署）：Astro 构建产物，挂载到根路径（须在所有路由/挂载之后）
    frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend-astro", "dist")
    if os.path.isdir(frontend_dist):
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
        logger.info(f"[Frontend] 前端静态资源已挂载: {frontend_dist}")
    else:
        logger.info(f"[Frontend] 未找到前端构建产物: {frontend_dist}（可先运行 npm run build 构建）")

    app_elapsed = _time.monotonic() - app_start
    logger.info(f"{worker_info} [create_app] 应用工厂完成，总耗时: {app_elapsed:.2f}s")

    return app


# Global app instance (for uvicorn to use directly)
try:
    app = create_app()
except Exception:
    traceback.print_exc()
    import sys
    sys.exit(1)
