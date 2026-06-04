"""
清洗器基类

定义所有清洗器的统一接口。
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class BaseCleaner(ABC):
    """
    清洗器基类

    所有清洗器必须继承此类并实现 clean() 方法。
    清洗器按管道顺序依次执行，每个清洗器接收并返回同一条目数据。
    """

    # 子类应覆盖此属性，用于日志和调试
    name: str = "base"

    @abstractmethod
    async def clean(
        self,
        item_id: int,
        content: str,
        title: str = "",
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        清洗单条采集条目。

        Args:
            item_id: 采集条目 ID
            content: 原始/已清洗的内容
            title: 标题
            metadata: 元数据字典

        Returns:
            dict: {
                "content": str,         # 清洗后内容
                "title": str,           # 清洗后标题
                "metadata": dict,       # 更新后的元数据
                "changed": bool,        # 是否有变更
            }
        """
        ...
