"""
翻译API聚合路由器 - V2统一入口
整合V1的translation相关模块

使用懒加载模式：仅在首次访问 router 时才导入 V1 子模块。
"""
from fastapi import APIRouter

_router = None


def _build_router():
    global _router
    if _router is not None:
        return _router

    router = APIRouter(tags=["i18n"])

    from src.api.v1.translation.i18n import router as i18n_router
    from src.api.v1.translation.translation_io import router as translation_io_router
    from src.api.v1.translation.translation_progress import router as translation_progress_router
    from src.api.v1.translation.translation_service import router as translation_service_router
    from src.api.v1.translation.translations import router as translations_router

    router.include_router(i18n_router, prefix="/i18n")
    router.include_router(translation_io_router, prefix="/io")
    router.include_router(translation_progress_router, prefix="/progress")
    router.include_router(translation_service_router, prefix="/service")
    router.include_router(translations_router, prefix="/translations")

    _router = router
    return _router


def __getattr__(name):
    if name == "router":
        return _build_router()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
