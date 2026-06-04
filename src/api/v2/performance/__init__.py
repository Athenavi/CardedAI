"""
性能优化API聚合路由器 - V2统一入口
整合V1的performance相关模块

使用懒加载模式：仅在首次访问 router 时才导入 V1 子模块。
"""
from fastapi import APIRouter

_router = None


def _build_router():
    global _router
    if _router is not None:
        return _router

    router = APIRouter(tags=["performance"])

    from src.api.v1.performance.cache_management import router as cache_management_router
    from src.api.v1.performance.css_optimizer import router as css_optimizer_router
    from src.api.v1.performance.http2_config import router as http2_config_router
    from src.api.v1.performance.load_balancer import router as load_balancer_router
    from src.api.v1.performance.localization import router as localization_router
    from src.api.v1.performance.object_cache import router as object_cache_router
    from src.api.v1.performance.performance_monitor import router as performance_monitor_router
    from src.api.v1.performance.performance_tracking import router as performance_tracking_router
    from src.api.v1.performance.query_monitor import router as query_monitor_router
    from src.api.v1.performance.query_optimization import router as query_optimization_router
    from src.api.v1.performance.resource_optimization import router as resource_optimization_router
    from src.api.v2.performance.cdn_optimization import router as cdn_optimization_router

    router.include_router(cache_management_router, prefix="/admin/caches")
    router.include_router(performance_monitor_router, prefix="/performance-monitor")
    router.include_router(performance_tracking_router, prefix="/performance-tracking")
    router.include_router(css_optimizer_router, prefix="/css-optimizer")
    router.include_router(http2_config_router, prefix="/http2")
    router.include_router(load_balancer_router, prefix="/load-balancer")
    router.include_router(localization_router, prefix="/localization")
    router.include_router(object_cache_router, prefix="/object-cache")
    router.include_router(query_monitor_router, prefix="/query-monitor")
    router.include_router(query_optimization_router, prefix="/query-optimization")
    router.include_router(resource_optimization_router, prefix="/resource-optimization")
    router.include_router(cdn_optimization_router, prefix="/cdn")

    _router = router
    return _router


def __getattr__(name):
    if name == "router":
        return _build_router()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
