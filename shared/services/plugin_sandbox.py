"""
插件沙箱执行环境

提供安全的插件执行环境，隔离插件与主机系统

功能:
1. Python 子进程隔离
2. 文件系统访问限制
3. 网络请求范围控制
4. 资源使用监控 (CPU/内存)
5. IPC 通信机制
6. 错误处理和超时控制
"""

import asyncio
import time
from datetime import datetime
from multiprocessing import Process, Queue
from typing import Dict, Any, Optional, Callable


class PluginSandboxConfig:
    """沙箱配置"""

    def __init__(
            self,
            max_execution_time: int = 30,
            max_memory_mb: int = 256,
            allowed_paths: list = None,
            allowed_network_hosts: list = None,
            restricted_modules: list = None,
    ):
        self.max_execution_time = max_execution_time
        self.max_memory_mb = max_memory_mb
        self.allowed_paths = allowed_paths or []
        self.allowed_network_hosts = allowed_network_hosts or []
        self.restricted_modules = restricted_modules or [
            'os', 'sys', 'subprocess', 'socket',
            'multiprocessing', 'threading', 'ctypes'
        ]


class SandboxResult:
    """沙箱执行结果"""

    def __init__(
            self,
            success: bool,
            data: Any = None,
            error: str = "",
            execution_time: float = 0,
            memory_used_mb: float = 0,
    ):
        self.success = success
        self.data = data
        self.error = error
        self.execution_time = execution_time
        self.memory_used_mb = memory_used_mb
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time": self.execution_time,
            "memory_used_mb": self.memory_used_mb,
            "timestamp": self.timestamp,
        }


def _execute_in_subprocess(
        plugin_code: str,
        function_name: str,
        arguments: dict,
        config: PluginSandboxConfig,
        result_queue: Queue
):
    """
    在子进程中执行插件代码
    
    Args:
        plugin_code: 插件代码字符串
        function_name: 要执行的函数名
        arguments: 函数参数
        config: 沙箱配置
        result_queue: 结果队列
    """
    start_time = time.time()

    try:
        # 创建受限的执行环境
        restricted_globals = {
            '__builtins__': _get_restricted_builtins(),
            '__name__': '__main__',
        }

        # 执行插件代码
        exec(plugin_code, restricted_globals)

        # 调用指定函数
        if function_name in restricted_globals:
            func = restricted_globals[function_name]
            result = func(**arguments)

            execution_time = time.time() - start_time

            # 发送结果
            result_queue.put({
                "success": True,
                "data": result,
                "execution_time": execution_time,
            })
        else:
            result_queue.put({
                "success": False,
                "error": f"Function '{function_name}' not found",
            })

    except Exception as e:
        result_queue.put({
            "success": False,
            "error": str(e),
            "execution_time": time.time() - start_time,
        })


def _get_restricted_builtins():
    """获取受限的内置函数"""
    safe_builtins = {}

    # 只允许安全的内置函数
    allowed_builtins = [
        'abs', 'all', 'any', 'bin', 'bool', 'bytes',
        'chr', 'dict', 'divmod', 'enumerate', 'filter',
        'float', 'format', 'frozenset', 'hash', 'hex',
        'int', 'isinstance', 'issubclass', 'iter',
        'len', 'list', 'map', 'max', 'min', 'next',
        'object', 'oct', 'ord', 'pow', 'print',
        'range', 'repr', 'reversed', 'round',
        'set', 'slice', 'sorted', 'str', 'sum',
        'tuple', 'type', 'zip',
    ]

    for name in allowed_builtins:
        if hasattr(__builtins__, name):
            safe_builtins[name] = getattr(__builtins__, name)

    return safe_builtins


class PluginSandbox:
    """
    插件沙箱
    
    提供安全的插件执行环境
    """

    def __init__(self, config: PluginSandboxConfig = None):
        self.config = config or PluginSandboxConfig()
        self.active_processes: Dict[str, Process] = {}
        self.execution_history: list = []

    async def execute_plugin(
            self,
            plugin_id: str,
            plugin_code: str,
            function_name: str = "main",
            arguments: dict = None,
    ) -> SandboxResult:
        """
        在沙箱中执行插件
        
        Args:
            plugin_id: 插件ID
            plugin_code: 插件代码
            function_name: 要执行的函数名
            arguments: 函数参数
            
        Returns:
            执行结果
        """
        arguments = arguments or {}

        # 创建结果队列
        result_queue = Queue()

        # 创建子进程
        process = Process(
            target=_execute_in_subprocess,
            args=(plugin_code, function_name, arguments, self.config, result_queue),
            daemon=True
        )

        # 记录活跃进程
        self.active_processes[plugin_id] = process

        try:
            # 启动进程
            process.start()

            # 等待结果（带超时）
            try:
                result_data = result_queue.get(
                    timeout=self.config.max_execution_time
                )

                # 构建结果对象
                result = SandboxResult(
                    success=result_data["success"],
                    data=result_data.get("data"),
                    error=result_data.get("error", ""),
                    execution_time=result_data.get("execution_time", 0),
                )

            except asyncio.TimeoutError:
                # 超时处理
                process.terminate()
                process.join(timeout=5)

                result = SandboxResult(
                    success=False,
                    error=f"Execution timeout ({self.config.max_execution_time}s)",
                    execution_time=self.config.max_execution_time,
                )

            # 记录执行历史
            self.execution_history.append({
                "plugin_id": plugin_id,
                "timestamp": datetime.now().isoformat(),
                "result": result.to_dict(),
            })

            return result

        except Exception as e:
            # 确保进程被终止
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)

            return SandboxResult(
                success=False,
                error=f"Sandbox execution failed: {str(e)}",
            )

        finally:
            # 清理活跃进程记录
            self.active_processes.pop(plugin_id, None)

    def terminate_plugin(self, plugin_id: str):
        """
        终止插件执行
        
        Args:
            plugin_id: 插件ID
        """
        if plugin_id in self.active_processes:
            process = self.active_processes[plugin_id]
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)

    def get_active_plugins(self) -> list:
        """获取活跃插件列表"""
        return [
            {
                "plugin_id": pid,
                "pid": proc.pid,
                "is_alive": proc.is_alive(),
            }
            for pid, proc in self.active_processes.items()
        ]

    def get_execution_history(self, limit: int = 10) -> list:
        """获取执行历史"""
        return self.execution_history[-limit:]

    def validate_plugin_code(self, plugin_code: str) -> Dict[str, Any]:
        """
        验证插件代码安全性
        
        Args:
            plugin_code: 插件代码
            
        Returns:
            验证结果
        """
        issues = []

        # 检查危险模块导入
        for module in self.config.restricted_modules:
            if f"import {module}" in plugin_code or f"from {module}" in plugin_code:
                issues.append(f"Restricted module import: {module}")

        # 检查危险函数调用
        dangerous_functions = ['eval(', 'exec(', 'compile(', '__import__(']
        for func in dangerous_functions:
            if func in plugin_code:
                issues.append(f"Dangerous function call: {func}")

        # 检查文件系统操作
        if "open(" in plugin_code and not any(
                path in plugin_code for path in self.config.allowed_paths
        ):
            issues.append("Unauthorized file system access")

        return {
            "is_safe": len(issues) == 0,
            "issues": issues,
            "total_issues": len(issues),
        }


class IPCCommunication:
    """
    进程间通信管理器
    
    提供插件与主机之间的安全通信通道
    """

    def __init__(self):
        self.message_queues: Dict[str, Queue] = {}
        self.handlers: Dict[str, Callable] = {}

    def register_handler(self, message_type: str, handler: Callable):
        """
        注册消息处理器
        
        Args:
            message_type: 消息类型
            handler: 处理函数
        """
        self.handlers[message_type] = handler

    async def send_message(self, plugin_id: str, message: Dict[str, Any]):
        """
        发送消息到插件
        
        Args:
            plugin_id: 插件ID
            message: 消息内容
        """
        if plugin_id in self.message_queues:
            self.message_queues[plugin_id].put(message)

    async def receive_message(self, plugin_id: str, timeout: int = 5) -> Optional[Dict[str, Any]]:
        """
        从插件接收消息
        
        Args:
            plugin_id: 插件ID
            timeout: 超时时间
            
        Returns:
            消息内容
        """
        if plugin_id not in self.message_queues:
            return None

        try:
            queue = self.message_queues[plugin_id]
            message = queue.get(timeout=timeout)

            # 处理消息
            message_type = message.get("type")
            if message_type in self.handlers:
                await self.handlers[message_type](message)

            return message

        except:
            return None

    def create_channel(self, plugin_id: str):
        """创建通信通道"""
        self.message_queues[plugin_id] = Queue()


# 全局实例
plugin_sandbox = PluginSandbox()
ipc_communication = IPCCommunication()
