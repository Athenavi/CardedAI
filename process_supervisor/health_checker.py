#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康检查模块
提供三层健康检查机制：进程存活、端口监听、HTTP 端点
"""


import socket
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logging.warning("requests 库未安装，HTTP 健康检查将不可用")

from src.unified_logger import default_logger as logger


class HealthStatus(Enum):
    """健康状态"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    TIMEOUT = "timeout"


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    status: HealthStatus
    message: str = ""
    response_time: float = 0.0  # 毫秒
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = time.time()


class HealthChecker:
    """健康检查器"""
    
    def __init__(self, process_name: str):
        self.process_name = process_name
        self.last_check_time: float = 0
        self.consecutive_failures: int = 0
        self.last_result: Optional[HealthCheckResult] = None
    
    def check_process_alive(self, pid: Optional[int]) -> HealthCheckResult:
        """
        Layer 1: 检查进程是否存活
        
        Args:
            pid: 进程 ID
            
        Returns:
            健康检查结果
        """
        if pid is None:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message="进程 PID 为空"
            )
        
        try:
            import psutil
            try:
                process = psutil.Process(pid)
                is_running = process.is_running()
                
                if is_running:
                    return HealthCheckResult(
                        status=HealthStatus.HEALTHY,
                        message=f"进程 {self.process_name} (PID: {pid}) 正在运行"
                    )
                else:
                    return HealthCheckResult(
                        status=HealthStatus.UNHEALTHY,
                        message=f"进程 {self.process_name} (PID: {pid}) 已退出"
                    )
            except psutil.NoSuchProcess:
                return HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    message=f"进程 {self.process_name} (PID: {pid}) 不存在"
                )
        except ImportError:
            # 如果没有 psutil，使用基础检查
            import os
            try:
                os.kill(pid, 0)  # 信号 0 不发送任何信号，只检查进程是否存在
                return HealthCheckResult(
                    status=HealthStatus.HEALTHY,
                    message=f"进程 {self.process_name} (PID: {pid}) 存在"
                )
            except OSError:
                return HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    message=f"进程 {self.process_name} (PID: {pid}) 不存在"
                )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                message=f"检查进程状态失败：{e}"
            )
    
    def check_port_listening(self, host: str, port: int, timeout: int = 3) -> HealthCheckResult:
        """
        Layer 2: 检查端口是否在监听
        
        Args:
            host: 主机地址
            port: 端口号
            timeout: 超时时间（秒）
            
        Returns:
            健康检查结果
        """
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            result = sock.connect_ex((host, port))
            elapsed_ms = (time.time() - start_time) * 1000
            
            sock.close()
            
            if result == 0:
                return HealthCheckResult(
                    status=HealthStatus.HEALTHY,
                    message=f"端口 {host}:{port} 正在监听",
                    response_time=elapsed_ms
                )
            else:
                return HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    message=f"端口 {host}:{port} 无法连接 (错误码：{result})",
                    response_time=elapsed_ms
                )
                
        except socket.timeout:
            return HealthCheckResult(
                status=HealthStatus.TIMEOUT,
                message=f"连接 {host}:{port} 超时",
                response_time=timeout * 1000
            )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                message=f"检查端口失败：{e}"
            )
    
    def check_health_endpoint(self, url: str, timeout: int = 5) -> HealthCheckResult:
        """
        Layer 3: HTTP 健康端点检查
        
        Args:
            url: 健康检查 URL
            timeout: 超时时间（秒）
            
        Returns:
            健康检查结果
        """
        if not REQUESTS_AVAILABLE:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                message="requests 库未安装，无法进行 HTTP 检查"
            )
        
        try:
            start_time = time.time()
            response = requests.get(url, timeout=timeout)
            elapsed_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return HealthCheckResult(
                    status=HealthStatus.HEALTHY,
                    message=f"健康端点响应正常 (状态码：{response.status_code})",
                    response_time=elapsed_ms
                )
            elif response.status_code >= 500:
                return HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    message=f"健康端点返回服务器错误 (状态码：{response.status_code})",
                    response_time=elapsed_ms
                )
            else:
                return HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    message=f"健康端点返回异常状态码：{response.status_code}",
                    response_time=elapsed_ms
                )
                
        except requests.exceptions.Timeout:
            return HealthCheckResult(
                status=HealthStatus.TIMEOUT,
                message=f"HTTP 请求超时 ({timeout}秒)"
            )
        except requests.exceptions.ConnectionError as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message=f"无法连接到健康端点：{e}"
            )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                message=f"HTTP 健康检查失败：{e}"
            )
    
    def perform_full_check(self, 
                          pid: Optional[int],
                          host: Optional[str] = None,
                          port: Optional[int] = None,
                          health_endpoint: Optional[str] = None,
                          timeout: int = 5) -> Tuple[HealthStatus, list]:
        """
        执行完整的三层健康检查
        
        Args:
            pid: 进程 ID
            host: 主机地址（用于端口检查）
            port: 端口号（用于端口检查）
            health_endpoint: HTTP 健康端点 URL
            timeout: 超时时间
            
        Returns:
            (总体健康状态，各层检查结果列表)
        """
        results = []
        overall_status = HealthStatus.HEALTHY
        
        # Layer 1: 进程存活检查
        alive_result = self.check_process_alive(pid)
        results.append(alive_result)
        
        if alive_result.status != HealthStatus.HEALTHY:
            overall_status = alive_result.status
            logger.warning(f"[{self.process_name}] 进程存活检查失败：{alive_result.message}")
            # 如果进程都不存在，不需要继续检查
            return overall_status, results
        
        # Layer 2: 端口监听检查
        if host and port:
            port_result = self.check_port_listening(host, port, timeout)
            results.append(port_result)
            
            if port_result.status != HealthStatus.HEALTHY:
                overall_status = port_result.status
                logger.warning(f"[{self.process_name}] 端口监听检查失败：{port_result.message}")
        
        # Layer 3: HTTP 端点检查
        if health_endpoint:
            endpoint_result = self.check_health_endpoint(health_endpoint, timeout)
            results.append(endpoint_result)
            
            if endpoint_result.status != HealthStatus.HEALTHY:
                overall_status = endpoint_result.status
                logger.warning(f"[{self.process_name}] HTTP 端点检查失败：{endpoint_result.message}")
        
        # 更新检查记录
        self.last_check_time = time.time()
        self.last_result = results[-1] if results else None
        
        if overall_status == HealthStatus.HEALTHY:
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1
        
        return overall_status, results
    
    def get_failure_count(self) -> int:
        """获取连续失败次数"""
        return self.consecutive_failures
    
    def reset_failure_count(self):
        """重置连续失败计数"""
        self.consecutive_failures = 0


class HealthMonitor:
    """健康监控器 - 管理多个进程的健康检查"""
    
    def __init__(self):
        self.checkers: dict[str, HealthChecker] = {}
    
    def add_checker(self, process_name: str) -> HealthChecker:
        """为指定进程添加健康检查器"""
        if process_name not in self.checkers:
            self.checkers[process_name] = HealthChecker(process_name)
            logger.info(f"为进程 {process_name} 创建健康检查器")
        return self.checkers[process_name]
    
    def remove_checker(self, process_name: str):
        """移除进程的健康检查器"""
        if process_name in self.checkers:
            del self.checkers[process_name]
            logger.info(f"移除进程 {process_name} 的健康检查器")
    
    def get_checker(self, process_name: str) -> Optional[HealthChecker]:
        """获取进程的健康检查器"""
        return self.checkers.get(process_name)
    
    def perform_all_checks(self, process_info: dict) -> dict:
        """
        执行所有进程的健康检查
        
        Args:
            process_info: 进程信息字典 {name: {pid, host, port, health_endpoint}}
            
        Returns:
            检查结果字典 {name: (status, results)}
        """
        results = {}
        
        for name, info in process_info.items():
            checker = self.get_checker(name)
            if not checker:
                checker = self.add_checker(name)
            
            status, check_results = checker.perform_full_check(
                pid=info.get('pid'),
                host=info.get('host'),
                port=info.get('port'),
                health_endpoint=info.get('health_endpoint')
            )
            
            results[name] = (status, check_results)
        
        return results


# 全局健康监控实例
_health_monitor: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    """获取全局健康监控实例"""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    return _health_monitor
