"""简化的审计服务（个人站长轻量版）"""


class AuditService:
    """审计服务（简化版）"""

    async def record(self, action: str, resource: str, resource_id: int = None,
                     user_id: int = None, details: dict = None) -> None:
        """记录审计事件"""
        pass


# 全局单例
audit_service = AuditService()
