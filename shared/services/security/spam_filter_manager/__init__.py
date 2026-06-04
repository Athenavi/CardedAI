"""
垃圾评论过滤器包
提供多维度垃圾评论检测功能
"""

from shared.services.security.spam_filter_manager.service import SpamFilterService
from shared.services.security.spam_filter_manager.strategies import (
    KeywordStrategy,
    LinkDensityStrategy,
    DuplicateStrategy,
    FrequencyStrategy,
    HoneypotStrategy,
    UserAgentStrategy
)

# 全局实例
spam_filter = SpamFilterService()

__all__ = [
    'SpamFilterService',
    'KeywordStrategy',
    'LinkDensityStrategy',
    'DuplicateStrategy',
    'FrequencyStrategy',
    'HoneypotStrategy',
    'UserAgentStrategy',
    'spam_filter',
]
