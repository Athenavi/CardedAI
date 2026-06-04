"""
插件依赖管理服务
处理插件之间的依赖关系、冲突检测和版本锁定
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# 延迟导入以避免循环依赖
from shared.services.plugins.plugin_manager.version_utils import check_version_match


class PluginDependencyManager:
    """
    插件依赖管理器
    
    功能:
    1. 插件依赖声明解析
    2. 自动安装依赖插件
    3. 冲突检测
    4. 依赖版本锁定
    """
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        # 元数据缓存 {slug: metadata}
        self._metadata_cache: Dict[str, Dict] = {}
        self._cache_enabled = True

    def _get_metadata(self, plugin_slug: str) -> Optional[Dict]:
        """获取插件元数据（带缓存）"""
        if self._cache_enabled and plugin_slug in self._metadata_cache:
            return self._metadata_cache[plugin_slug]

        metadata_file = self.plugins_dir / plugin_slug / "metadata.json"
        if not metadata_file.exists():
            return None

        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            if self._cache_enabled:
                self._metadata_cache[plugin_slug] = metadata

            return metadata
        except Exception:
            return None

    def clear_cache(self):
        """清除元数据缓存"""
        self._metadata_cache.clear()
    
    def parse_dependencies(self, plugin_slug: str) -> Dict[str, Any]:
        """
        解析插件的依赖声明
        
        Args:
            plugin_slug: 插件标识
            
        Returns:
            依赖信息
        """
        metadata = self._get_metadata(plugin_slug)

        if not metadata:
            return {
                "success": False,
                "error": f"插件元数据不存在: {plugin_slug}"
            }

        dependencies = metadata.get("dependencies", {})
        conflicts = metadata.get("conflicts", [])
        requires_version = metadata.get("requires", "")

        return {
            "success": True,
            "plugin": plugin_slug,
            "dependencies": dependencies,
            "conflicts": conflicts,
            "requires_version": requires_version
        }
    
    def check_dependencies(
        self,
        plugin_slug: str,
        installed_plugins: List[str]
    ) -> Dict[str, Any]:
        """
        检查插件依赖是否满足
        
        Args:
            plugin_slug: 要检查的插件
            installed_plugins: 已安装的插件列表
            
        Returns:
            检查结果
        """
        dep_info = self.parse_dependencies(plugin_slug)
        
        if not dep_info["success"]:
            return dep_info
        
        missing_deps = []
        satisfied_deps = []
        
        # 检查每个依赖
        for dep_slug, dep_version in dep_info["dependencies"].items():
            if dep_slug not in installed_plugins:
                missing_deps.append({
                    "slug": dep_slug,
                    "required_version": dep_version,
                    "installed": False
                })
            else:
                # 检查版本是否匹配
                if dep_version:  # 如果有版本要求
                    # 获取已安装插件的版本
                    dep_metadata = self._get_metadata(dep_slug)
                    if dep_metadata:
                        installed_version = dep_metadata.get("version", "0.0.0")

                        # 比较版本（延迟导入）
                        from shared.services.plugins.plugin_manager.version_utils import check_version_match
                        if check_version_match(installed_version, dep_version):
                            satisfied_deps.append(dep_slug)
                        else:
                            missing_deps.append({
                                "slug": dep_slug,
                                "required_version": dep_version,
                                "installed_version": installed_version,
                                "installed": True,
                                "version_mismatch": True
                            })
                    else:
                        satisfied_deps.append(dep_slug)  # 无法读取版本，假设兼容
                else:
                    satisfied_deps.append(dep_slug)  # 无版本要求
        
        return {
            "success": len(missing_deps) == 0,
            "plugin": plugin_slug,
            "missing_dependencies": missing_deps,
            "satisfied_dependencies": satisfied_deps,
            "total_deps": len(dep_info["dependencies"])
        }
    
    def detect_conflicts(
        self,
        plugin_slug: str,
        installed_plugins: List[str]
    ) -> Dict[str, Any]:
        """
        检测插件冲突
        
        Args:
            plugin_slug: 要检查的插件
            installed_plugins: 已安装的插件列表
            
        Returns:
            冲突检测结果
        """
        dep_info = self.parse_dependencies(plugin_slug)
        
        if not dep_info["success"]:
            return dep_info
        
        conflicts_found = []
        
        # 检查与已安装插件的冲突
        for conflict_plugin in dep_info["conflicts"]:
            if conflict_plugin in installed_plugins:
                conflicts_found.append({
                    "conflicting_plugin": conflict_plugin,
                    "reason": f"与 {conflict_plugin} 存在冲突"
                })
        
        # 检查反向冲突（已安装插件是否与新插件冲突）
        for installed in installed_plugins:
            installed_dep = self.parse_dependencies(installed)
            if installed_dep["success"]:
                if plugin_slug in installed_dep["conflicts"]:
                    conflicts_found.append({
                        "conflicting_plugin": installed,
                        "reason": f"{installed} 声明与 {plugin_slug} 冲突"
                    })
        
        return {
            "has_conflicts": len(conflicts_found) > 0,
            "conflicts": conflicts_found,
            "can_install": len(conflicts_found) == 0
        }
    
    def get_install_order(
        self,
        plugin_slug: str,
        installed_plugins: List[str]
    ) -> Dict[str, Any]:
        """
        获取插件安装顺序（包括依赖）
        
        Args:
            plugin_slug: 目标插件
            installed_plugins: 已安装的插件列表
            
        Returns:
            安装顺序列表
        """
        install_queue = []
        visited = set()
        
        def resolve_deps(slug):
            if slug in visited:
                return
            
            visited.add(slug)
            
            # 如果已安装，跳过
            if slug in installed_plugins:
                return
            
            # 解析依赖
            dep_info = self.parse_dependencies(slug)
            if not dep_info["success"]:
                return
            
            # 先安装依赖
            for dep_slug in dep_info["dependencies"].keys():
                resolve_deps(dep_slug)
            
            # 然后添加当前插件
            install_queue.append(slug)
        
        resolve_deps(plugin_slug)
        
        return {
            "success": True,
            "install_order": install_queue,
            "total_plugins": len(install_queue),
            "already_installed": [p for p in install_queue if p in installed_plugins],
            "to_install": [p for p in install_queue if p not in installed_plugins]
        }
    
    def lock_dependency_versions(
        self,
        plugin_slug: str
    ) -> Dict[str, Any]:
        """
        锁定插件依赖版本
        
        Args:
            plugin_slug: 插件标识
            
        Returns:
            版本锁定信息
        """
        dep_info = self.parse_dependencies(plugin_slug)
        
        if not dep_info["success"]:
            return dep_info
        
        locked_versions = {}

        # 锁定每个依赖的实际版本
        for dep_slug in dep_info["dependencies"].keys():
            dep_metadata = self._get_metadata(dep_slug)
            if dep_metadata:
                locked_versions[dep_slug] = dep_metadata.get("version", "unknown")
        
        # 保存锁定文件
        lock_file = self.plugins_dir / plugin_slug / "dependency-lock.json"
        try:
            from datetime import datetime
            with open(lock_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "plugin": plugin_slug,
                    "locked_at": datetime.now().isoformat(),
                    "dependencies": locked_versions
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            return {
                "success": False,
                "error": f"保存锁定文件失败: {str(e)}"
            }
        
        return {
            "success": True,
            "locked_versions": locked_versions,
            "lock_file": str(lock_file)
        }
    
    def validate_compatibility(
        self,
        plugin_slug: str,
        platform_version: str
    ) -> Dict[str, Any]:
        """
        验证插件与平台的兼容性
        
        Args:
            plugin_slug: 插件标识
            platform_version: 平台版本
            
        Returns:
            兼容性检查结果
        """
        dep_info = self.parse_dependencies(plugin_slug)
        
        if not dep_info["success"]:
            return dep_info
        
        requires = dep_info["requires_version"]
        
        if not requires:
            return {
                "compatible": True,
                "message": "无版本要求"
            }

        # 简单的版本比较
        compatible = check_version_match(platform_version, requires)
        
        return {
            "compatible": compatible,
            "platform_version": platform_version,
            "required_version": requires,
            "message": "兼容" if compatible else f"需要版本 {requires}"
        }


# 全局实例
plugin_dependency_manager = PluginDependencyManager()
