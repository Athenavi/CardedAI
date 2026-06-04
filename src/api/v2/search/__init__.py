"""
搜索API聚合路由器 - V2统一入口
整合V1的search相关模块

使用懒加载模式：仅在首次访问 router 时才导入 V1 子模块。
"""
from fastapi import APIRouter

_router = None


def _build_router():
    global _router
    if _router is not None:
        return _router

    router = APIRouter(tags=["search"])

    from src.api.v1.search.fulltext_search import router as fulltext_search_router

    router.include_router(fulltext_search_router, prefix="/fulltext")

    _router = router
    return _router


def __getattr__(name):
    if name == "router":
        return _build_router()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
