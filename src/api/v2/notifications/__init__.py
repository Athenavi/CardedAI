"""
通知API聚合路由器 - V2统一入口
整合V1的notifications相关模块

使用懒加载模式：仅在首次访问 router 时才导入 V1 子模块。
"""
from fastapi import APIRouter

_router = None


def _build_router():
    global _router
    if _router is not None:
        return _router

    router = APIRouter(tags=["notifications"])

    from src.api.v1.notifications.email_service import router as email_service_router
    from src.api.v1.notifications.notifications import router as notifications_router
    from src.api.v1.notifications.push_notifications import router as push_notifications_router

    router.include_router(notifications_router, prefix="")
    router.include_router(email_service_router, prefix="/email")
    router.include_router(push_notifications_router, prefix="/push")

    _router = router
    return _router


def __getattr__(name):
    if name == "router":
        return _build_router()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
