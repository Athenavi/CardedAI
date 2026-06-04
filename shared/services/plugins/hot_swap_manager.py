"""
插件动态热插拔管理器
支持在不重启服务的情况下加载、卸载和更新插件
"""
import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Dict, Any


class PluginHotSwapper:
    """插件热插拔核心逻辑"""

    def __init__(self):
        self.loaded_plugins: Dict[str, Any] = {}
        self._module_names: Dict[str, str] = {}  # slug -> module_name 映射

    async def load_plugin(self, plugin_slug: str):
        """动态加载插件模块"""
        plugin_path = Path(f"plugins/{plugin_slug}") / "plugin.py"
        if not plugin_path.exists():
            raise FileNotFoundError(f"Plugin {plugin_slug} not found")

        try:
            # 使用唯一的模块名避免冲突
            module_name = f"plugins.{plugin_slug}.plugin"
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # 支持 plugin_instance 或 plugin 两种命名方式
            instance = None
            if hasattr(module, "plugin_instance"):
                instance = module.plugin_instance
            elif hasattr(module, "plugin"):
                instance = module.plugin

            if instance:
                self.loaded_plugins[plugin_slug] = instance
                self._module_names[plugin_slug] = module_name
                # 注册钩子
                if hasattr(instance, "register_hooks"):
                    instance.register_hooks()
                return True
            else:
                print(f"Plugin {plugin_slug}: no plugin_instance or plugin found")
                return False
        except Exception as e:
            print(f"Failed to load plugin {plugin_slug}: {e}")
            return False

    async def unload_plugin(self, plugin_slug: str):
        """动态卸载插件"""
        if plugin_slug in self.loaded_plugins:
            plugin = self.loaded_plugins.pop(plugin_slug)
            # 注销钩子
            if hasattr(plugin, "unregister_hooks"):
                plugin.unregister_hooks()

            # 从 sys.modules 中移除
            module_name = self._module_names.pop(plugin_slug, None)
            if module_name and module_name in sys.modules:
                del sys.modules[module_name]
            return True
        return False

    async def reload_plugin(self, plugin_slug: str):
        """热更新插件"""
        await self.unload_plugin(plugin_slug)
        return await self.load_plugin(plugin_slug)


hot_swapper = PluginHotSwapper()
