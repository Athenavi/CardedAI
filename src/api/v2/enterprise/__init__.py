"""
企业管理API聚合路由器 - V2统一入口
整合许可证管理、技术支持工单、部署脚本和监控告警

使用懒加载模式：仅在首次访问 router 时才导入 V1 子模块。
"""
from fastapi import APIRouter

_router = None


def _build_router():
    global _router
    if _router is not None:
        return _router

    router = APIRouter(tags=["enterprise-v2"])

    from src.api.v1.enterprise.enterprise_api import router as base_enterprise_router
    from src.api.v2.enterprise.admin_endpoints import router as admin_enterprise_router

    router.include_router(base_enterprise_router, prefix="")
    router.include_router(admin_enterprise_router, prefix="/admin")

    _router = router
    return _router


def __getattr__(name):
    if name == "router":
        return _build_router()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
