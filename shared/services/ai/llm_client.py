"""
通用 LLM 客户端

提供 OpenAI 兼容 API 的统一调用接口，支持多种 LLM 提供商

使用方式:
    from shared.services.ai.llm_client import llm_client

    response = await llm_client.chat_completion(
        messages=[{"role": "user", "content": "你好"}],
        system_prompt="你是一个有用的助手"
    )
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional

try:
    import httpx
except ImportError:
    httpx = None

logger = logging.getLogger(__name__)


class LLMClient:
    """通用 LLM 客户端，兼容 OpenAI API 格式"""

    def __init__(self):
        self.api_key = os.environ.get("LLM_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
        self.api_base = os.environ.get("LLM_API_BASE", os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1"))
        self.model = os.environ.get("LLM_MODEL", "gpt-3.5-turbo")
        self.max_tokens = int(os.environ.get("LLM_MAX_TOKENS", "2000"))
        self.temperature = float(os.environ.get("LLM_TEMPERATURE", "0.7"))
        self._available: Optional[bool] = None

    @property
    def is_available(self) -> bool:
        """检查 LLM 服务是否可用"""
        if self._available is not None:
            return self._available
        self._available = bool(self.api_key and httpx)
        return self._available

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        temperature: float = None,
        max_tokens: int = None,
        response_format: str = None,
    ) -> Dict[str, Any]:
        """
        调用 Chat Completion API

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大 token 数
            response_format: 响应格式 ("json_object" 等)

        Returns:
            {"success": True, "content": "...", "usage": {...}} 或 {"success": False, "error": "..."}
        """
        if not self.is_available:
            return {"success": False, "error": "LLM service not available (no API key or httpx not installed)"}

        try:
            full_messages = []
            if system_prompt:
                full_messages.append({"role": "system", "content": system_prompt})
            full_messages.extend(messages)

            payload = {
                "model": self.model,
                "messages": full_messages,
                "temperature": temperature or self.temperature,
                "max_tokens": max_tokens or self.max_tokens,
            }
            if response_format:
                payload["response_format"] = {"type": response_format}

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    usage = data.get("usage", {})
                    return {
                        "success": True,
                        "content": content.strip(),
                        "usage": usage,
                        "model": data.get("model", self.model),
                    }
                else:
                    error_text = response.text[:500]
                    return {"success": False, "error": f"LLM API error ({response.status_code}): {error_text}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = None,
        max_tokens: int = None,
    ) -> Dict[str, Any]:
        """
        简化的文本生成接口

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            {"success": True, "content": "..."} 或 {"success": False, "error": "..."}
        """
        return await self.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        """
        生成 JSON 格式的响应

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            temperature: 温度参数（较低以获得更确定的输出）

        Returns:
            {"success": True, "content": {...}} 或 {"success": False, "error": "..."}
        """
        json_prompt = f"{prompt}\n\n请以 JSON 格式返回结果。"
        result = await self.chat_completion(
            messages=[{"role": "user", "content": json_prompt}],
            system_prompt=system_prompt or "你是一个有用的助手。请始终以有效的 JSON 格式回复。",
            temperature=temperature,
            response_format="json_object",
        )

        if result.get("success"):
            try:
                content = result["content"]
                # 尝试从 markdown code block 中提取 JSON
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0].strip()
                else:
                    json_str = content
                result["content"] = json.loads(json_str)
            except (json.JSONDecodeError, IndexError):
                # 如果无法解析为 JSON，保留原始文本
                pass

        return result


# 全局实例
llm_client = LLMClient()
