"""
用户管理 API（基于 PyJWT + SQLAlchemy，无 fastapi-jwt-auth 依赖）
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# SQLAlchemy 模型与服务（保持不变）
from shared.models.user import User as UserModel
from src.extensions import get_async_db_session as get_async_db
from src.setting import settings

# token_blacklist 改为惰性导入：避免模块加载时触发 Redis .ping() 导致启动缓慢

_tb_instance = None


def _get_token_blacklist():
    global _tb_instance
    if _tb_instance is None:
        from src.utils.token_blacklist import token_blacklist
        _tb_instance = token_blacklist
    return _tb_instance


# ---------------------------------------------------------------------------
# JWT 工具函数
# ---------------------------------------------------------------------------

def create_jwt_token(
        subject: str,
        token_type: str = "access",
        expires_delta: Optional[timedelta] = None
) -> str:
    """生成 JWT（包含标准声明 sub, exp, jti, type）"""
    now = datetime.now(timezone.utc)
    if expires_delta is None:
        if token_type == "access":
            expires_delta = timedelta(seconds=settings.JWT_EXPIRATION_DELTA)
        else:
            expires_delta = timedelta(seconds=settings.REFRESH_TOKEN_EXPIRATION_DELTA)
    expire = now + expires_delta

    payload = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "jti": str(uuid.uuid4()),
        "type": token_type,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_jwt_token(token: str) -> dict:
    """解码并验证 JWT，返回 payload。若无效抛出 HTTPException"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": True},
        )

        # 黑名单检查
        jti = payload.get("jti")
        _tb = _get_token_blacklist()
        if jti and _tb.is_available and _tb.is_blacklisted(jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def extract_token_from_request(request: Request) -> Optional[str]:
    """从 Authorization header 或 cookie 中提取 JWT"""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[len("Bearer "):]
    # 兼容 cookie，名称根据你的需求调整
    return request.cookies.get("access_token") or request.cookies.get("access_token_cookie")


# ---------------------------------------------------------------------------
# FastAPI 依赖：获取当前用户
# ---------------------------------------------------------------------------

async def get_current_active_user(
        request: Request,
        db: AsyncSession = Depends(get_async_db),
) -> UserModel:
    """获取当前活跃用户（强制验证）"""
    token = extract_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_jwt_token(token)

    # 提取用户 ID
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing subject",
        )
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format",
        )

    # 黑名单检查
    jti = payload.get("jti")
    _tb = _get_token_blacklist()
    if jti and _tb.is_available and _tb.is_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    # 加载用户
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
    return user


async def get_current_user_optional(
        request: Request,
        db: AsyncSession = Depends(get_async_db),
) -> Optional[UserModel]:
    """可选获取当前用户（未登录时返回 None）"""
    token = extract_token_from_request(request)
    if not token:
        return None
    try:
        payload = decode_jwt_token(token)
    except HTTPException:
        return None

    user_id_str = payload.get("sub")
    if not user_id_str:
        return None
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        return None

    # 黑名单检查
    jti = payload.get("jti")
    _tb = _get_token_blacklist()
    if jti and _tb.is_available and _tb.is_blacklisted(jti):
        return None

    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    return result.scalar_one_or_none()


# 向后兼容的别名
get_current_user = get_current_active_user
jwt_required = get_current_active_user  # 相当于原 jwt_required 依赖
jwt_optional = get_current_user_optional  # 相当于原 jwt_optional 函数


# ---------------------------------------------------------------------------
# 辅助函数：生成 API 响应及格式转换
# ---------------------------------------------------------------------------

def _create_article_response(article):
    """将文章 ORM 对象转换为前端需要的字典"""
    return {
        "id": article.id,
        "title": article.title,
        "slug": article.slug,
        "excerpt": article.excerpt,
        "cover_image": article.cover_image,
        "tags": [],
        "views": article.views or 0,
        "likes": article.likes or 0,
        "created_at": article.created_at.isoformat() if hasattr(article.created_at,
                                                                "isoformat") else article.created_at,
        "updated_at": article.updated_at.isoformat() if hasattr(article.updated_at,
                                                                "isoformat") else article.updated_at,
    }


def _create_user_response(user):
    """将用户 ORM 对象转换为前端需要的字典"""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "bio": user.bio or "",
        "location": user.locale or "",
        "website": "",
        "profile_private": user.profile_private,
        "display_name": user.username,
        "locale": user.locale or "zh_CN",
        "created_at": user.date_joined if hasattr(user, "date_joined") and user.date_joined else None,
        "updated_at": None,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "is_staff": user.is_staff,
        "vip_level": getattr(user, "vip_level", 0),
        "avatar": user.profile_picture or "",
    }


def _get_user_stats(articles_count: int = 0):
    return {"articles_count": articles_count, "followers_count": 0, "following_count": 0}
