import base64
import hashlib
import io
import json
import secrets
import time

import qrcode
from fastapi import Request


def gen_qr_token(user_agent: str, timestamp: str, sys_version: str, encoding: str = "utf-8") -> str:
    """生成随机的二维码 token"""
    data = f"{user_agent}{timestamp}{sys_version}{secrets.token_hex(16)}"
    return hashlib.sha256(data.encode(encoding)).hexdigest()


def _cache_set(cache, key: str, value, ttl: int = 180):
    """统一缓存写入，兼容不同缓存接口。
    对 dict/list 类型自动序列化为 JSON 字符串再存储，避免 Redis 存储 Python repr 导致反序列化失败。
    """
    # 将 dict/list 序列化为 JSON 字符串，确保 Redis 中存储的是合法 JSON
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False)
    try:
        cache.set(key, value, timeout=ttl)
    except TypeError:
        try:
            cache.set(key, value, ex=ttl)
        except Exception:
            cache.set(key, value)  # 最后的兜底，无过期时间


def _cache_get(cache, key: str):
    """统一缓存读取，自动尝试 JSON 反序列化。
    解决 Redis 返回字符串而代码期望 dict 的兼容性问题。
    """
    raw = cache.get(key)
    if raw is None:
        return None
    # 尝试 JSON 反序列化（兼容 dict/list 的 JSON 字符串）
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return raw
    return raw


async def qr_login(request: Request, sys_version: str, global_encoding: str, domain: str, cache):
    """生成登录二维码，返回 base64 图片与 token"""
    ct = str(int(time.time()))
    user_agent = request.headers.get("User-Agent", "Unknown")

    # 构造完整的回调地址
    if not domain.startswith(("http://", "https://")):
        host = request.headers.get("host", "localhost:9421")
        scheme = request.url.scheme if hasattr(request.url, "scheme") else "http"
        full_domain = f"{scheme}://{host}/"
    else:
        full_domain = domain

    token = gen_qr_token(user_agent, ct, sys_version, global_encoding)
    qr_data = f"{full_domain}mobile-login?login_token={token}"

    # 生成二维码图片
    img = qrcode.make(qr_data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode(global_encoding)

    # 存储待扫码状态（JSON 序列化由 _cache_set 自动处理）
    _cache_set(cache, f"QR-token_{token}", {"status": "pending", "created_at": ct}, ttl=180)

    return {
        "success": True,
        "qr_code": f"data:image/png;base64,{qr_b64}",
        "token": token,
        "expires_at": str(int(time.time()) + 180),
    }


async def phone_scan_back(request: Request, current_user, cache, login_token: str = None):
    """手机扫码确认，将当前用户的 refresh_token 写入缓存"""
    token = login_token or request.query_params.get("login_token") or request.query_params.get("token")
    if not token:
        return {"success": False, "message": "Missing login token"}

    # 验证二维码 token 是否有效（使用 _cache_get 自动反序列化）
    cached = _cache_get(cache, f"QR-token_{token}")
    if not cached:
        return {"success": False, "message": "Invalid or expired token"}

    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        # 如果 cookie 中没有 refresh_token，从当前用户生成一个新的
        from src.api.v1.auth import create_jwt_token
        refresh_token = create_jwt_token(subject=str(current_user.id), token_type="refresh")
    current_user_id = current_user.id

    # 写入授权信息（包含 refresh_token）（JSON 序列化由 _cache_set 自动处理）
    allow_data = {
        "status": "success",
        "refresh_token": refresh_token,
        "user_id": current_user_id,
    }
    _cache_set(cache, f"QR-allow_{token}", allow_data, ttl=180)
    # 更新二维码状态为 success
    _cache_set(cache, f"QR-token_{token}", {"status": "success"}, ttl=180)

    return {"success": True, "message": "授权成功，请在两分钟内完成登录"}


async def check_qr_login_back(request: Request, cache):
    """PC 端轮询检查扫码状态，优先检查二维码有效性，成功时返回 refresh_token"""
    token = request.query_params.get("token")
    next_url = request.query_params.get("next", "/profile")

    if not token:
        return {"success": False, "status": "error", "message": "Missing token parameter"}

    # 1. 先检查二维码本身的状态（是否过期）（使用 _cache_get 自动反序列化）
    qr_status = _cache_get(cache, f"QR-token_{token}")
    if not qr_status:
        return {"success": True, "status": "expired", "message": "QR code expired"}

    # 安全获取 status 字段（兼容 dict 和意外的字符串格式）
    if isinstance(qr_status, dict):
        status = qr_status.get("status", "pending")
    else:
        # 如果是意外的字符串格式，尝试提取状态
        status = "success" if "success" in str(qr_status) else "pending"

    # 2. 如果是成功状态，再去读取授权信息（使用 _cache_get 自动反序列化）
    if status == "success":
        import asyncio
        allow_info = _cache_get(cache, f"QR-allow_{token}")
        if not allow_info:
            # 极少数并发情况：授权信息还在写入中，稍作重试
            await asyncio.sleep(0.5)
            allow_info = _cache_get(cache, f"QR-allow_{token}")
        if allow_info and isinstance(allow_info, dict):
            return {
                "success": True,
                "status": "success",
                "next_url": next_url,
                "refresh_token": allow_info.get("refresh_token", ""),
            }

    # 3. 返回当前状态（pending 或 success 但授权信息尚未就绪）
    return {"success": True, "status": status}
