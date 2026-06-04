"""
多站点管理模块

提供站点管理和管理员权限检查功能
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.user import User
from src.unified_logger import default_logger as logger


async def check_admin_permission(
        db: AsyncSession,
        user_id: int
) -> bool:
    """
    检查用户是否具有管理员权限

    Args:
        db: 数据库会话
        user_id: 用户 ID

    Returns:
        bool: 是否具有管理员权限
    """
    try:
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalars().first()

        if not user:
            logger.warning(f"Admin permission check: user {user_id} not found")
            return False

        is_admin = getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False)
        return bool(is_admin)

    except Exception as e:
        logger.error(f"Admin permission check failed: {e}")
        return False
