"""
LLM 调用节点执行器

通过 LLM 客户端执行文本生成 / JSON 生成 / 对话补全。
支持 prompt 模板变量替换（从 inputs 中提取）。
"""

import json
from typing import Any, Dict

from src.unified_logger import default_logger as logger
from shared.services.workflow.node_executors.base import BaseNodeExecutor


class LLMNodeExecutor(BaseNodeExecutor):
    """LLM 调用节点"""

    @property
    def node_type(self) -> str:
        return "llm"

    async def execute(self, node: Dict, inputs: Dict) -> Dict:
        """
        执行 LLM 调用

        config 参数:
            prompt_template: str - prompt 模板，支持 {key} 占位符
            system_prompt: str - 系统 prompt（可选）
            mode: str - "text" | "json" | "chat"，默认 "text"
            temperature: float - 温度参数，默认 0.7
            max_tokens: int - 最大 token 数，默认 2000
        """
        from shared.services.ai.llm_client import llm_client

        if not llm_client.is_available:
            return {"success": False, "error": "LLM 客户端不可用"}

        prompt_template = self._get_config(node, "prompt_template", "")
        system_prompt = self._get_config(node, "system_prompt")
        mode = self._get_config(node, "mode", "text")
        temperature = self._get_config(node, "temperature", 0.7)
        max_tokens = self._get_config(node, "max_tokens", 2000)

        # 模板变量替换
        prompt = self._render_template(prompt_template, inputs)

        try:
            if mode == "json":
                result = await llm_client.generate_json(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                )
            else:
                result = await llm_client.generate_text(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

            return {
                "success": result.get("success", False),
                "output": result.get("content", ""),
                "mode": mode,
            }
        except Exception as exc:
            logger.error(f"[LLMNode] 执行失败: {exc}")
            return {"success": False, "error": str(exc)}

    @staticmethod
    def _render_template(template: str, inputs: Dict) -> str:
        """安全的模板变量替换，支持 {key} 占位符"""
        result = template
        for key, value in inputs.items():
            placeholder = "{" + key + "}"
            if placeholder in result:
                if isinstance(value, (dict, list)):
                    result = result.replace(placeholder, json.dumps(value, ensure_ascii=False))
                else:
                    result = result.replace(placeholder, str(value))
        return result
