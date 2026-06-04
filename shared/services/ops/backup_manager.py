"""
P8-3: 自动化备份服务
提供定时备份、云存储同步和自动清理功能
"""
import os
import gzip
import shutil
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import boto3
from sqlalchemy import text

from src.unified_logger import default_logger as logger
from src.utils.database.main import get_async_session


class BackupManager:
    """
    P8-3: 自动化备份管理器
    
    功能：
    1. 定时数据库备份（每日/每周）
    2. 文件备份（媒体文件、主题、插件）
    3. 云存储同步（S3, OSS, Google Cloud Storage）
    4. 一键恢复功能
    5. 备份保留策略（自动清理旧备份）
    """

    def __init__(self):
        self.backup_dir = Path("backups/automated")
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # 备份保留策略
        self.retention_policy = {
            'daily': 7,  # 保留 7 天日备份
            'weekly': 4,  # 保留 4 周周备份
            'monthly': 12,  # 保留 12 个月月备份
        }

        # 云存储配置（从环境变量读取）
        self.s3_config = {
            'enabled': os.getenv('BACKUP_S3_ENABLED', 'false').lower() == 'true',
            'bucket': os.getenv('BACKUP_S3_BUCKET', ''),
            'region': os.getenv('BACKUP_S3_REGION', 'us-east-1'),
            'access_key': os.getenv('BACKUP_S3_ACCESS_KEY', ''),
            'secret_key': os.getenv('BACKUP_S3_SECRET_KEY', ''),
        }

    async def create_database_backup(self, backup_type: str = 'daily') -> Dict[str, Any]:
        """
        创建数据库备份
        
        Args:
            backup_type: 备份类型 (daily/weekly/monthly)
            
        Returns:
            备份信息
        """
        try:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"db_backup_{backup_type}_{timestamp}.sql.gz"
            backup_path = self.backup_dir / backup_filename

            # 获取数据库连接信息
            database_url = os.getenv('DATABASE_URL', '')

            if not database_url:
                raise Exception("DATABASE_URL 未配置")

            # 使用 pg_dump 进行备份（PostgreSQL）
            import subprocess

            # 解析数据库连接信息
            # 格式: postgresql://user:pass@host:port/dbname
            parts = database_url.replace('postgresql://', '').split('@')
            user_pass = parts[0].split(':')
            host_db = parts[1].split('/')

            db_user = user_pass[0]
            db_password = user_pass[1] if len(user_pass) > 1 else ''
            host_port = host_db[0].split(':')
            db_host = host_port[0]
            db_port = host_port[1] if len(host_port) > 1 else '5432'
            db_name = host_db[1]

            # 执行 pg_dump
            env = os.environ.copy()
            env['PGPASSWORD'] = db_password

            cmd = [
                'pg_dump',
                '-h', db_host,
                '-p', db_port,
                '-U', db_user,
                '-d', db_name,
                '--format=custom',
                '--compress=9'
            ]

            with open(backup_path, 'wb') as f:
                result = subprocess.run(cmd, env=env, stdout=f, stderr=subprocess.PIPE)

                if result.returncode != 0:
                    raise Exception(f"pg_dump failed: {result.stderr.decode()}")

            # 压缩备份文件
            compressed_path = Path(str(backup_path) + '.gz')
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            backup_path.unlink()  # 删除未压缩文件

            # 上传到云存储
            cloud_url = None
            if self.s3_config['enabled']:
                cloud_url = await self._upload_to_s3(compressed_path, backup_type)

            # 清理旧备份
            await self.cleanup_old_backups(backup_type)

            backup_info = {
                "success": True,
                "filename": compressed_path.name,
                "path": str(compressed_path),
                "size_bytes": compressed_path.stat().st_size,
                "type": backup_type,
                "created_at": datetime.utcnow().isoformat(),
                "cloud_url": cloud_url
            }

            logger.info(f"Database backup created: {backup_info['filename']}")

            return backup_info

        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": backup_type
            }

    async def create_files_backup(self) -> Dict[str, Any]:
        """
        创建文件备份（媒体文件、主题、插件）
        
        Returns:
            备份信息
        """
        try:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"files_backup_{timestamp}.tar.gz"
            backup_path = self.backup_dir / backup_filename

            # 需要备份的目录
            directories_to_backup = [
                'media',
                'themes',
                'plugins',
                'static',
            ]

            import tarfile

            with tarfile.open(backup_path, "w:gz") as tar:
                for dir_name in directories_to_backup:
                    dir_path = Path(dir_name)
                    if dir_path.exists():
                        tar.add(dir_path, arcname=dir_name)

            # 上传到云存储
            cloud_url = None
            if self.s3_config['enabled']:
                cloud_url = await self._upload_to_s3(backup_path, 'files')

            backup_info = {
                "success": True,
                "filename": backup_filename,
                "path": str(backup_path),
                "size_bytes": backup_path.stat().st_size,
                "created_at": datetime.utcnow().isoformat(),
                "cloud_url": cloud_url,
                "directories": directories_to_backup
            }

            logger.info(f"Files backup created: {backup_filename}")

            return backup_info

        except Exception as e:
            logger.error(f"Files backup failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _upload_to_s3(self, file_path: Path, backup_type: str) -> Optional[str]:
        """
        上传备份到 S3
        
        Args:
            file_path: 备份文件路径
            backup_type: 备份类型
            
        Returns:
            S3 URL
        """
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=self.s3_config['access_key'],
                aws_secret_access_key=self.s3_config['secret_key'],
                region_name=self.s3_config['region']
            )

            s3_key = f"backups/{backup_type}/{file_path.name}"

            s3_client.upload_file(str(file_path), self.s3_config['bucket'], s3_key)

            url = f"https://{self.s3_config['bucket']}.s3.{self.s3_config['region']}.amazonaws.com/{s3_key}"

            logger.info(f"Backup uploaded to S3: {url}")

            return url

        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            return None

    async def cleanup_old_backups(self, backup_type: str):
        """
        清理旧备份（根据保留策略）
        
        Args:
            backup_type: 备份类型 (daily/weekly/monthly/files)
        """
        try:
            retention_days = self.retention_policy.get(backup_type, 7)
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

            # 查找旧备份文件
            pattern = f"*{backup_type}*.sql.gz" if backup_type != 'files' else "files_*.tar.gz"
            old_backups = list(self.backup_dir.glob(pattern))

            deleted_count = 0

            for backup_file in old_backups:
                # 从文件名提取时间戳（简化实现）
                file_mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)

                if file_mtime < cutoff_date:
                    backup_file.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old backup: {backup_file.name}")

            if deleted_count > 0:
                logger.info(f"Cleanup completed: {deleted_count} old backups deleted")

        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")

    async def restore_database_backup(self, backup_filename: str) -> Dict[str, Any]:
        """
        恢复数据库备份
        
        Args:
            backup_filename: 备份文件名
            
        Returns:
            恢复结果
        """
        try:
            backup_path = self.backup_dir / backup_filename

            if not backup_path.exists():
                return {
                    "success": False,
                    "error": f"Backup file not found: {backup_filename}"
                }

            # 解压备份文件
            import subprocess

            temp_sql_path = backup_path.with_suffix('').with_suffix('.sql')

            with gzip.open(backup_path, 'rb') as f_in:
                with open(temp_sql_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # 使用 psql 恢复
            database_url = os.getenv('DATABASE_URL', '')

            # 解析数据库连接信息（同备份）
            parts = database_url.replace('postgresql://', '').split('@')
            user_pass = parts[0].split(':')
            host_db = parts[1].split('/')

            db_user = user_pass[0]
            db_password = user_pass[1] if len(user_pass) > 1 else ''
            host_port = host_db[0].split(':')
            db_host = host_port[0]
            db_port = host_port[1] if len(host_port) > 1 else '5432'
            db_name = host_db[1]

            env = os.environ.copy()
            env['PGPASSWORD'] = db_password

            cmd = [
                'psql',
                '-h', db_host,
                '-p', db_port,
                '-U', db_user,
                '-d', db_name,
                '-f', str(temp_sql_path)
            ]

            result = subprocess.run(cmd, env=env, capture_output=True, text=True)

            temp_sql_path.unlink()  # 清理临时文件

            if result.returncode != 0:
                raise Exception(f"psql failed: {result.stderr}")

            logger.info(f"Database restored from backup: {backup_filename}")

            return {
                "success": True,
                "message": "Database restored successfully",
                "backup_file": backup_filename
            }

        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def list_backups(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        列出备份文件
        
        Args:
            limit: 返回数量限制
            
        Returns:
            备份文件列表
        """
        backups = []

        for backup_file in sorted(self.backup_dir.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)[:limit]:
            backups.append({
                "filename": backup_file.name,
                "size_bytes": backup_file.stat().st_size,
                "created_at": datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat(),
                "type": "database" if "db_backup" in backup_file.name else "files"
            })

        return backups


# 全局实例
backup_manager = BackupManager()
