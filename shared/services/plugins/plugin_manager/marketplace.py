"""
插件市场服务
提供插件浏览、搜索、安装、更新等完整功能
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional


class PluginMarketService:
    """
    插件市场管理器 (整合版)
    
    功能:
    1. 扫描本地插件
    2. 插件搜索和过滤
    3. 分类管理
    4. 插件详情查询
    5. 远程市场浏览
    6. 一键安装/卸载
    7. 版本更新检查
    """

    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(parents=True, exist_ok=True)

        # 远程市场URL
        self.marketplace_url = "https://plugins.fastblog.com/api/v1"

        # 缓存
        self._cached_plugins = None
        self._cache_timestamp = None
        self._cache_ttl = 3600  # 1小时

    def discover_plugins(self) -> List[Dict[str, Any]]:
        """扫描插件目录，发现所有可用插件（带缓存）"""
        # 检查缓存是否有效
        if self._cached_plugins is not None and self._cache_timestamp is not None:
            from datetime import datetime, timezone
            cache_age = (datetime.now(timezone.utc) - self._cache_timestamp).total_seconds()
            if cache_age < self._cache_ttl:
                return self._cached_plugins

        # 缓存失效，重新扫描
        discovered = []

        if not self.plugins_dir.exists():
            return discovered

        for plugin_dir in self.plugins_dir.iterdir():
            if not plugin_dir.is_dir():
                continue

            metadata_file = plugin_dir / "metadata.json"
            if not metadata_file.exists():
                continue

            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                    # 添加额外信息
                    metadata['path'] = str(plugin_dir)
                    metadata['slug'] = plugin_dir.name

                    # 检查是否有主文件
                    main_file = plugin_dir / "plugin.py"
                    metadata['has_main_file'] = main_file.exists()

                    # 检查是否已安装
                    metadata['is_installed'] = True
                    metadata['is_active'] = self._is_plugin_active(plugin_dir.name)

                    # 检查截图
                    screenshots_dir = plugin_dir / "screenshots"
                    if screenshots_dir.exists():
                        metadata['screenshots_local'] = [
                            f"/plugins/{plugin_dir.name}/screenshots/{f.name}"
                            for f in screenshots_dir.glob("*.png")
                        ]

                    discovered.append(metadata)
            except Exception as e:
                print(f"读取插件元数据失败 {plugin_dir.name}: {e}")

        # 更新缓存
        from datetime import datetime, timezone
        self._cached_plugins = discovered
        self._cache_timestamp = datetime.now(timezone.utc)

        return discovered

    def search_plugins(
            self,
            keyword: str = "",
            category: str = "",
            sort_by: str = "name",
            order: str = "asc"
    ) -> List[Dict[str, Any]]:
        """
        搜索插件
        
        Args:
            keyword: 搜索关键词
            category: 分类过滤
            sort_by: 排序字段 (name, rating, installs, created_at)
            order: 排序方向 (asc, desc)
            
        Returns:
            匹配的插件列表
        """
        plugins = self.discover_plugins()

        # 关键词搜索
        if keyword:
            keyword_lower = keyword.lower()
            plugins = [
                p for p in plugins
                if keyword_lower in p.get('name', '').lower()
                   or keyword_lower in p.get('description', '').lower()
                   or keyword_lower in p.get('slug', '').lower()
                   or keyword_lower in p.get('author', '').lower()
            ]

        # 分类过滤
        if category:
            plugins = [p for p in plugins if p.get('category') == category]

        # 排序
        reverse = order.lower() == 'desc'

        if sort_by == 'rating':
            plugins.sort(key=lambda x: x.get('rating', 0), reverse=reverse)
        elif sort_by == 'installs':
            plugins.sort(key=lambda x: x.get('installs', 0), reverse=reverse)
        elif sort_by == 'created_at':
            plugins.sort(
                key=lambda x: x.get('created_at', ''),
                reverse=reverse
            )
        else:  # name
            plugins.sort(key=lambda x: x.get('name', ''), reverse=reverse)

        return plugins

    def get_categories(self) -> List[Dict[str, Any]]:
        """
        获取所有插件分类
        
        Returns:
            分类列表，包含名称和数量
        """
        plugins = self.discover_plugins()

        # 统计每个分类的插件数量
        category_count = {}
        for plugin in plugins:
            category = plugin.get('category', 'uncategorized')
            category_count[category] = category_count.get(category, 0) + 1

        # 转换为列表格式
        categories = [
            {
                'slug': slug,
                'name': self._get_category_name(slug),
                'count': count
            }
            for slug, count in category_count.items()
        ]

        # 按名称排序
        categories.sort(key=lambda x: x['name'])

        return categories

    def get_plugin_detail(self, plugin_slug: str) -> Optional[Dict[str, Any]]:
        """
        获取插件详细信息
        
        Args:
            plugin_slug: 插件slug
            
        Returns:
            插件详细信息
        """
        plugin_dir = self.plugins_dir / plugin_slug

        if not plugin_dir.exists():
            return None

        metadata_file = plugin_dir / "metadata.json"
        if not metadata_file.exists():
            return None

        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # 添加额外信息
            metadata['path'] = str(plugin_dir)
            metadata['slug'] = plugin_slug

            # 检查主文件
            main_file = plugin_dir / "plugin.py"
            metadata['has_main_file'] = main_file.exists()

            # 读取README
            readme_file = plugin_dir / "README.md"
            if readme_file.exists():
                with open(readme_file, 'r', encoding='utf-8') as f:
                    metadata['readme'] = f.read()

            # 检查截图
            screenshots_dir = plugin_dir / "screenshots"
            if screenshots_dir.exists():
                metadata['screenshots_local'] = [
                    f"/plugins/{plugin_slug}/screenshots/{f.name}"
                    for f in screenshots_dir.glob("*.png")
                ]

            # 检查版本历史
            changelog_file = plugin_dir / "CHANGELOG.md"
            if changelog_file.exists():
                with open(changelog_file, 'r', encoding='utf-8') as f:
                    metadata['changelog_full'] = f.read()

            return metadata

        except Exception as e:
            print(f"读取插件详情失败 {plugin_slug}: {e}")
            return None

    def _get_category_name(self, category_slug: str) -> str:
        """
        获取分类显示名称
        
        Args:
            category_slug: 分类slug
            
        Returns:
            分类显示名称
        """
        category_names = {
            'seo': 'SEO优化',
            'security': '安全防护',
            'analytics': '数据分析',
            'social': '社交分享',
            'media': '媒体处理',
            'performance': '性能优化',
            'backup': '备份恢复',
            'marketing': '营销工具',
            'workflow': '工作流',
            'search': '搜索增强',
            'cdn': 'CDN加速',
            'email': '邮件营销',
            'uncategorized': '未分类',
        }

        return category_names.get(category_slug, category_slug)

    def get_featured_plugins(self, limit: int = 6) -> List[Dict[str, Any]]:
        """
        获取推荐插件（按评分和安装量排序）
        
        Args:
            limit: 返回数量
            
        Returns:
            推荐插件列表
        """
        plugins = self.discover_plugins()

        # 综合评分和安装量排序
        plugins.sort(
            key=lambda x: (x.get('rating', 0) * 0.6 +
                           min(x.get('installs', 0) / 10000, 5) * 0.4),
            reverse=True
        )

        return plugins[:limit]

    def get_recent_plugins(self, limit: int = 6) -> List[Dict[str, Any]]:
        """
        获取最新插件
        
        Args:
            limit: 返回数量
            
        Returns:
            最新插件列表
        """
        plugins = self.discover_plugins()

        # 按版本号排序（简化处理）
        plugins.sort(
            key=lambda x: x.get('version', '0.0.0'),
            reverse=True
        )

        return plugins[:limit]

    def clear_cache(self):
        """清除插件列表缓存"""
        self._cached_plugins = None
        self._cache_timestamp = None

    def _is_plugin_active(self, plugin_slug: str) -> bool:
        """检查插件是否激活"""
        try:
            from shared.models.plugin import Plugin
            from src.extensions import get_sync_db

            for db_session in get_sync_db():
                plugin = db_session.query(Plugin).filter(Plugin.slug == plugin_slug).first()
                return plugin.is_active if plugin else False
        except Exception:
            return False


# 全局实例
plugin_marketplace = PluginMarketService()
