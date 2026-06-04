"""
工作流节点执行器模块

支持 LLM、采集器、RAG、条件判断、通知等节点类型。

用法:
    from shared.services.workflow.node_executors.base import BaseNodeExecutor
    from shared.services.workflow.node_executors.llm_node import LLMNodeExecutor
    # ...

或通过 lazy import:
    from shared.services.workflow import LLMNodeExecutor
"""


def __getattr__(name: str):
    """延迟导入"""
    _lazy_imports = {
        "BaseNodeExecutor": "shared.services.workflow.node_executors.base",
        "LLMNodeExecutor": "shared.services.workflow.node_executors.llm_node",
        "CollectorNodeExecutor": "shared.services.workflow.node_executors.collector_node",
        "RAGNodeExecutor": "shared.services.workflow.node_executors.rag_node",
        "ConditionNodeExecutor": "shared.services.workflow.node_executors.condition_node",
        "NotifyNodeExecutor": "shared.services.workflow.node_executors.notify_node",
    }

    if name in _lazy_imports:
        import importlib
        module = importlib.import_module(_lazy_imports[name])
        obj = getattr(module, name)
        globals()[name] = obj
        return obj

    raise AttributeError(f"module 'shared.services.workflow.node_executors' has no attribute {name!r}")


def get_all_executors():
    """
    获取所有节点执行器实例的字典

    Returns:
        Dict[str, BaseNodeExecutor]: {node_type_name: executor_instance}
    """
    from .llm_node import LLMNodeExecutor
    from .collector_node import CollectorNodeExecutor
    from .rag_node import RAGNodeExecutor
    from .condition_node import ConditionNodeExecutor
    from .notify_node import NotifyNodeExecutor

    return {
        "llm": LLMNodeExecutor(),
        "collector": CollectorNodeExecutor(),
        "rag": RAGNodeExecutor(),
        "condition": ConditionNodeExecutor(),
        "notify": NotifyNodeExecutor(),
    }
