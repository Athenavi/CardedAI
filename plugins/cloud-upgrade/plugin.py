"""
FastBlog Cloud 一键升级插件
提供安全的版本检测、自动更新、回滚机制和兼容性检查
"""

import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from zipfile import ZipFile

from shared.services.plugins.plugin_manager.core import BasePlugin, plugin_hooks


class CloudUpgradePlugin(BasePlugin):
    """
    FastBlog Cloud 一键升级插件

    功能:
    1. 版本检测和比较
    2. 升级流程编排 (10个步骤)
    3. 安全回滚机制
    4. 依赖兼容性检查
    5. 数据库迁移自动化
    6. 升级前健康检查
    7. 升级后验证测试
    8. 灰度发布支持
    9. 升级历史记录
    10. 通知和告警
    """

    def __init__(self):
        super().__init__(
            plugin_id=0,
            name="FastBlog Cloud Upgrade",
            slug="cloud-upgrade",
            version="1.0.0"
        )

        # 默认设置
        self.settings = {
            'enabled': True,

            # 更新源配置
            'update_sources': {
                'github': {
                    'enabled': True,
                    'repo': 'Athenavi/fast_blog',
                    'check_interval_hours': 24,
                },
                'local': {
                    'enabled': True,
                    'releases_dir': 'releases',
                },
                'custom_server': {
                    'enabled': False,
                    'url': '',
                    'api_key': '',
                }
            },

            # 升级策略
            'upgrade_policy': {
                'auto_check': True,
                'auto_download': False,
                'auto_install': False,
                'backup_before_upgrade': True,
                'auto_rollback_on_failure': True,
                'require_confirmation': True,
            },

            # 兼容性检查
            'compatibility_check': {
                'check_python_version': True,
                'min_python_version': '3.10.0',
                'check_dependencies': True,
                'check_database_schema': True,
                'check_plugins_compatibility': True,
            },

            # 健康检查
            'health_check': {
                'pre_upgrade': True,
                'post_upgrade': True,
                'check_services': ['postgresql', 'redis', 'nginx'],
                'check_api_endpoints': True,
                'check_disk_space': True,
                'min_disk_space_mb': 1024,
            },

            # 回滚配置
            'rollback': {
                'enabled': True,
                'max_rollback_versions': 3,
                'auto_cleanup_old_backups': True,
                'backup_retention_days': 30,
            },

            # 通知配置
            'notifications': {
                'on_update_available': True,
                'on_upgrade_start': True,
                'on_upgrade_success': True,
                'on_upgrade_failure': True,
                'on_rollback': True,
                'channels': ['email', 'webhook'],
            }
        }

        # 升级状态追踪
        self.upgrade_state = {
            'in_progress': False,
            'current_step': None,
            'total_steps': 10,
            'started_at': None,
            'target_version': None,
        }

        # 升级历史
        self.upgrade_history_file = Path("plugins_data") / "cloud-upgrade" / "history.json"
        self.upgrade_history_file.parent.mkdir(parents=True, exist_ok=True)

        # 加载升级历史
        self._load_upgrade_history()

        print("[CloudUpgrade] Plugin initialized")

    def register_hooks(self):
        """注册钩子"""
        # 定时检查更新
        if self.settings['upgrade_policy']['auto_check']:
            plugin_hooks.add_action(
                "daily_cleanup",
                self.check_for_updates,
                priority=5
            )

    def activate(self):
        """激活插件"""
        super().activate()
        print("[CloudUpgrade] Plugin activated")

    def deactivate(self):
        """停用插件"""
        super().deactivate()
        print("[CloudUpgrade] Plugin deactivated")

    def _load_upgrade_history(self):
        """加载升级历史"""
        if self.upgrade_history_file.exists():
            try:
                with open(self.upgrade_history_file, 'r') as f:
                    self.upgrade_history = json.load(f)
            except:
                self.upgrade_history = []
        else:
            self.upgrade_history = []

    def _save_upgrade_history(self):
        """保存升级历史"""
        try:
            with open(self.upgrade_history_file, 'w') as f:
                json.dump(self.upgrade_history, f, indent=2)
        except Exception as e:
            print(f"[CloudUpgrade] Failed to save history: {e}")

    async def check_for_updates(self) -> Dict[str, Any]:
        """
        检查可用更新

        Returns:
            更新信息
        """
        print("[CloudUpgrade] Checking for updates...")

        result = {
            'has_update': False,
            'current_version': self._get_current_version(),
            'available_versions': [],
            'recommended_version': None,
        }

        # 检查 GitHub
        if self.settings['update_sources']['github']['enabled']:
            github_update = await self._check_github_updates()
            if github_update:
                result['available_versions'].append(github_update)

        # 检查本地
        if self.settings['update_sources']['local']['enabled']:
            local_update = await self._check_local_updates()
            if local_update:
                result['available_versions'].append(local_update)

        # 检查自定义服务器
        if self.settings['update_sources']['custom_server']['enabled']:
            custom_update = await self._check_custom_server_updates()
            if custom_update:
                result['available_versions'].append(custom_update)

        # 确定是否有更新
        if result['available_versions']:
            # 按版本号排序
            result['available_versions'].sort(
                key=lambda x: self._parse_version(x['version']),
                reverse=True
            )

            result['has_update'] = True
            result['recommended_version'] = result['available_versions'][0]

        print(f"[CloudUpgrade] Update check complete: {len(result['available_versions'])} versions available")

        return result

    async def _check_github_updates(self) -> Optional[Dict[str, Any]]:
        """检查 GitHub 更新"""
        try:
            import aiohttp

            repo = self.settings['update_sources']['github']['repo']
            url = f"https://api.github.com/repos/{repo}/releases/latest"

            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'FastBlog-Upgrade-Checker'
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()

                        version = data.get('tag_name', '').lstrip('vV')
                        if version:
                            return {
                                'source': 'github',
                                'version': version,
                                'name': data.get('name', ''),
                                'published_at': data.get('published_at', ''),
                                'download_url': data.get('assets', [{}])[0].get('browser_download_url', ''),
                                'description': data.get('body', ''),
                                'html_url': data.get('html_url', ''),
                            }

        except Exception as e:
            print(f"[CloudUpgrade] GitHub update check failed: {e}")

        return None

    async def _check_local_updates(self) -> Optional[Dict[str, Any]]:
        """检查本地更新"""
        try:
            releases_dir = Path(self.settings['update_sources']['local']['releases_dir'])

            if not releases_dir.exists():
                return None

            update_packages = list(releases_dir.glob("update_*.zip"))

            if not update_packages:
                return None

            # 按文件名排序，获取最新版本
            update_packages.sort(key=lambda x: x.name, reverse=True)
            latest_package = update_packages[0]

            version = latest_package.stem.replace('update_', '')

            return {
                'source': 'local',
                'version': version,
                'file_path': str(latest_package),
                'size_bytes': latest_package.stat().st_size,
                'created_at': datetime.fromtimestamp(latest_package.stat().st_ctime).isoformat(),
            }

        except Exception as e:
            print(f"[CloudUpgrade] Local update check failed: {e}")

        return None

    async def _check_custom_server_updates(self) -> Optional[Dict[str, Any]]:
        """检查自定义服务器更新"""
        try:
            import aiohttp
        except ImportError:
            print("[CloudUpgrade] aiohttp not installed, custom server check unavailable")
            return None

        custom_cfg = self.settings.get('update_sources', {}).get('custom_server', {})
        server_url = custom_cfg.get('url', '')
        api_key = custom_cfg.get('api_key', '')

        if not server_url:
            return None

        try:
            headers = {'Content-Type': 'application/json'}
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{server_url.rstrip('/')}/api/version",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            'version': data.get('version', ''),
                            'download_url': data.get('download_url', ''),
                            'changelog': data.get('changelog', ''),
                            'source': 'custom_server',
                        }
                    else:
                        print(f"[CloudUpgrade] Custom server returned status {resp.status}")
                        return None
        except Exception as e:
            print(f"[CloudUpgrade] Custom server check failed: {e}")
            return None

    async def start_upgrade(
            self,
            version: str,
            source: str = 'github',
            backup_before: bool = None,
            auto_rollback: bool = None
    ) -> Dict[str, Any]:
        """
        开始升级流程

        Args:
            version: 目标版本号
            source: 更新源 (github/local/custom)
            backup_before: 升级前备份
            auto_rollback: 失败时自动回滚

        Returns:
            升级结果
        """
        if self.upgrade_state['in_progress']:
            return {
                'success': False,
                'error': 'Upgrade already in progress'
            }

        # 使用配置的默认值
        if backup_before is None:
            backup_before = self.settings['upgrade_policy']['backup_before_upgrade']

        if auto_rollback is None:
            auto_rollback = self.settings['upgrade_policy']['auto_rollback_on_failure']

        # 更新状态
        self.upgrade_state['in_progress'] = True
        self.upgrade_state['target_version'] = version
        self.upgrade_state['started_at'] = datetime.now().isoformat()

        result = {
            'success': False,
            'version': version,
            'source': source,
            'steps': [],
            'started_at': self.upgrade_state['started_at'],
        }

        try:
            # Step 1: 升级前健康检查
            step1 = await self._step_pre_upgrade_health_check()
            result['steps'].append(step1)
            if not step1['success']:
                raise Exception(f"Pre-upgrade health check failed: {step1.get('error')}")

            # Step 2: 创建备份
            if backup_before:
                step2 = await self._step_create_backup(version)
                result['steps'].append(step2)
                if not step2['success']:
                    raise Exception(f"Backup failed: {step2.get('error')}")

            # Step 3: 下载更新包
            step3 = await self._step_download_package(version, source)
            result['steps'].append(step3)
            if not step3['success']:
                raise Exception(f"Download failed: {step3.get('error')}")

            # Step 4: 验证完整性
            step4 = await self._step_verify_integrity(step3['package_path'])
            result['steps'].append(step4)
            if not step4['success']:
                raise Exception(f"Verification failed: {step4.get('error')}")

            # Step 5: 兼容性检查
            step5 = await self._step_compatibility_check(version)
            result['steps'].append(step5)
            if not step5['success']:
                raise Exception(f"Compatibility check failed: {step5.get('error')}")

            # Step 6: 停止服务
            step6 = await self._step_stop_services()
            result['steps'].append(step6)
            if not step6['success']:
                raise Exception(f"Stop services failed: {step6.get('error')}")

            # Step 7: 应用更新
            step7 = await self._step_apply_updates(step3['package_path'])
            result['steps'].append(step7)
            if not step7['success']:
                raise Exception(f"Apply updates failed: {step7.get('error')}")

            # Step 8: 数据库迁移
            step8 = await self._step_run_migrations()
            result['steps'].append(step8)
            if not step8['success']:
                raise Exception(f"Database migration failed: {step8.get('error')}")

            # Step 9: 启动服务
            step9 = await self._step_start_services()
            result['steps'].append(step9)
            if not step9['success']:
                raise Exception(f"Start services failed: {step9.get('error')}")

            # Step 10: 升级后验证
            step10 = await self._step_post_upgrade_verify(version)
            result['steps'].append(step10)
            if not step10['success']:
                raise Exception(f"Post-upgrade verification failed: {step10.get('error')}")

            # 升级成功
            result['success'] = True
            result['completed_at'] = datetime.now().isoformat()
            result['duration_seconds'] = (
                    datetime.fromisoformat(result['completed_at']) -
                    datetime.fromisoformat(result['started_at'])
            ).total_seconds()

            # 记录历史
            self._record_upgrade_history(result)

            # 发送成功通知
            await self._send_notification('upgrade_success', result)

            print(f"[CloudUpgrade] Upgrade to {version} completed successfully")

        except Exception as e:
            result['error'] = str(e)
            result['completed_at'] = datetime.now().isoformat()

            # 自动回滚
            if auto_rollback:
                print(f"[CloudUpgrade] Upgrade failed, attempting rollback...")
                rollback_result = await self.rollback_upgrade()
                result['rollback'] = rollback_result

            # 记录失败历史
            self._record_upgrade_history(result)

            # 发送失败通知
            await self._send_notification('upgrade_failure', result)

            print(f"[CloudUpgrade] Upgrade failed: {e}")

        finally:
            # 重置状态
            self.upgrade_state['in_progress'] = False
            self.upgrade_state['current_step'] = None

        return result

    async def _step_pre_upgrade_health_check(self) -> Dict[str, Any]:
        """Step 1: 升级前健康检查"""
        print("[CloudUpgrade] Step 1: Pre-upgrade health check")

        checks = {
            'disk_space': await self._check_disk_space(),
            'services': await self._check_services(),
            'database': await self._check_database(),
            'api_endpoints': await self._check_api_endpoints(),
        }

        all_passed = all(check['passed'] for check in checks.values())

        return {
            'step': 1,
            'name': 'Pre-upgrade health check',
            'success': all_passed,
            'checks': checks,
        }

    async def _step_create_backup(self, version: str) -> Dict[str, Any]:
        """Step 2: 创建备份"""
        print(f"[CloudUpgrade] Step 2: Creating backup before upgrade to {version}")

        try:
            backup_dir = Path("backups") / "upgrade" / f"before_{version}_{int(time.time())}"
            backup_dir.mkdir(parents=True, exist_ok=True)

            # 备份关键目录
            dirs_to_backup = [
                'src/',
                'shared/',
                'config/',
                'plugins/',
                '.env',
            ]

            for dir_path in dirs_to_backup:
                src = Path(dir_path)
                if src.exists():
                    dst = backup_dir / dir_path.replace('/', '_').rstrip('_')
                    if src.is_file():
                        shutil.copy2(src, dst)
                    else:
                        shutil.copytree(src, dst, dirs_exist_ok=True)

            # 备份数据库
            await self._backup_database(backup_dir)

            # 保存备份信息
            backup_info = {
                'version': self._get_current_version(),
                'target_version': version,
                'backup_path': str(backup_dir),
                'created_at': datetime.now().isoformat(),
            }

            with open(backup_dir / 'backup_info.json', 'w') as f:
                json.dump(backup_info, f, indent=2)

            return {
                'step': 2,
                'name': 'Create backup',
                'success': True,
                'backup_path': str(backup_dir),
            }

        except Exception as e:
            return {
                'step': 2,
                'name': 'Create backup',
                'success': False,
                'error': str(e),
            }

    async def _step_download_package(self, version: str, source: str) -> Dict[str, Any]:
        """Step 3: 下载更新包"""
        print(f"[CloudUpgrade] Step 3: Downloading update package {version} from {source}")

        try:
            if source == 'local':
                # 从本地查找
                releases_dir = Path(self.settings['update_sources']['local']['releases_dir'])
                package_path = releases_dir / f"update_{version}.zip"

                if not package_path.exists():
                    return {
                        'step': 3,
                        'name': 'Download package',
                        'success': False,
                        'error': f'Package not found: {package_path}',
                    }

                return {
                    'step': 3,
                    'name': 'Download package',
                    'success': True,
                    'package_path': str(package_path),
                    'source': 'local',
                }

            elif source == 'github':
                # 从 GitHub 下载
                import aiohttp

                repo = self.settings['update_sources']['github']['repo']
                url = f"https://api.github.com/repos/{repo}/releases/tags/v{version}"

                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status != 200:
                            return {
                                'step': 3,
                                'name': 'Download package',
                                'success': False,
                                'error': f'GitHub API error: {response.status}',
                            }

                        data = await response.json()
                        assets = data.get('assets', [])

                        if not assets:
                            return {
                                'step': 3,
                                'name': 'Download package',
                                'success': False,
                                'error': 'No assets found in release',
                            }

                        download_url = assets[0]['browser_download_url']

                        # 下载到 releases 目录
                        releases_dir = Path('releases')
                        releases_dir.mkdir(exist_ok=True)
                        package_path = releases_dir / f"update_{version}.zip"

                        async with session.get(download_url) as dl_response:
                            with open(package_path, 'wb') as f:
                                async for chunk in dl_response.content.iter_chunked(8192):
                                    f.write(chunk)

                return {
                    'step': 3,
                    'name': 'Download package',
                    'success': True,
                    'package_path': str(package_path),
                    'source': 'github',
                }

            else:
                return {
                    'step': 3,
                    'name': 'Download package',
                    'success': False,
                    'error': f'Unsupported source: {source}',
                }

        except Exception as e:
            return {
                'step': 3,
                'name': 'Download package',
                'success': False,
                'error': str(e),
            }

    async def _step_verify_integrity(self, package_path: str) -> Dict[str, Any]:
        """Step 4: 验证完整性"""
        print(f"[CloudUpgrade] Step 4: Verifying package integrity")

        try:
            package = Path(package_path)

            if not package.exists():
                return {
                    'step': 4,
                    'name': 'Verify integrity',
                    'success': False,
                    'error': 'Package file not found',
                }

            # 检查文件大小
            if package.stat().st_size < 1024:
                return {
                    'step': 4,
                    'name': 'Verify integrity',
                    'success': False,
                    'error': 'Package file too small',
                }

            # 测试 ZIP 完整性
            with ZipFile(package, 'r') as zip_ref:
                bad_file = zip_ref.testzip()
                if bad_file is not None:
                    return {
                        'step': 4,
                        'name': 'Verify integrity',
                        'success': False,
                        'error': f'Corrupted file in archive: {bad_file}',
                    }

            return {
                'step': 4,
                'name': 'Verify integrity',
                'success': True,
            }

        except Exception as e:
            return {
                'step': 4,
                'name': 'Verify integrity',
                'success': False,
                'error': str(e),
            }

    async def _step_compatibility_check(self, version: str) -> Dict[str, Any]:
        """Step 5: 兼容性检查"""
        print(f"[CloudUpgrade] Step 5: Running compatibility checks")

        checks = {}

        # 检查 Python 版本
        if self.settings['compatibility_check']['check_python_version']:
            min_version = self.settings['compatibility_check']['min_python_version']
            current_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

            checks['python_version'] = {
                'passed': self._compare_versions(current_version, min_version) >= 0,
                'current': current_version,
                'required': min_version,
            }

        # 检查依赖
        if self.settings['compatibility_check']['check_dependencies']:
            checks['dependencies'] = await self._check_dependencies()

        # 检查数据库 schema
        if self.settings['compatibility_check']['check_database_schema']:
            checks['database_schema'] = await self._check_database_schema()

        # 检查插件兼容性
        if self.settings['compatibility_check']['check_plugins_compatibility']:
            checks['plugins'] = await self._check_plugins_compatibility(version)

        all_passed = all(check.get('passed', True) for check in checks.values())

        return {
            'step': 5,
            'name': 'Compatibility check',
            'success': all_passed,
            'checks': checks,
        }

    async def _step_stop_services(self) -> Dict[str, Any]:
        """Step 6: 停止服务"""
        print("[CloudUpgrade] Step 6: Stopping services")

        try:
            # 停止 Web 服务
            # 这里需要根据实际部署方式调整
            subprocess.run(['systemctl', 'stop', 'fastblog'], timeout=30)

            return {
                'step': 6,
                'name': 'Stop services',
                'success': True,
            }

        except Exception as e:
            return {
                'step': 6,
                'name': 'Stop services',
                'success': False,
                'error': str(e),
            }

    async def _step_apply_updates(self, package_path: str) -> Dict[str, Any]:
        """Step 7: 应用更新"""
        print(f"[CloudUpgrade] Step 7: Applying updates")

        try:
            temp_dir = Path(tempfile.mkdtemp(prefix='upgrade_'))

            # 解压更新包
            with ZipFile(package_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # 复制文件到目标位置
            # 这里需要根据实际的目录结构调整
            for item in temp_dir.iterdir():
                if item.is_dir():
                    dst = Path(item.name)
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(item, dst)
                else:
                    shutil.copy2(item, Path(item.name))

            # 清理临时目录
            shutil.rmtree(temp_dir)

            return {
                'step': 7,
                'name': 'Apply updates',
                'success': True,
            }

        except Exception as e:
            return {
                'step': 7,
                'name': 'Apply updates',
                'success': False,
                'error': str(e),
            }

    async def _step_run_migrations(self) -> Dict[str, Any]:
        """Step 8: 数据库迁移"""
        print("[CloudUpgrade] Step 8: Running database migrations")

        try:
            # 运行 Alembic 迁移
            result = subprocess.run(
                [sys.executable, '-m', 'alembic', 'upgrade', 'head'],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                return {
                    'step': 8,
                    'name': 'Run migrations',
                    'success': True,
                    'output': result.stdout,
                }
            else:
                return {
                    'step': 8,
                    'name': 'Run migrations',
                    'success': False,
                    'error': result.stderr,
                }

        except Exception as e:
            return {
                'step': 8,
                'name': 'Run migrations',
                'success': False,
                'error': str(e),
            }

    async def _step_start_services(self) -> Dict[str, Any]:
        """Step 9: 启动服务"""
        print("[CloudUpgrade] Step 9: Starting services")

        try:
            # 启动 Web 服务
            subprocess.run(['systemctl', 'start', 'fastblog'], timeout=30)

            # 等待服务启动
            await asyncio.sleep(5)

            return {
                'step': 9,
                'name': 'Start services',
                'success': True,
            }

        except Exception as e:
            return {
                'step': 9,
                'name': 'Start services',
                'success': False,
                'error': str(e),
            }

    async def _step_post_upgrade_verify(self, version: str) -> Dict[str, Any]:
        """Step 10: 升级后验证"""
        print(f"[CloudUpgrade] Step 10: Post-upgrade verification")

        checks = {
            'version': await self._verify_version(version),
            'services': await self._check_services(),
            'api_endpoints': await self._check_api_endpoints(),
            'database': await self._check_database(),
        }

        all_passed = all(check['passed'] for check in checks.values())

        return {
            'step': 10,
            'name': 'Post-upgrade verification',
            'success': all_passed,
            'checks': checks,
        }

    async def rollback_upgrade(self) -> Dict[str, Any]:
        """回滚升级"""
        print("[CloudUpgrade] Rolling back upgrade...")

        try:
            # 找到最新的备份
            backup_dir = Path("backups") / "upgrade"

            if not backup_dir.exists():
                return {
                    'success': False,
                    'error': 'No backup found for rollback',
                }

            # 获取最新的备份
            backups = sorted(backup_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)

            if not backups:
                return {
                    'success': False,
                    'error': 'No backup found for rollback',
                }

            latest_backup = backups[0]

            # 停止服务
            subprocess.run(['systemctl', 'stop', 'fastblog'], timeout=30)

            # 恢复文件
            backup_info_file = latest_backup / 'backup_info.json'
            if backup_info_file.exists():
                with open(backup_info_file, 'r') as f:
                    backup_info = json.load(f)

                # 恢复各个目录
                for item in latest_backup.iterdir():
                    if item.name == 'backup_info.json':
                        continue

                    dst_name = item.name.replace('_', '/')
                    dst = Path(dst_name)

                    if item.is_file():
                        shutil.copy2(item, dst)
                    else:
                        if dst.exists():
                            shutil.rmtree(dst)
                        shutil.copytree(item, dst)

            # 恢复数据库
            await self._restore_database(latest_backup)

            # 启动服务
            subprocess.run(['systemctl', 'start', 'fastblog'], timeout=30)

            return {
                'success': True,
                'message': 'Rollback completed successfully',
                'backup_used': str(latest_backup),
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }

    # 辅助方法

    def _get_current_version(self) -> str:
        """获取当前版本"""
        try:
            from shared.utils.version_manager import version_manager
            backend_info = version_manager.get_backend_version()
            return backend_info.get('version', '0.0.0')
        except:
            return '0.0.0'

    def _parse_version(self, version_str: str) -> List[int]:
        """解析版本号"""
        try:
            version_str = version_str.lstrip('vV')
            parts = version_str.split('.')
            return [int(p) for p in parts if p.isdigit()]
        except:
            return [0, 0, 0]

    def _compare_versions(self, v1: str, v2: str) -> int:
        """比较版本号"""
        p1 = self._parse_version(v1)
        p2 = self._parse_version(v2)

        for a, b in zip(p1, p2):
            if a > b:
                return 1
            elif a < b:
                return -1

        return 0

    async def _check_disk_space(self) -> Dict[str, Any]:
        """检查磁盘空间"""
        try:
            import shutil

            total, used, free = shutil.disk_usage('/')
            free_mb = free / (1024 * 1024)
            min_required = self.settings['health_check']['min_disk_space_mb']

            return {
                'passed': free_mb >= min_required,
                'free_mb': round(free_mb, 2),
                'required_mb': min_required,
            }
        except:
            return {'passed': False, 'error': 'Failed to check disk space'}

    async def _check_services(self) -> Dict[str, Any]:
        """检查服务状态"""
        services = self.settings['health_check']['check_services']
        results = {}

        for service in services:
            try:
                result = subprocess.run(
                    ['systemctl', 'is-active', service],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                results[service] = result.stdout.strip() == 'active'
            except:
                results[service] = False

        return {
            'passed': all(results.values()),
            'services': results,
        }

    async def _check_database(self) -> Dict[str, Any]:
        """检查数据库连接"""
        try:
            # 简单的数据库连接测试
            import subprocess
            result = subprocess.run(
                ['pg_isready'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return {'passed': result.returncode == 0}
        except:
            return {'passed': False}

    async def _check_api_endpoints(self) -> Dict[str, Any]:
        """检查 API 端点"""
        try:
            import aiohttp
        except ImportError:
            return {'passed': True, 'skipped': True, 'reason': 'aiohttp not installed'}

        base_url = os.getenv('FASTBLOG_BASE_URL', 'http://127.0.0.1:8000')
        endpoints = ['/api/v1/health', '/api/v1/articles', '/api/v1/auth/me']
        results = {}

        try:
            async with aiohttp.ClientSession() as session:
                for endpoint in endpoints:
                    url = f"{base_url.rstrip('/')}{endpoint}"
                    try:
                        async with session.get(
                            url, timeout=aiohttp.ClientTimeout(total=10)
                        ) as resp:
                            # 2xx 或 401 (未认证但服务正常) 都算通过
                            results[endpoint] = resp.status in (200, 201, 204, 401, 403)
                    except Exception as e:
                        results[endpoint] = False

            all_passed = all(results.values())
            return {
                'passed': all_passed,
                'endpoints': results,
            }
        except Exception as e:
            return {'passed': False, 'error': str(e)}

    async def _check_dependencies(self) -> Dict[str, Any]:
        """检查依赖"""
        import importlib

        req_file = Path('requirements.txt')
        if not req_file.exists():
            return {'passed': True, 'skipped': True, 'reason': 'requirements.txt not found'}

        missing = []
        installed = []
        try:
            with open(req_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or line.startswith('-'):
                        continue
                    # 提取包名（去除版本约束）
                    pkg_name = \
                    line.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].split('!=')[0].split('[')[
                        0].strip()
                    try:
                        importlib.import_module(pkg_name.replace('-', '_'))
                        installed.append(pkg_name)
                    except ImportError:
                        missing.append(pkg_name)

            return {
                'passed': len(missing) == 0,
                'installed': len(installed),
                'missing': missing,
            }
        except Exception as e:
            return {'passed': False, 'error': str(e)}

    async def _check_database_schema(self) -> Dict[str, Any]:
        """检查数据库 schema"""
        try:
            alembic_ini = Path('alembic.ini')
            if not alembic_ini.exists():
                return {'passed': True, 'skipped': True, 'reason': 'alembic.ini not found'}

            result = subprocess.run(
                ['alembic', 'current'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return {
                    'passed': False,
                    'error': result.stderr.strip(),
                }

            # 检查是否有待执行的迁移
            head_result = subprocess.run(
                ['alembic', 'heads'],
                capture_output=True,
                text=True,
                timeout=15
            )

            current_rev = result.stdout.strip().split('\n')[0] if result.stdout.strip() else ''
            head_rev = head_result.stdout.strip().split('\n')[0] if head_result.stdout.strip() else ''

            is_current = (current_rev == head_rev) if (current_rev and head_rev) else True

            return {
                'passed': is_current,
                'current_revision': current_rev,
                'head_revision': head_rev,
                'needs_migration': not is_current,
            }
        except FileNotFoundError:
            return {'passed': True, 'skipped': True, 'reason': 'alembic command not found'}
        except Exception as e:
            return {'passed': False, 'error': str(e)}

    async def _check_plugins_compatibility(self, version: str) -> Dict[str, Any]:
        """检查插件兼容性"""
        incompatible = []
        checked = []

        try:
            plugins_dir = Path('plugins')
            if not plugins_dir.exists():
                return {'passed': True, 'skipped': True, 'reason': 'plugins directory not found'}

            target_parts = version.lstrip('v').split('.')
            target_major = int(target_parts[0]) if target_parts else 0

            for plugin_dir in plugins_dir.iterdir():
                if not plugin_dir.is_dir():
                    continue

                # 检查 plugin.json 元数据
                meta_file = plugin_dir / 'plugin.json'
                if not meta_file.exists():
                    continue

                try:
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        meta = json.load(f)

                    plugin_name = meta.get('name', plugin_dir.name)
                    min_fastblog = meta.get('min_fastblog_version', '')
                    max_fastblog = meta.get('max_fastblog_version', '')

                    checked.append(plugin_name)

                    if min_fastblog:
                        min_parts = min_fastblog.lstrip('v').split('.')
                        min_major = int(min_parts[0]) if min_parts else 0
                        if target_major < min_major:
                            incompatible.append({
                                'plugin': plugin_name,
                                'reason': f'requires min version {min_fastblog}'
                            })
                            continue

                    if max_fastblog:
                        max_parts = max_fastblog.lstrip('v').split('.')
                        max_major = int(max_parts[0]) if max_parts else 999
                        if target_major > max_major:
                            incompatible.append({
                                'plugin': plugin_name,
                                'reason': f'supports max version {max_fastblog}'
                            })

                except (json.JSONDecodeError, ValueError):
                    continue

            return {
                'passed': len(incompatible) == 0,
                'checked': checked,
                'incompatible': incompatible,
            }
        except Exception as e:
            return {'passed': False, 'error': str(e)}

    async def _backup_database(self, backup_dir: Path):
        """备份数据库"""
        try:
            dump_file = backup_dir / 'database.sql'

            cmd = [
                'pg_dump',
                '-h', os.getenv('DB_HOST', 'localhost'),
                '-p', os.getenv('DB_PORT', '5432'),
                '-U', os.getenv('DB_USER', 'postgres'),
                '-d', os.getenv('DB_NAME', 'fast_blog'),
                '-f', str(dump_file),
            ]

            env = os.environ.copy()
            env['PGPASSWORD'] = os.getenv('DB_PASSWORD', '')

            subprocess.run(cmd, env=env, timeout=300)
        except Exception as e:
            print(f"[CloudUpgrade] Database backup failed: {e}")

    async def _restore_database(self, backup_dir: Path):
        """恢复数据库"""
        try:
            dump_file = backup_dir / 'database.sql'

            if not dump_file.exists():
                return

            cmd = [
                'psql',
                '-h', os.getenv('DB_HOST', 'localhost'),
                '-p', os.getenv('DB_PORT', '5432'),
                '-U', os.getenv('DB_USER', 'postgres'),
                '-d', os.getenv('DB_NAME', 'fast_blog'),
                '-f', str(dump_file),
            ]

            env = os.environ.copy()
            env['PGPASSWORD'] = os.getenv('DB_PASSWORD', '')

            subprocess.run(cmd, env=env, timeout=300)
        except Exception as e:
            print(f"[CloudUpgrade] Database restore failed: {e}")

    async def _verify_version(self, expected_version: str) -> Dict[str, Any]:
        """验证版本"""
        current = self._get_current_version()
        return {
            'passed': current == expected_version,
            'expected': expected_version,
            'actual': current,
        }

    def _record_upgrade_history(self, result: Dict[str, Any]):
        """记录升级历史"""
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'from_version': self._get_current_version(),
            'to_version': result.get('version'),
            'success': result.get('success', False),
            'duration_seconds': result.get('duration_seconds'),
            'error': result.get('error'),
            'steps': len(result.get('steps', [])),
        }

        self.upgrade_history.append(history_entry)

        # 限制历史记录数量
        if len(self.upgrade_history) > 100:
            self.upgrade_history = self.upgrade_history[-100:]

        self._save_upgrade_history()

    async def _send_notification(self, event_type: str, data: Dict[str, Any]):
        """发送通知"""
        channels = self.settings['notifications']['channels']

        message = f"[Upgrade] {event_type}: {data.get('version', 'unknown')}"

        if 'email' in channels:
            await self._send_email_notification(event_type, data)

        if 'webhook' in channels:
            await self._send_webhook_notification(event_type, data)

    async def _send_email_notification(self, event_type: str, data: Dict[str, Any]):
        """发送邮件通知"""
        try:
            from shared.services.notifications.email_service import EmailService

            email_service = EmailService()

            # 构建邮件主题和内容
            status_icons = {
                'upgrade_started': '🚀',
                'upgrade_completed': '✅',
                'upgrade_failed': '❌',
                'rollback_started': '⏪',
                'rollback_completed': '✅',
                'backup_completed': '💾'
            }
            icon = status_icons.get(event_type, 'ℹ️')

            subject = f'[FastBlog] 升级 {icon} {event_type}'
            html_content = f"""
            <h2>{icon} 系统升级通知 - {event_type}</h2>
            <p><strong>版本:</strong> {data.get('version', 'N/A')}</p>
            <p><strong>事件类型:</strong> {event_type}</p>
            """

            if 'message' in data:
                html_content += f"<p><strong>消息:</strong> {data['message']}</p>"

            if 'duration' in data:
                html_content += f"<p><strong>耗时:</strong> {data['duration']:.2f} 秒</p>"

            html_content += f"""
            <p><strong>详细信息:</strong></p>
            <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px;">{json.dumps(data, indent=2, ensure_ascii=False)}</pre>
            <p><strong>时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            """

            # 获取收件人邮箱
            to_email = os.getenv('ADMIN_EMAIL', '')
            if not to_email:
                print("[CloudUpgrade] Admin email not configured, skipping email notification")
                return

            # 发送邮件
            success = email_service.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content
            )

            if success:
                print(f"[CloudUpgrade] Email notification sent to {to_email}")
            else:
                print(f"[CloudUpgrade] Failed to send email notification")

        except Exception as e:
            print(f"[CloudUpgrade] Email notification error: {e}")

    async def _send_webhook_notification(self, event_type: str, data: Dict[str, Any]):
        """发送 Webhook 通知"""
        webhook_url = self.settings['notifications'].get('webhook_url', '')

        if not webhook_url:
            print("[CloudUpgrade] Webhook URL not configured")
            return

        import aiohttp

        payload = {
            'service': 'cloud-upgrade',
            'event': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        print(f"[CloudUpgrade] Webhook notification sent successfully")
                    else:
                        print(f"[CloudUpgrade] Webhook returned status {response.status}")
        except Exception as e:
            print(f"[CloudUpgrade] Webhook notification failed: {e}")

    def get_upgrade_status(self) -> Dict[str, Any]:
        """获取升级状态"""
        return {
            'in_progress': self.upgrade_state['in_progress'],
            'current_step': self.upgrade_state['current_step'],
            'target_version': self.upgrade_state['target_version'],
            'started_at': self.upgrade_state['started_at'],
        }

    def get_upgrade_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取升级历史"""
        return self.upgrade_history[-limit:]

    def get_settings_ui(self) -> Dict[str, Any]:
        """返回设置界面配置"""
        return {
            'fields': [
                {
                    'key': 'upgrade_policy.auto_check',
                    'type': 'boolean',
                    'label': '自动检查更新',
                },
                {
                    'key': 'upgrade_policy.backup_before_upgrade',
                    'type': 'boolean',
                    'label': '升级前自动备份',
                },
                {
                    'key': 'upgrade_policy.auto_rollback_on_failure',
                    'type': 'boolean',
                    'label': '失败时自动回滚',
                },
                {
                    'key': 'upgrade_policy.require_confirmation',
                    'type': 'boolean',
                    'label': '需要确认',
                },
            ],
            'actions': [
                {
                    'type': 'button',
                    'label': '检查更新',
                    'action': 'check_updates',
                    'variant': 'outline',
                },
                {
                    'type': 'button',
                    'label': '查看升级历史',
                    'action': 'view_history',
                    'variant': 'default',
                },
            ]
        }


# 全局实例
plugin = CloudUpgradePlugin()
