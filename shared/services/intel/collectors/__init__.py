"""
数据采集器模块

支持 RSS、网页、API、搜索引擎等多种数据源采集。
"""

from shared.services.intel.collectors.base import BaseCollector, CollectedItemData

__all__ = [
    "BaseCollector",
    "CollectedItemData",
]
