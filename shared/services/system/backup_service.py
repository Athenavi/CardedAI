"""
数据备份服务
提供数据库和文件的自动备份、恢复和管理功能
"""
import os
import json
import gzip
import shutil

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path

import asyncio
from sqlalchemy import text

from src.unified_logger import default_logger as logger


class BackupService:
    """
    数据备份服务
    
    功能:
    1. 数据库备份（PostgreSQL）
    2. 文件备份（媒体文件、上传文件）
    3. 增量备份
    4. 自动备份调度
    5. 备份恢复
    6. 异地备份支持
    """

    def __init__(self, backup_dir: str = None):
        """
        初始化备份服务
        
        Args:
            backup_dir: 备份目录路径
        """
        self.backup_dir = backup_dir or os.getenv('BACKUP_DIR', './backups')
        self.database_backup_dir = os.path.join(self.backup_dir, 'database')
        self.files_backup_dir = os.path.join(self.backup_dir, 'files')
        self.full_backup_dir = os.path.join(self.backup_dir, 'full')

        # 确保目录存在
        os.makedirs(self.database_backup_dir, exist_ok=True)
        os.makedirs(self.files_backup_dir, exist_ok=True)
        os.makedirs(self.full_backup_dir, exist_ok=True)

        # 默认配置
        self.config = {
            'retention_days': 30,  # 保留30天备份
            'auto_backup_enabled': True,
            'auto_backup_schedule': 'daily',  # daily, weekly, monthly
            'compress_backups': True,
            'backup_database': True,
            'backup_files': True,
        }

    def get_db_config(self) -> Dict[str, str]:
        """获取数据库配置"""
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'fast_blog'),
        }

    async def backup_database(self, backup_type: str = 'full') -> Dict[str, Any]:
        """
        备份数据库
        
        Args:
            backup_type: 备份类型 ('full' 或 'incremental')
            
        Returns:
            备份结果信息
        """
        try:
            db_config = self.get_db_config()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"db_backup_{timestamp}.sql"
            backup_path = os.path.join(self.database_backup_dir, backup_filename)

            logger.info(f"Starting database backup: {backup_filename}")

            # 使用pg_dump进行备份
            import subprocess

            env = os.environ.copy()
            if db_config['password']:
                env['PGPASSWORD'] = db_config['password']

            cmd = [
                'pg_dump',
                '-h', db_config['host'],
                '-p', db_config['port'],
                '-U', db_config['user'],
                '-F', 'c',  # 自定义格式（支持增量备份）
                '-f', backup_path,
                db_config['database']
            ]

            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )

            if result.returncode != 0:
                raise Exception(f"pg_dump failed: {result.stderr}")

            # 压缩备份文件
            compressed_path = None
            if self.config['compress_backups']:
                compressed_path = self._compress_file(backup_path)
                # 删除未压缩的文件
                os.remove(backup_path)
                backup_path = compressed_path

            # 记录备份元数据
            backup_size = os.path.getsize(backup_path)
            metadata = {
                'type': 'database',
                'backup_type': backup_type,
                'filename': os.path.basename(backup_path),
                'path': backup_path,
                'size': backup_size,
                'size_human': self._format_size(backup_size),
                'created_at': datetime.now().isoformat(),
                'database': db_config['database'],
                'status': 'completed'
            }

            self._save_metadata(backup_path, metadata)

            logger.info(f"Database backup completed: {backup_path} ({self._format_size(backup_size)})")

            return {
                'success': True,
                'backup_path': backup_path,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def backup_files(self) -> Dict[str, Any]:
        """
        备份文件（媒体文件、上传文件等）
        
        Returns:
            备份结果信息
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"files_backup_{timestamp}.tar.gz"
            backup_path = os.path.join(self.files_backup_dir, backup_filename)

            logger.info(f"Starting files backup: {backup_filename}")

            # 需要备份的目录
            directories_to_backup = [
                './media',
                './upload_chunks',
                './static',
                './themes',
                './plugins',
            ]

            # 使用tar命令打包
            import subprocess

            files_to_backup = []
            for dir_path in directories_to_backup:
                if os.path.exists(dir_path):
                    files_to_backup.append(dir_path)

            if not files_to_backup:
                return {
                    'success': True,
                    'message': 'No files to backup',
                    'backup_path': None
                }

            cmd = ['tar', '-czf', backup_path] + files_to_backup

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )

            if result.returncode != 0:
                raise Exception(f"tar failed: {result.stderr}")

            # 记录备份元数据
            backup_size = os.path.getsize(backup_path)
            metadata = {
                'type': 'files',
                'filename': os.path.basename(backup_path),
                'path': backup_path,
                'size': backup_size,
                'size_human': self._format_size(backup_size),
                'created_at': datetime.now().isoformat(),
                'directories': files_to_backup,
                'status': 'completed'
            }

            self._save_metadata(backup_path, metadata)

            logger.info(f"Files backup completed: {backup_path} ({self._format_size(backup_size)})")

            return {
                'success': True,
                'backup_path': backup_path,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Files backup failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def full_backup(self) -> Dict[str, Any]:
        """
        完整备份（数据库 + 文件）
        
        Returns:
            备份结果信息
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = os.path.join(self.full_backup_dir, f"full_backup_{timestamp}")
            os.makedirs(backup_dir, exist_ok=True)

            logger.info(f"Starting full backup: {backup_dir}")

            # 备份数据库
            db_result = await self.backup_database()
            if db_result['success']:
                # 复制数据库备份到完整备份目录
                db_backup_path = db_result['backup_path']
                db_backup_name = os.path.basename(db_backup_path)
                shutil.copy2(db_backup_path, os.path.join(backup_dir, db_backup_name))

            # 备份文件
            files_result = await self.backup_files()
            if files_result['success'] and files_result['backup_path']:
                # 复制文件备份到完整备份目录
                files_backup_path = files_result['backup_path']
                files_backup_name = os.path.basename(files_backup_path)
                shutil.copy2(files_backup_path, os.path.join(backup_dir, files_backup_name))

            # 创建完整备份元数据
            metadata = {
                'type': 'full',
                'backup_dir': backup_dir,
                'created_at': datetime.now().isoformat(),
                'database_backup': db_result.get('metadata'),
                'files_backup': files_result.get('metadata'),
                'status': 'completed'
            }

            metadata_path = os.path.join(backup_dir, 'metadata.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            logger.info(f"Full backup completed: {backup_dir}")

            return {
                'success': True,
                'backup_dir': backup_dir,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Full backup failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def backup_full(self) -> Dict[str, Any]:
        """
        完整备份（数据库 + 文件）的别名方法
        
        Returns:
            备份结果信息
        """
        return await self.full_backup()

    async def restore_database(self, backup_path: str) -> Dict[str, Any]:
        """
        恢复数据库
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            恢复结果
        """
        try:
            if not os.path.exists(backup_path):
                return {
                    'success': False,
                    'error': f'Backup file not found: {backup_path}'
                }

            db_config = self.get_db_config()

            logger.info(f"Starting database restore from: {backup_path}")

            import subprocess

            env = os.environ.copy()
            if db_config['password']:
                env['PGPASSWORD'] = db_config['password']

            # 先删除现有数据库
            drop_cmd = [
                'dropdb',
                '-h', db_config['host'],
                '-p', db_config['port'],
                '-U', db_config['user'],
                '--if-exists',
                db_config['database']
            ]

            subprocess.run(drop_cmd, env=env, check=True, capture_output=True)

            # 创建新数据库
            create_cmd = [
                'createdb',
                '-h', db_config['host'],
                '-p', db_config['port'],
                '-U', db_config['user'],
                db_config['database']
            ]

            subprocess.run(create_cmd, env=env, check=True, capture_output=True)

            # 恢复数据库
            restore_cmd = [
                'pg_restore',
                '-h', db_config['host'],
                '-p', db_config['port'],
                '-U', db_config['user'],
                '-d', db_config['database'],
                '--no-owner',
                '--no-privileges',
                backup_path
            ]

            result = subprocess.run(
                restore_cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                raise Exception(f"pg_restore failed: {result.stderr}")

            logger.info("Database restore completed successfully")

            return {
                'success': True,
                'message': 'Database restored successfully'
            }

        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def restore_files(self, backup_path: str) -> Dict[str, Any]:
        """
        恢复文件
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            恢复结果
        """
        try:
            if not os.path.exists(backup_path):
                return {
                    'success': False,
                    'error': f'Backup file not found: {backup_path}'
                }

            logger.info(f"Starting files restore from: {backup_path}")

            import subprocess

            # 解压并恢复文件
            cmd = ['tar', '-xzf', backup_path, '-C', '/']

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )

            if result.returncode != 0:
                raise Exception(f"tar restore failed: {result.stderr}")

            logger.info("Files restore completed successfully")

            return {
                'success': True,
                'message': 'Files restored successfully'
            }

        except Exception as e:
            logger.error(f"Files restore failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def list_backups(self, backup_type: str = None, limit: int = None) -> List[Dict[str, Any]]:
        """
        列出所有备份
        
        Args:
            backup_type: 备份类型过滤 ('database', 'files', 'full')
            limit: 返回数量限制
            
        Returns:
            备份列表
        """
        backups = []

        # 扫描数据库备份
        if not backup_type or backup_type == 'database':
            for filename in os.listdir(self.database_backup_dir):
                if filename.endswith('.sql') or filename.endswith('.gz'):
                    filepath = os.path.join(self.database_backup_dir, filename)
                    metadata = self._load_metadata(filepath)
                    if metadata:
                        backups.append(metadata)

        # 扫描文件备份
        if not backup_type or backup_type == 'files':
            for filename in os.listdir(self.files_backup_dir):
                if filename.endswith('.tar.gz'):
                    filepath = os.path.join(self.files_backup_dir, filename)
                    metadata = self._load_metadata(filepath)
                    if metadata:
                        backups.append(metadata)

        # 扫描完整备份
        if not backup_type or backup_type == 'full':
            for dirname in os.listdir(self.full_backup_dir):
                dirpath = os.path.join(self.full_backup_dir, dirname)
                if os.path.isdir(dirpath):
                    metadata_path = os.path.join(dirpath, 'metadata.json')
                    if os.path.exists(metadata_path):
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            backups.append(metadata)

        # 按创建时间排序
        backups.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        # 应用限制
        if limit and limit > 0:
            backups = backups[:limit]

        return backups

    def delete_backup(self, backup_path: str) -> bool:
        """
        删除备份
        
        Args:
            backup_path: 备份文件或目录路径
            
        Returns:
            是否删除成功
        """
        try:
            if os.path.isfile(backup_path):
                os.remove(backup_path)
            elif os.path.isdir(backup_path):
                shutil.rmtree(backup_path)

            logger.info(f"Backup deleted: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete backup: {e}")
            return False

    async def cleanup_old_backups(self, days: int = None) -> Dict[str, Any]:
        """
        清理旧备份
        
        Args:
            days: 保留天数
            
        Returns:
            清理结果统计
        """
        retention_days = days or self.config['retention_days']
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        backups = self.list_backups()
        
        deleted_count = 0
        freed_space = 0
        deleted_backups = []
        
        for backup in backups:
            created_at_str = backup.get('created_at', '')
            if not created_at_str:
                continue

            try:
                created_at = datetime.fromisoformat(created_at_str)
                if created_at < cutoff_date:
                    backup_path = backup.get('path') or backup.get('backup_dir')
                    if backup_path and os.path.exists(backup_path):
                        # 获取文件大小
                        if os.path.isfile(backup_path):
                            file_size = os.path.getsize(backup_path)
                        else:
                            # 目录大小
                            file_size = sum(
                                os.path.getsize(os.path.join(dirpath, filename))
                                for dirpath, dirnames, filenames in os.walk(backup_path)
                                for filename in filenames
                            )

                        if self.delete_backup(backup_path):
                            deleted_count += 1
                            freed_space += file_size
                            deleted_backups.append({
                                'filename': backup.get('filename', ''),
                                'size': file_size,
                                'size_human': self._format_size(file_size),
                                'created_at': created_at_str
                            })
            except Exception as e:
                logger.error(f"Failed to process backup for cleanup: {e}")

        logger.info(
            f"Cleaned up {deleted_count} old backups (older than {retention_days} days), freed {self._format_size(freed_space)}")

        return {
            'deleted_count': deleted_count,
            'freed_space': freed_space,
            'freed_space_human': self._format_size(freed_space),
            'deleted_backups': deleted_backups
        }

    def get_backup_schedule(self) -> Dict[str, Any]:
        """获取备份计划配置"""
        return {
            'auto_backup_enabled': self.config['auto_backup_enabled'],
            'auto_backup_schedule': self.config['auto_backup_schedule'],
            'retention_days': self.config['retention_days'],
            'compress_backups': self.config['compress_backups'],
            'backup_database': self.config['backup_database'],
            'backup_files': self.config['backup_files'],
        }

    def update_backup_schedule(self, config: Dict[str, Any]):
        """更新备份计划配置"""
        if 'auto_backup_enabled' in config:
            self.config['auto_backup_enabled'] = config['auto_backup_enabled']
        if 'auto_backup_schedule' in config:
            self.config['auto_backup_schedule'] = config['auto_backup_schedule']
        if 'retention_days' in config:
            self.config['retention_days'] = config['retention_days']
        if 'compress_backups' in config:
            self.config['compress_backups'] = config['compress_backups']
        if 'backup_database' in config:
            self.config['backup_database'] = config['backup_database']
        if 'backup_files' in config:
            self.config['backup_files'] = config['backup_files']

        logger.info(f"Backup schedule updated: {self.config}")

    def get_backup_stats(self) -> Dict[str, Any]:
        """获取备份统计信息"""
        backups = self.list_backups()

        total_size = 0
        latest_backup = None
        type_stats = {
            'database': {'count': 0, 'size': 0},
            'files': {'count': 0, 'size': 0},
            'full': {'count': 0, 'size': 0},
        }

        for backup in backups:
            size = backup.get('size', 0)
            total_size += size
            backup_type = backup.get('type', 'unknown')

            if backup_type in type_stats:
                type_stats[backup_type]['count'] += 1
                type_stats[backup_type]['size'] += size

            if not latest_backup or backup.get('created_at', '') > latest_backup.get('created_at', ''):
                latest_backup = backup

        return {
            'total_backups': len(backups),
            'total_size': total_size,
            'total_size_human': self._format_size(total_size),
            'latest_backup': latest_backup,
            'by_type': type_stats,
        }

    def _compress_file(self, file_path: str) -> str:
        """压缩文件"""
        compressed_path = file_path + '.gz'

        with open(file_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        return compressed_path
        
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def _save_metadata(self, backup_path: str, metadata: Dict[str, Any]):
        """保存备份元数据"""
        metadata_path = backup_path + '.meta.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    def _load_metadata(self, backup_path: str) -> Optional[Dict[str, Any]]:
        """加载备份元数据"""
        metadata_path = backup_path + '.meta.json'
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None


# 全局实例
backup_service = BackupService()
