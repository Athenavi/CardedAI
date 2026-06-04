"""
协作API聚合路由器 - V2统一入口
整合V1的collaboration相关模块

使用懒加载模式：仅在首次访问 router 时才导入 V1 子模块。
"""
from fastapi import APIRouter

_router = None


def _build_router():
    global _router
    if _router is not None:
        return _router

    router = APIRouter(tags=["collaboration"])

    from src.api.v1.collaboration.collaboration_invites import router as collaboration_invites_router
    from src.api.v1.collaboration.collaboration_save import router as collaboration_save_router
    from src.api.v1.collaboration.team_collaboration import router as team_collaboration_router
    from src.api.v1.collaboration.team_comments import router as team_comments_router
    from src.api.v1.collaboration.yjs_collaboration import router as yjs_collaboration_router

    router.include_router(collaboration_invites_router, prefix="/invites")
    router.include_router(collaboration_save_router, prefix="/collaboration")
    router.include_router(team_collaboration_router, prefix="/admin/team")
    router.include_router(team_comments_router, prefix="/team/comments")
    router.include_router(yjs_collaboration_router, prefix="/yjs")

    _router = router
    return _router


def __getattr__(name):
    if name == "router":
        return _build_router()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
