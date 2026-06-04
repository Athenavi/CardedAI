#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进程管理器（增强版）
负责启动、监控和管理所有子进程
功能：配置加载、健康检查、智能重启、详细日志
"""


import os
import subprocess
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any

from src.unified_logger import default_logger as logger
from .config_manager import ProcessConfig, get_config_manager
from .health_checker import (
    HealthChecker, HealthStatus
)


class ProcessStatus(Enum):
    """进程状态枚举"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"
    RESTARTING = "restarting"


@dataclass
class ProcessConfig:
    """进程配置"""
    name: str
    command: List[str]
    working_dir: str = "."
    autostart: bool = True
    autorestart: bool = True
    restart_limit: int = 3
    restart_delay: int = 5  # 秒
    stdout_logfile: Optional[str] = None
    stderr_logfile: Optional[str] = None
    environment: Dict[str, str] = None


class ManagedProcess:
    """被管理的进程（增强版）"""

    def __init__(self, config: ProcessConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.status = ProcessStatus.STOPPED
        self.restart_count = 0
        self.last_start_time = 0
        self.stdout_log = None
        self.stderr_log = None
        self.health_checker: Optional[HealthChecker] = None
        self.last_restart_delay = config.restart_delay  # 当前重启延迟（支持指数退避）
        
        # 初始化健康检查器
        self.health_checker = HealthChecker(config.name)

    def start(self) -> bool:
        """启动进程（增强版：带详细日志和健康检查）"""
        if self.status in [ProcessStatus.RUNNING, ProcessStatus.STARTING]:
            logger.warning(f"[{self.config.name}] 进程已在运行，PID: {self.process.pid if self.process else 'N/A'}")
            return True
    
        try:
            logger.info(f"[{self.config.name}] === 正在启动进程 ===")
            logger.debug(f"[{self.config.name}] 命令：{' '.join(self.config.command)}")
            logger.debug(f"[{self.config.name}] 工作目录：{self.config.working_dir}")
            logger.debug(f"[{self.config.name}] 环境变量：{self.config.environment}")
                
            self.status = ProcessStatus.STARTING
            self.last_start_time = time.time()
    
            # 准备日志文件
            if self.config.stdout_logfile:
                log_dir = os.path.dirname(self.config.stdout_logfile)
                if log_dir and not os.path.exists(log_dir):
                    os.makedirs(log_dir, exist_ok=True)
                self.stdout_log = open(self.config.stdout_logfile, 'a', encoding='utf-8')
                logger.info(f"[{self.config.name}] 标准输出日志：{self.config.stdout_logfile}")
                    
            if self.config.stderr_logfile:
                log_dir = os.path.dirname(self.config.stderr_logfile)
                if log_dir and not os.path.exists(log_dir):
                    os.makedirs(log_dir, exist_ok=True)
                self.stderr_log = open(self.config.stderr_logfile, 'a', encoding='utf-8')
                logger.info(f"[{self.config.name}] 错误输出日志：{self.config.stderr_logfile}")
    
            # 设置环境变量
            env = os.environ.copy()
            if self.config.environment:
                env.update(self.config.environment)
                logger.debug(f"[{self.config.name}] 追加环境变量：{list(self.config.environment.keys())}")
    
            # 启动进程
            logger.info(f"[{self.config.name}] 执行启动命令...")
            self.process = subprocess.Popen(
                self.config.command,
                cwd=self.config.working_dir,
                stdout=self.stdout_log or subprocess.PIPE,
                stderr=self.stderr_log or subprocess.PIPE,
                env=env,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
    
            self.status = ProcessStatus.RUNNING
            self.restart_count = 0
            self.last_restart_delay = self.config.restart_delay  # 重置延迟

            logger.info(f"[{self.config.name}] [OK] 进程启动成功")
            logger.info(f"[{self.config.name}] PID: {self.process.pid}")
            logger.info(f"[{self.config.name}] 启动时间：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.last_start_time))}")
                
            # 等待短暂时间检查是否立即退出
            time.sleep(0.5)
            if self.process.poll() is not None:
                logger.error(f"[{self.config.name}] [ERROR] 进程启动后立即退出，返回码：{self.process.returncode}")
                self.status = ProcessStatus.FAILED
                return False
                
            return True
    
        except Exception as e:
            self.status = ProcessStatus.FAILED
            logger.error(f"[{self.config.name}] [ERROR] 启动进程失败：{e}", exc_info=True)
            return False

    def stop(self, timeout: int = 10) -> bool:
        """停止进程（增强版：带详细日志）"""
        if not self.process or self.status not in [ProcessStatus.RUNNING, ProcessStatus.STARTING]:
            logger.warning(f"[{self.config.name}] 进程未在运行状态，当前状态：{self.status.value}")
            return True
    
        try:
            logger.info(f"[{self.config.name}] === 正在停止进程 ===")
            logger.info(f"[{self.config.name}] 当前 PID: {self.process.pid}")
            logger.info(f"[{self.config.name}] 已运行时间：{int(time.time() - self.last_start_time)}秒")
                
            self.status = ProcessStatus.STOPPING
    
            # 发送终止信号
            if os.name == 'nt':
                # Windows 使用 taskkill
                logger.debug(f"[{self.config.name}] Windows 平台，使用 taskkill 终止进程")
                result = subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.process.pid)],
                               capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info(f"[{self.config.name}] taskkill 执行成功")
                else:
                    logger.warning(f"[{self.config.name}] taskkill 输出：{result.stderr}")
            else:
                # Unix/Linux 使用 SIGTERM
                logger.debug(f"[{self.config.name}] Unix 平台，使用 SIGTERM 终止进程")
                self.process.terminate()
                try:
                    self.process.wait(timeout=timeout)
                    logger.info(f"[{self.config.name}] 进程在 {timeout} 秒内正常退出")
                except subprocess.TimeoutExpired:
                    logger.warning(f"[{self.config.name}] 未在 {timeout} 秒内停止，强制终止")
                    self.process.kill()
                    self.process.wait()
                    logger.info(f"[{self.config.name}] 进程已被强制终止")
    
            # 清理资源
            if self.stdout_log:
                self.stdout_log.close()
                self.stdout_log = None
            if self.stderr_log:
                self.stderr_log.close()
                self.stderr_log = None
    
            self.process = None
            self.status = ProcessStatus.STOPPED

            logger.info(f"[{self.config.name}] [OK] 进程已完全停止")
            logger.info(f"[{self.config.name}] 总重启次数：{self.restart_count}")
            return True
    
        except Exception as e:
            logger.error(f"[{self.config.name}] [ERROR] 停止进程失败：{e}", exc_info=True)
            self.status = ProcessStatus.FAILED
            return False

    def is_running(self) -> bool:
        """检查进程是否正在运行（增强版：带状态同步）"""
        if not self.process:
            return False

        try:
            # 检查进程是否还在运行
            if self.process.poll() is None:
                return True
            else:
                # 进程已退出，同步状态
                exit_code = self.process.returncode
                logger.warning(f"[{self.config.name}] 进程已退出，返回码：{exit_code}")
                
                if exit_code == 0:
                    logger.info(f"[{self.config.name}] 进程正常退出")
                else:
                    logger.error(f"[{self.config.name}] 进程异常退出，返回码：{exit_code}")
                
                self.status = ProcessStatus.STOPPED
                return False
        except Exception as e:
            logger.error(f"[{self.config.name}] 检查进程状态失败：{e}")
            self.status = ProcessStatus.FAILED
            return False

    def perform_health_check(self) -> tuple[HealthStatus, list]:
        """执行健康检查（增强版：支持多种检查策略）"""
        if not self.health_checker:
            return HealthStatus.UNKNOWN, []
        
        pid = self.process.pid if self.process else None
        
        # 从配置中获取健康检查参数
        health_endpoint = self.config.health_check.endpoint if self.config.health_check else None
        timeout = self.config.health_check.timeout if self.config.health_check else 5

        # 智能提取端口和主机
        host = "127.0.0.1"
        port = None

        # 从命令中提取端口
        for i, cmd in enumerate(self.config.command):
            # 检查是否为端口号
            if cmd.isdigit() and 1000 <= int(cmd) <= 65535:
                port = int(cmd)
                break
            # 检查是否包含端口地址 (如 127.0.0.1:8000)
            if ':' in cmd and cmd.replace(':', '').replace('.', '').isdigit():
                parts = cmd.split(':')
                if len(parts) == 2 and parts[1].isdigit():
                    port = int(parts[1])
                    host = parts[0]
                    break

        # 如果有健康端点，优先使用端点检查
        if health_endpoint:
            logger.debug(f"[{self.config.name}] 执行 HTTP 健康检查：{health_endpoint}")
        elif port:
            logger.debug(f"[{self.config.name}] 执行端口健康检查：{host}:{port}")
        else:
            logger.debug(f"[{self.config.name}] 仅执行进程存活检查 (PID: {pid})")
        
        return self.health_checker.perform_full_check(
            pid=pid,
            host=host,
            port=port,
            health_endpoint=health_endpoint,
            timeout=timeout
        )
    
    def calculate_next_restart_delay(self) -> int:
        """计算下次重启延迟（指数退避）"""
        # 指数退避：delay = base_delay * (multiplier ^ restart_count)
        exponential_delay = self.config.restart_delay * (self.config.restart_backoff_multiplier ** self.restart_count)
        
        # 限制最大延迟
        next_delay = min(exponential_delay, self.config.max_restart_delay)
        
        return int(next_delay)
    
    def should_restart(self) -> tuple[bool, str]:
        """判断是否应该重启"""
        if not self.config.autorestart:
            return False, "自动重启已禁用"
        
        if self.restart_count >= self.config.restart_limit:
            return False, f"已达到最大重启次数限制 ({self.restart_count}/{self.config.restart_limit})"
        
        # 检查连续健康检查失败次数
        if self.health_checker and self.health_checker.consecutive_failures >= 5:
            return False, f"健康检查连续失败 {self.health_checker.consecutive_failures} 次"
        
        return True, "满足重启条件"

    def get_status_info(self) -> Dict[str, Any]:
        """获取进程状态信息（增强版）"""
        import psutil

        # 动态更新进程状态
        if self.process and self.status == ProcessStatus.RUNNING:
            # 检查进程是否还在运行
            if self.process.poll() is not None:
                # 进程已退出
                logger.warning(
                    f"[{self.config.name}] 检测到进程已退出 (poll={self.process.poll()}, returncode={self.process.returncode})")
                self.status = ProcessStatus.STOPPED
        
        info = {
            'name': self.config.name,
            'status': self.status.value,
            'pid': self.process.pid if self.process else None,
            'restart_count': self.restart_count,
            'uptime': time.time() - self.last_start_time if self.last_start_time else 0,
            'uptime_formatted': self._format_uptime(time.time() - self.last_start_time) if self.last_start_time else '0s',
            'last_restart_delay': self.last_restart_delay,
            'health_check_failures': self.health_checker.consecutive_failures if self.health_checker else 0,
        }
        
        # 添加资源使用信息
        if self.process and self.process.pid and self.status == ProcessStatus.RUNNING:
            try:
                p = psutil.Process(self.process.pid)
                info['cpu_percent'] = p.cpu_percent(interval=0.1)
                info['memory_mb'] = round(p.memory_info().rss / 1024 / 1024, 2)
                info['memory_percent'] = round(p.memory_percent(), 2)
            except (psutil.NoSuchProcess, Exception) as e:
                info['resource_error'] = str(e)
        
        return info
    
    def _format_uptime(self, seconds: float) -> str:
        """格式化运行时间"""
        hours, remainder = divmod(int(seconds), 3600)
        minutes, secs = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"


class ProcessSupervisor:
    """进程监督器主类（增强版）"""

    def __init__(self, config_file: str = None):
        self.config_manager = get_config_manager(config_file)
        self.processes: Dict[str, ManagedProcess] = {}
        self.config_file = config_file
        self.running = False
        self.monitor_thread = None

        # 从配置管理器加载配置
        self._load_processes_from_config()

    def _load_processes_from_config(self):
        """从配置管理器加载进程配置"""
        configs = self.config_manager.get_all_process_configs()
        
        for name, config in configs.items():
            self.processes[name] = ManagedProcess(config)
        
        logger.info(f"从配置加载了 {len(self.processes)} 个进程")

    def start_all_processes(self) -> bool:
        """启动所有配置的进程"""
        logger.info("开始启动所有进程...")
        success = True

        for name, process in self.processes.items():
            if process.config.autostart:
                if not process.start():
                    success = False
                    logger.error(f"启动进程 {name} 失败")
                else:
                    time.sleep(1)  # 给进程启动时间

        return success

    def stop_all_processes(self):
        """停止所有进程"""
        logger.info("开始停止所有进程...")

        for name, process in self.processes.items():
            process.stop()

    def start_process(self, name: str) -> bool:
        """启动指定进程"""
        if name not in self.processes:
            logger.error(f"进程 {name} 不存在")
            return False

        return self.processes[name].start()

    def stop_process(self, name: str) -> bool:
        """停止指定进程"""
        if name not in self.processes:
            logger.error(f"进程 {name} 不存在")
            return False

        return self.processes[name].stop()

    def restart_process(self, name: str) -> bool:
        """重启指定进程"""
        if name not in self.processes:
            logger.error(f"进程 {name} 不存在")
            return False

        process = self.processes[name]
        process.stop()
        time.sleep(1)
        return process.start()

    def get_process_status(self, name: str) -> Optional[Dict[str, Any]]:
        """获取指定进程状态"""
        if name not in self.processes:
            return None
        return self.processes[name].get_status_info()

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有进程状态"""
        return {name: process.get_status_info() for name, process in self.processes.items()}

    def _monitor_processes(self):
        """监控进程运行状态（增强版：健康检查 + 智能重启 + 日志聚合）"""
        last_log_aggregation = 0
        log_aggregation_interval = 300  # 每 5 分钟聚合一次日志
        
        while self.running:
            try:
                current_time = int(time.time())
                
                for name, process in self.processes.items():
                    # 检查进程是否意外退出
                    if not process.is_running():
                        if process.status == ProcessStatus.RUNNING:
                            logger.warning(f"[{name}] 检测到进程意外退出")
                                
                            # 判断是否应该重启
                            should_restart, reason = process.should_restart()
                                
                            if should_restart:
                                process.restart_count += 1
                                delay = process.calculate_next_restart_delay()
                                    
                                logger.info(f"[{name}] 准备重启进程 (次数：{process.restart_count}/{process.config.restart_limit}, 延迟：{delay}秒)")
                                logger.info(f"[{name}] 重启原因：{reason}")
                                    
                                time.sleep(delay)
                                    
                                if process.start():
                                    logger.info(f"[{name}] [OK] 进程重启成功")
                                    # 重启成功后等待更长时间确保稳定
                                    time.sleep(5)
                                else:
                                    logger.error(f"[{name}] [ERROR] 进程重启失败")
                                    process.status = ProcessStatus.FAILED
                            else:
                                logger.error(f"[{name}] [SKIP] 不满足重启条件：{reason}")
                                process.status = ProcessStatus.FAILED
                        
                    # 定期健康检查（仅对运行中的进程）
                    elif process.status == ProcessStatus.RUNNING:
                        # 根据配置的检查间隔执行
                        check_interval = process.config.health_check.interval if process.config.health_check else 30
                        if current_time % check_interval < 5:  # 在间隔的前 5 秒内执行
                            status, results = process.perform_health_check()

                            if status != HealthStatus.HEALTHY:
                                logger.warning(f"[{name}] 健康检查失败：{status.value}")
                                for result in results:
                                    logger.debug(f"[{name}] {result.status.value}: {result.message}")

                                # 连续健康检查失败过多，考虑重启
                                if process.health_checker.consecutive_failures >= 3:
                                    logger.warning(
                                        f"[{name}] 健康检查连续失败 {process.health_checker.consecutive_failures} 次，考虑重启")
                                    process.status = ProcessStatus.RESTARTING
                            else:
                                logger.debug(f"[{name}] 健康检查通过")

                # 定期日志聚合
                if current_time - last_log_aggregation >= log_aggregation_interval:
                    self._aggregate_logs()
                    last_log_aggregation = current_time
    
                time.sleep(5)  # 每 5 秒检查一次
    
            except Exception as e:
                logger.error(f"进程监控出错：{e}", exc_info=True)
                time.sleep(10)

    def start_monitoring(self):
        """启动监控线程"""
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_processes, daemon=True)
            self.monitor_thread.start()
            logger.info("进程监控已启动")

    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("进程监控已停止")

    def shutdown(self):
        """关闭监督器"""
        logger.info("正在关闭进程监督器...")
        self.stop_monitoring()
        self.stop_all_processes()
        logger.info("进程监督器已关闭")

    def _aggregate_logs(self):
        """聚合所有进程的日志文件"""
        try:
            aggregated_log = "logs/aggregated_system.log"
            log_dir = os.path.dirname(aggregated_log)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            logger.info(f"开始聚合日志到 {aggregated_log}")

            with open(aggregated_log, 'a', encoding='utf-8') as agg_file:
                agg_file.write(f"\n{'=' * 80}\n")
                agg_file.write(f"日志聚合时间：{time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                agg_file.write(f"{'=' * 80}\n\n")

                for name, process in self.processes.items():
                    agg_file.write(f"\n--- {name} 的日志 ---\n")

                    # 读取标准输出日志
                    if process.config.stdout_logfile and os.path.exists(process.config.stdout_logfile):
                        try:
                            with open(process.config.stdout_logfile, 'r', encoding='utf-8',
                                      errors='ignore') as stdout_f:
                                lines = stdout_f.readlines()[-50:]  # 只取最后 50 行
                                if lines:
                                    agg_file.write(f"[stdout] ({len(lines)} 行)\n")
                                    agg_file.writelines(lines)
                        except Exception as e:
                            logger.error(f"读取 {name} 标准输出日志失败：{e}")

                    # 读取错误日志
                    if process.config.stderr_logfile and os.path.exists(process.config.stderr_logfile):
                        try:
                            with open(process.config.stderr_logfile, 'r', encoding='utf-8',
                                      errors='ignore') as stderr_f:
                                lines = stderr_f.readlines()[-50:]  # 只取最后 50 行
                                if lines:
                                    agg_file.write(f"[stderr] ({len(lines)} 行)\n")
                                    agg_file.writelines(lines)
                        except Exception as e:
                            logger.error(f"读取 {name} 错误日志失败：{e}")

                    agg_file.write("\n")

            logger.info(f"日志聚合完成：{aggregated_log}")

        except Exception as e:
            logger.error(f"日志聚合失败：{e}")


# 全局监督器实例
_supervisor = None


def get_supervisor() -> ProcessSupervisor:
    """获取全局监督器实例"""
    global _supervisor
    if _supervisor is None:
        _supervisor = ProcessSupervisor()
    return _supervisor


def cleanup_supervisor():
    """清理全局监督器"""
    global _supervisor
    if _supervisor:
        _supervisor.shutdown()
        _supervisor = None
