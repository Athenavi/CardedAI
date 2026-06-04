"""
SEO 模块 - V2 统一入口
整合所有 SEO 相关功能

使用懒加载模式：仅在首次访问 router 时才导入 V1 子模块。
"""
from fastapi import APIRouter

_router = None


def _build_router():
    global _router
    if _router is not None:
        return _router

    router = APIRouter(tags=["seo"])

    from src.api.v1.seo.batch_seo import router as batch_seo_router
    from src.api.v1.seo.breadcrumbs import router as breadcrumbs_router
    from src.api.v1.seo.content_quality import router as content_quality_router
    from src.api.v1.seo.hreflang_api import router as hreflang_router
    from src.api.v1.seo.internal_links import router as internal_links_router
    from src.api.v1.seo.redirect_management import router as redirect_router
    from src.api.v1.seo.schema_generator import router as schema_generator_router
    from src.api.v1.seo.seo_dashboard import router as seo_dashboard_router
    from src.api.v1.seo.seo_management import router as seo_management_router
    from src.api.v1.seo.seo_optimization import router as seo_optimization_router
    from src.api.v1.seo.seo_tracking import router as seo_tracking_router
    from src.api.v1.seo.sitemap import router as sitemap_router

    router.include_router(sitemap_router, prefix="/sitemap")
    router.include_router(breadcrumbs_router, prefix="/breadcrumbs")
    router.include_router(hreflang_router, prefix="/hreflang")
    router.include_router(internal_links_router, prefix="/internal-links")
    router.include_router(redirect_router, prefix="/redirects")
    router.include_router(seo_management_router, prefix="/management")
    router.include_router(seo_optimization_router, prefix="/opt")
    router.include_router(seo_tracking_router, prefix="/tracking")
    router.include_router(batch_seo_router, prefix="/batch")
    router.include_router(content_quality_router, prefix="/content-quality")
    router.include_router(schema_generator_router, prefix="/schema")
    router.include_router(seo_dashboard_router, prefix="/dashboard")

    _router = router
    return _router


def __getattr__(name):
    if name == "router":
        return _build_router()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
