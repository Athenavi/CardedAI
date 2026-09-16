"""
条件判断节点执行器

支持简单表达式评估和比较操作。
输出 branch 字段 ("true"/"false") 用于下游条件分支路由。
"""

import operator
import re
from typing import Any, Dict

from src.unified_logger import default_logger as logger
from shared.services.workflow.node_executors.base import BaseNodeExecutor


# 支持的比较运算符
_OPERATORS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "in": lambda a, b: a in b,
    "not in": lambda a, b: a not in b,
    "contains": lambda a, b: str(b) in str(a),
    "starts_with": lambda a, b: str(a).startswith(str(b)),
    "ends_with": lambda a, b: str(a).endswith(str(b)),
    "is_empty": lambda a, _: not a if isinstance(a, str) else a is None,
    "is_not_empty": lambda a, _: bool(a) if isinstance(a, str) else a is not None,
}


class ConditionNodeExecutor(BaseNodeExecutor):
    """条件判断节点"""

    @property
    def node_type(self) -> str:
        return "condition"

    async def execute(self, node: Dict, inputs: Dict) -> Dict:
        """
        评估条件表达式

        config 参数:
            expression: str - 条件表达式，格式为 "{field} {op} {value}"
                例如: "score > 0.8", "category == 'tech'", "count >= 10"
            field: str - 直接指定输入字段名
            op: str - 直接指定运算符
            value: Any - 直接指定比较值
            conditions: List[Dict] - 多条件列表（所有条件 AND 组合）

        支持两种配置方式:
        1. expression 字符串: "score > 0.8"
        2. field / op / value 分别配置
        3. conditions 列表（多条件 AND）
        """
        config = node.get("config", {})

        try:
            result = self._evaluate(config, inputs)
            return {
                "condition_result": result,
                "branch": "true" if result else "false",
            }
        except Exception as exc:
            logger.error(f"[ConditionNode] 条件评估失败: {exc}")
            return {
                "condition_result": False,
                "branch": "false",
                "error": str(exc),
            }

    def _evaluate(self, config: Dict, inputs: Dict) -> bool:
        """评估条件"""
        # 多条件 AND 组合
        conditions = config.get("conditions")
        if conditions:
            for cond in conditions:
                if not self._eval_single(cond, inputs):
                    return False
            return True

        # 单条件
        return self._eval_single(config, inputs)

    def _eval_single(self, config: Dict, inputs: Dict) -> bool:
        """评估单个条件"""
        # 方式一: expression 字符串
        expression = config.get("expression")
        if expression:
            return self._eval_expression(expression, inputs)

        # 方式二: field / op / value
        field = config.get("field")
        op = config.get("op", "==")
        value = config.get("value")

        if field is None:
            raise ValueError("条件节点必须配置 expression 或 field")

        actual = self._resolve_field(field, inputs)
        op_func = _OPERATORS.get(op)
        if op_func is None:
            raise ValueError(f"不支持的运算符: {op}, 支持: {list(_OPERATORS.keys())}")

        return op_func(actual, value)

    def _eval_expression(self, expression: str, inputs: Dict) -> bool:
        """解析并评估表达式字符串

        格式: "{field} {op} {value}"
        例如: "score > 0.8", "status == 'active'"
        """
        # 匹配: field_name operator value
        match = re.match(
            r"^\s*(\w+)\s*(==|!=|>=|<=|>|<|in|not in|contains|starts_with|ends_with|is_empty|is_not_empty)\s*(.+?)\s*$",
            expression,
        )
        if not match:
            raise ValueError(f"无法解析表达式: {expression}")

        field_name = match.group(1)
        op_str = match.group(2)
        value_str = match.group(3).strip("'\"")

        actual = self._resolve_field(field_name, inputs)

        # 尝试类型转换
        expected = self._auto_cast(value_str, type(actual) if actual is not None else str)

        op_func = _OPERATORS.get(op_str)
        if op_func is None:
            raise ValueError(f"不支持的运算符: {op_str}")

        return op_func(actual, expected)

    @staticmethod
    def _resolve_field(field_path: str, inputs: Dict) -> Any:
        """从 inputs 中提取字段值，支持点号路径 (e.g. 'result.score')"""
        parts = field_path.split(".")
        current = inputs
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current

    @staticmethod
    def _auto_cast(value_str: str, target_type: type) -> Any:
        """自动类型转换"""
        if target_type is int:
            try:
                return int(value_str)
            except ValueError:
                pass
        if target_type is float:
            try:
                return float(value_str)
            except ValueError:
                pass
        if target_type is bool:
            return value_str.lower() in ("true", "1", "yes")
        return value_str
