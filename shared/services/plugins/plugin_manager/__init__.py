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

# ==================== 懒加载映射表 ====================
# 名称 -> (子模块路径, 原始名称)
_LAZY_IMPORTS = {
    # Core
    'BasePlugin': ('.core', 'BasePlugin'),
    'PluginManager': ('.core', 'PluginManager'),
    'PluginHook': ('.core', 'PluginHook'),
    'plugin_hooks': ('.core', 'plugin_hooks'),
    'plugin_manager': ('.core', 'plugin_manager'),

    # Dependency
    'PluginDependencyManager': ('.dependency', 'PluginDependencyManager'),
    'plugin_dependency_manager': ('.dependency', 'plugin_dependency_manager'),

    # Init
    'initialize_plugins': ('.init', 'initialize_plugins'),
    'trigger_plugin_event': ('.init', 'trigger_plugin_event'),
    'apply_plugin_filter': ('.init', 'apply_plugin_filter'),

    # Installer
    'PluginInstaller': ('.installer', 'PluginInstaller'),
    'plugin_installer': ('.installer', 'plugin_installer'),

    # Manifest
    'PluginManifest': ('.manifest', 'PluginManifest'),
    'ManifestValidator': ('.manifest', 'ManifestValidator'),
    'PluginCapability': ('.manifest', 'PluginCapability'),
    'PluginDependency': ('.manifest', 'PluginDependency'),
    'PluginSettingsField': ('.manifest', 'PluginSettingsField'),
    'DependencyResolver': ('.manifest', 'DependencyResolver'),
    'PREDEFINED_CAPABILITIES': ('.manifest', 'PREDEFINED_CAPABILITIES'),
    'get_capability_description': ('.manifest', 'get_capability_description'),

    # Marketplace
    'PluginMarketService': ('.marketplace', 'PluginMarketService'),

    # Public API
    'PluginPublicAPI': ('.public_api', 'PluginPublicAPI'),
    'plugin_api': ('.public_api', 'plugin_api'),

    # Version Utils
    'compare_versions': ('.version_utils', 'compare_versions'),
    'check_version_match': ('.version_utils', 'check_version_match'),
}

# 已加载的缓存
_loaded = {}


def __getattr__(name):
    """模块级 __getattr__：按需懒加载"""
    if name in _loaded:
        return _loaded[name]

    spec = _LAZY_IMPORTS.get(name)
    if spec is not None:
        import importlib
        module_path, attr_name = spec
        module = importlib.import_module(module_path, package=__name__)
        cls = getattr(module, attr_name)
        # 缓存到模块命名空间
        globals()[name] = cls
        _loaded[name] = cls
        return cls

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


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
