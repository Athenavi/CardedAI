"""
访问明细采集（Phase 2）

前端在页面加载/卸载时通过 navigator.sendBeacon 上报，此端点负责落库：

- 匿名可用：未登录访客的 user_id 为空
- 不存原始 IP：仅保存 sha256(ip|ua) 前 32 位作为 visitor_hash，用于 UV 去重
- 防刷：同一 visitor_hash + path 在 30 秒内只记一次
- 停留时长：离站补报时更新最近一条同访客同路径的记录
- 保留策略：每 200 次上报触发一次清理，删除 180 天前的明细
"""

import hashlib
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.page_view import PageView
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_optional_dependency
from src.extensions import cache
from src.unified_logger import default_logger as logger
from src.utils.database.main import get_async_session

router = APIRouter(tags=["analytics-collect"])

DEDUP_WINDOW_SECONDS = 30  # 同一访客同一路径的去重窗口
RETENTION_DAYS = 180  # 明细保留天数
CLEANUP_EVERY = 200  # 每 N 次上报触发一次清理
COUNTER_KEY = "pageview:collect:counter"


class PageViewPayload(BaseModel):
    path: str
    article_id: Optional[int] = None
    referrer: Optional[str] = None
    duration_ms: Optional[int] = None


def _visitor_hash(request: Request) -> str:
    """IP + UA 哈希（不落原始 IP）"""
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")
    return hashlib.sha256(f"{ip}|{ua}".encode("utf-8")).hexdigest()[:32]


async def _maybe_cleanup(db: AsyncSession) -> None:
    """低频清理过期明细（失败不影响上报）"""
    try:
        raw = cache.get(COUNTER_KEY)
        count = int(raw) + 1 if raw else 1
        cache.set(COUNTER_KEY, str(count), ex=86400)
        if count % CLEANUP_EVERY != 0:
            return
        cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
        await db.execute(delete(PageView).where(PageView.created_at < cutoff))
        await db.commit()
        logger.info(f"[PageView] cleaned records older than {RETENTION_DAYS} days")
    except Exception as exc:
        logger.warning(f"[PageView] cleanup skipped: {exc}")


@router.post("/pageview")
async def collect_pageview(
    request: Request,
    payload: PageViewPayload,
    current_user=Depends(jwt_optional_dependency),
    db: AsyncSession = Depends(get_async_session),
):
    """
    记录一次页面访问；带 duration_ms 时视为离站补报（更新最近记录）
    """
    try:
        path = (payload.path or "").strip()[:512]
        if not path:
            return ApiResponse(success=False, error="path 不能为空")

        visitor = _visitor_hash(request)
        user_id = getattr(current_user, "id", None)
        now = datetime.now()

        # 离站补报：更新最近 30 分钟内同访客同路径的停留时长
        if payload.duration_ms is not None:
            duration = max(0, min(int(payload.duration_ms), 24 * 3600 * 1000))
            window_start = now - timedelta(minutes=30)
            result = await db.execute(
                select(PageView.id)
                .where(
                    PageView.visitor_hash == visitor,
                    PageView.path == path,
                    PageView.created_at >= window_start,
                )
                .order_by(PageView.created_at.desc())
                .limit(1)
            )
            recent = result.scalars().first()
            if recent:
                await db.execute(
                    update(PageView).where(PageView.id == recent).values(duration_ms=duration)
                )
                await db.commit()
                return ApiResponse(success=True, data={"updated": True, "id": recent})

        # 去重（同一访客同一路径 30 秒内只记一次）
        dedup_key = f"pageview:dedup:{visitor}:{hashlib.md5(path.encode()).hexdigest()[:16]}"
        try:
            if cache.get(dedup_key):
                return ApiResponse(success=True, data={"accepted": False, "reason": "deduplicated"})
            cache.set(dedup_key, "1", ex=DEDUP_WINDOW_SECONDS)
        except Exception:
            pass  # 缓存不可用时不做去重，保证上报不失败

        db.add(PageView(
            path=path,
            article_id=payload.article_id,
            user_id=user_id,
            visitor_hash=visitor,
            referrer=(payload.referrer or None) and payload.referrer[:512],
            user_agent=(request.headers.get("user-agent") or "")[:512] or None,
            duration_ms=None,
            created_at=now,
        ))
        await db.commit()
        await _maybe_cleanup(db)

        return ApiResponse(success=True, data={"accepted": True})
    except Exception as exc:
        logger.warning(f"[PageView] collect failed: {exc}")
        return ApiResponse(success=False, error=str(exc))
