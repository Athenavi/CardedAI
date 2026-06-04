"""
插件管理系统

统一的插件管理包，提供完整的插件生命周期管理功能：
- 插件加载和激活
- 钩子系统（Actions & Filters）
- 插件市场（浏览、搜索、安装）
- 依赖管理
- 版本更新和回滚
- 权限控制
"""

from shared.services.plugins.plugin_manager.core import (
    BasePlugin,
    PluginManager,
    PluginHook,
    plugin_hooks,
    plugin_manager,
)
from shared.services.plugins.plugin_manager.dependency import (
    PluginDependencyManager,
    plugin_dependency_manager,
)
from shared.services.plugins.plugin_manager.init import (
    initialize_plugins,
    trigger_plugin_event,
    apply_plugin_filter,
)
from shared.services.plugins.plugin_manager.installer import (
    PluginInstaller,
    plugin_installer,
)
from shared.services.plugins.plugin_manager.manifest import (
    PluginManifest,
    ManifestValidator,
    PluginCapability,
    PluginDependency,
    PluginSettingsField,
    DependencyResolver,
    PREDEFINED_CAPABILITIES,
    get_capability_description,
)
from shared.services.plugins.plugin_manager.marketplace import (
    PluginMarketService,
)
from shared.services.plugins.plugin_manager.public_api import (
    PluginPublicAPI,
    plugin_api,
)
from shared.services.plugins.plugin_manager.version_utils import (
    compare_versions,
    check_version_match,
)

__all__ = [
    # Core
    'BasePlugin',
    'PluginManager',
    'PluginHook',
    'plugin_hooks',
    'plugin_manager',

    # Manifest
    'PluginManifest',
    'ManifestValidator',
    'PluginCapability',
    'PluginDependency',
    'PluginSettingsField',
    'DependencyResolver',
    'PREDEFINED_CAPABILITIES',
    'get_capability_description',

    # Installer
    'PluginInstaller',
    'plugin_installer',

    # Marketplace
    'PluginMarketService',

    # Dependency
    'PluginDependencyManager',
    'plugin_dependency_manager',

    # Updater

    # Public API
    'PluginPublicAPI',
    'plugin_api',

    # Init
    'initialize_plugins',
    'trigger_plugin_event',
    'apply_plugin_filter',

    # Version Utils
    'compare_versions',
    'check_version_match',
]

__version__ = '1.0.0'
