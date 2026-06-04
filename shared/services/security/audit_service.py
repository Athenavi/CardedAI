"""
审计日志服务
记录所有敏感操作并提供查询接口
"""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.audit_log import AuditLog
from src.utils.database.main import get_async_session


class AuditService:
    """审计日志核心服务"""

    @staticmethod
    async def log_action(
            user_id: int,
            action: str,
            ip_address: Optional[str] = None,
            user_agent: Optional[str] = None,
            resource_type: Optional[str] = None,
            resource_id: Optional[str] = None,
            request_data: Optional[dict] = None,
            status: str = "success",
            error_message: Optional[str] = None
    ):
        """记录一次操作行为"""
        import json
        async for db in get_async_session():
            log_entry = AuditLog(
                user_id=user_id,
                action=action,
                ip_address=ip_address,
                user_agent=user_agent,
                resource_type=resource_type,
                resource_id=resource_id,
                request_data=json.dumps(request_data) if request_data else None,
                status=status,
                error_message=error_message,
                created_at=datetime.utcnow()
            )
            db.add(log_entry)
            await db.commit()

    @staticmethod
    async def get_logs(
            user_id: Optional[int] = None,
            action: Optional[str] = None,
            limit: int = 50,
            offset: int = 0
    ) -> List[AuditLog]:
        """查询审计日志"""
        async for db in get_async_session():
            query = select(AuditLog).order_by(desc(AuditLog.created_at))

            if user_id:
                query = query.where(AuditLog.user_id == user_id)
            if action:
                query = query.where(AuditLog.action == action)

            query = query.offset(offset).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()


audit_service = AuditService()
