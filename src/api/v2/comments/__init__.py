"""
评论API聚合路由器 - V2统一入口
整合V1的comments相关模块

使用懒加载模式：仅在首次访问 router 时才导入 V1 子模块。
"""
from fastapi import APIRouter

_router = None


def _build_router():
    global _router
    if _router is not None:
        return _router

    router = APIRouter(tags=["comments"])

    from src.api.v1.comments.comment_config import router as comment_config_router
    from src.api.v1.comments.comment_subscriptions import router as comment_subscriptions_router
    from src.api.v1.comments.comments import router as comments_router
    from src.api.v1.comments.comments_enhanced import router as comments_enhanced_router

    router.include_router(comments_router, prefix="")
    router.include_router(comments_enhanced_router, prefix="/enhanced")
    router.include_router(comment_config_router, prefix="/config")
    router.include_router(comment_subscriptions_router, prefix="/subscriptions")

    _router = router
    return _router


def __getattr__(name):
    if name == "router":
        return _build_router()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
