"""垃圾评论过滤管理器"""
from .service import SpamFilterService, spam_filter
from .strategies import SpamStrategy, RateLimitStrategy

__all__ = ['SpamFilterService', 'spam_filter', 'SpamStrategy', 'RateLimitStrategy']
