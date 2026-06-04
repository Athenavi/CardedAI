"""
插件系统核心模块

提供插件基类、钩子系统和插件管理功能
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any, Callable, Optional

# 导入 manifest 模块
from shared.services.plugins.plugin_manager.manifest import ManifestValidator, get_capability_description

# 导入审计日志器
try:
    from shared.utils.audit_logger import audit_logger
except ImportError:
    audit_logger = None


class PluginHook:
    """
    插件钩子系统

    支持两种类型的钩子:
    1. Action: 执行动作,无返回值
    2. Filter: 过滤数据,有返回值
    """

    def __init__(self):
        # 动作钩子: {hook_name: [(callback, priority), ...]}
        self.actions: Dict[str, List[tuple]] = {}
        # 过滤器钩子: {hook_name: [(callback, priority), ...]}
        self.filters: Dict[str, List[tuple]] = {}

    def add_action(self, hook_name: str, callback: Callable, priority: int = 10):
        """添加动作钩子"""
        if hook_name not in self.actions:
            self.actions[hook_name] = []
        self.actions[hook_name].append((callback, priority))
        self.actions[hook_name].sort(key=lambda x: x[1])

    def add_filter(self, hook_name: str, callback: Callable, priority: int = 10):
        """添加过滤器钩子"""
        if hook_name not in self.filters:
            self.filters[hook_name] = []
        self.filters[hook_name].append((callback, priority))
        self.filters[hook_name].sort(key=lambda x: x[1])

    async def do_action(self, hook_name: str, *args, **kwargs):
        """执行动作钩子（异步版本）"""
        if hook_name not in self.actions:
            return
        for callback, priority in self.actions[hook_name]:
            try:
                result = callback(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                print(f"[PluginHook] Error in action '{hook_name}': {str(e)}")

    def do_action_sync(self, hook_name: str, *args, **kwargs):
        """执行动作钩子（同步版本）"""
        if hook_name not in self.actions:
            return
        for callback, priority in self.actions[hook_name]:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"[PluginHook] Error in action '{hook_name}': {str(e)}")

    def apply_filters(self, hook_name: str, value: Any, *args, **kwargs) -> Any:
        """应用过滤器钩子"""
        if hook_name not in self.filters:
            return value
        result = value
        for callback, priority in self.filters[hook_name]:
            try:
                result = callback(result, *args, **kwargs)
            except Exception as e:
                print(f"[PluginHook] Error in filter '{hook_name}': {str(e)}")
        return result

    def remove_action(self, hook_name: str, callback: Callable):
        """移除动作钩子"""
        if hook_name in self.actions:
            self.actions[hook_name] = [
                (cb, p) for cb, p in self.actions[hook_name]
                if cb != callback
            ]

    def remove_filter(self, hook_name: str, callback: Callable):
        """移除过滤器钩子"""
        if hook_name in self.filters:
            self.filters[hook_name] = [
                (cb, p) for cb, p in self.filters[hook_name]
                if cb != callback
            ]


# 全局钩子实例
plugin_hooks = PluginHook()


class BasePlugin:
    """
    插件基类

    所有插件都应继承此类并实现必要的方法
    """

    def __init__(
            self,
            plugin_id: int,
            name: str,
            slug: str,
            version: str,
            description: str = "",
            author: str = "",
            author_url: str = "",
            plugin_url: str = "",
    ):
        self.plugin_id = plugin_id
        self.name = name
        self.slug = slug
        self.version = version
        self.description = description
        self.author = author
        self.author_url = author_url
        self.plugin_url = plugin_url

        # 插件状态
        self.active = False
        self.installed = False

        # 插件设置
        self.settings = {}

        # 插件目录
        self.plugin_dir = Path("plugins") / slug

        # 元数据
        self.metadata = {}

        # 权限声明
        self.capabilities: List[str] = []
        self.manifest = None

    def activate(self):
        """激活插件"""
        if self.active:
            return

        # 如果插件需要数据库，自动初始化
        if self.metadata.get('requires_database', False):
            try:
                self._init_plugin_database()
            except Exception as e:
                print(f"[Plugin] Warning: Failed to initialize database for {self.name}: {e}")

        self.active = True
        self.register_hooks()
        print(f"[Plugin] Activated: {self.name} v{self.version}")

    def deactivate(self):
        """停用插件"""
        if not self.active:
            return

        self.unregister_hooks()
        self.active = False
        print(f"[Plugin] Deactivated: {self.name}")

    def install(self):
        """安装插件"""
        if self.installed:
            return

        self.installed = True
        self.load_metadata()
        print(f"[Plugin] Installed: {self.name} v{self.version}")

    def uninstall(self):
        """卸载插件"""
        if self.active:
            self.deactivate()
        self.installed = False
        print(f"[Plugin] Uninstalled: {self.name}")

    def register_hooks(self):
        """注册钩子 - 子类应重写此方法"""
        pass

    def unregister_hooks(self):
        """注销钩子 - 子类可以重写此方法"""
        pass

    def load_metadata(self):
        """加载插件元数据"""
        metadata_file = self.plugin_dir / "metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)

                # 加载 manifest 和权限声明
                is_valid, msg, manifest = ManifestValidator.validate_file(metadata_file)
                if is_valid and manifest:
                    self.manifest = manifest
                    self.capabilities = manifest.capabilities
                    print(f"[Plugin] Loaded manifest for {self.name}: {len(self.capabilities)} capabilities declared")
                else:
                    print(f"[Plugin] Warning: Invalid manifest for {self.name}: {msg}")
                    self.capabilities = self.metadata.get('capabilities', [])

            except Exception as e:
                print(f"[Plugin] Failed to load metadata: {str(e)}")

    def _init_plugin_database(self):
        """初始化插件数据库"""
        import importlib.util
        import sys

        plugin_path = self.plugin_dir / "plugin.py"
        if not plugin_path.exists():
            return

        try:
            spec = importlib.util.spec_from_file_location(
                f"plugin_{self.slug.replace('-', '_')}",
                plugin_path
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            init_func_name = f"init_{self.slug.replace('-', '_')}_db"
            if hasattr(module, init_func_name):
                getattr(module, init_func_name)()
                print(f"[Plugin] Database initialized for {self.name}")

        except Exception as e:
            print(f"[Plugin] Failed to initialize database: {e}")
            raise

    def save_settings(self):
        """保存插件设置"""
        settings_file = self.plugin_dir / "settings.json"
        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Plugin] Failed to save settings: {str(e)}")

    def load_settings(self):
        """加载插件设置"""
        settings_file = self.plugin_dir / "settings.json"
        if settings_file.exists():
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
            except Exception as e:
                print(f"[Plugin] Failed to load settings: {str(e)}")

    def get_settings_ui(self) -> Dict[str, Any]:
        """获取设置界面配置"""
        return {'fields': []}

    def get_info(self) -> Dict[str, Any]:
        """获取插件信息"""
        # 使用内置 hash 替代 hashlib，提升性能
        unique_id = abs(hash(self.slug)) % (10 ** 8)

        return {
            'id': unique_id,
            'name': self.name,
            'slug': self.slug,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'author_url': self.author_url,
            'plugin_url': self.plugin_url,
            'active': self.active,
            'installed': self.installed,
            'settings': self.settings,
            'capabilities': self.capabilities,
            'is_installed': self.installed,
            'is_active': self.active,
            'category': self.metadata.get('category', 'other'),
            'tags': self.metadata.get('tags', []),
            'icon': self.metadata.get('icon', ''),
        }

    def has_capability(self, capability: str) -> bool:
        """检查插件是否拥有指定权限"""
        return capability in self.capabilities

    def check_capability(self, capability: str, raise_error: bool = False) -> bool:
        """检查权限，可选择抛出异常"""
        has_cap = self.has_capability(capability)

        if audit_logger:
            audit_logger.log_permission_check(
                plugin_slug=self.slug,
                capability=capability,
                granted=has_cap
            )

        if has_cap:
            return True

        if raise_error:
            cap_desc = get_capability_description(capability)
            raise PermissionError(
                f"Plugin '{self.name}' does not have required capability: {capability} ({cap_desc})"
            )

        print(f"[Plugin] Permission denied: {self.name} requested {capability}")
        return False


class PluginManager:
    """
    插件管理器

    负责插件的加载、激活、停用和管理
    """

    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugins_dir = Path("plugins")
        self.state_file = Path("storage/plugin_state.json")

    def discover_plugins(self) -> List[str]:
        """发现所有插件"""
        if not self.plugins_dir.exists():
            return []

        plugins = []
        for item in self.plugins_dir.iterdir():
            if item.is_dir():
                metadata_file = item / "metadata.json"
                plugin_file = item / "plugin.py"
                if metadata_file.exists() and plugin_file.exists():
                    plugins.append(item.name)
        return plugins

    def load_plugin(self, plugin_slug: str) -> Optional[BasePlugin]:
        """加载单个插件"""
        import importlib.util
        import sys

        plugin_path = self.plugins_dir / plugin_slug / "plugin.py"
        if not plugin_path.exists():
            print(f"[PluginManager] Plugin file not found: {plugin_slug}")
            return None

        try:
            spec = importlib.util.spec_from_file_location(
                f"plugin_{plugin_slug.replace('-', '_')}",
                plugin_path
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            # 支持两种命名方式：plugin_instance 或 plugin
            plugin = None
            if hasattr(module, 'plugin_instance'):
                plugin = module.plugin_instance
            elif hasattr(module, 'plugin'):
                plugin = module.plugin

            if plugin:
                plugin.plugin_id = len(self.plugins) + 1
                plugin.load_settings()
                self.plugins[plugin_slug] = plugin
                print(f"[PluginManager] Loaded plugin: {plugin.name}")
                return plugin
            else:
                print(f"[PluginManager] No plugin_instance or plugin found in {plugin_slug}")
                return None

        except Exception as e:
            import traceback
            print(f"[PluginManager] Failed to load plugin {plugin_slug}: {str(e)}")
            print(traceback.format_exc())
            return None

    def load_all_plugins(self):
        """加载所有插件"""
        plugin_slugs = self.discover_plugins()
        for slug in plugin_slugs:
            self.load_plugin(slug)
        print(f"[PluginManager] Loaded {len(self.plugins)} plugins")

    def activate_plugin(self, plugin_slug: str) -> bool:
        """激活插件"""
        plugin = self.plugins.get(plugin_slug)
        if not plugin:
            print(f"[PluginManager] Plugin not found: {plugin_slug}")
            return False

        try:
            plugin.activate()
            self._save_plugin_state()
            return True
        except Exception as e:
            print(f"[PluginManager] Failed to activate {plugin_slug}: {str(e)}")
            return False

    def deactivate_plugin(self, plugin_slug: str) -> bool:
        """停用插件"""
        plugin = self.plugins.get(plugin_slug)
        if not plugin:
            return False

        try:
            plugin.deactivate()
            self._save_plugin_state()
            return True
        except Exception as e:
            print(f"[PluginManager] Failed to deactivate {plugin_slug}: {str(e)}")
            return False

    def install_plugin(self, plugin_slug: str) -> bool:
        """安装插件"""
        plugin = self.plugins.get(plugin_slug)
        if not plugin:
            plugin = self.load_plugin(plugin_slug)
            if not plugin:
                return False

        try:
            plugin.install()
            self._save_plugin_state()
            return True
        except Exception as e:
            print(f"[PluginManager] Failed to install {plugin_slug}: {str(e)}")
            return False

    def uninstall_plugin(self, plugin_slug: str) -> bool:
        """卸载插件"""
        plugin = self.plugins.get(plugin_slug)
        if not plugin:
            return False

        try:
            plugin.uninstall()
            del self.plugins[plugin_slug]
            self._save_plugin_state()
            return True
        except Exception as e:
            print(f"[PluginManager] Failed to uninstall {plugin_slug}: {str(e)}")
            return False

    def update_plugin_settings(self, plugin_slug: str, settings: Dict[str, Any]) -> bool:
        """更新插件设置"""
        plugin = self.plugins.get(plugin_slug)
        if not plugin:
            return False

        try:
            plugin.settings.update(settings)
            plugin.save_settings()
            return True
        except Exception as e:
            print(f"[PluginManager] Failed to update settings: {str(e)}")
            return False

    def get_plugin(self, plugin_slug: str) -> Optional[BasePlugin]:
        """获取插件实例"""
        return self.plugins.get(plugin_slug)

    def get_active_plugins(self) -> List[BasePlugin]:
        """获取所有激活的插件"""
        return [p for p in self.plugins.values() if p.active]

    def get_installed_plugins(self) -> List[Dict[str, Any]]:
        """获取所有已安装插件的信息"""
        return [p.get_info() for p in self.plugins.values()]

    def _save_plugin_state(self):
        """保存插件状态到文件"""
        state = {
            plugin_slug: {
                'active': plugin.active,
                'installed': plugin.installed,
            }
            for plugin_slug, plugin in self.plugins.items()
        }

        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[PluginManager] Failed to save state: {str(e)}")

    def _load_plugin_state(self) -> bool:
        """加载插件状态（优先从数据库，回退到文件）

        Returns:
            bool: 是否成功恢复了至少一个插件的状态
        """
        # 尝试从数据库加载
        if self._load_state_from_db():
            return True

        # 回退到文件加载
        return self._load_state_from_file()

    def _load_state_from_db(self) -> bool:
        """从数据库加载插件状态"""
        try:
            from shared.models.plugin import Plugin
            from src.extensions import get_sync_db

            print("\n[PluginManager] Loading plugin state from database...")

            for db_session in get_sync_db():
                # 获取所有已安装的插件（不仅仅是激活的）
                installed_plugins = db_session.query(Plugin).filter(Plugin.is_installed == True).all()
                print(f"[PluginManager] Found {len(installed_plugins)} installed plugins in database")

                for plugin_record in installed_plugins:
                    plugin = self.plugins.get(plugin_record.slug)
                    if plugin:
                        # 先安装插件
                        if not plugin.installed:
                            print(f"[PluginManager] Installing plugin: {plugin.name} ({plugin_record.slug})")
                            plugin.install()

                        # 如果数据库中是激活状态，则激活插件
                        if plugin_record.is_active:
                            print(f"[PluginManager] Activating plugin: {plugin.name} ({plugin_record.slug})")
                            plugin.activate()
                    else:
                        print(f"[PluginManager] Warning: Plugin '{plugin_record.slug}' in database but not loaded")

                print(f"[PluginManager] ✅ Plugin state loaded from database successfully\n")
                return True

            return False

        except Exception as e:
            print(f"[PluginManager] Failed to load state from database: {e}")
            print(f"[PluginManager] Falling back to file-based state loading...")
            return False

    def _load_state_from_file(self) -> bool:
        """从文件加载插件状态

        Returns:
            bool: 是否成功恢复了至少一个插件的状态
        """
        if not self.state_file.exists():
            return False

        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)

            restored = False
            for plugin_slug, plugin_state in state.items():
                plugin = self.plugins.get(plugin_slug)
                if plugin:
                    # 先确保插件已安装
                    if plugin_state.get('installed') and not plugin.installed:
                        print(f"[PluginManager] Installing plugin from state file: {plugin_slug}")
                        plugin.install()

                    # 如果状态文件中是激活状态，则激活插件
                    if plugin_state.get('active'):
                        print(f"[PluginManager] Activating plugin from state file: {plugin_slug}")
                        plugin.activate()
                        restored = True

            return restored
        except Exception as e:
            print(f"[PluginManager] Failed to load state from file: {e}")
            return False

    # ==================== 热插拔功能 ====================

    def hot_reload_plugin(self, plugin_slug: str) -> bool:
        """
        热重载插件（无需重启应用）

        步骤:
        1. 停用当前插件（注销钩子）
        2. 重新加载模块代码
        3. 创建新的插件实例
        4. 激活新插件（注册钩子）

        Args:
            plugin_slug: 插件slug

        Returns:
            是否成功
        """
        import sys
        import importlib

        try:
            print(f"[HotReload] Starting hot reload for plugin: {plugin_slug}")

            # 1. 停用当前插件
            if plugin_slug in self.plugins:
                old_plugin = self.plugins[plugin_slug]
                if old_plugin.active:
                    print(f"[HotReload] Deactivating old plugin instance...")
                    old_plugin.deactivate()

            # 2. 重新加载模块
            module_name = f"plugins.{plugin_slug}.plugin"
            if module_name in sys.modules:
                print(f"[HotReload] Reloading module: {module_name}")
                module = sys.modules[module_name]
                importlib.reload(module)
            else:
                print(f"[HotReload] Module not loaded, importing fresh: {module_name}")
                module = importlib.import_module(module_name)

            # 3. 创建新的插件实例
            print(f"[HotReload] Creating new plugin instance...")
            if hasattr(module, 'plugin'):
                new_plugin = module.plugin
                # 确保插件ID和基本信息保持一致
                if plugin_slug in self.plugins:
                    old_plugin = self.plugins[plugin_slug]
                    new_plugin.plugin_id = old_plugin.plugin_id
                    new_plugin.settings = old_plugin.settings.copy()
                    new_plugin.installed = old_plugin.installed

                # 4. 替换旧实例
                self.plugins[plugin_slug] = new_plugin

                # 5. 激活新插件
                if old_plugin and old_plugin.active:
                    print(f"[HotReload] Activating new plugin instance...")
                    new_plugin.activate()

                self._save_plugin_state()
                print(f"[HotReload] ✅ Plugin '{plugin_slug}' hot reloaded successfully")
                return True
            else:
                print(f"[HotReload] ❌ Module has no 'plugin' attribute")
                return False

        except Exception as e:
            print(f"[HotReload] ❌ Failed to hot reload plugin '{plugin_slug}': {e}")
            import traceback
            traceback.print_exc()
            return False

    def hot_load_plugin(self, plugin_slug: str) -> bool:
        """
        热加载新插件（运行时动态加载，无需重启）

        Args:
            plugin_slug: 插件slug

        Returns:
            是否成功
        """
        import importlib

        try:
            print(f"[HotLoad] Loading new plugin: {plugin_slug}")

            # 检查是否已加载
            if plugin_slug in self.plugins:
                print(f"[HotLoad] Plugin already loaded, use hot_reload instead")
                return self.hot_reload_plugin(plugin_slug)

            # 1. 导入模块
            module_name = f"plugins.{plugin_slug}.plugin"
            print(f"[HotLoad] Importing module: {module_name}")
            module = importlib.import_module(module_name)

            # 2. 获取插件实例
            if not hasattr(module, 'plugin'):
                print(f"[HotLoad] ❌ Module has no 'plugin' attribute")
                return False

            new_plugin = module.plugin

            # 3. 安装并激活
            print(f"[HotLoad] Installing plugin...")
            new_plugin.install()

            print(f"[HotLoad] Activating plugin...")
            new_plugin.activate()

            # 4. 注册到管理器
            self.plugins[plugin_slug] = new_plugin
            self._save_plugin_state()

            print(f"[HotLoad] ✅ Plugin '{plugin_slug}' loaded and activated successfully")
            return True

        except Exception as e:
            print(f"[HotLoad] ❌ Failed to load plugin '{plugin_slug}': {e}")
            import traceback
            traceback.print_exc()
            return False

    def hot_unload_plugin(self, plugin_slug: str) -> bool:
        """
        热卸载插件（运行时动态卸载，无需重启）

        Args:
            plugin_slug: 插件slug

        Returns:
            是否成功
        """
        import sys

        try:
            print(f"[HotUnload] Unloading plugin: {plugin_slug}")

            # 1. 获取插件
            if plugin_slug not in self.plugins:
                print(f"[HotUnload] Plugin not found")
                return False

            plugin = self.plugins[plugin_slug]

            # 2. 停用插件（注销钩子）
            if plugin.active:
                print(f"[HotUnload] Deactivating plugin...")
                plugin.deactivate()

            # 3. 卸载插件
            print(f"[HotUnload] Uninstalling plugin...")
            plugin.uninstall()

            # 4. 从管理器移除
            del self.plugins[plugin_slug]
            self._save_plugin_state()

            # 5. 从sys.modules移除（可选，谨慎使用）
            module_name = f"plugins.{plugin_slug}.plugin"
            if module_name in sys.modules:
                print(f"[HotUnload] Removing module from cache: {module_name}")
                del sys.modules[module_name]

            print(f"[HotUnload] ✅ Plugin '{plugin_slug}' unloaded successfully")
            return True

        except Exception as e:
            print(f"[HotUnload] ❌ Failed to unload plugin '{plugin_slug}': {e}")
            import traceback
            traceback.print_exc()
            return False

    def scan_for_new_plugins(self) -> List[str]:
        """
        扫描插件目录，发现新插件并返回slug列表

        Returns:
            新发现的插件slug列表
        """

        new_plugins = []
        plugins_dir = Path("plugins")

        if not plugins_dir.exists():
            return new_plugins

        # 扫描所有插件目录
        for item in plugins_dir.iterdir():
            if item.is_dir() and (item / "plugin.py").exists():
                plugin_slug = item.name

                # 跳过已加载的插件
                if plugin_slug not in self.plugins:
                    new_plugins.append(plugin_slug)
                    print(f"[Scan] Found new plugin: {plugin_slug}")

        return new_plugins


# 全局插件管理器实例
plugin_manager = PluginManager()
