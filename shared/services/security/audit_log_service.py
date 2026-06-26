"""简化的审计日志服务（个人站长轻量版）"""
from enum import Enum
from typing import Any, Optional


class AuditLogAction(str, Enum):
    CREATE = 'create'
    READ = 'read'
    UPDATE = 'update'
    DELETE = 'delete'
    LOGIN = 'login'
    LOGOUT = 'logout'
    EXPORT = 'export'


class AuditLogLevel(str, Enum):
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'


class AuditLogService:
    """审计日志服务（简化版 - 仅打印日志）"""

    async def log(self, action: str, resource_type: str, resource_id: Optional[Any] = None,
                  user_id: Optional[int] = None, details: Optional[dict] = None,
                  ip_address: Optional[str] = None, level: str = 'info') -> None:
        """记录审计日志（简化版仅输出到日志）"""
        import logging
        logger = logging.getLogger('audit')
        logger.info(f'[审计] {action} {resource_type}(id={resource_id}) by user={user_id}')


# 全局单例
audit_log_service = AuditLogService()
