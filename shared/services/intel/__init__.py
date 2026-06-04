"""
情报引擎服务模块

提供数据采集、清洗、分析、简报生成等功能。
"""

from shared.services.intel.collector_engine import CollectorEngine, collector_engine, setup_default_collectors

__all__ = [
    "CollectorEngine",
    "collector_engine",
    "setup_default_collectors",
]
