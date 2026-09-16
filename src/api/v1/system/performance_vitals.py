"""
前端性能指标上报（Web Vitals）

前端在 lib/performance.ts 中通过 navigator.sendBeacon 上报 LCP/CLS/INP 等指标，
此前后端没有对应端点（每次上报都是 404）。这里提供最小可用的收集端点。

- 匿名可用（不需要登录）：指标上报不应打断页面卸载
- 只做校验 + 记录，不做存储（需要历史分析时可在此处落库或转发到监控系统）
"""

from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

from src.api.v1.core.responses import ApiResponse
from src.unified_logger import default_logger as logger

router = APIRouter(tags=["performance"])

# 允许上报的指标名（Web Vitals 标准指标）
ALLOWED_METRICS = {"LCP", "CLS", "INP", "FID", "TTFB", "FCP"}


class VitalsPayload(BaseModel):
    name: Optional[str] = None
    value: Optional[float] = None
    rating: Optional[str] = None
    url: Optional[str] = None
    navigationType: Optional[str] = None


@router.post("/vitals")
async def collect_web_vitals(request: Request, payload: VitalsPayload):
    """接收前端 Web Vitals 指标（匿名可用，只记录不存储）"""
    name = (payload.name or "").upper()
    if name and name not in ALLOWED_METRICS:
        # 未知指标也接受，但不做重点记录
        logger.debug(f"[WebVitals] unknown metric: {name} value={payload.value}")

    logger.info(
        "[WebVitals] %s=%s rating=%s url=%s",
        name or "unknown",
        payload.value,
        payload.rating or "-",
        (payload.url or "-")[:120],
    )
    return ApiResponse(success=True, data={"accepted": True})
