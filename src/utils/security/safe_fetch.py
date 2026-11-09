"""
带 SSRF 防护的 httpx 请求辅助

出站请求的两类风险：
1. 初始 URL 直接指向内网 / 回环 / 云元数据地址
2. 公网地址返回 3xx，把请求重定向到内网地址

因此这里禁用 httpx 的自动重定向，改为手工跟随，并在**每一跳**重新校验主机。
"""

from typing import Any
from urllib.parse import urljoin

from src.unified_logger import default_logger as logger
from src.utils.security.safe import assert_safe_outbound_url

_MAX_REDIRECTS = 3
_REDIRECT_CODES = (301, 302, 303, 307, 308)


async def safe_request(
    client: Any,
    method: str,
    url: str,
    *,
    max_redirects: int = _MAX_REDIRECTS,
    **kwargs: Any,
) -> Any:
    """发起经过 SSRF 校验的请求，返回 httpx.Response。

    :raises ValueError: URL 非法、指向内网地址，或重定向次数超限
    """
    kwargs.pop("follow_redirects", None)
    current_url = assert_safe_outbound_url(url)
    current_method = method.upper()

    for _ in range(max_redirects + 1):
        resp = await client.request(
            current_method, current_url, follow_redirects=False, **kwargs
        )

        if resp.status_code not in _REDIRECT_CODES:
            return resp

        location = resp.headers.get("location")
        if not location:
            return resp

        next_url = urljoin(current_url, location)
        # 关键：重定向目标同样必须是公网地址
        assert_safe_outbound_url(next_url)

        logger.debug(f"出站请求跟随重定向: {current_url} -> {next_url}")
        await resp.aclose()

        # 303 语义：后续请求改为 GET，且丢弃请求体
        if resp.status_code == 303:
            current_method = "GET"
            for key in ("json", "data", "content", "files"):
                kwargs.pop(key, None)

        current_url = next_url

    raise ValueError("重定向次数过多")
