"""
数据采集节点执行器

触发指定数据源的采集任务，聚合结果。
复用情报引擎的 CollectorEngine。
"""

from typing import Any, Dict, List

from src.unified_logger import default_logger as logger
from shared.services.workflow.node_executors.base import BaseNodeExecutor


class CollectorNodeExecutor(BaseNodeExecutor):
    """数据采集节点"""

    @property
    def node_type(self) -> str:
        return "collector"

    async def execute(self, node: Dict, inputs: Dict) -> Dict:
        """
        触发数据采集

        config 参数:
            source_ids: List[int] - 数据源 ID 列表
            wait_for_results: bool - 是否等待采集完成，默认 True
        """
        from shared.services.intel.collector_engine import collector_engine

        source_ids: List[int] = self._get_config(node, "source_ids", [])
        if not source_ids:
            return {"success": False, "error": "未配置 source_ids"}

        results = []
        errors = []

        for sid in source_ids:
            try:
                outcome = await collector_engine.run_collection(sid)
                results.append({
                    "source_id": sid,
                    **outcome,
                })
            except Exception as exc:
                logger.error(f"[CollectorNode] 数据源 {sid} 采集失败: {exc}")
                errors.append({"source_id": sid, "error": str(exc)})

        total_items = sum(r.get("item_count", 0) for r in results)

        return {
            "success": len(errors) == 0,
            "collected_items": total_items,
            "source_results": results,
            "errors": errors,
        }
