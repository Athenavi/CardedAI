"""
SEO 模块 - 统一入口
整合所有 SEO 相关功能：站点地图、robots.txt、面包屑、hreflang、内部链接、重定向管理等
"""
from fastapi import APIRouter

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
# 导入所有 SEO 子模块路由
from src.api.v1.seo.sitemap import router as sitemap_router

router = APIRouter(tags=["seo"])

# 包含所有 SEO 子路由
# 注意：子路由的前缀将在 v2 注册时通过主路由前缀 /api/v2/seo 统一管理
router.include_router(sitemap_router)
router.include_router(breadcrumbs_router)
router.include_router(hreflang_router)
router.include_router(internal_links_router)
router.include_router(redirect_router)
router.include_router(seo_management_router)
router.include_router(seo_optimization_router)
router.include_router(seo_tracking_router)
router.include_router(batch_seo_router)
router.include_router(content_quality_router)
router.include_router(schema_generator_router)
router.include_router(seo_dashboard_router)
