"""
标签 API
- GET /api/v2/tags           标签列表（含文章计数，支持排序/搜索/分页）
- GET /api/v2/tags/suggest   标签自动补全（前缀匹配，最多 5 个）

数据来源：已发布文章的 `Article.tags_list` 字段聚合（不新增表结构）。
聚合结果带短 TTL 缓存，避免每次请求全表扫描。
"""

import json
import re
import traceback
from collections import Counter

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.article import Article
from src.api.v1.core.responses import ApiResponse
from src.extensions import cache
from src.utils.database.main import get_async_session
from src.utils.seo import slugify

from src.unified_logger import default_logger as logger

router = APIRouter(tags=["tags"])

TAG_SUMMARY_CACHE_KEY = 'v2_tag_summary'
TAG_SUMMARY_TTL = 300  # 5 分钟


def _split_tags(tags_str) -> list:
    """将标签字符串拆分为数组，同时支持中英文逗号/分号分隔符"""
    if not tags_str:
        return []
    if isinstance(tags_str, (list, tuple)):
        return [str(t).strip() for t in tags_str if str(t).strip()]
    normalized = str(tags_str).replace('，', ',').replace('；', ';')
    return [t.strip() for t in re.split(r'[,;]', normalized) if t.strip()]


async def _collect_tag_counts(db: AsyncSession) -> Counter:
    """聚合已发布文章的标签计数"""
    result = await db.execute(
        select(Article.tags_list).where(
            Article.status == 1,
            Article.hidden == False,  # noqa: E712 - 与项目其它查询保持一致
            Article.is_vip_only == False,  # noqa: E712
        )
    )

    counter: Counter = Counter()
    for row in result.all():
        for tag in _split_tags(row[0]):
            counter[tag] += 1
    return counter


async def _get_tag_counts(db: AsyncSession) -> Counter:
    """带缓存的标签计数（缓存不可用时静默降级为直接查询）"""
    try:
        raw = cache.get(TAG_SUMMARY_CACHE_KEY)
        if raw:
            if isinstance(raw, (bytes, bytearray)):
                raw = raw.decode('utf-8', errors='replace')
            if isinstance(raw, str):
                raw = json.loads(raw)
            if isinstance(raw, dict):
                return Counter(raw)
    except Exception:
        pass

    counter = await _collect_tag_counts(db)

    try:
        cache.set(TAG_SUMMARY_CACHE_KEY, json.dumps(dict(counter), ensure_ascii=False), ex=TAG_SUMMARY_TTL)
    except Exception:
        pass

    return counter


@router.get('')
async def list_tags(
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(48, ge=1, le=200, description="每页数量"),
    sort: str = Query("count", pattern="^(count|name)$", description="排序方式：count=按文章数，name=按名称"),
    q: str = Query("", description="按标签名过滤（不区分大小写）"),
    db: AsyncSession = Depends(get_async_session),
):
    """
    标签列表（含文章计数）

    返回结构：
        data.tags: [{name, slug, count}]
        data.total_tags: 标签总数
        data.pagination: 分页信息
    """
    try:
        counter = await _get_tag_counts(db)

        items = [
            {"name": name, "slug": slugify(name) or name, "count": count}
            for name, count in counter.items()
        ]

        keyword = (q or "").strip().lower()
        if keyword:
            items = [item for item in items if keyword in item["name"].lower()]

        if sort == "name":
            items.sort(key=lambda item: item["name"])
        else:
            items.sort(key=lambda item: (-item["count"], item["name"]))

        total = len(items)
        total_pages = max(1, (total + per_page - 1) // per_page)
        start = (page - 1) * per_page

        return ApiResponse(success=True, data={
            "tags": items[start:start + per_page],
            "total_tags": total,
            "pagination": {
                "current_page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
                "has_prev": page > 1,
                "has_next": page < total_pages,
            },
        })
    except Exception as e:
        logger.error(f"Error in list_tags: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=str(e))


@router.get('/suggest')
async def suggest_tags(
    query: str = Query("", alias="q"),
    db: AsyncSession = Depends(get_async_session),
):
    """
    根据前缀建议标签

    Args:
        query: 标签前缀

    Returns:
        匹配的标签列表（最多5个，保持原有裸数组响应格式）
    """
    counter = await _get_tag_counts(db)
    return sorted(tag for tag in counter.keys() if tag.startswith(query))[:5]
