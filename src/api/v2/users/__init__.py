"""
用户API聚合路由器 - V2统一入口
整合V1的users相关模块

使用懒加载模式：仅在首次访问 router 时才导入 V1 子模块。
"""
from fastapi import APIRouter

_router = None


def _build_router():
    global _router
    if _router is not None:
        return _router

    router = APIRouter(tags=["users"])

    from src.api.v1.users.unified_users import router as user_router
    from src.api.v1.users.user_settings import router as user_settings_router

    router.include_router(user_router, prefix="/users")
    router.include_router(user_settings_router, prefix="/settings")

    _router = router
    return _router


def __getattr__(name):
    if name == "router":
        return _build_router()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
