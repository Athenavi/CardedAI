"""简化的垃圾评论过滤服务（个人站长轻量版）"""
from typing import Any, Optional

from .strategies import SpamStrategy


class SpamFilterService:
    """垃圾评论过滤服务"""

    def __init__(self):
        self._blacklist: set[str] = set()
        self._whitelist: set[str] = set()
        self._stats = {'checked': 0, 'flagged': 0, 'blocked': 0}

    def check_spam(self, content: str, ip: Optional[str] = None,
                   author_name: Optional[str] = None, author_email: Optional[str] = None) -> dict[str, Any]:
        """检查是否为垃圾评论"""
        self._stats['checked'] += 1

        # IP黑名单检查
        if ip and ip in self._blacklist:
            self._stats['blocked'] += 1
            return {'is_spam': True, 'reason': 'IP在黑名单中', 'score': 1.0}

        # IP白名单跳过检查
        if ip and ip in self._whitelist:
            return {'is_spam': False, 'reason': None, 'score': 0.0}

        # 内容检查
        is_spam, reason = SpamStrategy.check_content(content)
        if is_spam:
            self._stats['flagged'] += 1
            return {'is_spam': True, 'reason': reason, 'score': 0.8}

        return {'is_spam': False, 'reason': None, 'score': 0.0}

    def get_stats(self) -> dict[str, int]:
        """获取过滤统计"""
        return dict(self._stats)

    def add_ip_to_blacklist(self, ip: str) -> None:
        self._blacklist.add(ip)

    def remove_ip_from_blacklist(self, ip: str) -> None:
        self._blacklist.discard(ip)

    def add_ip_to_whitelist(self, ip: str) -> None:
        self._whitelist.add(ip)

    def remove_ip_from_whitelist(self, ip: str) -> None:
        self._whitelist.discard(ip)

    def update_config(self, config: dict) -> bool:
        return True


# 全局单例
spam_filter = SpamFilterService()
