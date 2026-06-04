"""
Widget管理器包
提供小部件注册、配置、渲染和缓存功能
"""

from shared.services.widgets.widget_manager.config import WIDGET_TYPES, WIDGET_AREAS
from shared.services.widgets.widget_manager.renderer import WidgetRenderer
from shared.services.widgets.widget_manager.service import WidgetService

# 全局实例
widget_service = WidgetService()

__all__ = [
    'WidgetService',
    'WidgetRenderer',
    'WIDGET_TYPES',
    'WIDGET_AREAS',
    'widget_service',
]
