"""
第三方集成模块 - V2 统一入口
个人站长精简版：轻量聚合
"""
from fastapi import APIRouter

_router = None


def _build_router():
    global _router
    if _router is not None:
        return _router

    router = APIRouter(tags=["integrations"])
    _router = router
    return router


def __getattr__(name):
    if name == "router":
        return _build_router()
    raise AttributeError(f"module 'src.api.v2.integrations' has no attribute {name!r}")
