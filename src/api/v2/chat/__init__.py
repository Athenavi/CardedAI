"""
聊天API聚合路由器 - V2统一入口
整合V1的chat相关模块

使用懒加载模式：仅在首次访问 router 时才导入 V1 子模块。
"""
from fastapi import APIRouter

_router = None


def _build_router():
    global _router
    if _router is not None:
        return _router

    router = APIRouter(tags=["chat"])

    from src.api.v1.chat.chat import router as chat_router
    from src.api.v1.chat.chat_groups import router as chat_groups_router
    from src.api.v1.chat.private_messages import router as private_messages_router

    router.include_router(chat_groups_router, prefix="/groups")
    router.include_router(private_messages_router, prefix="/messages/private")
    router.include_router(chat_router, prefix="")

    _router = router
    return _router


def __getattr__(name):
    if name == "router":
        return _build_router()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
