"""
懒加载模块管理器

用于优化应用启动时间，通过延迟加载非关键模块

功能:
1. 模块懒加载
2. 按需导入
3. 模块依赖管理
4. 加载优先级控制
"""

import importlib
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime


class LazyModule:
    """
    懒加载模块包装器
    
    延迟导入模块，直到首次访问
    """

    def __init__(self, module_path: str, priority: int = 0, critical: bool = False):
        self.module_path = module_path
        self.priority = priority  # 优先级，数字越小越优先加载
        self.critical = critical  # 是否关键模块（关键模块会立即加载）
        self._module = None
        self._load_time = None
        self._access_count = 0

    def _load(self):
        """实际加载模块"""
        if self._module is None:
            start_time = time.time()
            try:
                self._module = importlib.import_module(self.module_path)
                self._load_time = time.time() - start_time
                print(f"[LazyLoader] 已加载模块: {self.module_path} ({self._load_time:.4f}s)")
            except ImportError as e:
                print(f"[LazyLoader] 加载失败: {self.module_path} - {e}")
                raise

    def __getattr__(self, name):
        """属性访问时自动加载模块"""
        if self._module is None:
            self._load()
        self._access_count += 1
        return getattr(self._module, name)

    def get_load_info(self) -> Dict[str, Any]:
        """获取加载信息"""
        return {
            "module_path": self.module_path,
            "loaded": self._module is not None,
            "load_time": self._load_time,
            "access_count": self._access_count,
            "priority": self.priority,
            "critical": self.critical,
        }


class LazyLoaderManager:
    """
    懒加载管理器
    
    管理所有懒加载模块
    """

    def __init__(self):
        self.modules: Dict[str, LazyModule] = {}
        self.load_order: list = []

    def register_module(
            self,
            name: str,
            module_path: str,
            priority: int = 0,
            critical: bool = False
    ):
        """
        注册懒加载模块
        
        Args:
            name: 模块名称（用于引用）
            module_path: 模块路径
            priority: 加载优先级
            critical: 是否关键模块
        """
        lazy_module = LazyModule(module_path, priority, critical)
        self.modules[name] = lazy_module

        # 添加到加载顺序列表
        self.load_order.append((priority, name))
        self.load_order.sort(key=lambda x: x[0])

        # 如果是关键模块，立即加载
        if critical:
            try:
                _ = lazy_module._module  # 触发加载
            except Exception:
                pass

    def get_module(self, name: str) -> LazyModule:
        """
        获取懒加载模块
        
        Args:
            name: 模块名称
            
        Returns:
            懒加载模块实例
        """
        if name not in self.modules:
            raise KeyError(f"Module '{name}' not registered")

        return self.modules[name]

    def load_by_priority(self, max_priority: int = None):
        """
        按优先级加载模块
        
        Args:
            max_priority: 最大优先级（只加载优先级<=max_priority的模块）
        """
        for priority, name in self.load_order:
            if max_priority is not None and priority > max_priority:
                break

            module = self.modules[name]
            if not module.critical and module._module is None:
                try:
                    module._load()
                except Exception as e:
                    print(f"[LazyLoader] 加载失败 {name}: {e}")

    def load_all(self):
        """加载所有模块"""
        self.load_by_priority()

    def get_loading_stats(self) -> Dict[str, Any]:
        """获取加载统计信息"""
        total_modules = len(self.modules)
        loaded_modules = sum(1 for m in self.modules.values() if m._module is not None)
        total_load_time = sum(
            m._load_time for m in self.modules.values()
            if m._load_time is not None
        )

        return {
            "total_modules": total_modules,
            "loaded_modules": loaded_modules,
            "unloaded_modules": total_modules - loaded_modules,
            "total_load_time_seconds": round(total_load_time, 4),
            "modules": {
                name: module.get_load_info()
                for name, module in self.modules.items()
            },
            "timestamp": datetime.now().isoformat(),
        }

    def optimize_loading_strategy(self) -> Dict[str, Any]:
        """
        分析并提供加载策略优化建议
        
        Returns:
            优化建议
        """
        suggestions = []

        # 检查未使用的模块
        unused_modules = [
            name for name, module in self.modules.items()
            if module._module is not None and module._access_count == 0
        ]

        if unused_modules:
            suggestions.append({
                "type": "unused_modules",
                "severity": "warning",
                "message": f"发现 {len(unused_modules)} 个已加载但未使用的模块",
                "modules": unused_modules,
                "recommendation": "考虑将这些模块改为真正的懒加载，或移除不必要的导入",
            })

        # 检查慢加载模块
        slow_modules = [
            {
                "name": name,
                "load_time": module._load_time,
            }
            for name, module in self.modules.items()
            if module._load_time and module._load_time > 1.0
        ]

        if slow_modules:
            suggestions.append({
                "type": "slow_modules",
                "severity": "warning",
                "message": f"发现 {len(slow_modules)} 个加载时间超过1秒的模块",
                "modules": slow_modules,
                "recommendation": "考虑优化这些模块的初始化逻辑，或使用异步加载",
            })

        # 检查关键模块数量
        critical_count = sum(1 for m in self.modules.values() if m.critical)
        if critical_count > len(self.modules) * 0.5:
            suggestions.append({
                "type": "too_many_critical",
                "severity": "info",
                "message": f"关键模块占比过高 ({critical_count}/{len(self.modules)})",
                "recommendation": "重新评估哪些模块真正需要在启动时立即加载",
            })

        return {
            "suggestions": suggestions,
            "stats": self.get_loading_stats(),
        }


# 全局懒加载管理器实例
lazy_loader = LazyLoaderManager()


def register_lazy_modules():
    """
    注册所有可懒加载的模块
    
    这里定义哪些模块可以懒加载以及它们的优先级
    """
    # 核心模块（立即加载）
    lazy_loader.register_module("database", "src.utils.database.unified_manager", priority=0, critical=True)
    lazy_loader.register_module("extensions", "src.extensions", priority=0, critical=True)

    # 高优先级模块（启动后尽快加载）
    lazy_loader.register_module("scheduler", "src.scheduler", priority=1, critical=False)
    lazy_loader.register_module("plugins", "shared.services.plugins.plugin_manager.init", priority=1, critical=False)

    # 中优先级模块（按需加载）
    lazy_loader.register_module("analytics", "shared.services.analytics", priority=2, critical=False)
    lazy_loader.register_module("seo", "shared.services.seo", priority=2, critical=False)
    lazy_loader.register_module("security", "shared.services.security", priority=2, critical=False)

    # 低优先级模块（真正需要时才加载）
    lazy_loader.register_module("ai", "shared.services.ai", priority=3, critical=False)
    lazy_loader.register_module("nlp", "shared.services.nlp", priority=3, critical=False)
    lazy_loader.register_module("translation", "shared.services.translation", priority=3, critical=False)

    # API路由模块（按需加载）
    lazy_loader.register_module("api_v2", "src.api.v2", priority=4, critical=False)
    lazy_loader.register_module("api_v3", "src.api.v3", priority=4, critical=False)


def init_lazy_loading():
    """初始化懒加载系统"""
    register_lazy_modules()

    # 立即加载关键模块
    lazy_loader.load_by_priority(max_priority=0)

    print("[LazyLoader] 懒加载系统已初始化")
    print(f"[LazyLoader] 注册了 {len(lazy_loader.modules)} 个模块")
    print(f"[LazyLoader] 关键模块: {sum(1 for m in lazy_loader.modules.values() if m.critical)}")


def get_lazy_loader_stats():
    """获取懒加载统计信息（供API调用）"""
    return lazy_loader.get_loading_stats()


def get_lazy_loader_suggestions():
    """获取懒加载优化建议（供API调用）"""
    return lazy_loader.optimize_loading_strategy()
