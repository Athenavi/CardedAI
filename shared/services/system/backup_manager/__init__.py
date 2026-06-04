"""
备份管理器包
提供数据库备份、恢复和远程存储功能
"""

from shared.services.system.backup_manager.remote_storage import RemoteStorageManager
from shared.services.system.backup_manager.service import BackupService

# 全局实例
backup_service = BackupService()
remote_storage = RemoteStorageManager()

__all__ = [
    'BackupService',
    'RemoteStorageManager',
    'backup_service',
    'remote_storage',
]
