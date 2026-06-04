"""
性能监控中间件

用于监控和优化应用性能，包括：
1. 请求响应时间跟踪
2. 慢查询检测
3. 内存使用监控
4. CPU使用率监控
5. 数据库查询优化建议
"""

import time
import psutil
import os
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class PerformanceMonitor:
    """
    性能监控器
    
    跟踪和记录应用性能指标
    """

    def __init__(self):
        self.request_times: Dict[str, float] = {}
        self.slow_requests: list = []
        self.slow_threshold = 1.0  # 慢请求阈值（秒）
        self.start_time = time.time()

    def record_request_start(self, request_id: str):
        """记录请求开始时间"""
        self.request_times[request_id] = time.time()

    def record_request_end(self, request_id: str, path: str, method: str, status_code: int) -> float:
        """
        记录请求结束时间并返回耗时
        
        Returns:
            请求耗时（秒）
        """
        start_time = self.request_times.pop(request_id, None)
        if start_time is None:
            return 0.0

        duration = time.time() - start_time

        # 记录慢请求
        if duration > self.slow_threshold:
            slow_request = {
                "path": path,
                "method": method,
                "status_code": status_code,
                "duration": duration,
                "timestamp": datetime.now().isoformat(),
            }
            self.slow_requests.append(slow_request)

            # 只保留最近100个慢请求
            if len(self.slow_requests) > 100:
                self.slow_requests = self.slow_requests[-100:]

        return duration

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()

        uptime = time.time() - self.start_time

        return {
            "uptime_seconds": round(uptime, 2),
            "memory": {
                "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
                "percent": process.memory_percent(),
            },
            "cpu": {
                "percent": process.cpu_percent(interval=0.1),
                "count": psutil.cpu_count(),
            },
            "slow_requests": {
                "count": len(self.slow_requests),
                "threshold_seconds": self.slow_threshold,
                "recent": self.slow_requests[-10:],  # 最近10个
            },
        }

    def get_startup_optimization_suggestions(self) -> Dict[str, Any]:
        """获取启动优化建议"""
        suggestions = []

        # 检查内存使用
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024

        if memory_mb > 500:
            suggestions.append({
                "type": "memory",
                "severity": "warning",
                "message": f"内存使用较高 ({memory_mb:.2f} MB)",
                "recommendation": "考虑启用懒加载非关键模块",
            })

        # 检查启动时间
        uptime = time.time() - self.start_time
        if uptime < 60:  # 刚启动
            suggestions.append({
                "type": "startup",
                "severity": "info",
                "message": "应用刚启动，性能数据可能不准确",
                "recommendation": "等待一段时间后再查看性能统计",
            })

        return {
            "suggestions": suggestions,
            "timestamp": datetime.now().isoformat(),
        }


# 全局性能监控实例
performance_monitor = PerformanceMonitor()


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    性能监控中间件
    
    自动监控所有请求的性能
    """

    async def dispatch(self, request: Request, call_next):
        # 生成请求ID
        import uuid
        request_id = str(uuid.uuid4())

        # 记录开始时间
        performance_monitor.record_request_start(request_id)

        # 处理请求
        response = await call_next(request)

        # 记录结束时间
        duration = performance_monitor.record_request_end(
            request_id,
            str(request.url.path),
            request.method,
            response.status_code,
        )

        # 添加性能头
        response.headers["X-Response-Time"] = f"{duration:.4f}s"

        # 如果是慢请求，记录日志
        if duration > performance_monitor.slow_threshold:
            print(f"[SLOW REQUEST] {request.method} {request.url.path} - {duration:.4f}s")

        return response


def get_performance_stats() -> Dict[str, Any]:
    """获取性能统计（供API调用）"""
    return performance_monitor.get_performance_stats()


def get_optimization_suggestions() -> Dict[str, Any]:
    """获取优化建议（供API调用）"""
    return performance_monitor.get_startup_optimization_suggestions()
