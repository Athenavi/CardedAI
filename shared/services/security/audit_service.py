"""简化的审计服务（个人站长轻量版）"""
import logging

logger = logging.getLogger("fastblog.audit")


class AuditService:
    """审计服务（简化版）"""

    def __init__(self):
        self._records: list[dict] = []
        self._max_records = 1000

    async def record(self, action: str, resource: str, resource_id: int = None,
                     user_id: int = None, details: dict = None) -> None:
        """记录审计事件"""
        import time
        record = {
            'action': action,
            'resource': resource,
            'resource_id': resource_id,
            'user_id': user_id,
            'details': details or {},
            'timestamp': time.time(),
        }
        self._records.append(record)
        if len(self._records) > self._max_records:
            self._records.pop(0)
        logger.info(f"审计事件: {action} on {resource}(id={resource_id}) by user={user_id}")


# 全局单例
audit_service = AuditService()
