"""
节点执行器基类

所有节点执行器必须继承 BaseNodeExecutor 并实现 execute() 方法。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseNodeExecutor(ABC):
    """工作流节点执行器抽象基类"""

    @property
    def node_type(self) -> str:
        """节点类型标识，子类应覆盖"""
        return "base"

    @abstractmethod
    async def execute(self, node: Dict, inputs: Dict) -> Any:
        """执行节点

        Args:
            node: 节点定义，包含 id / type / config 等字段
            inputs: 上游节点的输出数据

        Returns:
            节点执行结果（通常为 dict）
        """
        ...

    def _get_config(self, node: Dict, key: str, default=None):
        """从节点 config 中安全读取配置"""
        return node.get("config", {}).get(key, default)
