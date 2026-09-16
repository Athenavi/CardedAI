"""
第三方登录（OAuth 2.0）— GitHub / Google

路由前缀：/api/v2/auth/oauth（由 src/api/v1/auth 聚合注册，与前端既有约定一致）

配置来源（决策：只读后台配置）：
    system_settings 表中的 oauth_<provider>_enabled / client_id / client_secret / redirect_uri

端点：
    GET /api/v2/auth/oauth/providers             已支持/已启用的提供商状态（前端据此渲染按钮）
    GET /api/v2/auth/oauth/{provider}/authorize  302 跳转到第三方授权页（state 为 HMAC 签名，无状态、带时效）
    GET /api/v2/auth/oauth/{provider}/callback   用 code 换 token → 取用户信息 → 绑定/建号 → 签发本站 JWT → 跳回站内

失败一律 302 回 /login?oauth_error=<reason>，便于前端给出友好提示。
"""

import base64
import hashlib
import hmac
import json
import re
import secrets
import time
from datetime import datetime
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.o_auth_account import OAuthAccount
from shared.models.user import User
from src.api.v1.core.responses import ApiResponse
from src.api.v1.system.admin_settings import get_system_settings_dict
from src.auth.auth_deps import (
    create_access_token,
    jwt_optional_dependency,
    jwt_required_dependency as jwt_required,
)
from src.setting import settings
from src.unified_logger import default_logger as logger
from src.utils.database.main import get_async_session

router = APIRouter(tags=["oauth"])

STATE_TTL_SECONDS = 600  # 授权链接有效期（10 分钟）
ACCESS_COOKIE_MAX_AGE = 3600  # 与 login_api 保持一致

# ── 支持的提供商（仅 GitHub / Google） ──
PROVIDERS: Dict[str, Dict[str, Any]] = {
    "github": {
        "label": "GitHub",
        "authorize_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "user_url": "https://api.github.com/user",
        "emails_url": "https://api.github.com/user/emails",
        "scope": "read:user user:email",
    },
    "google": {
        "label": "Google",
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "user_url": "https://www.googleapis.com/oauth2/v3/userinfo",
        "emails_url": None,
        "scope": "openid email profile",
    },
}


# ══════════════════════════════════════════════════════
# 配置读取
# ══════════════════════════════════════════════════════
async def _provider_config(db: AsyncSession, provider: str) -> Dict[str, Any]:
    """从 system_settings 读取 oauth_<provider>_* 配置"""
    all_settings = await get_system_settings_dict(db)

    def get(field: str, default: str = "") -> str:
        value = all_settings.get(f"oauth_{provider}_{field}", default)
        if value is None:
            return default
        return str(value).strip()

    return {
        "enabled": get("enabled").lower() in ("1", "true", "yes", "on"),
        "client_id": get("client_id"),
        "client_secret": get("client_secret"),
        "redirect_uri": get("redirect_uri"),
    }


def _resolve_redirect_uri(request: Request, provider: str, configured: str) -> str:
    """优先使用后台配置的回调地址，否则按当前请求推断"""
    if configured:
        return configured
    base = str(request.base_url).rstrip("/")
    return f"{base}/api/v2/auth/oauth/{provider}/callback"


def _safe_next(next_url: Optional[str]) -> str:
    """只允许跳回站内路径，避免开放重定向"""
    if not next_url or not next_url.startswith("/") or next_url.startswith("//"):
        return "/"
    return next_url


# ══════════════════════════════════════════════════════
# state（HMAC 签名，无状态）
# ══════════════════════════════════════════════════════
def _state_secret() -> bytes:
    secret = getattr(settings, "JWT_SECRET_KEY", None) or getattr(settings, "SECRET_KEY", None)
    return str(secret or "carded-ai-oauth-state").encode()


def _sign_state(provider: str, next_url: str, bind_user_id: Optional[int] = None) -> str:
    payload: Dict[str, Any] = {"p": provider, "n": next_url, "t": int(time.time()), "r": secrets.token_hex(6)}
    if bind_user_id is not None:
        # 绑定模式：state 里带上发起绑定的用户，回调时校验，避免把别人的第三方账号绑到自己名下
        payload["b"] = int(bind_user_id)
    raw = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode()
    ).decode().rstrip("=")
    signature = hmac.new(_state_secret(), raw.encode(), hashlib.sha256).hexdigest()[:32]
    return f"{raw}.{signature}"


def _verify_state(state: str) -> Optional[dict]:
    if not state or "." not in state:
        return None
    raw, signature = state.rsplit(".", 1)
    expected = hmac.new(_state_secret(), raw.encode(), hashlib.sha256).hexdigest()[:32]
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        padded = raw + "=" * (-len(raw) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode()).decode())
    except Exception:
        return None
    if int(time.time()) - int(payload.get("t", 0)) > STATE_TTL_SECONDS:
        return None
    return payload


# ══════════════════════════════════════════════════════
# 第三方接口调用
# ══════════════════════════════════════════════════════
async def _exchange_code(meta: Dict[str, Any], cfg: Dict[str, Any], code: str, redirect_uri: str) -> Dict[str, Any]:
    """用 authorization code 换取 access_token"""
    data = {
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(meta["token_url"], data=data, headers={"Accept": "application/json"})
        resp.raise_for_status()
        payload = resp.json()

    if not isinstance(payload, dict) or not payload.get("access_token"):
        raise RuntimeError(f"token endpoint returned no access_token: {str(payload)[:200]}")
    return payload


async def _fetch_profile(meta: Dict[str, Any], provider: str, access_token: str) -> Dict[str, Any]:
    """拉取第三方用户资料（统一成 provider_user_id / username / email / avatar）"""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "User-Agent": "CardedAI-OAuth",
    }
    async with httpx.AsyncClient(timeout=15, headers=headers) as client:
        resp = await client.get(meta["user_url"])
        resp.raise_for_status()
        data = resp.json()

        email = data.get("email")
        # GitHub 的 /user 在用户隐藏邮箱时不返回 email，需要再查 /user/emails
        if provider == "github" and meta.get("emails_url"):
            try:
                emails_resp = await client.get(meta["emails_url"])
                if emails_resp.status_code == 200:
                    emails = emails_resp.json() or []
                    primary = next(
                        (e for e in emails if e.get("primary") and e.get("verified")),
                        None,
                    ) or next((e for e in emails if e.get("verified")), None)
                    if primary:
                        email = primary.get("email")
            except Exception as exc:  # 取不到邮箱不阻断登录
                logger.warning(f"[OAuth] github emails lookup failed: {exc}")

    if provider == "github":
        return {
            "provider_user_id": str(data.get("id") or ""),
            "username": data.get("login") or "",
            "display_name": data.get("name") or data.get("login") or "",
            "email": email,
            "avatar": data.get("avatar_url") or "",
        }

    # Google userinfo（OIDC）
    return {
        "provider_user_id": str(data.get("sub") or ""),
        "username": (data.get("email") or "").split("@")[0],
        "display_name": data.get("name") or "",
        "email": email,
        "avatar": data.get("picture") or "",
    }


# ══════════════════════════════════════════════════════
# 本地账号：查找 / 绑定 / 首次登录自动创建
# ══════════════════════════════════════════════════════
async def _unique_username(db: AsyncSession, base: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]", "", base or "")[:24] or "user"
    candidate = cleaned
    for index in range(1, 60):
        exists = await db.execute(select(User.id).where(User.username == candidate))
        if exists.scalars().first() is None:
            return candidate
        candidate = f"{cleaned}{index}"
    return f"{cleaned}{secrets.token_hex(3)}"


async def _get_or_create_user(db: AsyncSession, provider: str, profile: Dict[str, Any]) -> User:
    """按 (provider, provider_user_id) 查找绑定；否则按邮箱关联已有账号；再否则自动建号"""
    provider_user_id = profile["provider_user_id"]

    account_res = await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_user_id == provider_user_id,
        )
    )
    account = account_res.scalars().first()

    if account:
        user_res = await db.execute(select(User).where(User.id == account.user_id))
        user = user_res.scalars().first()
        if user:
            account.extra_data = json.dumps(
                {"username": profile.get("username"), "avatar": profile.get("avatar")},
                ensure_ascii=False,
            )[:255]
            account.updated_at = datetime.now()
            user.last_login_at = datetime.now()
            await db.commit()
            return user

    # 按邮箱关联已有本地账号
    user = None
    email = profile.get("email")
    if email:
        user_res = await db.execute(select(User).where(User.email == email))
        user = user_res.scalars().first()

    if not user:
        username = await _unique_username(db, profile.get("username") or f"{provider}_user")
        user = User(
            username=username,
            email=email or None,
            password=None,  # 第三方登录账号不设本地密码
            profile_picture=profile.get("avatar") or None,
            is_active=True,
            is_superuser=False,
            is_staff=False,
            date_joined=datetime.now(),
            last_login_at=datetime.now(),
        )
        db.add(user)
        await db.flush()  # 取得自增 id
        logger.info(f"[OAuth] created local user via {provider}: id={user.id} username={username}")

    db.add(OAuthAccount(
        user_id=user.id,
        provider=provider,
        provider_user_id=provider_user_id,
        extra_data=json.dumps(
            {"username": profile.get("username"), "avatar": profile.get("avatar")},
            ensure_ascii=False,
        )[:255],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    ))
    user.last_login_at = datetime.now()
    await db.commit()
    await db.refresh(user)
    return user


def _fail(reason: str) -> RedirectResponse:
    return RedirectResponse(f"/login?oauth_error={reason}", status_code=302)


# ══════════════════════════════════════════════════════
# 端点
# ══════════════════════════════════════════════════════
@router.get("/providers", summary="已支持的第三方登录提供商及其启用状态")
async def list_oauth_providers(db: AsyncSession = Depends(get_async_session)):
    providers = []
    for key, meta in PROVIDERS.items():
        cfg = await _provider_config(db, key)
        providers.append({
            "key": key,
            "label": meta["label"],
            "enabled": cfg["enabled"],
            "configured": bool(cfg["enabled"] and cfg["client_id"] and cfg["client_secret"]),
        })
    return ApiResponse(success=True, data=providers)


@router.get("/{provider}/authorize", summary="跳转到第三方授权页")
async def oauth_authorize(
    provider: str,
    request: Request,
    next: str = Query("/", description="登录成功后跳回的站内路径"),
    mode: str = Query("login", description="login=直接登录；bind=绑定到当前登录账号"),
    current_user=Depends(jwt_optional_dependency),
    db: AsyncSession = Depends(get_async_session),
):
    meta = PROVIDERS.get(provider)
    if not meta:
        return _fail("unsupported_provider")

    cfg = await _provider_config(db, provider)
    if not cfg["enabled"]:
        return _fail("provider_disabled")
    if not cfg["client_id"] or not cfg["client_secret"]:
        return _fail("provider_not_configured")

    bind_user_id = None
    if mode == "bind":
        if not current_user:
            return _fail("login_required")
        bind_user_id = current_user.id

    params = {
        "client_id": cfg["client_id"],
        "redirect_uri": _resolve_redirect_uri(request, provider, cfg["redirect_uri"]),
        "scope": meta["scope"],
        "state": _sign_state(provider, _safe_next(next), bind_user_id),
        "response_type": "code",
    }
    if provider == "google":
        params["access_type"] = "online"
        params["prompt"] = "select_account"

    authorize_url = f"{meta['authorize_url']}?{urlencode(params)}"
    logger.info(f"[OAuth] authorize redirect -> {provider}")
    return RedirectResponse(authorize_url, status_code=302)


@router.get("/{provider}/callback", summary="第三方授权回调")
async def oauth_callback(
    provider: str,
    request: Request,
    code: str = Query("", description="授权码"),
    state: str = Query("", description="防 CSRF 的签名 state"),
    error: str = Query("", description="第三方返回的错误"),
    current_user=Depends(jwt_optional_dependency),
    db: AsyncSession = Depends(get_async_session),
):
    if error:
        logger.warning(f"[OAuth] {provider} returned error: {error}")
        return _fail("provider_denied")

    meta = PROVIDERS.get(provider)
    if not meta:
        return _fail("unsupported_provider")

    payload = _verify_state(state)
    if not payload or payload.get("p") != provider:
        logger.warning(f"[OAuth] invalid state for {provider}")
        return _fail("invalid_state")

    next_url = _safe_next(payload.get("n"))

    cfg = await _provider_config(db, provider)
    if not cfg["client_id"] or not cfg["client_secret"]:
        return _fail("provider_not_configured")
    if not code:
        return _fail("missing_code")

    redirect_uri = _resolve_redirect_uri(request, provider, cfg["redirect_uri"])

    try:
        token_data = await _exchange_code(meta, cfg, code, redirect_uri)
        profile = await _fetch_profile(meta, provider, token_data["access_token"])
    except Exception as exc:
        logger.error(f"[OAuth] {provider} exchange/profile failed: {exc}")
        return _fail("exchange_failed")

    if not profile.get("provider_user_id"):
        return _fail("profile_incomplete")

    bind_user_id = payload.get("b")
    if bind_user_id:
        linked = await _bind_to_user(db, provider, profile, bind_user_id, current_user)
        if isinstance(linked, str):
            return _fail(linked)
        user = linked
    else:
        try:
            user = await _get_or_create_user(db, provider, profile)
        except Exception as exc:
            logger.error(f"[OAuth] {provider} account link failed: {exc}")
            return _fail("account_link_failed")

    try:
        await db.execute(
            User.__table__.update().where(User.id == user.id).values(
                last_login_ip=request.client.host if request.client else None
            )
        )
        await db.commit()
    except Exception as exc:
        logger.warning(f"[OAuth] update last_login_ip failed: {exc}")

    access_token = create_access_token(user.id)
    response = RedirectResponse(next_url, status_code=302)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=False,
        # 仅当“配置允许 + 实际走 https”时才加 Secure，避免本地 http 调试时 cookie 失效
        secure=bool(getattr(settings, "JWT_COOKIE_SECURE", False)) and request.url.scheme == "https",
        samesite="lax",
        max_age=ACCESS_COOKIE_MAX_AGE,
    )
    logger.info(f"[OAuth] {provider} login success: user_id={user.id}")
    return response


# ══════════════════════════════════════════════════════
# 账号绑定管理（需登录）
# ══════════════════════════════════════════════════════
async def _bind_to_user(
    db: AsyncSession,
    provider: str,
    profile: Dict[str, Any],
    bind_user_id: int,
    current_user: Optional[User],
):
    """绑定模式：把第三方账号绑定到当前登录用户（返回 User，或返回错误字符串）"""
    if not current_user or int(current_user.id) != int(bind_user_id):
        return "bind_session_mismatch"

    existing = await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_user_id == profile["provider_user_id"],
        )
    )
    account = existing.scalars().first()
    extra = json.dumps(
        {"username": profile.get("username"), "avatar": profile.get("avatar")},
        ensure_ascii=False,
    )[:255]

    if account:
        if int(account.user_id) != int(current_user.id):
            return "already_bound_to_other"
        account.extra_data = extra
        account.updated_at = datetime.now()
        await db.commit()
        logger.info(f"[OAuth] refreshed {provider} binding for user_id={current_user.id}")
        return current_user

    db.add(OAuthAccount(
        user_id=current_user.id,
        provider=provider,
        provider_user_id=profile["provider_user_id"],
        extra_data=extra,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    ))
    await db.commit()
    await db.refresh(current_user)
    logger.info(f"[OAuth] bound {provider} to user_id={current_user.id}")
    return current_user


@router.get("/bindings", summary="当前用户已绑定的第三方账号")
async def list_oauth_bindings(
    current_user=Depends(jwt_required),
    db: AsyncSession = Depends(get_async_session),
):
    result = await db.execute(
        select(OAuthAccount).where(OAuthAccount.user_id == current_user.id)
    )
    accounts = result.scalars().all()

    bindings = []
    for account in accounts:
        extra: Dict[str, Any] = {}
        try:
            extra = json.loads(account.extra_data) if account.extra_data else {}
        except Exception:
            extra = {}
        bindings.append({
            "provider": account.provider,
            "label": PROVIDERS.get(account.provider, {}).get("label", account.provider),
            "provider_user_id": account.provider_user_id,
            "username": extra.get("username"),
            "avatar": extra.get("avatar"),
            "created_at": account.created_at.isoformat() if account.created_at else None,
        })

    return ApiResponse(success=True, data={
        "bindings": bindings,
        "has_password": bool(current_user.password),
        "supported": [{"key": key, "label": meta["label"]} for key, meta in PROVIDERS.items()],
    })


@router.delete("/bindings/{provider}", summary="解绑第三方账号")
async def unbind_oauth(
    provider: str,
    current_user=Depends(jwt_required),
    db: AsyncSession = Depends(get_async_session),
):
    if provider not in PROVIDERS:
        return ApiResponse(success=False, error="不支持的第三方登录方式")

    result = await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.user_id == current_user.id,
            OAuthAccount.provider == provider,
        )
    )
    account = result.scalars().first()
    if not account:
        return ApiResponse(success=False, error="尚未绑定该第三方账号")

    # 防止解绑后用户再也无法登录：既没有本地密码，也没有其它绑定
    others = await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.user_id == current_user.id,
            OAuthAccount.provider != provider,
        )
    )
    remaining = len(others.scalars().all())
    if not current_user.password and remaining == 0:
        return ApiResponse(success=False, error="这是你唯一的登录方式，请先设置本地密码或绑定其它账号")

    await db.delete(account)
    await db.commit()
    logger.info(f"[OAuth] unbound {provider} from user_id={current_user.id}")
    return ApiResponse(success=True, data={"provider": provider})
