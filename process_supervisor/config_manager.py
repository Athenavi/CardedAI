#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进程监督器配置管理
支持 JSON/YAML 配置文件加载和热更新
"""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, Optional, List

from src.unified_logger import default_logger as logger


@dataclass
class HealthCheckConfig:
    """健康检查配置"""
    endpoint: str = ""
    interval: int = 30  # 秒
    timeout: int = 5  # 秒
    retries: int = 3


@dataclass
class ProcessLogConfig:
    """日志配置"""
    stdout: str = ""
    stderr: str = ""
    max_size: str = "10MB"
    backup_count: int = 5


@dataclass
class ProcessConfig:
    """进程配置数据类"""
    name: str
    command: List[str]
    working_dir: str = "."
    autostart: bool = True
    autorestart: bool = True
    restart_limit: int = 3
    restart_delay: int = 5
    restart_backoff_multiplier: float = 1.5  # 指数退避乘数
    max_restart_delay: int = 60  # 最大重启延迟（秒）
    stdout_logfile: Optional[str] = None
    stderr_logfile: Optional[str] = None
    environment: Dict[str, str] = field(default_factory=dict)
    health_check: HealthCheckConfig = field(default_factory=HealthCheckConfig)
    logs: ProcessLogConfig = field(default_factory=ProcessLogConfig)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessConfig':
        """从字典创建"""
        health_check_data = data.pop('health_check', {})
        logs_data = data.pop('logs', {})

        return cls(
            name=data.get('name', ''),
            command=data.get('command', []),
            working_dir=data.get('working_dir', '.'),
            autostart=data.get('autostart', True),
            autorestart=data.get('autorestart', True),
            restart_limit=data.get('restart_limit', 3),
            restart_delay=data.get('restart_delay', 5),
            restart_backoff_multiplier=data.get('restart_backoff_multiplier', 1.5),
            max_restart_delay=data.get('max_restart_delay', 60),
            stdout_logfile=data.get('stdout_logfile'),
            stderr_logfile=data.get('stderr_logfile'),
            environment=data.get('environment', {}),
            health_check=HealthCheckConfig(**health_check_data) if health_check_data else HealthCheckConfig(),
            logs=ProcessLogConfig(**logs_data) if logs_data else ProcessLogConfig()
        )


@dataclass
class SupervisorConfig:
    """监督器配置"""
    monitor_interval: int = 5
    log_level: str = "INFO"
    log_file: str = "logs/supervisor.log"
    pid_file: str = "logs/supervisor.pid"
    auto_update_config: bool = True
    graceful_shutdown_timeout: int = 10
    memory_limit_mb: int = 512

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SupervisorConfig':
        """从字典创建"""
        return cls(**data)


class ConfigManager:
    """配置管理器"""

    DEFAULT_CONFIG_FILE = "process_supervisor/supervisor_config.json"
    FALLBACK_CONFIG_FILE = "process_supervisor/config.yaml"

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self.process_configs: Dict[str, ProcessConfig] = {}
        self.supervisor_config: SupervisorConfig = SupervisorConfig()
        self.last_modified_time: float = 0

        # 加载配置
        self.load_configuration()

    def load_configuration(self) -> bool:
        """加载配置文件"""
        try:
            # 确定配置文件路径
            if self.config_file:
                config_path = Path(self.config_file)
            else:
                # 尝试默认路径
                config_path = Path(self.DEFAULT_CONFIG_FILE)
                if not config_path.exists():
                    yaml_path = Path(self.FALLBACK_CONFIG_FILE)
                    if yaml_path.exists():
                        config_path = yaml_path

            if not config_path.exists():
                logger.warning(f"配置文件不存在：{config_path}，使用默认配置")
                self._load_default_configs()
                return True

            # 根据文件扩展名选择加载方式
            if config_path.suffix in ['.json']:
                self._load_json_config(config_path)
            elif config_path.suffix in ['.yaml', '.yml']:
                self._load_yaml_config(config_path)
            else:
                logger.warning(f"不支持的配置文件格式：{config_path.suffix}，使用默认配置")
                self._load_default_configs()

            # 记录最后修改时间
            self.last_modified_time = config_path.stat().st_mtime
            logger.info(f"配置加载成功：{config_path}")
            return True

        except Exception as e:
            logger.error(f"加载配置文件失败：{e}，使用默认配置")
            self._load_default_configs()
            return False

    def _load_json_config(self, config_path: Path):
        """加载 JSON 配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # 解析进程配置
            processes_data = config_data.get('processes', {})
            for name, process_data in processes_data.items():
                process_data['name'] = name
                self.process_configs[name] = ProcessConfig.from_dict(process_data)

            # 解析监督器配置
            supervisor_data = config_data.get('supervisor', {})
            self.supervisor_config = SupervisorConfig.from_dict(supervisor_data)

            logger.info(f"成功加载 JSON 配置文件，共 {len(self.process_configs)} 个进程")

        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败：{e}")
            raise

    def _load_yaml_config(self, config_path: Path):
        """加载 YAML 配置文件"""
        try:
            import yaml

            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            # 解析进程配置
            processes_data = config_data.get('processes', {})
            for name, process_data in processes_data.items():
                process_data['name'] = name
                self.process_configs[name] = ProcessConfig.from_dict(process_data)

            # 解析监督器配置
            supervisor_data = config_data.get('supervisor', {})
            self.supervisor_config = SupervisorConfig.from_dict(supervisor_data)

            logger.info(f"成功加载 YAML 配置文件，共 {len(self.process_configs)} 个进程")

        except ImportError:
            logger.warning("PyYAML 未安装，无法加载 YAML 配置文件")
            self._load_default_configs()
        except Exception as e:
            logger.error(f"YAML 解析失败：{e}")
            raise

    def _load_default_configs(self):
        """加载默认配置"""
        import sys

        default_configs = [
            ProcessConfig(
                name="update_server",
                command=[sys.executable, "-m", "update_server.server"],
                working_dir=".",
                autostart=True,
                autorestart=True,
                restart_limit=3,
                restart_delay=5,
                stdout_logfile="logs/update_server.log",
                stderr_logfile="logs/update_server.err.log",
                health_check=HealthCheckConfig(
                    endpoint="http://127.0.0.1:8001/api/v1/health",
                    interval=60,
                    timeout=3,
                    retries=3
                )
            ),
            ProcessConfig(
                name="main_app",
                command=[sys.executable, "main.py", "--env", "prod"],
                working_dir=".",
                autostart=True,
                autorestart=True,
                restart_limit=3,
                restart_delay=10,
                stdout_logfile="logs/main_app.log",
                stderr_logfile="logs/main_app.err.log",
                health_check=HealthCheckConfig(
                    endpoint="http://127.0.0.1:9421/api/v2/health",
                    interval=30,
                    timeout=5,
                    retries=3
                )
            ),
            ProcessConfig(
                name="frontend_dev",
                command=["npm", "run", "dev"],
                working_dir="frontend-next",
                autostart=False,  # 仅开发环境启用
                autorestart=True,
                restart_limit=3,
                restart_delay=5,
                stdout_logfile="logs/frontend_dev.log",
                stderr_logfile="logs/frontend_dev.err.log",
                environment={"NODE_ENV": "development", "PORT": "3000"}
            )
        ]

        for config in default_configs:
            self.process_configs[config.name] = config

        logger.info(f"已加载 {len(self.process_configs)} 个默认进程配置")

    def check_config_changed(self) -> bool:
        """检查配置文件是否发生变化"""
        if not self.config_file:
            return False

        config_path = Path(self.config_file)
        if not config_path.exists():
            return False

        current_mtime = config_path.stat().st_mtime
        if current_mtime != self.last_modified_time:
            self.last_modified_time = current_mtime
            return True

        return False

    def reload_config(self) -> bool:
        """重新加载配置"""
        logger.info("重新加载配置文件...")
        old_configs = self.process_configs.copy()

        try:
            self.load_configuration()
            logger.info("配置重新加载成功")
            return True
        except Exception as e:
            logger.error(f"重新加载配置失败：{e}，回滚到旧配置")
            self.process_configs = old_configs
            return False

    def get_process_config(self, name: str) -> Optional[ProcessConfig]:
        """获取指定进程的配置"""
        return self.process_configs.get(name)

    def get_all_process_configs(self) -> Dict[str, ProcessConfig]:
        """获取所有进程配置"""
        return self.process_configs.copy()

    def add_process_config(self, config: ProcessConfig):
        """添加进程配置"""
        self.process_configs[config.name] = config
        logger.info(f"添加进程配置：{config.name}")

    def remove_process_config(self, name: str):
        """移除进程配置"""
        if name in self.process_configs:
            del self.process_configs[name]
            logger.info(f"移除进程配置：{name}")


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_file: Optional[str] = None) -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_file)
    return _config_manager


def reset_config_manager():
    """重置配置管理器（用于测试）"""
    global _config_manager
    _config_manager = None
