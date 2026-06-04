"""
仪表板API聚合路由器 - V2统一入口
整合V1的dashboard相关模块

使用懒加载模式：仅在首次访问 router 时才导入 V1 子模块。
"""
from fastapi import APIRouter

_router = None


def _build_router():
    global _router
    if _router is not None:
        return _router

    router = APIRouter(tags=["dashboard"])

    from src.api.v1.dashboard.analytics import router as analytics_router
    from src.api.v1.dashboard.dashboard import router as dashboard_router
    from src.api.v1.dashboard.realtime_monitor import router as realtime_monitor_router

    router.include_router(dashboard_router, prefix="")
    router.include_router(analytics_router, prefix="/analytics")
    router.include_router(realtime_monitor_router, prefix="/monitor")

    _router = router
    return _router


def __getattr__(name):
    if name == "router":
        return _build_router()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
