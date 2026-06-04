"""
插件更新和冲突检测服务
提供版本管理、兼容性检查、回滚机制等功能
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from shared.services.plugins.plugin_manager.marketplace import PluginMarketService
from shared.services.plugins.plugin_manager.version_utils import compare_versions


class PluginUpdateManager:
    """
    插件更新管理器
    
    功能:
    1. 检查可用更新
    2. 版本比较
    3. 更新日志
    4. 批量更新
    5. 版本历史管理
    6. 回滚支持
    """

    def __init__(self, plugins_dir: str = "plugins", backup_dir: str = "backups/plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        # 创建 marketplace 实例
        self.marketplace = PluginMarketService(plugins_dir)

    def check_updates(self) -> Dict[str, Any]:
        """
        检查所有已安装插件的可用更新
        
        Returns:
            更新报告
        """
        installed_plugins = self.marketplace.discover_plugins()

        updates_available = []
        up_to_date = []

        for plugin in installed_plugins:
            slug = plugin['slug']
            current_version = plugin.get('version', '0.0.0')

            # 从远程仓库获取最新版本信息
            try:
                plugin_detail = self.marketplace.get_plugin_detail(slug)
                if plugin_detail and 'latest_version' in plugin_detail:
                    latest_version = plugin_detail['latest_version']
                else:
                    latest_version = current_version  # 无法获取，使用当前版本
            except Exception:
                latest_version = current_version  # 出错时使用当前版本

            if compare_versions(latest_version, current_version) > 0:
                updates_available.append({
                    'slug': slug,
                    'name': plugin.get('name', ''),
                    'current_version': current_version,
                    'latest_version': latest_version,
                    'has_update': True,
                    'download_url': plugin.get('download_url', ''),
                    'changelog': plugin.get('changelog', '')
                })
            else:
                up_to_date.append({
                    'slug': slug,
                    'name': plugin.get('name', ''),
                    'version': current_version,
                    'has_update': False
                })

        return {
            'total': len(installed_plugins),
            'updates_available': len(updates_available),
            'up_to_date': len(up_to_date),
            'updates': updates_available,
            'up_to_date_list': up_to_date
        }



    def get_update_info(self, plugin_slug: str) -> Optional[Dict[str, Any]]:
        """
        获取插件更新信息
        
        Args:
            plugin_slug: 插件slug
            
        Returns:
            更新信息
        """
        plugin = self.marketplace.get_plugin_detail(plugin_slug)

        if not plugin:
            return None

        current_version = plugin.get('version', '0.0.0')

        # 从远程获取最新版本
        try:
            plugin_detail = self.marketplace.get_plugin_detail(plugin_slug)
            if plugin_detail and 'latest_version' in plugin_detail:
                latest_version = plugin_detail['latest_version']
            else:
                latest_version = current_version
        except Exception:
            latest_version = current_version

        return {
            'slug': plugin_slug,
            'name': plugin.get('name', ''),
            'current_version': current_version,
            'latest_version': latest_version,
            'has_update': compare_versions(latest_version, current_version) > 0,
            'changelog': plugin.get('changelog', ''),
            'download_url': plugin.get('download_url', '')
        }

    def backup_plugin_version(self, plugin_slug: str) -> Dict[str, Any]:
        """
        备份插件当前版本
        
        Args:
            plugin_slug: 插件slug
            
        Returns:
            备份结果
        """
        try:
            plugin_path = self.plugins_dir / plugin_slug
            
            if not plugin_path.exists():
                return {
                    'success': False,
                    'error': f'插件不存在: {plugin_slug}'
                }
            
            # 读取元数据获取版本
            metadata_file = plugin_path / 'metadata.json'
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                version = metadata.get('version', 'unknown')
            else:
                version = 'unknown'
            
            # 创建备份目录
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{plugin_slug}_v{version}_{timestamp}"
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # 复制插件文件
            shutil.copytree(plugin_path, backup_path / 'plugin', dirs_exist_ok=True)
            
            # 保存备份信息
            backup_info = {
                'plugin_slug': plugin_slug,
                'version': version,
                'backup_time': datetime.now().isoformat(),
                'backup_path': str(backup_path),
                'backup_name': backup_name
            }
            
            with open(backup_path / 'backup_info.json', 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)
            
            return {
                'success': True,
                'backup_name': backup_name,
                'version': version,
                'message': f'插件 {plugin_slug} v{version} 备份成功'
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'备份失败: {str(e)}'
            }
    
    def get_version_history(self, plugin_slug: str) -> List[Dict[str, Any]]:
        """
        获取插件版本历史
        
        Args:
            plugin_slug: 插件slug
            
        Returns:
            版本历史列表
        """
        history = []
        
        # 查找该插件的所有备份
        for backup_dir in self.backup_dir.iterdir():
            if not backup_dir.is_dir():
                continue
            
            if not backup_dir.name.startswith(f"{plugin_slug}_"):
                continue
            
            info_file = backup_dir / 'backup_info.json'
            if info_file.exists():
                try:
                    with open(info_file, 'r', encoding='utf-8') as f:
                        info = json.load(f)
                    history.append(info)
                except:
                    pass
        
        # 按时间倒序排列
        history.sort(key=lambda x: x.get('backup_time', ''), reverse=True)
        
        return history
    
    def rollback_to_version(self, plugin_slug: str, backup_name: str) -> Dict[str, Any]:
        """
        回滚到指定版本
        
        Args:
            plugin_slug: 插件slug
            backup_name: 备份名称
            
        Returns:
            回滚结果
        """
        try:
            backup_path = self.backup_dir / backup_name
            
            if not backup_path.exists():
                return {
                    'success': False,
                    'error': f'备份不存在: {backup_name}'
                }
            
            # 先备份当前版本
            current_backup = self.backup_plugin_version(plugin_slug)
            if not current_backup['success']:
                return {
                    'success': False,
                    'error': f'备份当前版本失败: {current_backup.get("error")}'
                }
            
            # 恢复旧版本
            plugin_path = self.plugins_dir / plugin_slug
            plugin_source = backup_path / 'plugin'
            
            if not plugin_source.exists():
                return {
                    'success': False,
                    'error': '备份中缺少插件文件'
                }
            
            # 删除当前版本
            if plugin_path.exists():
                shutil.rmtree(plugin_path)
            
            # 恢复备份版本
            shutil.copytree(plugin_source, plugin_path, dirs_exist_ok=True)
            
            # 读取恢复的版本信息
            metadata_file = plugin_path / 'metadata.json'
            restored_version = 'unknown'
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                restored_version = metadata.get('version', 'unknown')
            
            return {
                'success': True,
                'restored_version': restored_version,
                'message': f'插件 {plugin_slug} 已回滚到 v{restored_version}'
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'回滚失败: {str(e)}'
            }


class ConflictDetector:
    """
    冲突检测器
    
    功能:
    1. 插件间冲突检测
    2. 资源冲突检查
    3. API端点冲突
    """

    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)

    def detect_all_conflicts(self) -> Dict[str, Any]:
        """
        检测所有已安装插件之间的冲突
        
        Returns:
            冲突报告
        """
        # 创建 marketplace 实例
        marketplace = PluginMarketService(str(self.plugins_dir))
        installed = marketplace.discover_plugins()

        report = {
            'total_checked': len(installed),
            'conflicts_found': 0,
            'conflicts': [],
            'warnings': []
        }

        # 两两检查冲突
        for i in range(len(installed)):
            for j in range(i + 1, len(installed)):
                plugin1 = installed[i]
                plugin2 = installed[j]

                conflicts = self._check_pair_conflict(plugin1, plugin2)

                if conflicts:
                    report['conflicts_found'] += len(conflicts)
                    report['conflicts'].extend(conflicts)

        # 检查警告(如性能影响)
        report['warnings'] = self._check_warnings(installed)

        return report

    def _check_pair_conflict(
            self,
            plugin1: Dict[str, Any],
            plugin2: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        检查两个插件之间的冲突
        
        Args:
            plugin1: 插件1信息
            plugin2: 插件2信息
            
        Returns:
            冲突列表
        """
        conflicts = []

        # 1. 检查互斥声明
        excludes1 = set(plugin1.get('excludes', []))
        excludes2 = set(plugin2.get('excludes', []))

        if plugin2['slug'] in excludes1 or plugin1['slug'] in excludes2:
            conflicts.append({
                'type': 'mutual_exclusion',
                'severity': 'error',
                'plugins': [plugin1['slug'], plugin2['slug']],
                'message': f"插件 '{plugin1['name']}' 和 '{plugin2['name']}' 互斥"
            })

        # 2. 检查功能重叠
        provides1 = set(plugin1.get('provides', []))
        provides2 = set(plugin2.get('provides', []))

        overlap = provides1 & provides2
        if overlap:
            conflicts.append({
                'type': 'feature_overlap',
                'severity': 'warning',
                'plugins': [plugin1['slug'], plugin2['slug']],
                'features': list(overlap),
                'message': f"功能重叠: {', '.join(overlap)}"
            })

        # 3. 检查相同路由/端点
        routes1 = set(plugin1.get('routes', []))
        routes2 = set(plugin2.get('routes', []))
        
        route_conflicts = routes1 & routes2
        if route_conflicts:
            conflicts.append({
                'type': 'route_conflict',
                'severity': 'error',
                'plugins': [plugin1['slug'], plugin2['slug']],
                'routes': list(route_conflicts),
                'message': f"路由冲突: {', '.join(route_conflicts)}"
            })
        
        # 4. 检查 API 端点冲突
        api_endpoints1 = set(plugin1.get('api_endpoints', []))
        api_endpoints2 = set(plugin2.get('api_endpoints', []))
        
        endpoint_conflicts = api_endpoints1 & api_endpoints2
        if endpoint_conflicts:
            conflicts.append({
                'type': 'api_endpoint_conflict',
                'severity': 'error',
                'plugins': [plugin1['slug'], plugin2['slug']],
                'endpoints': list(endpoint_conflicts),
                'message': f"API 端点冲突: {', '.join(endpoint_conflicts)}"
            })

        return conflicts

    def _check_warnings(self, plugins: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        检查潜在警告
        
        Args:
            plugins: 插件列表
            
        Returns:
            警告列表
        """
        warnings = []

        # 检查是否有过多插件可能影响性能
        if len(plugins) > 20:
            warnings.append({
                'type': 'performance',
                'message': f'已安装 {len(plugins)} 个插件,可能影响系统性能'
            })

        # 检查未维护的插件
        for plugin in plugins:
            last_updated = plugin.get('last_updated')
            if last_updated:
                try:
                    from datetime import datetime, timedelta
                    
                    # 解析最后更新时间
                    if isinstance(last_updated, str):
                        last_update_date = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                    else:
                        last_update_date = last_updated
                    
                    # 计算距离现在的天数
                    days_since_update = (datetime.now(last_update_date.tzinfo) - last_update_date).days
                    
                    # 如果超过6个月未更新，发出警告
                    if days_since_update > 180:
                        warnings.append({
                            'type': 'maintenance',
                            'plugin': plugin.get('name', plugin.get('slug', '')),
                            'message': f"插件 {plugin.get('name', '')} 已超过 {days_since_update} 天未更新，可能存在安全风险"
                        })
                except Exception:
                    pass  # 忽略解析错误

        return warnings


# 全局实例
plugin_update_manager = PluginUpdateManager()
conflict_detector = ConflictDetector()
