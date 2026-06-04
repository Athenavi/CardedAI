"""
第三方发布 API 路由
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from shared.models.user import User
from shared.services.content_management.third_party_publisher import publisher_service
from src.auth.auth_deps import jwt_required_dependency as jwt_required

router = APIRouter(prefix="/publish", tags=["Third-party Publishing"])


class PublishRequest(BaseModel):
    article_id: int
    platforms: list[str]  # e.g., ["zhihu", "juejin", "medium"]


@router.post("/sync")
async def sync_to_platforms(
        req: PublishRequest,
        current_user: User = Depends(jwt_required)
):
    """P5-2: 一键同步文章到第三方平台"""
    # 1. 获取文章内容
    # 2. 调用 publisher_service 对应的方法

    results = {}
    for platform in req.platforms:
        if platform == "zhihu":
            results["zhihu"] = await publisher_service.publish_to_zhihu({"title": "Test"})
        elif platform == "juejin":
            results["juejin"] = await publisher_service.publish_to_juejin({"title": "Test"})
        elif platform == "medium":
            results["medium"] = await publisher_service.publish_to_medium({"title": "Test"})

    return {"success": True, "results": results}
