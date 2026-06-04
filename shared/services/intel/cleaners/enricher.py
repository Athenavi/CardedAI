"""
数据富化清洗器

提取实体（人名、组织、地点）、补充元数据、自动打标签。
"""

import logging
import re
from typing import Dict, List, Optional

from shared.services.intel.cleaners.base import BaseCleaner

logger = logging.getLogger(__name__)

# 中文常见实体后缀
_ORG_SUFFIXES = [
    "公司", "集团", "有限公司", "股份", "研究院", "研究所", "大学",
    "学院", "银行", "基金", "协会", "委员会", "局", "部", "厅",
    "司", "处", "中心", "研究院", "实验室", "联盟",
]

# 简单的关键词提取正则（中文 + 英文）
_KEYWORD_RE = re.compile(r"[\u4e00-\u9fff]{2,8}|[a-zA-Z]{3,}")


class EnricherCleaner(BaseCleaner):
    """
    数据富化清洗器

    功能：
    1. 提取实体（基于规则，可选 LLM 增强）
    2. 提取关键词
    3. 语言检测
    4. 补充元数据
    """

    name = "enricher_cleaner"

    def __init__(self, use_llm: bool = False):
        """
        Args:
            use_llm: 是否使用 LLM 进行实体提取（需要 LLM 服务可用）
        """
        self.use_llm = use_llm

    async def clean(
        self,
        item_id: int,
        content: str,
        title: str = "",
        metadata: Optional[dict] = None,
    ) -> dict:
        meta = metadata or {}
        changed = False

        if not content:
            return {
                "content": content,
                "title": title,
                "metadata": meta,
                "changed": False,
            }

        # 1. 提取关键词
        if "keywords" not in meta:
            keywords = self._extract_keywords(content)
            if keywords:
                meta["keywords"] = keywords
                changed = True

        # 2. 语言检测
        if "language" not in meta:
            lang = self._detect_language(content)
            if lang:
                meta["language"] = lang
                changed = True

        # 3. 实体提取
        if "entities" not in meta:
            entities = self._extract_entities(content)
            if entities:
                meta["entities"] = entities
                changed = True

        # 4. LLM 增强（可选）
        if self.use_llm and "entities_llm" not in meta:
            llm_entities = await self._llm_extract_entities(content)
            if llm_entities:
                meta["entities_llm"] = llm_entities
                changed = True

        # 5. 内容长度统计
        meta["char_count"] = len(content)
        meta["word_count"] = len(re.findall(r"\w+", content))

        return {
            "content": content,
            "title": title,
            "metadata": meta,
            "changed": changed,
        }

    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """基于 TF 的关键词提取（简化版）"""
        words = _KEYWORD_RE.findall(text.lower())
        if not words:
            return []

        # 计算词频
        freq: Dict[str, int] = {}
        for w in words:
            # 过滤停用词（简化版）
            if len(w) < 2 or w in {"的", "了", "在", "是", "和", "有", "为", "与", "对", "等",
                                     "the", "and", "for", "that", "this", "with", "from", "are"}:
                continue
            freq[w] = freq.get(w, 0) + 1

        # 按频率排序取 Top N
        sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [w for w, _ in sorted_words[:max_keywords]]

    def _detect_language(self, text: str) -> str:
        """简单的语言检测"""
        # 统计中文字符比例
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        total_chars = len(text.strip())

        if total_chars == 0:
            return "unknown"

        ratio = chinese_chars / total_chars

        if ratio > 0.3:
            return "zh"
        elif ratio > 0.05:
            return "mixed"
        else:
            return "en"

    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """基于规则的实体提取（简化版）"""
        entities: Dict[str, List[str]] = {
            "organizations": [],
            "urls": [],
            "emails": [],
        }

        # 提取组织名称（简化：查找包含组织后缀的短语）
        for suffix in _ORG_SUFFIXES:
            pattern = re.compile(r"[\u4e00-\u9fff]{2,20}" + re.escape(suffix))
            for match in pattern.finditer(text):
                org = match.group()
                if org not in entities["organizations"]:
                    entities["organizations"].append(org)

        # 提取 URL
        url_pattern = re.compile(r"https?://[^\s<>\"']+")
        entities["urls"] = list(set(url_pattern.findall(text)))

        # 提取邮箱
        email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
        entities["emails"] = list(set(email_pattern.findall(text)))

        # 清除空列表
        entities = {k: v for k, v in entities.items() if v}

        return entities

    async def _llm_extract_entities(self, text: str) -> Optional[Dict]:
        """使用 LLM 进行高级实体提取"""
        try:
            from shared.services.ai.llm_client import llm_client

            if not llm_client.is_available:
                return None

            # 截断到合理长度
            truncated = text[:2000]

            result = await llm_client.generate_json(
                prompt=f"从以下文本中提取关键实体（人名、组织、地点、产品、事件），以 JSON 格式返回：\n\n{truncated}",
                system_prompt="你是一个实体提取助手。请返回 JSON 格式，键为实体类型（persons/organizations/locations/products/events），值为实体名称数组。",
                temperature=0.2,
            )

            if result.get("success") and isinstance(result.get("content"), dict):
                return result["content"]

        except Exception as e:
            logger.warning(f"LLM 实体提取失败: {e}")

        return None
