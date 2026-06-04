"""
内容摘要生成器

调用 LLM 生成文本摘要。
"""

import logging
from typing import Any, Dict, Optional

from shared.services.ai.llm_client import llm_client

logger = logging.getLogger(__name__)


class ContentSummarizer:
    """内容摘要生成器"""

    def __init__(self, default_max_length: int = 200):
        """
        Args:
            default_max_length: 默认摘要最大字数
        """
        self.default_max_length = default_max_length

    async def summarize(self, text: str, max_length: int = 0) -> Dict[str, Any]:
        """
        生成文本摘要。

        Args:
            text: 原始文本
            max_length: 摘要最大字数（0 使用默认值）

        Returns:
            dict: {
                "summary": str,
                "method": "llm" | "fallback",
                "success": bool
            }
        """
        if not text or not text.strip():
            return {"summary": "", "method": "fallback", "success": False}

        limit = max_length or self.default_max_length

        if not llm_client.is_available:
            # 简单截断作为 fallback
            summary = text[:limit]
            if len(text) > limit:
                summary += "..."
            return {"summary": summary, "method": "fallback", "success": True}

        # 截断到合理长度（给 LLM 更多上下文）
        truncated = text[:3000]

        try:
            result = await llm_client.generate_text(
                prompt=f"请对以下文本生成一段简洁的中文摘要，不超过 {limit} 字：\n\n{truncated}",
                system_prompt="你是一个专业的内容摘要助手。请生成简洁、准确的摘要，保留核心信息。",
                temperature=0.3,
                max_tokens=500,
            )

            if result.get("success") and result.get("content"):
                summary = result["content"].strip()
                return {"summary": summary, "method": "llm", "success": True}

            logger.warning(f"摘要生成 LLM 响应异常: {result.get('error', 'unknown')}")

        except Exception as e:
            logger.error(f"摘要生成异常: {e}")

        # fallback
        summary = text[:limit]
        if len(text) > limit:
            summary += "..."
        return {"summary": summary, "method": "fallback", "success": True}
