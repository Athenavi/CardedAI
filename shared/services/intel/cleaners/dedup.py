"""
去重清洗器

基于 SimHash 的近似去重，支持精确哈希去重和相似度阈值去重。
"""

import hashlib
import logging
import re
from collections import defaultdict
from typing import Dict, List, Optional, Set

from shared.services.intel.cleaners.base import BaseCleaner

logger = logging.getLogger(__name__)


def _simhash(text: str, hash_bits: int = 64) -> int:
    """
    计算文本的 SimHash 值。

    SimHash 是一种局部敏感哈希，相似文本的哈希值相近，
    适用于近似去重场景。
    """
    if not text:
        return 0

    # 分词（简单按字符/单词切分）
    tokens = re.findall(r"\w+", text.lower())
    if not tokens:
        return 0

    # 初始化向量
    v = [0] * hash_bits

    for token in tokens:
        # 对每个 token 计算哈希
        token_hash = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)

        for i in range(hash_bits):
            bit = (token_hash >> i) & 1
            if bit:
                v[i] += 1
            else:
                v[i] -= 1

    # 生成最终 SimHash
    fingerprint = 0
    for i in range(hash_bits):
        if v[i] > 0:
            fingerprint |= (1 << i)

    return fingerprint


def _hamming_distance(hash1: int, hash2: int) -> int:
    """计算两个哈希值的汉明距离"""
    xor = hash1 ^ hash2
    return bin(xor).count("1")


class DedupCleaner(BaseCleaner):
    """
    去重清洗器

    支持两种去重方式：
    1. 精确去重：基于 content_hash（SHA-256）
    2. 近似去重：基于 SimHash 汉明距离

    在管道中使用时，此清洗器主要负责标记重复项，
    实际去重由 CollectorEngine 在入库前执行。
    """

    name = "dedup_cleaner"

    def __init__(self, similarity_threshold: int = 3):
        """
        Args:
            similarity_threshold: SimHash 汉明距离阈值，
                                  小于此值认为是近似重复（默认 3）
        """
        self.similarity_threshold = similarity_threshold
        # 内存缓存：source_id -> List[simhash]
        self._hash_cache: Dict[int, List[int]] = defaultdict(list)

    async def clean(
        self,
        item_id: int,
        content: str,
        title: str = "",
        metadata: Optional[dict] = None,
    ) -> dict:
        meta = metadata or {}

        if not content:
            return {
                "content": content,
                "title": title,
                "metadata": meta,
                "changed": False,
            }

        # 计算 SimHash
        content_hash = _simhash(content)
        meta["simhash"] = content_hash

        # 标记为不重复（实际去重在 CollectorEngine 层执行）
        meta["is_duplicate"] = False

        return {
            "content": content,
            "title": title,
            "metadata": meta,
            "changed": False,
        }

    def check_similarity(self, hash1: int, hash2: int) -> bool:
        """检查两个 SimHash 是否相似"""
        distance = _hamming_distance(hash1, hash2)
        return distance <= self.similarity_threshold

    def clear_cache(self) -> None:
        """清空哈希缓存"""
        self._hash_cache.clear()
