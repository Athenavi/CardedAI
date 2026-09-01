"""
用户管理 API（统一使用 auth_deps 提供的认证依赖）
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# SQLAlchemy 模型与服务（保持不变）
from shared.models.user import User as UserModel
from src.extensions import get_async_db_session as get_async_db
from src.setting import settings

# 统一使用 auth_deps 的认证依赖
from src.auth.auth_deps import _get_token_blacklist, _get_token_from_request, _authenticate_user
from src.utils.token_blacklist import get_token_blacklist


# ---------------------------------------------------------------------------
# JWT 工具函数 - 统一委托给 auth_deps
# ---------------------------------------------------------------------------

def create_jwt_token(
        subject: str,
        token_type: str = "access",
        expires_delta: Optional[timedelta] = None
) -> str:
    """生成 JWT（委托给 auth_deps.create_access_token）"""
    from src.auth.auth_deps import create_access_token
    return create_access_token(subject, lifetime=expires_delta)


def decode_jwt_token(token: str) -> dict:
    """解码并验证 JWT（委托给 auth_deps._authenticate_user 的黑名单检查逻辑）"""
    try:
        import jwt
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
    """从请求中提取 JWT（委托给 auth_deps）"""
    return _get_token_from_request(request)


# ---------------------------------------------------------------------------
# FastAPI 依赖：获取当前用户（委托给 auth_deps）
# ---------------------------------------------------------------------------

async def get_current_active_user(
        request: Request,
        db: AsyncSession = Depends(get_async_db),
) -> UserModel:
    """获取当前活跃用户（强制验证）"""
    return await _authenticate_user(request, db, required=True)


async def get_current_user_optional(
        request: Request,
        db: AsyncSession = Depends(get_async_db),
) -> Optional[UserModel]:
    """可选获取当前用户（未登录时返回 None）"""
    return await _authenticate_user(request, db, required=False)


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
