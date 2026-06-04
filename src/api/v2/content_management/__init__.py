"""
内容管理API聚合路由器 - V2统一入口
整合V1的content_management相关模块

使用懒加载模式：仅在首次访问 router 时才导入 V1 子模块。
"""
from fastapi import APIRouter

_router = None


def _build_router():
    global _router
    if _router is not None:
        return _router

    router = APIRouter(tags=["content-management"])

    from src.api.v1.content_management.block_editor import router as block_editor_router
    from src.api.v1.content_management.block_patterns import router as block_patterns_router
    from src.api.v1.content_management.category_management import router as category_management_router
    from src.api.v1.content_management.custom_block_patterns import router as custom_block_patterns_router
    from src.api.v1.content_management.custom_post_types import router as custom_post_types_router
    from src.api.v1.content_management.feed import router as feed_router
    from src.api.v1.content_management.form_builder import router as form_builder_router
    from src.api.v1.content_management.global_styles import router as global_styles_router
    from src.api.v1.content_management.menu_management import router as menu_management_router
    from src.api.v1.content_management.page_builder_routes import router as page_builder_router
    from src.api.v1.content_management.shortcode import router as shortcode_router
    from src.api.v1.content_management.widgets import router as widgets_router

    router.include_router(category_management_router, prefix="/categories")
    router.include_router(form_builder_router, prefix="/admin/form")
    router.include_router(menu_management_router, prefix="/admin/menu")
    router.include_router(custom_block_patterns_router, prefix="/pattern")
    router.include_router(block_patterns_router, prefix="/block-patterns")
    router.include_router(global_styles_router, prefix="/global-styles")
    router.include_router(block_editor_router, prefix="/editor")
    router.include_router(custom_post_types_router, prefix="/post-types")
    router.include_router(feed_router, prefix="")
    router.include_router(shortcode_router, prefix="/shortcodes")
    router.include_router(widgets_router, prefix="/widgets")
    router.include_router(page_builder_router, prefix="")

    _router = router
    return _router


def __getattr__(name):
    if name == "router":
        return _build_router()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
