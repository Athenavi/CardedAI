"""
情感分析器

调用 LLM 对文本进行情感倾向分析。
"""

import json
import logging
from typing import Any, Dict, Optional

from shared.services.ai.llm_client import llm_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个专业的情感分析助手。请分析以下文本的情感倾向。

返回 JSON 格式：
{
    "sentiment": "positive" | "negative" | "neutral",
    "confidence": 0.0-1.0,
    "reason": "简短的理由"
}

只返回 JSON，不要添加其他内容。"""


class SentimentAnalyzer:
    """情感分析器（调用 LLM）"""

    def __init__(self, fallback_sentiment: str = "neutral"):
        """
        Args:
            fallback_sentiment: LLM 不可用时的默认情感值
        """
        self.fallback_sentiment = fallback_sentiment

    async def analyze(self, text: str) -> Dict[str, Any]:
        """
        分析文本情感。

        Args:
            text: 待分析文本

        Returns:
            dict: {
                "sentiment": "positive" | "negative" | "neutral",
                "confidence": float,
                "reason": str,
                "method": "llm" | "fallback"
            }
        """
        if not text or not text.strip():
            return {
                "sentiment": self.fallback_sentiment,
                "confidence": 0.0,
                "reason": "空文本",
                "method": "fallback",
            }

        if not llm_client.is_available:
            return {
                "sentiment": self.fallback_sentiment,
                "confidence": 0.0,
                "reason": "LLM 服务不可用",
                "method": "fallback",
            }

        # 截断到合理长度
        truncated = text[:1500]

        try:
            result = await llm_client.generate_json(
                prompt=f"请分析以下文本的情感倾向：\n\n{truncated}",
                system_prompt=SYSTEM_PROMPT,
                temperature=0.2,
            )

            if result.get("success") and isinstance(result.get("content"), dict):
                data = result["content"]
                sentiment = data.get("sentiment", self.fallback_sentiment)
                # 校验合法值
                if sentiment not in ("positive", "negative", "neutral"):
                    sentiment = self.fallback_sentiment

                return {
                    "sentiment": sentiment,
                    "confidence": float(data.get("confidence", 0.5)),
                    "reason": data.get("reason", ""),
                    "method": "llm",
                }

            logger.warning(f"情感分析 LLM 响应异常: {result.get('error', 'unknown')}")

        except Exception as e:
            logger.error(f"情感分析异常: {e}")

        return {
            "sentiment": self.fallback_sentiment,
            "confidence": 0.0,
            "reason": "分析失败",
            "method": "fallback",
        }
