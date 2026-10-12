"""
V2 全局性能统计 API

聚合四大引擎（情报 / 知识 / 自动化 / 性能）的运行时指标与实体规模，
供管理后台与运维监控使用。
"""

import logging

from fastapi import APIRouter, Depends

from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required

logger = logging.getLogger(__name__)
router = APIRouter(tags=["performance-stats"])


async def _collect_engine_counts() -> dict:
    """汇总各引擎的数据库实体规模"""
    try:
        from sqlalchemy import func, select

        from shared.models import (
            AgentTool,
            Briefing,
            CollectedItem,
            DataSource,
            DocumentChunk,
            GeneratedReport,
            Intelligence,
            KnowledgeBase,
            KnowledgeDocument,
            WorkflowDefinition,
            WorkflowExecution,
        )
        from src.extensions import get_async_session_context

        async def _count(db, model) -> int:
            return (await db.execute(select(func.count(model.id)))).scalar() or 0

        async with get_async_session_context() as db:
            return {
                "intel": {
                    "data_sources": await _count(db, DataSource),
                    "collected_items": await _count(db, CollectedItem),
                    "intelligence": await _count(db, Intelligence),
                    "briefings": await _count(db, Briefing),
                },
                "knowledge": {
                    "knowledge_bases": await _count(db, KnowledgeBase),
                    "documents": await _count(db, KnowledgeDocument),
                    "chunks": await _count(db, DocumentChunk),
                    "reports": await _count(db, GeneratedReport),
                },
                "workflow": {
                    "definitions": await _count(db, WorkflowDefinition),
                    "executions": await _count(db, WorkflowExecution),
                    "tools": await _count(db, AgentTool),
                },
            }
    except Exception as e:  # 统计失败不应影响端点整体可用性
        logger.warning(f"引擎实体计数采集失败: {e}")
        return {}


@router.get("/stats", summary="全局性能统计", response_model=ApiResponse)
async def get_global_performance_stats(current_user=Depends(jwt_required)):
    """
    获取全局性能统计

    返回内容：
    - runtime：进程内性能组件（采集队列 / RAG 缓存 / 批量 Embedding / 并发控制）
    - system：服务端从性能监控器采集的基础指标
    - engines：情报 / 知识 / 自动化 引擎的实体规模
    """
    try:
        from shared.services.performance.engine_optimizer import (
            get_collection_queue,
            get_engine_stats,
        )
        from shared.services.performance.performance_monitor import performance_monitor

        runtime = get_engine_stats()

        # 采集队列的待处理数量需要异步查询（Redis 后端下为 XLEN）
        try:
            runtime.setdefault("collection_queue", {})["pending"] = (
                await get_collection_queue().pending_count()
            )
        except Exception as e:
            logger.warning(f"采集队列待处理数查询失败: {e}")

        data = {
            "runtime": runtime,
            "system": performance_monitor.get_server_metrics(),
            "engines": await _collect_engine_counts(),
        }
        return ApiResponse(success=True, data=data)
    except Exception as e:
        logger.error(f"获取全局性能统计失败: {e}")
        return ApiResponse(success=False, error=f"获取统计失败: {str(e)}")


@router.get("/stats/runtime", summary="运行时性能组件统计", response_model=ApiResponse)
async def get_runtime_stats(current_user=Depends(jwt_required)):
    """仅返回进程内性能组件的统计（不访问数据库）"""
    try:
        from shared.services.performance.engine_optimizer import (
            get_collection_queue,
            get_engine_stats,
        )

        runtime = get_engine_stats()
        try:
            runtime.setdefault("collection_queue", {})["pending"] = (
                await get_collection_queue().pending_count()
            )
        except Exception as e:
            logger.warning(f"采集队列待处理数查询失败: {e}")

        return ApiResponse(success=True, data=runtime)
    except Exception as e:
        logger.error(f"获取运行时统计失败: {e}")
        return ApiResponse(success=False, error=f"获取统计失败: {str(e)}")
