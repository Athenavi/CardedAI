"""
统一认证依赖（基于 PyJWT）
支持 API 端点和页面路由，包含角色、权限、VIP 等检查
"""
import datetime
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.user import User as UserModel
from src.setting import settings
from src.utils.database.main import get_async_session

# token_blacklist 改为惰性导入：避免模块加载时触发 Redis .ping() 导致启动缓慢
# from src.utils.token_blacklist import token_blacklist  →  移至 _authenticate_user 内部


# ---------- 缓存 token_blacklist 单例，避免重复导入 ----------
_tb_instance = None


def _get_token_blacklist():
    global _tb_instance
    if _tb_instance is None:
        from src.utils.token_blacklist import token_blacklist
        _tb_instance = token_blacklist
    return _tb_instance


# ---------- JWT 工具 ----------
def create_access_token(
    user_id: int,
    lifetime: Optional[datetime.timedelta] = None,
) -> str:
    """
    生成 JWT 访问令牌
    """
    if lifetime is None:
        lifetime = datetime.timedelta(minutes=getattr(settings, "JWT_EXPIRATION_MINUTES", 60))

    payload = {
        "sub": str(user_id),
        "iat": datetime.datetime.now(),
        "exp": datetime.datetime.now() + lifetime,
    }
    return jwt.encode(
        payload,
        getattr(settings, "JWT_SECRET_KEY", settings.SECRET_KEY),
        algorithm=getattr(settings, "JWT_ALGORITHM", "HS256"),
    )


# ---------- 提取与验证 Token ----------
async def _get_token_from_request(request: Request) -> Optional[str]:
    """
    从 Authorization Header 或 Cookie 中提取 JWT token
    """
    # 1. 优先从 Bearer Header 获取
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[len("Bearer "):]

    # 2. 从 Cookie 获取（兼容页面路由）
    return request.cookies.get("access_token") or request.cookies.get("access_token_cookie")


async def _authenticate_user(
    request: Request,
    db: AsyncSession,
    *,
    required: bool = True,
) -> Optional[UserModel]:
    """
    内部核心：根据请求中的 token 验证身份，返回用户或 None。
    `required=True` 时无有效 token 会抛 401；`required=False` 时返回 None。
    """
    token = await _get_token_from_request(request)
    if not token:
        if required:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None

    jwt_secret = getattr(settings, "JWT_SECRET_KEY", settings.SECRET_KEY)
    jwt_algorithm = getattr(settings, "JWT_ALGORITHM", "HS256")

    try:
        payload = jwt.decode(token, jwt_secret, algorithms=[jwt_algorithm])
    except InvalidTokenError as e:
        if required:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None

    user_id_str = payload.get("sub")
    if not user_id_str:
        if required:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
            )
        return None

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        if required:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user ID")
        return None

    # 黑名单检查（惰性导入 token_blacklist，首次使用时才触发 Redis 连接）
    jti = payload.get("jti")
    if jti:
        _tb = _get_token_blacklist()
        if _tb.is_available and _tb.is_blacklisted(jti):
            if required:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked",
                )
            return None

    # 从数据库加载用户
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        if required:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive or non-existent user",
            )
        return None

    return user


# ---------- 依赖：获取当前用户（API 版 / 页面版） ----------
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
) -> UserModel:
    """API 端点依赖：必须提供有效 token，否则 401"""
    return await _authenticate_user(request, db, required=True)


async def get_current_user_or_redirect(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
):
    """页面路由依赖：无有效 token 时重定向到登录页"""
    user = await _authenticate_user(request, db, required=False)
    if user is None:
        next_url = str(request.url)
        return RedirectResponse(url=f"/login?next={next_url}")
    return user


# ---------- 管理员权限 ----------
async def admin_required(
    user: UserModel = Depends(get_current_user),
) -> UserModel:
    """API：需要超级管理员"""
    if not user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges")
    return user


async def admin_required_page(
    request: Request,
    user_or_redirect=Depends(get_current_user_or_redirect),
):
    """页面：需要超级管理员，否则重定向"""
    if isinstance(user_or_redirect, RedirectResponse):
        return user_or_redirect
    if not user_or_redirect.is_superuser:
        return RedirectResponse(url=f"/login?next={request.url}")
    return user_or_redirect


# ---------- 角色 / 权限检查 ----------
def require_permission(permission_code: str):
    """API：检查特定权限"""
    async def checker(user: UserModel = Depends(get_current_user)) -> UserModel:
        if not user.has_permission(permission_code):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return checker


def require_role(role_name: str):
    """API：检查特定角色"""
    async def checker(user: UserModel = Depends(get_current_user)) -> UserModel:
        if not user.has_role(role_name):
            raise HTTPException(status_code=403, detail="Insufficient role permissions")
        return user
    return checker


def require_permission_page(permission_code: str):
    """页面：检查特定权限，未认证重定向"""
    async def checker(
        request: Request,
        user_or_redirect=Depends(get_current_user_or_redirect),
    ):
        if isinstance(user_or_redirect, RedirectResponse):
            return user_or_redirect
        if not user_or_redirect.has_permission(permission_code):
            return RedirectResponse(url=f"/login?next={request.url}")
        return user_or_redirect
    return checker


def require_role_page(role_name: str):
    """页面：检查特定角色，未认证重定向"""
    async def checker(
        request: Request,
        user_or_redirect=Depends(get_current_user_or_redirect),
    ):
        if isinstance(user_or_redirect, RedirectResponse):
            return user_or_redirect
        if not user_or_redirect.has_role(role_name):
            return RedirectResponse(url=f"/login?next={request.url}")
        return user_or_redirect
    return checker


# ---------- VIP 检查 ----------
def require_vip():
    """API：要求 VIP 成员资格"""
    async def checker(user: UserModel = Depends(get_current_user)) -> UserModel:
        if not user.is_vip():
            raise HTTPException(status_code=403, detail="VIP membership required")
        return user
    return checker


# ---------- 导出别名（兼容旧代码） ----------
jwt_required = get_current_user
jwt_required_dependency = get_current_user
jwt_required_page = get_current_user_or_redirect
jwt_required_page_dependency = get_current_user_or_redirect
jwt_optional = _authenticate_user  # 需要配合自定义包装，见下方

async def jwt_optional_dependency(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
) -> Optional[UserModel]:
    """可选的 JWT 认证，未提供有效 token 时返回 None"""
    return await _authenticate_user(request, db, required=False)

# 兼容旧名称
get_current_active_user = get_current_user
get_current_super_user = admin_required
