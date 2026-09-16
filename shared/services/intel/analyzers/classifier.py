"""
内容分类器

调用 LLM 对文本进行分类。
"""

import logging
from typing import Any, Dict, List, Optional

from shared.services.ai.llm_client import llm_client

logger = logging.getLogger(__name__)


class ContentClassifier:
    """内容分类器"""

    # 默认分类体系
    DEFAULT_CATEGORIES = [
        "科技", "金融", "政策", "市场", "竞争情报",
        "产品", "人才", "风险", "行业动态", "其他",
    ]

    def __init__(self, categories: Optional[List[str]] = None):
        """
        Args:
            categories: 自定义分类列表（为空则使用默认分类）
        """
        self.categories = categories or self.DEFAULT_CATEGORIES

    async def classify(self, text: str) -> Dict[str, Any]:
        """
        对文本进行分类。

        Args:
            text: 待分类文本

        Returns:
            dict: {
                "category": str,         # 主分类
                "confidence": float,     # 置信度
                "tags": List[str],       # AI 提取的标签
                "method": "llm" | "fallback"
            }
        """
        if not text or not text.strip():
            return {
                "category": "其他",
                "confidence": 0.0,
                "tags": [],
                "method": "fallback",
            }

        if not llm_client.is_available:
            return {
                "category": "其他",
                "confidence": 0.0,
                "tags": [],
                "method": "fallback",
            }

        categories_str = "、".join(self.categories)
        truncated = text[:2000]

        try:
            result = await llm_client.generate_json(
                prompt=(
                    f"请将以下文本分类到以下类别之一：\n"
                    f"[{categories_str}]\n\n"
                    f"同时提取 3-5 个关键标签。\n\n"
                    f"返回 JSON 格式：\n"
                    f'{{"category": "分类名称", "confidence": 0.0-1.0, "tags": ["标签1", "标签2"]}}\n\n'
                    f"文本内容：\n{truncated}"
                ),
                system_prompt="你是一个专业的内容分类助手。请根据文本内容选择最合适的分类，并提取关键标签。",
                temperature=0.2,
            )

            if result.get("success") and isinstance(result.get("content"), dict):
                data = result["content"]
                category = data.get("category", "其他")
                # 校验分类是否在合法范围内
                if category not in self.categories:
                    category = "其他"

                return {
                    "category": category,
                    "confidence": float(data.get("confidence", 0.5)),
                    "tags": data.get("tags", []),
                    "method": "llm",
                }

            logger.warning(f"分类 LLM 响应异常: {result.get('error', 'unknown')}")

        except Exception as e:
            logger.error(f"分类异常: {e}")

        return {
            "category": "其他",
            "confidence": 0.0,
            "tags": [],
            "method": "fallback",
        }
