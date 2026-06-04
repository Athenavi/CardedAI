"""
静态生成API聚合路由器 - V2统一入口
整合V1的static_generation相关模块

使用懒加载模式：仅在首次访问 router 时才导入 V1 子模块。
"""
from fastapi import APIRouter

_router = None


def _build_router():
    global _router
    if _router is not None:
        return _router

    router = APIRouter(tags=["static-generation"])

    from src.api.v1.static_generation.static_site_generation import router as static_site_generation_router

    router.include_router(static_site_generation_router, prefix="/ssg")

    _router = router
    return _router


def __getattr__(name):
    if name == "router":
        return _build_router()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
