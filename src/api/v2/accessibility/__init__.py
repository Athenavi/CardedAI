"""
无障碍API聚合路由器 - V2统一入口
整合V1的accessibility相关模块

使用懒加载模式：仅在首次访问 router 时才导入 V1 子模块。
"""
from fastapi import APIRouter

_router = None


def _build_router():
    global _router
    if _router is not None:
        return _router

    router = APIRouter(tags=["accessibility"])

    from src.api.v1.accessibility.accessibility_audit import router as accessibility_audit_router
    from src.api.v1.accessibility.amp import router as amp_router

    router.include_router(accessibility_audit_router, prefix="/audit")
    router.include_router(amp_router, prefix="/amp")

    _router = router
    return _router


def __getattr__(name):
    if name == "router":
        return _build_router()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
