"""
统一认证依赖（基于 PyJWT）
支持 API 端点和页面路由，包含角色、权限、VIP 等检查
"""
import datetime
import uuid
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.user import User as UserModel
from src.setting import settings
from src.unified_logger import default_logger as logger
from src.utils.database.main import get_async_session

# token_blacklist 改为惰性导入：避免模块加载时触发 Redis .ping() 导致启动缓慢
# from src.utils.token_blacklist import token_blacklist  →  移至 _authenticate_user 内部


# ---------- 缓存 token_blacklist 单例，避免重复导入 ----------
_tb_instance = None


def _get_token_blacklist():
    global _tb_instance
    if _tb_instance is None:
        from src.utils.token_blacklist import get_token_blacklist
        _tb_instance = get_token_blacklist()
    return _tb_instance


# ---------- JWT 工具 ----------
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"
TEMP_2FA_TOKEN_TYPE = "2fa_temp"

# 允许被当作访问凭证的类型。历史 token 没有 type 字段，按 access 处理以保持兼容。
_ACCESS_TOKEN_TYPES = ("access", None)


def _default_lifetime(token_type: str) -> datetime.timedelta:
    """按 token 类型返回默认有效期（读取 setting 中已解析的配置）"""
    if token_type == REFRESH_TOKEN_TYPE:
        configured = getattr(settings, "JWT_REFRESH_TOKEN_EXPIRES", None)
        if isinstance(configured, datetime.timedelta):
            return configured
        return datetime.timedelta(seconds=getattr(settings, "REFRESH_TOKEN_EXPIRATION_DELTA", 64800))
    if token_type == TEMP_2FA_TOKEN_TYPE:
        return datetime.timedelta(minutes=5)
    configured = getattr(settings, "JWT_ACCESS_TOKEN_EXPIRES", None)
    if isinstance(configured, datetime.timedelta):
        return configured
    return datetime.timedelta(seconds=getattr(settings, "JWT_EXPIRATION_DELTA", 7200))


def create_access_token(
    user_id,
    lifetime: Optional[datetime.timedelta] = None,
    token_type: str = ACCESS_TOKEN_TYPE,
) -> str:
    """
    生成 JWT。

    Args:
        user_id: 用户 ID（写入 sub）
        lifetime: 自定义有效期，为空时按 token_type 取配置
        token_type: access / refresh / 2fa_temp，写入 type claim

    Notes:
        jti 是令牌唯一标识，登出与刷新轮换依赖它做黑名单撤销；
        type 用于区分访问凭证与刷新/临时凭证，避免越权使用。
    """
    if lifetime is None:
        lifetime = _default_lifetime(token_type)

    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + lifetime,
        "jti": uuid.uuid4().hex,
        "type": token_type,
    }
    return jwt.encode(
        payload,
        getattr(settings, "JWT_SECRET_KEY", settings.SECRET_KEY),
        algorithm=getattr(settings, "JWT_ALGORITHM", "HS256"),
    )


# ---------- 提取与验证 Token ----------
def verify_token(token: str) -> dict:
    """
    纯验证 JWT token 并解码 payload（不含数据库查询）。
    包含黑名单检查，失败时抛出 HTTPException。
    """
    try:
        payload = jwt.decode(
            token,
            getattr(settings, "JWT_SECRET_KEY", settings.SECRET_KEY),
            algorithms=[getattr(settings, "JWT_ALGORITHM", "HS256")],
            options={"verify_exp": True},
        )
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 黑名单检查
    jti = payload.get("jti")
    if jti:
        _tb = _get_token_blacklist()
        if _tb.is_blacklisted(jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return payload


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
        logger.debug('[Auth] token 解码失败 path=%s error=%s type=%s',
                     request.url.path, str(e), type(e).__name__)
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

    # 只有 access 类型（以及历史无 type 字段的 token）才能作为访问凭证，
    # 防止 refresh / 2fa_temp 被直接当作登录态使用。
    token_type = payload.get("type")
    if token_type not in _ACCESS_TOKEN_TYPES:
        if required:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token type not allowed for authentication",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None

    # 黑名单检查（Redis 命中直接拒绝；Redis 不可用时回退到 ORM 持久化层）
    jti = payload.get("jti")
    if jti:
        _tb = _get_token_blacklist()
        if await _tb.is_blacklisted_async(jti):
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
