"""简化的频率限制器（个人站长轻量版）"""
import time
from collections import defaultdict
from typing import Optional


class RateLimiter:
    """简单的内存频率限制器"""

    def __init__(self):
        self._windows: dict[str, list[float]] = defaultdict(list)

    async def check_rate_limit(self, key: str, max_requests: int = 60, window_seconds: int = 60) -> bool:
        """检查是否超过频率限制，True=允许通过"""
        now = time.time()
        window_start = now - window_seconds

        # 清理过期记录
        self._windows[key] = [t for t in self._windows[key] if t > window_start]

        if len(self._windows[key]) >= max_requests:
            return False

        self._windows[key].append(now)
        return True

    async def get_remaining(self, key: str, max_requests: int = 60) -> int:
        """获取剩余可用请求数"""
        now = time.time()
        window_start = now - 60
        self._windows[key] = [t for t in self._windows[key] if t > window_start]
        return max(0, max_requests - len(self._windows[key]))


# 全局单例
rate_limiter = RateLimiter()
