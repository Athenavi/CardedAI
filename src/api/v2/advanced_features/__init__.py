"""
高级功能API聚合路由器 - V2统一入口
整合V1的advanced_features相关模块

使用懒加载模式：仅在首次访问 router 时才导入 V1 子模块。
"""
from fastapi import APIRouter

_router = None


def _build_router():
    global _router
    if _router is not None:
        return _router

    router = APIRouter(tags=["advanced-features"])

    from src.api.v1.advanced_features.achievement_badges import router as achievement_badges_router
    from src.api.v1.advanced_features.ai_recommendations import router as ai_recommendations_router
    from src.api.v1.advanced_features.edge_functions import router as edge_functions_router
    from src.api.v1.advanced_features.expert_certification import router as expert_certification_router
    from src.api.v1.advanced_features.membership import router as membership_router
    from src.api.v1.advanced_features.nft import router as nft_router
    from src.api.v1.advanced_features.personalized_feed import router as personalized_feed_router
    from src.api.v1.advanced_features.points_system import router as points_system_router
    from src.api.v1.advanced_features.recommendations import router as recommendations_router
    from src.api.v1.advanced_features.tipping_system import router as tipping_system_router
    from src.api.v1.advanced_features.websocket import router as websocket_router

    router.include_router(membership_router, prefix="/membership")
    router.include_router(edge_functions_router, prefix="/edge-func")
    router.include_router(achievement_badges_router, prefix="/badges")
    router.include_router(ai_recommendations_router, prefix="/ai-recommendations")
    router.include_router(expert_certification_router, prefix="/expert-certification")
    router.include_router(nft_router, prefix="/nft")
    router.include_router(personalized_feed_router, prefix="/personalized-feed")
    router.include_router(points_system_router, prefix="/points")
    router.include_router(recommendations_router, prefix="/recommendations")
    router.include_router(tipping_system_router, prefix="/tipping")
    router.include_router(websocket_router, prefix="/ws")

    _router = router
    return _router


def __getattr__(name):
    if name == "router":
        return _build_router()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
