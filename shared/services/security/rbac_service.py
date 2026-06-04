"""
RBAC (基于角色的访问控制) 服务实现
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.role import Role
from shared.models.user_role import UserRole
from shared.models.role_capability import RoleCapability
from shared.models.capability import Capability
from src.utils.database.main import get_async_session


class RBACService:
    """RBAC 核心服务"""

    @staticmethod
    async def has_capability(user_id: int, capability_slug: str) -> bool:
        """检查用户是否拥有特定能力"""
        async for db in get_async_session():
            # 1. 获取用户的所有角色
            user_roles_query = select(UserRole).where(UserRole.user_id == user_id)
            user_roles_result = await db.execute(user_roles_query)
            user_roles = user_roles_result.scalars().all()

            role_ids = [ur.role_id for ur in user_roles]
            if not role_ids:
                return False

            # 2. 检查这些角色是否拥有指定能力
            query = (
                select(RoleCapability)
                .join(Capability, RoleCapability.capability_id == Capability.id)
                .where(
                    RoleCapability.role_id.in_(role_ids),
                    Capability.slug == capability_slug
                )
            )
            result = await db.execute(query)
            return result.scalar_one_or_none() is not None

    @staticmethod
    async def assign_role(user_id: int, role_slug: str):
        """为用户分配角色"""
        async for db in get_async_session():
            role_query = select(Role).where(Role.slug == role_slug)
            role_result = await db.execute(role_query)
            role = role_result.scalar_one_or_none()

            if not role:
                raise ValueError(f"Role '{role_slug}' not found")

            # 检查是否已分配
            existing = await db.execute(
                select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role.id)
            )
            if existing.scalar_one_or_none():
                return

            user_role = UserRole(user_id=user_id, role_id=role.id)
            db.add(user_role)
            await db.commit()


rbac_service = RBACService()
