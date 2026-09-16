"""
RAG 检索节点执行器

在知识库中进行语义检索，返回相关文档片段。
支持纯检索模式和 RAG 问答模式。
"""

from typing import Any, Dict

from src.unified_logger import default_logger as logger
from shared.services.workflow.node_executors.base import BaseNodeExecutor


class RAGNodeExecutor(BaseNodeExecutor):
    """RAG 检索节点"""

    @property
    def node_type(self) -> str:
        return "rag"

    async def execute(self, node: Dict, inputs: Dict) -> Dict:
        """
        执行 RAG 检索 / 问答

        config 参数:
            knowledge_base_id: int - 知识库 ID（必填）
            mode: str - "search" | "qa"，默认 "search"
            default_query: str - 默认查询语句（当 inputs 中无 query 时使用）
            top_k: int - 返回结果数量，默认 5
            score_threshold: float - 最低相关性阈值，默认 0.3
        """
        from shared.services.knowledge.rag_chain import rag_chain

        kb_id = self._get_config(node, "knowledge_base_id")
        if kb_id is None:
            return {"success": False, "error": "未配置 knowledge_base_id"}

        mode = self._get_config(node, "mode", "search")
        default_query = self._get_config(node, "default_query", "")
        top_k = self._get_config(node, "top_k", 5)
        score_threshold = self._get_config(node, "score_threshold", 0.3)

        # 从 inputs 或配置获取查询
        query = inputs.get("query") or inputs.get("question") or default_query
        if not query:
            return {"success": False, "error": "未提供查询内容 (query)"}

        try:
            if mode == "qa":
                result = await rag_chain.query(
                    query=query,
                    knowledge_base_id=kb_id,
                    top_k=top_k,
                    score_threshold=score_threshold,
                )
            else:
                result = await rag_chain.search(
                    query=query,
                    knowledge_base_id=kb_id,
                    top_k=top_k,
                    score_threshold=score_threshold,
                )

            return {
                "success": result.get("success", False),
                "answer": result.get("answer", ""),
                "sources": result.get("sources", []),
                "confidence": result.get("confidence", 0.0),
                "query": query,
            }
        except Exception as exc:
            logger.error(f"[RAGNode] RAG 执行失败: {exc}")
            return {"success": False, "error": str(exc)}
