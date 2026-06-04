"""
集成API聚合路由器 - V2统一入口
整合V1的integrations相关模块

使用懒加载模式：仅在首次访问 router 时才导入 V1 子模块。
"""
from fastapi import APIRouter

_router = None


def _build_router():
    global _router
    if _router is not None:
        return _router

    router = APIRouter(tags=["integrations"])

    from src.api.v1.integrations.baidu_analytics import router as baidu_analytics_router
    from src.api.v1.integrations.google_analytics import router as google_analytics_router
    from src.api.v1.integrations.ipfs import router as ipfs_router
    from src.api.v1.integrations.oauth_login import router as oauth_login_router
    from src.api.v1.integrations.sso import router as sso_router
    from src.api.v1.integrations.wordpress_import import router as wordpress_import_router

    router.include_router(baidu_analytics_router, prefix="/analytics/baidu")
    router.include_router(google_analytics_router, prefix="/analytics/google")
    router.include_router(ipfs_router, prefix="/ipfs")
    router.include_router(oauth_login_router, prefix="/oauth")
    router.include_router(wordpress_import_router, prefix="/wordpress")
    router.include_router(sso_router, prefix="/sso")

    _router = router
    return _router


def __getattr__(name):
    if name == "router":
        return _build_router()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
