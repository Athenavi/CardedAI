from enum import Enum
from typing import List

from fastapi import HTTPException, status
from fastapi import Request, Depends

from shared.models.user import User
from src.auth import jwt_required_page_dependency as jwt_required
from src.extensions import get_sync_db


# 定义角色枚举
class RoleEnum(Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"


# 定义权限需求
# 基于角色的权限
ADMIN_ROLE = RoleEnum.ADMIN
MANAGER_ROLE = RoleEnum.MANAGER
USER_ROLE = RoleEnum.USER


# 权限类
class Permission:
    def __init__(self, roles: List[RoleEnum]):
        self.roles = roles

    async def check(self, user: User) -> bool:
        """检查用户是否有权限"""
        if not user:
            return False

        # 检查用户角色是否在允许的角色列表中
        user_roles = [role.name for role in user.roles] if hasattr(user, 'roles') else [
            user.role if hasattr(user, 'role') else 'user']
        return any(role.value in user_roles for role in self.roles)


# 预定义权限
admin_permission = Permission([ADMIN_ROLE])
manager_permission = Permission([ADMIN_ROLE, MANAGER_ROLE])
user_permission = Permission([ADMIN_ROLE, MANAGER_ROLE, USER_ROLE])


def create_permission(roles: List[RoleEnum]):
    """创建基于角色列表的权限对象"""
    return Permission(roles)


# 权限依赖函数
async def permission_required(roles: List[RoleEnum], request: Request,
                              current_user=Depends(jwt_required)):
    """权限检查依赖函数"""
    # 获取当前用户
    current_user_id = current_user.id
    # 从数据库获取用户信息
    with next(get_sync_db()) as db:
        from sqlalchemy import select
        user_query = select(User).where(User.id == current_user_id)
        user_result = db.execute(user_query)
        user = user_result.scalar_one_or_none()

    # 检查用户是否有权限
    perm = Permission(roles)
    if not await perm.check(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )

    return user


async def role_required(role_name: RoleEnum, request: Request, current_user=Depends(jwt_required)):
    """角色检查依赖函数"""
    # 获取当前用户ID
    current_user_id = current_user.id

    # 从数据库获取用户信息
    with next(get_sync_db()) as db:
        from sqlalchemy import select
        user_query = select(User).where(User.id == current_user_id)
        user_result = db.execute(user_query)
        user = user_result.scalar_one_or_none()

    # 检查用户角色
    user_role = user.role if hasattr(user, 'role') else (
        user.roles[0].name if hasattr(user, 'roles') and user.roles else 'user')

    if user_role != role_name.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="角色权限不足"
        )

    return user


def init_security_headers(app):
    """初始化安全头配置"""

    # 为FastAPI应用添加安全中间件
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)

        # 添加安全头
        response.headers['X-Content-Type-Options'] = 'nosniff'
        # 允许同源iframe嵌套
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # 如果启用了HTTPS，添加Strict-Transport-Security头
        # 注意：FastAPI中没有app.debug这样的属性，需要通过其他方式判断环境
        import os
        if os.getenv("ENVIRONMENT") != "development":
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        return response
