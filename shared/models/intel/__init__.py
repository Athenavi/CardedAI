"""
intel 子模块 - 模型定义
由代码生成器自动生成 - 请勿手动修改
"""

# 导入所有 intel 模型，确保表注册到 Base.metadata
from shared.models.intel.data_source import DataSource
from shared.models.intel.collected_item import CollectedItem
from shared.models.intel.intelligence import Intelligence
from shared.models.intel.briefing import Briefing
from shared.models.intel.alert_rule import AlertRule
from shared.models.intel.alert_event import AlertEvent

__all__ = [
    'DataSource',
    'CollectedItem',
    'Intelligence',
    'Briefing',
    'AlertRule',
    'AlertEvent',
]
