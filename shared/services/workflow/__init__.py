"""
自动化引擎服务模块

提供工作流定义、DAG 执行、节点调度、触发器管理、工具注册等功能。

主要组件:
    dag_engine      - DAG 工作流执行引擎（拓扑排序 + 层级并行执行）
    trigger_service - 触发器服务（Cron / Event / Webhook）
    tool_registry   - Agent 工具注册中心（动态工具管理）

节点执行器:
    node_executors.llm_node         - LLM 调用节点
    node_executors.collector_node   - 数据采集节点
    node_executors.rag_node         - RAG 检索节点
    node_executors.condition_node   - 条件判断节点
    node_executors.notify_node      - 通知推送节点
"""


def __getattr__(name: str):
    """延迟导入，按需加载子模块"""
    _lazy_imports = {
        # 核心引擎
        "dag_engine": "shared.services.workflow.dag_engine",
        "DAGEngine": "shared.services.workflow.dag_engine",
        "ExecutionResult": "shared.services.workflow.dag_engine",
        # 触发器
        "trigger_service": "shared.services.workflow.trigger_service",
        "TriggerService": "shared.services.workflow.trigger_service",
        # 工具注册
        "tool_registry": "shared.services.workflow.tool_registry",
        "AgentToolRegistry": "shared.services.workflow.tool_registry",
        # 节点执行器
        "BaseNodeExecutor": "shared.services.workflow.node_executors.base",
        "LLMNodeExecutor": "shared.services.workflow.node_executors.llm_node",
        "CollectorNodeExecutor": "shared.services.workflow.node_executors.collector_node",
        "RAGNodeExecutor": "shared.services.workflow.node_executors.rag_node",
        "ConditionNodeExecutor": "shared.services.workflow.node_executors.condition_node",
        "NotifyNodeExecutor": "shared.services.workflow.node_executors.notify_node",
    }

    if name in _lazy_imports:
        import importlib
        module_path = _lazy_imports[name]
        module = importlib.import_module(module_path)
        obj = getattr(module, name)
        globals()[name] = obj  # 缓存
        return obj

    raise AttributeError(f"module 'shared.services.workflow' has no attribute {name!r}")
