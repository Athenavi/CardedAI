"""
认证相关 API
包含用户名/邮箱检查、登录状态检查、登录、注册、登出、token刷新、邮箱/短信验证等功能
"""
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.user import User as UserModel
from shared.services.users.email_verification_service import email_verification_service
from shared.services.users.login_security_service import login_security_service
from shared.services.users.session_management_service import session_management_service
from shared.services.users.sms_verification_service import sms_verification_service
from shared.services.users.user_manager import create_user_account
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db
from src.setting import settings
from src.unified_logger import default_logger as logger

# token_blacklist 改为惰性导入：避免模块加载时触发 Redis .ping() 导致启动缓慢

_tb_instance = None


def _get_token_blacklist():
    global _tb_instance
    if _tb_instance is None:
        from src.utils.token_blacklist import token_blacklist
        _tb_instance = token_blacklist
    return _tb_instance

router = APIRouter(tags=["auth"])


# ---------------------------------------------------------------------------
# 请求模型
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    """登录请求模型（支持 JSON）"""
    username: Optional[str] = None
    email: Optional[str] = None
    password: str
    remember_me: Optional[bool] = False


class RegisterRequest(BaseModel):
    """注册请求模型（支持 JSON）"""
    username: str
    email: str
    password: str


# ---------------------------------------------------------------------------
# JWT 工具函数
# ---------------------------------------------------------------------------

async def authenticate_user_with_session(
        username_or_email: str,
        password: str,
        db: AsyncSession,
) -> Optional[UserModel]:
    """
    验证用户凭据（用户名/邮箱 + 密码）

    Args:
        username_or_email: 用户名或邮箱
        password: 明文密码
        db: 数据库会话

    Returns:
        验证成功返回用户对象，否则返回 None
    """
    from src.utils.security.password_validator import verify_password

    # 尝试通过用户名或邮箱查找用户
    result = await db.execute(
        select(UserModel).where(
            (UserModel.username == username_or_email) | (UserModel.email == username_or_email)
        )
    )
    user = result.scalar_one_or_none()

    if not user or not user.password:
        return None

    # 使用统一的密码验证函数（支持 Django PBKDF2 和 bcrypt）
    if verify_password(password, user.password):
        return user

    return None


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
# 用户名/邮箱检查 API
# ---------------------------------------------------------------------------

@router.get("/check-username")
async def check_username(username: str = Query(...), db: AsyncSession = Depends(get_async_db)):
    """检查用户名是否可用"""
    try:
        existing = await db.scalar(
            select(UserModel).where(func.lower(UserModel.username) == func.lower(username))
        )
        return JSONResponse({
            "success": True,
            "available": existing is None,
            "exists": existing is not None
        })
    except Exception as e:
        logger.error(f"Check username error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@router.get("/check-email")
async def check_email(email: str = Query(...), db: AsyncSession = Depends(get_async_db)):
    """检查邮箱是否可用"""
    try:
        existing = await db.scalar(
            select(UserModel).where(func.lower(UserModel.email) == func.lower(email))
        )
        return JSONResponse({
            "success": True,
            "available": existing is None,
            "exists": existing is not None
        })
    except Exception as e:
        logger.error(f"Check email error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@router.get('/status', summary="检查登录状态")
async def check_login_status(current_user=Depends(jwt_required)):
    """检查用户登录状态"""
    return {
        'logged_in': True,
        'message': 'User is logged in',
        'user_id': current_user.id if hasattr(current_user, 'id') else None
    }


# ---------------------------------------------------------------------------
# 认证相关 API
# ---------------------------------------------------------------------------

@router.post("/login", summary="用户登录")
async def login_api(
        request: Request,
        db: AsyncSession = Depends(get_async_db),
):
    """使用用户名或邮箱登录，返回 access / refresh token（PyJWT）

    支持两种请求格式：
    1. JSON (application/json) - 推荐
    2. Form Data (application/x-www-form-urlencoded)
    """
    try:
        # 从请求中读取数据
        content_type = request.headers.get('content-type', '')
        username = None
        password = None
        remember_me = None

        if 'application/json' in content_type:
            # JSON 格式
            body = await request.json()
            username = body.get('username') or body.get('email')
            password = body.get('password')
            remember_me = body.get('remember_me') or body.get('rememberMe', False)
        else:
            # Form 格式
            form_data = await request.form()
            username = form_data.get('username') or form_data.get('email')
            password = form_data.get('password')
            raw_remember = form_data.get('remember_me')
            # Form 数据中 "false" 字符串在 Python 中是 truthy，需要显式解析
            remember_me = str(raw_remember).lower() in ('true', '1', 'on') if raw_remember is not None else False

        # 验证必填字段
        if not username or not password:
            logger.warning(f"[Login] Missing credentials - username: {bool(username)}, password: {bool(password)}")
            return ApiResponse(success=False, error="缺少用户名或密码")

        # 🔍 调试日志：打印接收到的登录信息（不打印密码）
        logger.info(
            f"[Login] Login attempt - username: '{username}', remember_me: {remember_me}, content_type: {content_type}")

        # 获取IP地址和User-Agent
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")

        # 安全检查：检查账户是否被锁定
        is_locked, unlock_time = await login_security_service.check_account_locked_async(username, db)

        if is_locked:
            # 记录这次被阻止的尝试
            await login_security_service.record_login_attempt_async(
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                is_success=False,
                failure_reason="Account locked due to too many failed attempts",
                db=db
            )

            unlock_minutes = (unlock_time - datetime.now()).total_seconds() / 60
            return ApiResponse(
                success=False,
                error=f"账户已被临时锁定，请在 {int(unlock_minutes)} 分钟后重试",
                data={
                    "locked": True,
                    "unlock_at": unlock_time.isoformat()
                }
            )

        # 1. 验证凭证
        user = await authenticate_user_with_session(username, password, db)
        if not user:
            # 记录失败尝试
            await login_security_service.record_login_attempt_async(
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                is_success=False,
                failure_reason="Invalid credentials",
                db=db
            )

            # 检查是否需要警告
            failed_count = await login_security_service.get_failed_attempts_count_async(username, db)
            remaining_attempts = login_security_service.max_failures - failed_count

            if remaining_attempts <= 2 and remaining_attempts > 0:
                return ApiResponse(
                    success=False,
                    error=f"用户名或密码错误（还剩 {remaining_attempts} 次尝试机会）"
                )

            return ApiResponse(success=False, error="用户名或密码错误")

        if not user.is_active:
            # 记录失败尝试
            await login_security_service.record_login_attempt_async(
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                is_success=False,
                failure_reason="Account disabled",
                db=db
            )

            return ApiResponse(success=False, error="账户已被禁用")

        # 2. 检查是否启用了2FA
        if user.is_2fa_enabled:
            # 生成临时令牌用于2FA验证阶段（有效期5分钟）
            temp_token = create_jwt_token(
                subject=str(user.id),
                token_type="2fa_temp",
                expires_delta=timedelta(minutes=5)
            )

            return ApiResponse(
                success=True,
                data={
                    "requires_2fa": True,
                    "temp_token": temp_token,
                    "user_id": user.id,
                    "username": user.username,
                    "message": "请输入2FA验证码"
                },
                message="需要2FA验证"
            )

        # 3. 生成 JWT（未启用2FA的用户）
        access_token = create_jwt_token(subject=str(user.id), token_type="access")
        # 仅在勾选"记住我"时才生成 refresh token
        refresh_token = create_jwt_token(subject=str(user.id), token_type="refresh") if remember_me else None

        # 3.5 创建用户会话记录
        try:
            user_agent = request.headers.get("User-Agent", "Unknown")
            ip_address = request.client.host if request.client else None

            device_info = {
                'user_agent': user_agent,
                'browser': request.headers.get('sec-ch-ua', 'Unknown'),
                'platform': request.headers.get('sec-ch-ua-platform', 'Unknown'),
            }

            session_management_service.create_session(
                user_id=user.id,
                device_info=device_info,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        except Exception as e:
            print(f"[Login API] Warning: Failed to create session record: {e}")
            # 会话创建失败不影响登录流程

        # 4. 更新最后登录时间
        user.last_login = datetime.now(timezone.utc)
        await db.commit()

        # 5. 记录成功登录
        await login_security_service.record_login_attempt_async(
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            is_success=True,
            db=db
        )

        # 6. 清除之前的失败记录
        await login_security_service.clear_failed_attempts_async(username, db)

        # 记录审计日志
        try:
            from shared.services.security.audit_log_service import audit_log_service, AuditLogAction
            await audit_log_service.log_action(
                db=db, user_id=user.id, user_name=user.username,
                action=AuditLogAction.LOGIN, resource_type='auth',
                description=f"用户登录：{user.username}",
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get('user-agent'),
            )
        except Exception:
            pass

        response_data = {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "profile_picture": user.profile_picture or None,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "is_staff": user.is_staff,
                "vip_level": getattr(user, "vip_level", 0),
            },
            "access_token": access_token,
        }
        # 仅在勾选"记住我"时返回 refresh_token
        if refresh_token:
            response_data["refresh_token"] = refresh_token

        return ApiResponse(
            success=True,
            data=response_data,
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise


@router.post("/register", summary="用户注册")
async def register_api(
        request: Request,
        db: AsyncSession = Depends(get_async_db),
):
    """用户注册并返回 token

    支持两种请求格式：
    1. JSON (application/json) - 推荐
    2. Form Data (application/x-www-form-urlencoded)
    """
    # 从请求中读取数据
    content_type = request.headers.get('content-type', '')
    username = None
    email = None
    password = None

    if 'application/json' in content_type:
        # JSON 格式
        body = await request.json()
        username = body.get('username')
        email = body.get('email')
        password = body.get('password')
    else:
        # Form 格式
        form_data = await request.form()
        username = form_data.get('username')
        email = form_data.get('email')
        password = form_data.get('password')

    # 验证必填字段
    if not username or not email or not password:
        return ApiResponse(success=False, error="缺少必填字段")
    # 基础校验
    if len(username) < 3:
        return ApiResponse(success=False, error="用户名至少需要 3 个字符")
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        return ApiResponse(success=False, error="邮箱格式不正确")
    if len(password) < 8:
        return ApiResponse(success=False, error="密码至少需要 8 个字符")
    if not re.search(r"[A-Z]", password):
        return ApiResponse(success=False, error="密码必须包含大写字母")
    if not re.search(r"[a-z]", password):
        return ApiResponse(success=False, error="密码必须包含小写字母")
    if not re.search(r"\d", password):
        return ApiResponse(success=False, error="密码必须包含数字")

    # 检查重名
    result = await db.execute(select(UserModel).where(UserModel.username == username))
    if result.scalar_one_or_none():
        return ApiResponse(success=False, error="用户名已存在")
    result = await db.execute(select(UserModel).where(UserModel.email == email))
    if result.scalar_one_or_none():
        return ApiResponse(success=False, error="邮箱已被注册")

    # 创建用户
    try:
        user = await create_user_account(db=db, username=username, email=email, password=password, is_active=True)
    except ValueError as e:
        return ApiResponse(success=False, error=str(e))

    # 生成 token
    access_token = create_jwt_token(subject=str(user.id), token_type="access")
    refresh_token = create_jwt_token(subject=str(user.id), token_type="refresh")

    # 创建用户会话记录
    try:
        user_agent = request.headers.get("User-Agent", "Unknown")
        ip_address = request.client.host if request.client else None

        device_info = {
            'user_agent': user_agent,
            'browser': request.headers.get('sec-ch-ua', 'Unknown'),
            'platform': request.headers.get('sec-ch-ua-platform', 'Unknown'),
        }

        session_management_service.create_session(
            user_id=user.id,
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except Exception as e:
        print(f"[Register API] Warning: Failed to create session: {e}")

    return ApiResponse(
        success=True,
        data={
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "is_staff": user.is_staff,
                "vip_level": getattr(user, "vip_level", 0),
            },
            "access_token": access_token,
            "refresh_token": refresh_token,
        },
        message="注册成功",
    )


# ---------------------------------------------------------------------------
# 邮箱验证 API
# ---------------------------------------------------------------------------

@router.post("/email/send-code", summary="发送邮箱验证码")
async def send_email_verification_code(
        request: Request,
        email: str = Form(..., description="邮箱地址")
):
    """
    发送邮箱验证码
    用于注册、找回密码等场景的邮箱验证
    """

    # 验证邮箱格式
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        return ApiResponse(success=False, error="邮箱格式不正确")

    result = email_verification_service.send_verification_code(email)

    if result['success']:
        return ApiResponse(
            success=True,
            message=result['message'],
            data={
                'expire_minutes': result['expire_minutes']
            }
        )
    else:
        return ApiResponse(
            success=False,
            error=result['message'],
            data={
                'can_resend_in': result.get('can_resend_in')
            }
        )


@router.post("/email/verify-code", summary="验证邮箱验证码")
async def verify_email_code(
        request: Request,
        email: str = Form(..., description="邮箱地址"),
        code: str = Form(..., description="验证码")
):
    """
    验证邮箱验证码
    验证成功后可用于后续操作(如注册、重置密码等)
    """

    # 验证验证码格式
    if not code or len(code) != 6 or not code.isdigit():
        return ApiResponse(success=False, error="验证码格式不正确")

    result = email_verification_service.verify_code(email, code)

    if result['success']:
        return ApiResponse(
            success=True,
            message=result['message'],
            data={
                'verified': True,
                'email': email
            }
        )
    else:
        return ApiResponse(
            success=False,
            error=result['message'],
            data={
                'remaining_attempts': result.get('remaining_attempts')
            }
        )


# ---------------------------------------------------------------------------
# 手机短信验证 API
# ---------------------------------------------------------------------------

@router.post("/sms/send-code", summary="发送手机验证码")
async def send_sms_verification_code(
        request: Request,
        phone: str = Form(..., description="手机号")
):
    """
    发送手机短信验证码
    用于注册、登录、找回密码等场景的手机验证
    """

    result = sms_verification_service.send_verification_code(phone)

    if result['success']:
        return ApiResponse(
            success=True,
            message=result['message'],
            data={
                'expire_minutes': result['expire_minutes']
            }
        )
    else:
        return ApiResponse(
            success=False,
            error=result['message']
        )


@router.post("/sms/verify-code", summary="验证手机验证码")
async def verify_sms_code(
        request: Request,
        phone: str = Form(..., description="手机号"),
        code: str = Form(..., description="验证码")
):
    """
    验证手机短信验证码
    验证成功后可用于后续操作(如注册、重置密码等)
    """

    # 验证验证码格式
    if not code or len(code) != 6 or not code.isdigit():
        return ApiResponse(success=False, error="验证码格式不正确")

    result = sms_verification_service.verify_code(phone, code)

    if result['success']:
        return ApiResponse(
            success=True,
            message=result['message'],
            data={
                'verified': True,
                'phone': phone
            }
        )
    else:
        return ApiResponse(
            success=False,
            error=result['message'],
            data={
                'remaining_attempts': result.get('remaining_attempts')
            }
        )


@router.post("/logout", summary="用户登出")
async def logout_api(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    """将当前 access_token 及可选的 refresh_token 加入黑名单"""
    try:
        body = await request.body()
        data = json.loads(body) if body else {}
        access_token_str = data.get("access_token")
        refresh_token_str = data.get("refresh_token")

        # 辅助函数：将 token 加入黑名单
        def _blacklist_token(token: str):
            try:
                payload = jwt.decode(
                    token,
                    settings.JWT_SECRET_KEY,
                    algorithms=[settings.JWT_ALGORITHM],
                    options={"verify_exp": False},  # 允许已过期的 token 也能被撤销
                )
                jti = payload.get("jti")
                exp = payload.get("exp")
                if jti and exp:
                    expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
                    _get_token_blacklist().add_to_blacklist(jti, expires_at)
            except Exception:
                pass

        if access_token_str:
            _blacklist_token(access_token_str)
        if refresh_token_str:
            _blacklist_token(refresh_token_str)

        # 记录审计日志
        try:
            from shared.services.security.audit_log_service import audit_log_service, AuditLogAction
            # 从 access_token 中解析用户信息记录登出日志
            log_user_id = None
            log_user_name = None
            if access_token_str:
                try:
                    payload = jwt.decode(access_token_str, settings.JWT_SECRET_KEY,
                                         algorithms=[settings.JWT_ALGORITHM],
                                         options={"verify_exp": False})
                    log_user_id = payload.get('user_id') or payload.get('sub')
                    log_user_name = payload.get('sub') or payload.get('username')
                except Exception:
                    pass
            if log_user_id:
                await audit_log_service.log_action(
                    db=db, user_id=log_user_id, user_name=log_user_name,
                    action=AuditLogAction.LOGOUT, resource_type='auth',
                    description="用户登出",
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get('user-agent'),
                )
        except Exception:
            pass

        return ApiResponse(success=True, message="登出成功")
    except Exception as e:
        return ApiResponse(success=False, error="登出失败，请稍后重试")


@router.post("/token/refresh", summary="刷新访问令牌")
async def refresh_token_api(request: Request):
    """使用 refresh_token 获取新的 access_token（支持 refresh token 轮换）"""
    try:
        body = await request.body()
        data = json.loads(body)
        refresh_token_str = data.get("refresh")
        if not refresh_token_str:
            return ApiResponse(success=False, error="缺少 refresh token")

        # 解码并验证 refresh token
        payload = decode_jwt_token(refresh_token_str)
        if payload.get("type") != "refresh":
            return ApiResponse(success=False, error="不是有效的 refresh token")

        user_id = payload.get("sub")
        if not user_id:
            return ApiResponse(success=False, error="无效的 refresh token")

        # 黑名单检查：检查 refresh token 的 JTI 是否在黑名单中
        jti = payload.get("jti")
        exp = payload.get("exp")
        _tb = _get_token_blacklist()
        if jti and _tb.is_available and _tb.is_blacklisted(jti):
            return ApiResponse(success=False, error="Token 已被撤销，请重新登录")

        # 生成新的 access token 和 refresh token（token 轮换）
        new_access_token = create_jwt_token(subject=user_id, token_type="access")
        new_refresh_token = create_jwt_token(subject=user_id, token_type="refresh")

        # 将旧的 refresh token 加入黑名单（token 轮换策略）
        if jti and exp:
            _get_token_blacklist().add_to_blacklist(
                jti,
                datetime.fromtimestamp(exp, tz=timezone.utc)
            )

        return ApiResponse(
            success=True,
            data={
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
            },
            message="Token refreshed successfully",
        )
    except HTTPException as e:
        # decode_jwt_token 会抛出 401，但这里我们想返回 ApiResponse 格式
        return ApiResponse(success=False, error=e.detail)
    except Exception:
        return ApiResponse(success=False, error="Token 刷新失败，请稍后重试")
