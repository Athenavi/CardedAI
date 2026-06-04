#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
备份管理模块 - 增强版
管理系统备份、数据库备份、自动调度和云存储集成
"""

import hashlib
import json

import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from src.unified_logger import default_logger as logger


class BackupManager:
    """备份管理器（增强版）
    
    功能:
    1. 自动定时备份
    2. 增量备份支持
    3. 云存储集成 (S3/OSS)
    4. 备份验证
    5. 保留策略管理
    """

    def __init__(self, backup_dir: str = "backups/update_backups", db_backup_dir: str = "backups/database"):
        self.backup_dir = Path(backup_dir)
        self.db_backup_dir = Path(db_backup_dir)
        self.backup_info_file = self.backup_dir / "backups_index.json"
        self.backups = []
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.db_backup_dir.mkdir(parents=True, exist_ok=True)
        self._load_backups()

        # 初始化调度器
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

        # 云存储配置
        self.cloud_config = {
            'enabled': False,
            'provider': 's3',  # s3, oss, cos
            'bucket': '',
            'access_key': '',
            'secret_key': '',
            'region': '',
        }

        # 备份保留策略
        self.retention_policy = {
            'daily': 7,  # 保留7天日备份
            'weekly': 4,  # 保留4周周备份
            'monthly': 12,  # 保留12个月月备份
        }
    
    def _load_backups(self):
        """加载备份索引"""
        if self.backup_info_file.exists():
            try:
                with open(self.backup_info_file, 'r', encoding='utf-8') as f:
                    self.backups = json.load(f)
            except Exception as e:
                logger.error(f"加载备份索引失败：{e}")
                self.backups = []
        else:
            self._scan_existing_backups()
    
    def _scan_existing_backups(self):
        """扫描现有备份目录"""
        try:
            if not self.backup_dir.exists():
                return
            
            for backup_path in self.backup_dir.iterdir():
                if backup_path.is_dir() and backup_path.name.startswith('backup_'):
                    info_file = backup_path / "backup_info.json"
                    if info_file.exists():
                        try:
                            with open(info_file, 'r', encoding='utf-8') as f:
                                info = json.load(f)
                                info['path'] = str(backup_path)
                                self.backups.append(info)
                        except Exception:
                            pass
            
            self.backups.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            self._save_backups()
        except Exception as e:
            logger.error(f"扫描备份失败：{e}")
    
    def _save_backups(self):
        """保存备份索引"""
        try:
            with open(self.backup_info_file, 'w', encoding='utf-8') as f:
                json.dump(self.backups, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存备份索引失败：{e}")
    
    def create(self, source_path: str, version: str = None) -> Optional[Dict]:
        """创建备份"""
        try:
            timestamp = int(datetime.now().timestamp())
            backup_name = f"backup_{timestamp}"
            backup_path = self.backup_dir / backup_name
            
            logger.info(f"开始创建备份：{backup_path}")
            shutil.copytree(source_path, backup_path, dirs_exist_ok=True)
            
            backup_info = {
                'timestamp': timestamp,
                'datetime': datetime.fromtimestamp(timestamp).isoformat(),
                'version': version or 'unknown',
                'path': str(backup_path),
                'status': 'success'
            }
            
            # 保存备份信息
            info_file = backup_path / "backup_info.json"
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)
            
            self.backups.append(backup_info)
            self._save_backups()
            
            logger.info(f"备份创建成功：{backup_path}")
            return backup_info
            
        except Exception as e:
            logger.error(f"创建备份失败：{e}")
            return None
    
    def get(self, backup_id: str) -> Optional[Dict]:
        """获取指定备份信息"""
        for backup in self.backups:
            if str(backup.get('timestamp')) == backup_id or backup.get('path') == backup_id:
                return backup
        return None
    
    def list(self, limit: int = 10) -> List[Dict]:
        """列出备份"""
        return self.backups[:limit]
    
    def restore(self, backup_id: str, target_path: str) -> bool:
        """恢复备份"""
        try:
            backup = self.get(backup_id)
            if not backup:
                logger.error(f"备份不存在：{backup_id}")
                return False
            
            backup_path = Path(backup['path'])
            if not backup_path.exists():
                logger.error(f"备份文件不存在：{backup_path}")
                return False
            
            logger.info(f"开始恢复备份：{backup_path} -> {target_path}")
            
            target = Path(target_path)
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(backup_path, target)
            
            logger.info(f"备份恢复成功：{target}")
            return True
            
        except Exception as e:
            logger.error(f"恢复备份失败：{e}")
            return False
    
    def delete(self, backup_id: str) -> bool:
        """删除备份"""
        try:
            backup = self.get(backup_id)
            if not backup:
                logger.error(f"备份不存在：{backup_id}")
                return False
            
            backup_path = Path(backup['path'])
            if backup_path.exists():
                shutil.rmtree(backup_path)
                logger.info(f"已删除备份文件：{backup_path}")
            
            self.backups = [b for b in self.backups if b.get('timestamp') != backup.get('timestamp')]
            self._save_backups()
            
            logger.info(f"备份已从索引中移除：{backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除备份失败：{e}")
            return False

    # ==================== 自动化备份功能 ====================

    def schedule_auto_backup(self, cron_expression: str = "0 2 * * *", backup_type: str = "full"):
        """
        设置自动备份调度
        
        Args:
            cron_expression: Cron表达式，默认每天凌晨2点
            backup_type: 备份类型 (full/incremental)
        """
        try:
            # 解析cron表达式
            trigger = CronTrigger.from_crontab(cron_expression)

            # 添加定时任务
            self.scheduler.add_job(
                func=self._auto_backup_job,
                trigger=trigger,
                id='auto_backup',
                name='自动数据库备份',
                kwargs={'backup_type': backup_type},
                replace_existing=True
            )

            logger.info(f"自动备份调度已设置: {cron_expression}, 类型: {backup_type}")
            return True

        except Exception as e:
            logger.error(f"设置自动备份调度失败: {e}")
            return False

    def _auto_backup_job(self, backup_type: str = "full"):
        """自动备份任务"""
        try:
            logger.info(f"开始执行自动备份: {backup_type}")

            # 执行备份
            if backup_type == "incremental":
                result = self.create_incremental_backup()
            else:
                result = self.create_full_backup()

            if result:
                logger.info(f"自动备份成功: {result.get('name')}")

                # 上传到云存储
                if self.cloud_config.get('enabled'):
                    self.upload_to_cloud(result['path'])

                # 清理过期备份
                self.cleanup_old_backups()
            else:
                logger.error("自动备份失败")

        except Exception as e:
            logger.error(f"自动备份任务执行失败: {e}", exc_info=True)

    def create_full_backup(self, source_paths: List[str] = None) -> Optional[Dict]:
        """
        创建完整备份
        
        Args:
            source_paths: 要备份的源路径列表
            
        Returns:
            备份信息字典
        """
        try:
            timestamp = datetime.now()
            backup_name = f"full_backup_{timestamp.strftime('%Y%m%d_%H%M%S')}"
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir(parents=True, exist_ok=True)

            # 如果没有指定源路径，备份整个项目
            if not source_paths:
                source_paths = [
                    'apps',
                    'config',
                    'plugins',
                    'themes',
                    '.env',
                ]

            # 复制文件
            for source in source_paths:
                src_path = Path(source)
                if src_path.exists():
                    dest_path = backup_path / src_path.name
                    if src_path.is_dir():
                        shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src_path, dest_path)

            # 创建备份元数据
            backup_info = {
                'id': backup_name,
                'name': backup_name,
                'type': 'full',
                'timestamp': int(timestamp.timestamp()),
                'datetime': timestamp.isoformat(),
                'path': str(backup_path),
                'size': self._get_directory_size(backup_path),
                'status': 'success',
                'source_paths': source_paths,
            }

            # 保存元数据
            info_file = backup_path / "backup_info.json"
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)

            # 添加到索引
            self.backups.insert(0, backup_info)
            self._save_backups()

            logger.info(f"完整备份创建成功: {backup_name}")
            return backup_info

        except Exception as e:
            logger.error(f"创建完整备份失败: {e}", exc_info=True)
            return None

    def create_incremental_backup(self, last_backup_id: str = None) -> Optional[Dict]:
        """
        创建增量备份
        
        Args:
            last_backup_id: 上次备份ID，如果为None则使用最近的备份
            
        Returns:
            备份信息字典
        """
        try:
            # 获取上次备份
            if not last_backup_id and self.backups:
                last_backup = self.backups[0]
                last_backup_id = last_backup.get('id')

            if not last_backup_id:
                logger.warning("没有历史备份，执行完整备份")
                return self.create_full_backup()

            last_backup = self.get(last_backup_id)
            if not last_backup:
                logger.error(f"找不到备份: {last_backup_id}")
                return None

            timestamp = datetime.now()
            backup_name = f"incremental_backup_{timestamp.strftime('%Y%m%d_%H%M%S')}"
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir(parents=True, exist_ok=True)

            # 比较文件变化
            changed_files = self._detect_changes(
                Path(last_backup['path']),
                Path('.'),
                backup_path
            )

            if not changed_files:
                logger.info("没有文件变化，跳过增量备份")
                shutil.rmtree(backup_path)
                return None

            # 创建备份元数据
            backup_info = {
                'id': backup_name,
                'name': backup_name,
                'type': 'incremental',
                'base_backup': last_backup_id,
                'timestamp': int(timestamp.timestamp()),
                'datetime': timestamp.isoformat(),
                'path': str(backup_path),
                'size': self._get_directory_size(backup_path),
                'status': 'success',
                'changed_files_count': len(changed_files),
            }

            # 保存元数据
            info_file = backup_path / "backup_info.json"
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)

            # 添加到索引
            self.backups.insert(0, backup_info)
            self._save_backups()

            logger.info(f"增量备份创建成功: {backup_name}, 变更文件: {len(changed_files)}")
            return backup_info

        except Exception as e:
            logger.error(f"创建增量备份失败: {e}", exc_info=True)
            return None

    def _detect_changes(self, base_path: Path, current_path: Path, diff_path: Path) -> List[str]:
        """
        检测文件变化
        
        Returns:
            变化的文件列表
        """
        changed_files = []

        try:
            # 扫描当前目录
            for file_path in current_path.rglob('*'):
                if not file_path.is_file():
                    continue

                # 跳过隐藏文件和特定目录
                if any(part.startswith('.') or part in ['node_modules', '__pycache__', '.git']
                       for part in file_path.parts):
                    continue

                # 计算相对路径
                rel_path = file_path.relative_to(current_path)
                base_file = base_path / rel_path

                # 检查文件是否存在或发生变化
                if not base_file.exists():
                    # 新文件
                    dest = diff_path / rel_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, dest)
                    changed_files.append(str(rel_path))
                else:
                    # 检查文件内容是否变化
                    if self._file_hash(file_path) != self._file_hash(base_file):
                        dest = diff_path / rel_path
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(file_path, dest)
                        changed_files.append(str(rel_path))

        except Exception as e:
            logger.error(f"检测文件变化失败: {e}")

        return changed_files

    def _file_hash(self, file_path: Path) -> str:
        """计算文件哈希值"""
        hasher = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except:
            return ""

    def _get_directory_size(self, path: Path) -> int:
        """计算目录大小"""
        total_size = 0
        try:
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except:
            pass
        return total_size

    # ==================== 云存储集成 ====================

    def configure_cloud_storage(self, config: Dict):
        """
        配置云存储
        
        Args:
            config: 云存储配置
        """
        self.cloud_config.update(config)
        logger.info(f"云存储配置已更新: {config.get('provider')}")

    def upload_to_cloud(self, backup_path: str) -> bool:
        """
        上传备份到云存储
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            是否成功
        """
        if not self.cloud_config.get('enabled'):
            logger.warning("云存储未启用")
            return False

        try:
            provider = self.cloud_config.get('provider')

            if provider == 's3':
                return self._upload_to_s3(backup_path)
            elif provider == 'oss':
                return self._upload_to_oss(backup_path)
            else:
                logger.error(f"不支持的云存储提供商: {provider}")
                return False

        except Exception as e:
            logger.error(f"上传到云存储失败: {e}")
            return False

    def _upload_to_s3(self, backup_path: str) -> bool:
        """上传到AWS S3"""
        try:
            import boto3
            from botocore.exceptions import ClientError

            s3_client = boto3.client(
                's3',
                aws_access_key_id=self.cloud_config['access_key'],
                aws_secret_access_key=self.cloud_config['secret_key'],
                region_name=self.cloud_config.get('region', 'us-east-1')
            )

            backup_file = Path(backup_path)
            object_key = f"backups/{backup_file.name}.tar.gz"

            # 压缩备份
            tar_path = backup_file.with_suffix('.tar.gz')
            shutil.make_archive(str(backup_file), 'gztar', backup_file.parent, backup_file.name)

            # 上传
            s3_client.upload_file(
                str(tar_path),
                self.cloud_config['bucket'],
                object_key
            )

            logger.info(f"备份已上传到S3: {object_key}")
            return True

        except ImportError:
            logger.error("boto3库未安装，请运行: pip install boto3")
            return False
        except Exception as e:
            logger.error(f"S3上传失败: {e}")
            return False

    def _upload_to_oss(self, backup_path: str) -> bool:
        """上传到阿里云OSS"""
        try:
            import oss2

            auth = oss2.Auth(
                self.cloud_config['access_key'],
                self.cloud_config['secret_key']
            )
            bucket = oss2.Bucket(
                auth,
                f"https://oss-{self.cloud_config.get('region', 'oss-cn-hangzhou')}.aliyuncs.com",
                self.cloud_config['bucket']
            )

            backup_file = Path(backup_path)
            object_key = f"backups/{backup_file.name}.tar.gz"

            # 压缩并上传
            tar_path = backup_file.with_suffix('.tar.gz')
            shutil.make_archive(str(backup_file), 'gztar', backup_file.parent, backup_file.name)

            bucket.put_object_from_file(object_key, str(tar_path))

            logger.info(f"备份已上传到OSS: {object_key}")
            return True

        except ImportError:
            logger.error("oss2库未安装，请运行: pip install oss2")
            return False
        except Exception as e:
            logger.error(f"OSS上传失败: {e}")
            return False

    # ==================== 备份清理策略 ====================

    def cleanup_old_backups(self):
        """根据保留策略清理旧备份"""
        try:
            now = datetime.now()
            deleted_count = 0

            for backup in self.backups[:]:
                backup_time = datetime.fromisoformat(backup.get('datetime', ''))
                age_days = (now - backup_time).days

                should_delete = False

                # 日备份超过保留期
                if age_days > self.retention_policy['daily']:
                    should_delete = True

                # 周备份超过保留期
                elif age_days > self.retention_policy['weekly'] * 7:
                    should_delete = True

                # 月备份超过保留期
                elif age_days > self.retention_policy['monthly'] * 30:
                    should_delete = True

                if should_delete:
                    self.delete(backup.get('id'))
                    deleted_count += 1

            if deleted_count > 0:
                logger.info(f"已清理 {deleted_count} 个过期备份")

        except Exception as e:
            logger.error(f"清理旧备份失败: {e}")

    # ==================== 备份验证 ====================

    def verify_backup(self, backup_id: str) -> Dict:
        """
        验证备份完整性
        
        Args:
            backup_id: 备份ID
            
        Returns:
            验证结果
        """
        try:
            backup = self.get(backup_id)
            if not backup:
                return {'valid': False, 'error': '备份不存在'}

            backup_path = Path(backup['path'])
            if not backup_path.exists():
                return {'valid': False, 'error': '备份文件不存在'}

            # 检查元数据文件
            info_file = backup_path / "backup_info.json"
            if not info_file.exists():
                return {'valid': False, 'error': '备份元数据缺失'}

            # 验证元数据
            with open(info_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # 检查文件大小
            actual_size = self._get_directory_size(backup_path)
            expected_size = backup.get('size', 0)

            size_match = abs(actual_size - expected_size) < 1024  # 允许1KB误差

            return {
                'valid': True,
                'backup_id': backup_id,
                'size_check': size_match,
                'actual_size': actual_size,
                'expected_size': expected_size,
                'metadata_valid': True,
            }

        except Exception as e:
            logger.error(f"验证备份失败: {e}")
            return {'valid': False, 'error': str(e)}


# 全局单例
backup_manager = BackupManager()
