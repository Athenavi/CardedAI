"""认证 Cookie 策略统一出口。

历史问题：
1. 配置里存在 ``JWT_COOKIE_SAMESITE``（默认 Strict），但登录 / 2FA / OAuth
   三处 ``set_cookie`` 都硬编码了 ``samesite="lax"``，配置形同虚设。
2. ``unified_users`` 里用 ``DEBUG == 'false'`` 推断 https，逻辑正好相反：
   生产打开 Secure 却依赖 DEBUG 取值，易在灰度环境给出错误结果。

这里集中解析，保证三处下发点行为一致且可配置。
"""

import os

_VALID_SAMESITE = ("strict", "lax", "none")


def cookie_samesite() -> str:
    """返回合法的 SameSite 取值（小写）。

    优先读环境变量，其次读 settings，非法值回退 ``lax``。
    """
    raw = os.environ.get("JWT_COOKIE_SAMESITE")
    if raw is None:
        try:
            from src.setting import settings

            raw = getattr(settings, "JWT_COOKIE_SAMESITE", "lax")
        except Exception:  # noqa: BLE001 - 配置不可用时用安全默认值
            raw = "lax"

    value = str(raw or "").strip().lower()
    return value if value in _VALID_SAMESITE else "lax"


def cookie_secure(request=None) -> bool:
    """是否给 Cookie 加 Secure。

    ``SameSite=None`` 必须搭配 Secure，否则浏览器直接丢弃该 Cookie，
    所以这种情况强制返回 True（本地 http 调试请改用 lax/strict）。
    """
    if cookie_samesite() == "none":
        return True

    try:
        from src.setting import settings

        enabled = bool(getattr(settings, "JWT_COOKIE_SECURE", False))
    except Exception:  # noqa: BLE001
        enabled = False

    if not enabled:
        return False

    # 只有确实走 https 时才加 Secure，避免本地 http 调试时 Cookie 失效
    try:
        return bool(request is not None and request.url.scheme == "https")
    except Exception:  # noqa: BLE001
        return False
