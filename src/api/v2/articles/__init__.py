"""
文章API聚合路由器 - V2统一入口
整合V1的articles相关模块

使用懒加载模式：仅在首次访问 router 时才导入 V1 子模块。
"""
from fastapi import APIRouter

_router = None


def _build_router():
    global _router
    if _router is not None:
        return _router

    router = APIRouter(tags=["articles"])

    from src.api.v1.articles.article_analytics import router as article_analytics_router
    from src.api.v1.articles.article_annotations import router as article_annotations_router
    from src.api.v1.articles.article_password import router as article_password_router
    from src.api.v1.articles.article_revisions import router as article_revisions_router
    from src.api.v1.articles.article_search import router as article_search_router
    from src.api.v1.articles.article_stats import router as article_stats_router
    from src.api.v1.articles.articles import router as articles_crud_router
    from src.api.v1.articles.draft_preview import router as draft_preview_router
    from src.api.v1.articles.scheduled_publish import router as scheduled_publish_router

    router.include_router(articles_crud_router, prefix="")
    router.include_router(article_password_router, prefix="")
    router.include_router(article_revisions_router, prefix="")
    router.include_router(article_analytics_router, prefix="/analytics")
    router.include_router(article_annotations_router, prefix="/annotations")
    router.include_router(article_search_router, prefix="/search")
    router.include_router(article_stats_router, prefix="/views")
    router.include_router(draft_preview_router, prefix="/draft")
    router.include_router(scheduled_publish_router, prefix="/scheduler")

    _router = router
    return _router


def __getattr__(name):
    if name == "router":
        return _build_router()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
