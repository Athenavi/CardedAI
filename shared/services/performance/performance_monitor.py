"""简化的性能监控（个人站长轻量版）"""
import time
from collections import defaultdict
from typing import Any, Optional


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self, max_history: int = 100):
        self._page_loads: list[dict] = []
        self._db_queries: list[dict] = []
        self._api_responses: list[dict] = []
        self._max_history = max_history

    def record_page_load(self, url: str, load_time: float, **kwargs) -> None:
        self._page_loads.append({'url': url, 'load_time': load_time, 'time': time.time()})
        if len(self._page_loads) > self._max_history:
            self._page_loads.pop(0)

    def record_db_query(self, query_type: str, duration: float, **kwargs) -> None:
        self._db_queries.append({
            'type': query_type, 'duration': duration, 'time': time.time(), **kwargs
        })
        if len(self._db_queries) > self._max_history:
            self._db_queries.pop(0)

    def record_api_response(self, endpoint: str, method: str, **kwargs) -> None:
        self._api_responses.append({
            'endpoint': endpoint, 'method': method, 'time': time.time(), **kwargs
        })
        if len(self._api_responses) > self._max_history:
            self._api_responses.pop(0)

    def get_server_metrics(self) -> dict:
        avg_time = 0.0
        if self._page_loads:
            recent = self._page_loads[-100:]
            avg_time = sum(p['load_time'] for p in recent) / len(recent)
        return {
            'avg_response_time_ms': round(avg_time * 1000, 2),
            'total_requests': len(self._page_loads),
        }


# 全局单例
performance_monitor = PerformanceMonitor()
