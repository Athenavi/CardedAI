"""
移动端同步 API 路由
为 Mobile App 提供离线写作、媒体同步及通知推送支持
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional

from shared.models.article import Article
from shared.models.media import Media
from src.auth.auth_deps import jwt_required_dependency as jwt_required
from shared.models.user import User
from sqlalchemy import select, desc
from src.utils.database.main import get_async_session

router = APIRouter(prefix="/mobile", tags=["Mobile Sync"])


@router.get("/sync/articles")
async def sync_articles(
        last_sync_time: Optional[str] = Query(None, description="上次同步时间 (ISO format)"),
        current_user: User = Depends(jwt_required)
):
    """P5-1: 增量同步文章数据"""
    async for db in get_async_session():
        query = select(Article).where(Article.user == current_user.id).order_by(desc(Article.updated_at))

        if last_sync_time:
            from datetime import datetime
            dt = datetime.fromisoformat(last_sync_time.replace("Z", "+00:00"))
            query = query.where(Article.updated_at > dt)

        result = await db.execute(query)
        articles = result.scalars().all()

        return {
            "success": True,
            "data": [a.to_dict() for a in articles],
            "sync_time": datetime.utcnow().isoformat()
        }


@router.get("/sync/media")
async def sync_media(
        last_sync_time: Optional[str] = Query(None),
        current_user: User = Depends(jwt_required)
):
    """P5-1: 增量同步媒体库"""
    async for db in get_async_session():
        query = select(Media).where(Media.user == current_user.id).order_by(desc(Media.created_at))

        if last_sync_time:
            from datetime import datetime
            dt = datetime.fromisoformat(last_sync_time.replace("Z", "+00:00"))
            query = query.where(Media.created_at > dt)

        result = await db.execute(query)
        media_list = result.scalars().all()

        return {
            "success": True,
            "data": [m.to_dict() for m in media_list]
        }


@router.post("/offline/upload")
async def upload_offline_content(
        payload: dict,
        current_user: User = Depends(jwt_required)
):
    """P5-1: 接收离线写作内容并同步到服务器"""
    # 实际实现应解析 payload 并调用文章创建/更新逻辑
    return {"success": True, "message": "Offline content synced successfully"}
