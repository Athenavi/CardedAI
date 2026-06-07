"""
DAG 工作流执行引擎

核心能力：
- 从 JSON 图结构解析节点和边
- 拓扑排序确定执行顺序（Kahn 算法）
- 按层级并行执行节点（带并发控制）
- 自动传递节点间数据
- 处理条件分支跳过
- 记录每一步的执行状态
- 集成 WorkflowConcurrencyManager 限制并发资源
"""

import asyncio
import json
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from src.unified_logger import default_logger as logger

# 性能优化：并发控制（延迟导入避免循环依赖）
def _get_concurrency_manager():
    """延迟获取并发管理器（允许在无 Redis 环境下优雅降级）"""
    try:
        from shared.services.performance.engine_optimizer import get_concurrency_manager
        return get_concurrency_manager()
    except Exception:
        return None


@dataclass
class ExecutionResult:
    """工作流执行结果"""
    execution_id: Optional[int] = None
    workflow_id: Optional[int] = None
    status: str = "pending"  # pending / running / completed / failed / cancelled
    output_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    node_results: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "status": self.status,
            "output_data": self.output_data,
            "error_message": self.error_message,
            "node_results": {k: str(v)[:200] for k, v in self.node_results.items()},
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class DAGEngine:
    """
    DAG 工作流执行引擎

    支持的功能：
    - 拓扑排序 + 层级并行执行
    - 节点类型动态分发（通过注册的执行器）
    - 条件分支：condition 节点返回 true/false 后，
      后续节点可通过 depends_on + branch 条件跳过
    - 执行状态持久化到数据库
    """

    # 默认节点超时（秒）
    DEFAULT_NODE_TIMEOUT = 300

    def __init__(self):
        self._node_executors: Dict[str, Callable] = {}
        self._cancel_flags: Dict[int, bool] = {}  # execution_id -> cancelled

    # ------------------------------------------------------------------
    # 执行器注册
    # ------------------------------------------------------------------

    def register_executor(self, node_type: str, executor: Callable) -> None:
        """注册节点类型执行器

        Args:
            node_type: 节点类型标识 (llm / collector / rag / condition / notify / ...)
            executor: 异步可调用对象，签名 async execute(node, inputs) -> dict
        """
        self._node_executors[node_type] = executor
        logger.info(f"[DAGEngine] 注册节点执行器: {node_type}")

    def get_registered_types(self) -> List[str]:
        """返回已注册的节点类型列表"""
        return sorted(self._node_executors.keys())

    # ------------------------------------------------------------------
    # 图解析 & 拓扑排序
    # ------------------------------------------------------------------

    @staticmethod
    def parse_graph(graph_data) -> Dict[str, Any]:
        """解析图结构 JSON

        Args:
            graph_data: dict 或 JSON 字符串，包含 nodes / edges

        Returns:
            {"nodes": [...], "edges": [...]}
        """
        if isinstance(graph_data, str):
            graph_data = json.loads(graph_data)
        if not isinstance(graph_data, dict):
            raise ValueError("graph_data 必须是 dict 或 JSON 字符串")
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        return {"nodes": nodes, "edges": edges}

    @staticmethod
    def topological_sort(nodes: List[Dict], edges: List[Dict]) -> List[List[Dict]]:
        """拓扑排序（Kahn 算法），返回按层级分组的节点列表

        每个层级内的节点互相无依赖，可以并行执行。

        Returns:
            [[node_layer_0], [node_layer_1], ...]
        """
        node_map = {n["id"]: n for n in nodes}
        in_degree: Dict[str, int] = {n["id"]: 0 for n in nodes}
        children: Dict[str, List[str]] = defaultdict(list)

        for edge in edges:
            src = edge.get("source") or edge.get("from")
            tgt = edge.get("target") or edge.get("to")
            if src in node_map and tgt in node_map:
                children[src].append(tgt)
                in_degree[tgt] = in_degree.get(tgt, 0) + 1

        # 零入度节点初始化第一层
        queue: deque = deque()
        for nid, deg in in_degree.items():
            if deg == 0:
                queue.append(nid)

        layers: List[List[Dict]] = []
        visited = 0

        while queue:
            layer = []
            for _ in range(len(queue)):
                nid = queue.popleft()
                layer.append(node_map[nid])
                visited += 1
                for child in children[nid]:
                    in_degree[child] -= 1
                    if in_degree[child] == 0:
                        queue.append(child)
            if layer:
                layers.append(layer)

        if visited != len(nodes):
            raise ValueError(
                f"DAG 存在环: 期望 {len(nodes)} 个节点, 实际访问 {visited} 个"
            )

        return layers

    @staticmethod
    def validate_graph(nodes: List[Dict], edges: List[Dict]) -> List[str]:
        """校验图结构，返回错误列表（空表示合法）

        检查项：
        - 节点 id 唯一
        - 边引用的节点 id 存在
        - 无环

        注意：允许空图（创建时用户尚未添加节点），
        完整性校验在激活或执行前进行。
        """
        errors: List[str] = []
        if not nodes:
            # 创建时允许空图，用户后续在编辑器中添加节点
            return errors

        ids = [n["id"] for n in nodes]
        if len(ids) != len(set(ids)):
            errors.append("存在重复的节点 id")

        node_set = set(ids)
        for e in edges:
            src = e.get("source") or e.get("from")
            tgt = e.get("target") or e.get("to")
            if src not in node_set:
                errors.append(f"边引用不存在的源节点: {src}")
            if tgt not in node_set:
                errors.append(f"边引用不存在的目标节点: {tgt}")

        # 环检测
        try:
            DAGEngine.topological_sort(nodes, edges)
        except ValueError as exc:
            errors.append(str(exc))

        return errors

    # ------------------------------------------------------------------
    # 执行入口
    # ------------------------------------------------------------------

    async def execute(
        self,
        workflow_id: int,
        graph_data,
        input_data: Optional[Dict] = None,
        trigger_type: str = "manual",
    ) -> ExecutionResult:
        """执行工作流

        Args:
            workflow_id: 工作流定义 ID
            graph_data: 图结构 (dict / JSON str)
            input_data: 全局输入数据
            trigger_type: 触发类型 (manual / scheduled / event)

        Returns:
            ExecutionResult
        """
        result = ExecutionResult(
            workflow_id=workflow_id,
            status="running",
            started_at=datetime.utcnow(),
        )

        # 性能优化：获取并发管理器（可选，无则降级为无限制模式）
        concurrency_mgr = _get_concurrency_manager()

        # 获取工作流级并发许可
        if concurrency_mgr:
            await concurrency_mgr.acquire_workflow(workflow_id)

        try:
            graph = self.parse_graph(graph_data)
            nodes = graph["nodes"]
            edges = graph["edges"]

            # 图校验
            errors = self.validate_graph(nodes, edges)
            if errors:
                raise ValueError(f"图校验失败: {'; '.join(errors)}")

            # 执行时不允许空图
            if not nodes:
                raise ValueError("工作流图中无节点，无法执行。请先在编辑器中添加节点。")

            # 拓扑排序
            layers = self.topological_sort(nodes, edges)
            logger.info(
                f"[DAGEngine] 工作流 {workflow_id} 共 {len(nodes)} 节点, "
                f"{len(layers)} 层"
            )

            # 构建上下文（节点 id -> 输出）
            context: Dict[str, Any] = {"__input__": input_data or {}}
            self._cancel_flags[workflow_id] = False

            for layer_idx, layer in enumerate(layers):
                # 检查取消标志
                if self._cancel_flags.get(workflow_id):
                    result.status = "cancelled"
                    result.error_message = "执行被用户取消"
                    break

                logger.info(
                    f"[DAGEngine] 执行第 {layer_idx + 1}/{len(layers)} 层, "
                    f"节点: {[n['id'] for n in layer]}"
                )

                # 同层并行（带并发信号量控制）
                tasks = []
                for node in layer:
                    node_coro = self._run_node(node, edges, context)
                    if concurrency_mgr:
                        # 通过信号量限制并发，防止单个工作流耗尽系统资源
                        limited_coro = concurrency_mgr.run_node_with_limit(
                            node_coro, node["id"], node.get("type", "unknown")
                        )
                        tasks.append(limited_coro)
                    else:
                        tasks.append(node_coro)

                results = await asyncio.gather(*tasks, return_exceptions=True)

                for node, res in zip(layer, results):
                    nid = node["id"]
                    if isinstance(res, Exception):
                        result.node_results[nid] = {
                            "status": "failed",
                            "error": str(res),
                        }
                        logger.error(
                            f"[DAGEngine] 节点 {nid} 执行失败: {res}"
                        )
                        # 根据节点配置决定是否继续
                        if node.get("config", {}).get("fail_fast", True):
                            raise res
                    else:
                        context[nid] = res
                        result.node_results[nid] = {
                            "status": "completed",
                            "output": res,
                        }

            # 聚合最终输出
            if result.status == "running":
                result.status = "completed"
                # 取最后一个节点的输出作为总输出
                if layers:
                    last_layer = layers[-1]
                    for node in last_layer:
                        nid = node["id"]
                        if nid in context:
                            result.output_data[nid] = context[nid]

        except Exception as exc:
            result.status = "failed"
            result.error_message = str(exc)
            logger.error(f"[DAGEngine] 工作流 {workflow_id} 执行失败: {exc}")

        finally:
            # 释放工作流级并发许可
            if concurrency_mgr:
                concurrency_mgr.release_workflow(workflow_id)

        result.completed_at = datetime.utcnow()
        return result

    # ------------------------------------------------------------------
    # 单节点执行
    # ------------------------------------------------------------------

    async def _run_node(
        self,
        node: Dict,
        edges: List[Dict],
        context: Dict[str, Any],
    ) -> Any:
        """执行单个节点

        1. 收集上游输出作为输入
        2. 查找对应执行器
        3. 执行并返回结果
        """
        node_id = node["id"]
        node_type = node.get("type", "unknown")
        config = node.get("config", {})

        # 检查条件分支：如果上游 condition 节点的结果不满足 branch 要求则跳过
        branch_filter = node.get("branch")
        if branch_filter:
            should_skip = self._check_branch_skip(node_id, edges, context, branch_filter)
            if should_skip:
                logger.info(f"[DAGEngine] 节点 {node_id} 因条件分支跳过")
                return {"skipped": True, "reason": f"branch '{branch_filter}' not taken"}

        # 收集输入
        inputs = self._resolve_inputs(node_id, edges, context)

        # 查找执行器
        executor = self._node_executors.get(node_type)
        if executor is None:
            # 未注册的节点类型，直接透传输入
            logger.warning(f"[DAGEngine] 未找到节点类型 '{node_type}' 的执行器，透传输入")
            return {"passthrough": True, "inputs": inputs}

        # 执行
        start = time.monotonic()
        try:
            result = await asyncio.wait_for(
                executor.execute(node, inputs),
                timeout=config.get("timeout", self.DEFAULT_NODE_TIMEOUT),
            )
        except asyncio.TimeoutError:
            raise TimeoutError(f"节点 {node_id} 执行超时 ({config.get('timeout', self.DEFAULT_NODE_TIMEOUT)}s)")

        elapsed = time.monotonic() - start
        logger.info(f"[DAGEngine] 节点 {node_id} ({node_type}) 完成, 耗时 {elapsed:.2f}s")
        return result

    def _resolve_inputs(
        self,
        node_id: str,
        edges: List[Dict],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """从上游节点收集输出作为当前节点输入"""
        inputs: Dict[str, Any] = {}
        for edge in edges:
            tgt = edge.get("target") or edge.get("to")
            src = edge.get("source") or edge.get("from")
            if tgt == node_id and src in context:
                output = context[src]
                if isinstance(output, dict):
                    inputs.update(output)
                else:
                    inputs[src] = output
        # 合并全局输入
        global_input = context.get("__input__", {})
        if isinstance(global_input, dict):
            for k, v in global_input.items():
                if k not in inputs:
                    inputs[k] = v
        return inputs

    def _check_branch_skip(
        self,
        node_id: str,
        edges: List[Dict],
        context: Dict[str, Any],
        branch_filter: str,
    ) -> bool:
        """检查条件分支：如果上游 condition 节点的 branch 不匹配则跳过"""
        for edge in edges:
            tgt = edge.get("target") or edge.get("to")
            src = edge.get("source") or edge.get("from")
            if tgt == node_id and src in context:
                upstream = context[src]
                if isinstance(upstream, dict):
                    upstream_branch = upstream.get("branch")
                    if upstream_branch is not None and upstream_branch != branch_filter:
                        return True
        return False

    # ------------------------------------------------------------------
    # 取消执行
    # ------------------------------------------------------------------

    def cancel_execution(self, workflow_id: int) -> None:
        """标记执行为取消状态"""
        self._cancel_flags[workflow_id] = True
        logger.info(f"[DAGEngine] 工作流 {workflow_id} 已标记为取消")


# 全局单例
dag_engine = DAGEngine()
