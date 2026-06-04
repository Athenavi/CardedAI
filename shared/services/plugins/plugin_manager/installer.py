"""
插件安装服务
支持ZIP包上传安装、依赖检查、激活/停用
"""

import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

from shared.services.plugins.plugin_manager.dependency import plugin_dependency_manager


class PluginInstaller:
    """
    插件安装器
    
    功能:
    1. ZIP包解压安装
    2. 依赖检查
    3. 版本兼容性验证
    4. 激活/停用管理
    """

    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(parents=True, exist_ok=True)

    def install_from_zip(self, zip_path: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        从ZIP文件安装插件
        
        Args:
            zip_path: ZIP文件路径
            
        Returns:
            (成功标志, 消息, 插件元数据)
        """
        try:
            zip_file = Path(zip_path)

            if not zip_file.exists():
                return False, f"ZIP文件不存在: {zip_path}", None

            # 验证ZIP文件格式
            if not zipfile.is_zipfile(zip_file):
                return False, "无效的插件ZIP文件", None

            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # 解压ZIP
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    # 安全检查: 防止路径遍历攻击
                    for member in zip_ref.namelist():
                        member_path = temp_path / member
                        if not str(member_path.resolve()).startswith(str(temp_path.resolve())):
                            return False, f"不安全的路径: {member}", None

                    zip_ref.extractall(temp_path)

                # 查找插件目录
                plugin_dir = self._find_plugin_directory(temp_path)

                if not plugin_dir:
                    return False, "无法找到插件目录结构", None

                # 读取metadata.json
                metadata_file = plugin_dir / "metadata.json"
                if not metadata_file.exists():
                    return False, "缺少metadata.json文件", None

                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                # 验证必需字段
                required_fields = ['name', 'slug', 'version']
                for field in required_fields:
                    if field not in metadata:
                        return False, f"缺少必需字段: {field}", None

                slug = metadata['slug']

                # 检查是否已安装
                existing_plugin_dir = self.plugins_dir / slug
                if existing_plugin_dir.exists():
                    return False, f"插件 '{slug}' 已安装", None

                # 依赖检查
                dependencies_result = self._check_dependencies(metadata)
                if not dependencies_result[0]:
                    return False, dependencies_result[1], None

                # 版本兼容性检查
                compatibility_result = self._check_compatibility(metadata)
                if not compatibility_result[0]:
                    return False, compatibility_result[1], None

                # 移动到插件目录
                target_dir = self.plugins_dir / slug
                shutil.copytree(plugin_dir, target_dir)

                return True, f"插件 '{metadata['name']}' 安装成功", metadata

        except zipfile.BadZipFile:
            return False, "损坏的ZIP文件", None
        except Exception as e:
            return False, f"安装失败: {str(e)}", None

    def _find_plugin_directory(self, extract_path: Path) -> Optional[Path]:
        """
        在解压目录中查找插件根目录
        
        Args:
            extract_path: 解压后的目录
            
        Returns:
            插件目录路径
        """
        # 检查是否有metadata.json
        if (extract_path / "metadata.json").exists():
            return extract_path

        # 查找包含metadata.json的子目录
        for item in extract_path.iterdir():
            if item.is_dir() and (item / "metadata.json").exists():
                return item

        return None

    def _check_dependencies(self, metadata: Dict[str, Any]) -> Tuple[bool, str]:
        """
        检查插件依赖
        
        Args:
            metadata: 插件元数据
            
        Returns:
            (满足标志, 消息)
        """
        try:
            plugin_slug = metadata.get('slug', '')
            result = plugin_dependency_manager.check_dependencies(
                plugin_slug,
                plugin_dependency_manager.discover_plugins() if hasattr(plugin_dependency_manager,
                                                                        'discover_plugins') else []
            )

            if not result.get("success"):
                missing = result.get("missing_dependencies", [])
                if missing:
                    missing_names = [dep['slug'] for dep in missing]
                    return False, f"缺少依赖: {', '.join(missing_names)}"
                return False, result.get("error", "依赖检查失败")

            return True, "依赖检查通过"
        except Exception as e:
            return False, f"依赖检查失败: {str(e)}"

    def _check_compatibility(self, metadata: Dict[str, Any]) -> Tuple[bool, str]:
        """
        检查插件兼容性
        
        Args:
            metadata: 插件元数据
            
        Returns:
            (兼容标志, 消息)
        """
        try:
            from pathlib import Path

            # 读取当前平台版本
            version_file = Path(__file__).parent.parent.parent / 'version.txt'
            platform_version = '0.0.1'
            if version_file.exists():
                with open(version_file, 'r') as f:
                    platform_version = f.read().strip()

            plugin_slug = metadata.get('slug', '')
            result = plugin_dependency_manager.validate_compatibility(plugin_slug, platform_version)

            if not result.get("compatible"):
                return False, result.get("message", "兼容性检查失败")

            return True, "兼容性检查通过"
        except Exception as e:
            return False, f"兼容性检查失败: {str(e)}"

    def uninstall_plugin(self, plugin_slug: str) -> Tuple[bool, str]:
        """
        卸载插件
        
        Args:
            plugin_slug: 插件slug
            
        Returns:
            (成功标志, 消息)
        """
        try:
            plugin_dir = self.plugins_dir / plugin_slug

            if not plugin_dir.exists():
                return False, f"插件 '{plugin_slug}' 未安装"

            # 删除插件目录
            shutil.rmtree(plugin_dir)

            return True, f"插件 '{plugin_slug}' 已卸载"

        except Exception as e:
            return False, f"卸载失败: {str(e)}"

    def activate_plugin(self, plugin_slug: str) -> Tuple[bool, str]:
        """
        激活插件
        
        Args:
            plugin_slug: 插件slug
            
        Returns:
            (成功标志, 消息)
        """
        try:
            from shared.models import Plugin
            from src.extensions import get_sync_db
            from datetime import datetime
            
            plugin_dir = self.plugins_dir / plugin_slug

            if not plugin_dir.exists():
                return False, f"插件 '{plugin_slug}' 未安装"

            # 检查主文件是否存在
            main_file = plugin_dir / "plugin.py"
            if not main_file.exists():
                return False, "插件主文件不存在"

            # 更新数据库中的激活状态
            for db_session in get_sync_db():
                plugin = db_session.query(Plugin).filter(Plugin.slug == plugin_slug).first()

                if not plugin:
                    # 如果数据库中不存在,创建记录
                    plugin = Plugin(
                        slug=plugin_slug,
                        name=plugin_slug,
                        version="1.0.0",
                        is_active=True,
                        is_installed=True,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    db_session.add(plugin)
                else:
                    # 更新现有记录
                    plugin.is_active = True
                    plugin.updated_at = datetime.now()

                db_session.commit()
                break

            return True, f"插件 '{plugin_slug}' 已激活"

        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"激活失败: {str(e)}"

    def deactivate_plugin(self, plugin_slug: str) -> Tuple[bool, str]:
        """
        停用插件
        
        Args:
            plugin_slug: 插件slug
            
        Returns:
            (成功标志, 消息)
        """
        try:
            from shared.models import Plugin
            from src.extensions import get_sync_db
            from datetime import datetime
            
            plugin_dir = self.plugins_dir / plugin_slug

            if not plugin_dir.exists():
                return False, f"插件 '{plugin_slug}' 未安装"

            # 更新数据库中的激活状态
            for db_session in get_sync_db():
                plugin = db_session.query(Plugin).filter(Plugin.slug == plugin_slug).first()

                if plugin:
                    plugin.is_active = False
                    plugin.updated_at = datetime.now()
                    db_session.commit()
                else:
                    # 如果数据库中不存在,说明从未激活过
                    pass

                break

            return True, f"插件 '{plugin_slug}' 已停用"

        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"停用失败: {str(e)}"

    def get_installed_plugins(self) -> List[Dict[str, Any]]:
        """
        获取已安装的插件列表
        
        Returns:
            插件信息列表
        """
        installed = []

        if not self.plugins_dir.exists():
            return installed

        for plugin_dir in self.plugins_dir.iterdir():
            if not plugin_dir.is_dir():
                continue

            metadata_file = plugin_dir / "metadata.json"
            if not metadata_file.exists():
                continue

            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                    metadata['path'] = str(plugin_dir)
                    metadata['slug'] = plugin_dir.name
                    metadata['is_installed'] = True

                    # 检查主文件
                    main_file = plugin_dir / "plugin.py"
                    metadata['has_main_file'] = main_file.exists()

                    installed.append(metadata)
            except Exception as e:
                print(f"读取插件元数据失败 {plugin_dir.name}: {e}")

        return installed

    def validate_plugin_structure(self, plugin_dir: Path) -> Tuple[bool, str]:
        """
        验证插件目录结构
        
        Args:
            plugin_dir: 插件目录路径
            
        Returns:
            (有效标志, 消息)
        """
        if not plugin_dir.exists():
            return False, "插件目录不存在"

        if not plugin_dir.is_dir():
            return False, "路径不是目录"

        # 检查必需文件
        required_files = ['metadata.json', 'plugin.py']
        for file in required_files:
            if not (plugin_dir / file).exists():
                return False, f"缺少必需文件: {file}"

        # 验证metadata.json格式
        try:
            with open(plugin_dir / 'metadata.json', 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            required_fields = ['name', 'slug', 'version']
            for field in required_fields:
                if field not in metadata:
                    return False, f"metadata.json缺少字段: {field}"

        except json.JSONDecodeError:
            return False, "metadata.json格式错误"

        return True, "插件结构验证通过"


# 全局实例
plugin_installer = PluginInstaller()
