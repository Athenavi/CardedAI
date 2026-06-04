"""
前后端分离版本管理模块
支持分别管理前端和后端版本信息
"""
import configparser
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any


class VersionManager:
    """版本管理器"""

    def __init__(self, version_file_path: Optional[str] = None):
        """初始化版本管理器"""
        if version_file_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.version_file = Path(base_dir) / 'version.txt'
        else:
            self.version_file = Path(version_file_path)

        self.config = configparser.ConfigParser()
        self._load_version_config()

    def _load_version_config(self):
        """加载版本配置文件"""
        if self.version_file.exists():
            self.config.read(self.version_file, encoding='utf-8')
        else:
            # 创建默认配置
            self._create_default_config()

    def _create_default_config(self):
        """创建默认版本配置"""
        self.config['FRONTEND'] = {
            'version': '0.1.0',
            'build_time': datetime.now().isoformat(),
            'framework': 'Next.js 16.1.6',
            'node_version': '18.x'
        }

        self.config['BACKEND'] = {
            'version': 'V0.0.0.2',
            'build_time': datetime.now().isoformat(),
            'framework': 'FastAPI 0.128.0',
            'python_version': '3.8+'
        }

        self.config['DATABASE'] = {
            'version': '1.0.0',
            'migration_status': 'up_to_date'
        }

        self.config['AUTHOR'] = {
            'maintainer': 'Athenavi',
            'repository': 'https://github.com/Athenavi/fast-blog'
        }

        self.save_config()

    def save_config(self):
        """保存配置到文件"""
        with open(self.version_file, 'w', encoding='utf-8') as f:
            self.config.write(f)

    def get_frontend_version(self) -> Dict[str, Any]:
        """获取前端版本信息"""
        if 'FRONTEND' not in self.config:
            return {}

        return dict(self.config['FRONTEND'])

    def get_backend_version(self) -> Dict[str, Any]:
        """获取后端版本信息"""
        if 'BACKEND' not in self.config:
            return {}

        return dict(self.config['BACKEND'])

    def get_database_version(self) -> Dict[str, Any]:
        """获取数据库版本信息"""
        if 'DATABASE' not in self.config:
            return {}

        return dict(self.config['DATABASE'])

    def get_author_info(self) -> Dict[str, Any]:
        """获取作者信息"""
        if 'AUTHOR' not in self.config:
            return {}

        return dict(self.config['AUTHOR'])

    def get_all_versions(self) -> Dict[str, Dict[str, Any]]:
        """获取所有组件的版本信息"""
        return {
            'frontend': self.get_frontend_version(),
            'backend': self.get_backend_version(),
            'database': self.get_database_version(),
            'author': self.get_author_info()
        }

    def update_frontend_version(self, version: str, **kwargs):
        """更新前端版本"""
        if 'FRONTEND' not in self.config:
            self.config['FRONTEND'] = {}

        self.config['FRONTEND']['version'] = version
        self.config['FRONTEND']['build_time'] = datetime.now().isoformat()

        # 更新其他可选字段
        for key, value in kwargs.items():
            self.config['FRONTEND'][key] = str(value)

        self.save_config()

    def update_backend_version(self, version: str, **kwargs):
        """更新后端版本"""
        if 'BACKEND' not in self.config:
            self.config['BACKEND'] = {}

        self.config['BACKEND']['version'] = version
        self.config['BACKEND']['build_time'] = datetime.now().isoformat()

        # 更新其他可选字段
        for key, value in kwargs.items():
            self.config['BACKEND'][key] = str(value)

        self.save_config()

    def update_database_version(self, version: str, migration_status: str = 'up_to_date'):
        """更新数据库版本"""
        if 'DATABASE' not in self.config:
            self.config['DATABASE'] = {}

        self.config['DATABASE']['version'] = version
        self.config['DATABASE']['migration_status'] = migration_status
        self.save_config()

    def get_frontend_package_version(self) -> str:
        """从前端package.json获取版本号"""
        frontend_dir = Path(__file__).parent.parent / 'frontend-next'
        package_json = frontend_dir / 'package.json'

        if package_json.exists():
            try:
                with open(package_json, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                    return package_data.get('version', 'unknown')
            except Exception:
                return 'unknown'
        return 'unknown'

    def sync_frontend_version(self):
        """同步前端package.json版本到配置文件"""
        package_version = self.get_frontend_package_version()
        if package_version != 'unknown':
            self.update_frontend_version(
                package_version,
                framework='Next.js 16.1.6',
                node_version='18.x'
            )
        return package_version


# 全局版本管理器实例
version_manager = VersionManager()


def get_current_version_info() -> Dict[str, Any]:
    """获取当前版本信息的便捷函数"""
    return version_manager.get_all_versions()


def get_version_summary() -> Dict[str, str]:
    """获取简洁的版本摘要"""
    versions = version_manager.get_all_versions()
    return {
        'frontend': versions['frontend'].get('version', 'unknown'),
        'backend': versions['backend'].get('version', 'unknown'),
        'database': versions['database'].get('version', 'unknown'),
        'build_time': datetime.now().isoformat()
    }


if __name__ == '__main__':
    # 测试版本管理功能
    vm = VersionManager()

    print("=== 当前版本信息 ===")
    all_versions = vm.get_all_versions()
    for component, info in all_versions.items():
        print(f"\n{component.upper()}:")
        for key, value in info.items():
            print(f"  {key}: {value}")

    print("\n=== 版本摘要 ===")
    summary = get_version_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # 同步前端版本
    print(f"\n同步前端版本: {vm.sync_frontend_version()}")
