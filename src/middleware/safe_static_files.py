"""
受限静态文件服务

`/api/v2/assets/storage` 之前直接挂载了整个 storage 目录，
会把 cache/、analytics/、plugin_state.json 等内部文件一并暴露到公网。

这里只放行明确需要公开的媒体子目录，并对可在浏览器内执行的内容
（HTML / SVG / XML 等）强制以附件形式下载，避免存储型 XSS。
"""

import os
from typing import Iterable

from fastapi import HTTPException
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

# 允许通过静态路由访问的子目录（相对 storage 根）
DEFAULT_PUBLIC_PREFIXES = ("objects", "thumbnails", "optimized")

# 可在浏览器中执行脚本、需要强制下载的内容类型
_UNSAFE_INLINE_TYPES = {
    "text/html",
    "application/xhtml+xml",
    "image/svg+xml",
    "text/xml",
    "application/xml",
    "application/javascript",
    "text/javascript",
}


class MediaStaticFiles(StaticFiles):
    """仅暴露白名单子目录，且对可执行内容强制下载的 StaticFiles"""

    def __init__(
        self,
        directory: str,
        public_prefixes: Iterable[str] = DEFAULT_PUBLIC_PREFIXES,
        **kwargs,
    ):
        super().__init__(directory=directory, **kwargs)
        self.public_prefixes = tuple(p for p in public_prefixes if p)

    async def get_response(self, path: str, scope: Scope) -> Response:
        # 归一化后判断是否落在白名单子目录内，白名单之外一律 404
        normalized = os.path.normpath(path).replace("\\", "/").lstrip("/")
        if normalized == "." or not any(
            normalized == prefix or normalized.startswith(prefix + "/")
            for prefix in self.public_prefixes
        ):
            raise HTTPException(status_code=404)

        response = await super().get_response(normalized, scope)

        # 禁止浏览器对响应体做 MIME 嗅探
        response.headers["X-Content-Type-Options"] = "nosniff"

        content_type = (response.headers.get("content-type") or "").split(";")[0].strip().lower()
        if content_type in _UNSAFE_INLINE_TYPES:
            filename = os.path.basename(normalized)
            response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
            response.headers["Content-Security-Policy"] = "sandbox; default-src 'none'"

        return response


__all__ = ["MediaStaticFiles", "DEFAULT_PUBLIC_PREFIXES"]
