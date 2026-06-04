"""
插件数据库初始化工具
自动扫描所有需要数据库的插件并初始化其数据库表
"""

import importlib.util
import sys
from pathlib import Path
from typing import List, Dict, Any

from shared.utils.plugin_database import plugin_db


class PluginDatabaseInitializer:
    """
    插件数据库初始化器
    
    功能:
    1. 自动发现需要数据库的插件
    2. 调用每个插件的初始化函数
    3. 提供批量初始化功能
    4. 支持单个插件初始化
    """

    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)

    def discover_plugins_needing_db(self) -> List[Dict[str, Any]]:
        """
        发现所有需要数据库的插件
        
        Returns:
            插件信息列表 [{slug, name, metadata}]
        """
        plugins = []

        if not self.plugins_dir.exists():
            return plugins

        for item in self.plugins_dir.iterdir():
            if not item.is_dir():
                continue

            metadata_file = item / "metadata.json"
            if not metadata_file.exists():
                continue

            try:
                import json
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                # 检查是否需要数据库
                if metadata.get('requires_database', False):
                    plugins.append({
                        'slug': metadata.get('slug', item.name),
                        'name': metadata.get('name', item.name),
                        'metadata': metadata,
                    })

            except Exception as e:
                print(f"[PluginDBInit] Failed to read metadata for {item.name}: {e}")

        return plugins

    def initialize_plugin_db(self, plugin_slug: str) -> bool:
        """
        初始化单个插件的数据库
        
        Args:
            plugin_slug: 插件标识
            
        Returns:
            是否成功
        """
        try:
            # 尝试从插件模块导入初始化函数
            plugin_path = self.plugins_dir / plugin_slug / "plugin.py"

            if not plugin_path.exists():
                print(f"[PluginDBInit] Plugin file not found: {plugin_slug}")
                return False

            # 动态导入插件模块
            spec = importlib.util.spec_from_file_location(
                f"plugin_{plugin_slug.replace('-', '_')}",
                plugin_path
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            # 查找初始化函数（约定：init_{plugin_slug}_db）
            init_func_name = f"init_{plugin_slug.replace('-', '_')}_db"

            if hasattr(module, init_func_name):
                init_func = getattr(module, init_func_name)
                init_func()
                print(f"[PluginDBInit] ✓ Initialized database for {plugin_slug}")
                return True
            else:
                print(f"[PluginDBInit] ⚠ No init function found for {plugin_slug}")
                return False

        except Exception as e:
            print(f"[PluginDBInit] ✗ Failed to initialize {plugin_slug}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def initialize_all(self) -> Dict[str, bool]:
        """
        初始化所有需要数据库的插件
        
        Returns:
            初始化结果 {plugin_slug: success}
        """
        plugins = self.discover_plugins_needing_db()

        if not plugins:
            print("[PluginDBInit] No plugins requiring database found")
            return {}

        print(f"[PluginDBInit] Found {len(plugins)} plugins requiring database initialization")
        print("=" * 60)

        results = {}
        success_count = 0
        fail_count = 0

        for plugin_info in plugins:
            slug = plugin_info['slug']
            name = plugin_info['name']

            print(f"\nInitializing: {name} ({slug})...")
            success = self.initialize_plugin_db(slug)

            results[slug] = success
            if success:
                success_count += 1
            else:
                fail_count += 1

        print("\n" + "=" * 60)
        print(f"[PluginDBInit] Initialization complete:")
        print(f"  Total: {len(plugins)}")
        print(f"  Success: {success_count}")
        print(f"  Failed: {fail_count}")

        return results

    def list_plugin_databases(self) -> List[Dict[str, Any]]:
        """
        列出所有插件数据库
        
        Returns:
            数据库信息列表
        """
        return plugin_db.list_plugin_databases()

    def reset_plugin_db(self, plugin_slug: str) -> bool:
        """
        重置插件数据库（删除并重新创建）
        
        Args:
            plugin_slug: 插件标识
            
        Returns:
            是否成功
        """
        try:
            print(f"[PluginDBInit] Resetting database for {plugin_slug}...")

            # 删除现有数据库
            if plugin_db.delete_plugin_db(plugin_slug):
                print(f"[PluginDBInit] Deleted existing database")

            # 重新初始化
            return self.initialize_plugin_db(plugin_slug)

        except Exception as e:
            print(f"[PluginDBInit] Failed to reset database: {e}")
            return False


def init_all_plugin_databases():
    """
    一键初始化所有插件数据库（向后兼容）
    
    这是主入口函数，可以被其他模块调用
    """
    initializer = PluginDatabaseInitializer()
    return initializer.initialize_all()


def init_single_plugin_db(plugin_slug: str):
    """
    初始化单个插件数据库
    
    Args:
        plugin_slug: 插件标识
    """
    initializer = PluginDatabaseInitializer()
    return initializer.initialize_plugin_db(plugin_slug)


# 命令行入口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Plugin Database Initialization Tool")
    parser.add_argument(
        '--plugin',
        type=str,
        help='Initialize specific plugin (by slug)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all plugin databases'
    )
    parser.add_argument(
        '--reset',
        type=str,
        help='Reset specific plugin database'
    )

    args = parser.parse_args()

    initializer = PluginDatabaseInitializer()

    if args.list:
        databases = initializer.list_plugin_databases()
        if databases:
            print("\nPlugin Databases:")
            print("-" * 60)
            for db in databases:
                size_kb = db['size_bytes'] / 1024
                print(f"  {db['plugin_slug']:30s} {size_kb:8.2f} KB")
        else:
            print("No plugin databases found")

    elif args.reset:
        initializer.reset_plugin_db(args.reset)

    elif args.plugin:
        initializer.initialize_plugin_db(args.plugin)

    else:
        # 默认行为：初始化所有
        init_all_plugin_databases()
