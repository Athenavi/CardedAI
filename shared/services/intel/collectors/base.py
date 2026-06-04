"""
采集器基类

定义所有采集器的统一接口，采用抽象基类模式（复用插件系统的设计模式）。
"""

import json
import hashlib
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CollectedItemData:
    """采集条目的数据传输对象（DTO），用于在采集器和引擎之间传递数据"""

    __slots__ = (
        "url", "title", "content_raw", "content_hash", "metadata",
    )

    def __init__(
        self,
        url: str,
        title: str = "",
        content_raw: str = "",
        content_hash: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.url = url
        self.title = title or ""
        self.content_raw = content_raw or ""
        self.content_hash = content_hash or self._compute_hash(content_raw)
        self.metadata = metadata or {}

    @staticmethod
    def _compute_hash(content: str) -> str:
        """计算内容哈希（SHA-256）"""
        if not content:
            return ""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "content_raw": self.content_raw,
            "content_hash": self.content_hash,
            "metadata": self.metadata,
        }


class BaseCollector(ABC):
    """
    采集器基类

    所有数据源采集器必须继承此类并实现 collect() 和 validate_config() 方法。
    """

    # 子类应覆盖此属性，对应 DataSource.source_type
    source_type: str = ""

    @abstractmethod
    async def collect(self, source_config: Dict[str, Any], url: str) -> List[CollectedItemData]:
        """
        执行采集，返回原始数据条目列表。

        Args:
            source_config: 数据源的 config JSON 解析后的字典（选择器、认证信息等）
            url: 数据源的 URL

        Returns:
            List[CollectedItemData]: 采集到的条目列表
        """
        ...

    @abstractmethod
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        验证采集配置是否合法。

        Args:
            config: 采集配置字典

        Returns:
            bool: 配置是否合法
        """
        ...

    def _build_item(self, url: str, title: str, content: str, **extra_meta) -> CollectedItemData:
        """辅助方法：构建 CollectedItemData"""
        metadata = {k: v for k, v in extra_meta.items() if v is not None}
        return CollectedItemData(
            url=url,
            title=title,
            content_raw=content,
            metadata=metadata,
        )
