"""
API 采集器

通用 REST API 采集，支持认证（Bearer/Basic/API Key）、分页、速率限制。
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

try:
    import httpx
except ImportError:
    httpx = None

from shared.services.intel.collectors.base import BaseCollector, CollectedItemData

logger = logging.getLogger(__name__)


class APICollector(BaseCollector):
    """通用 REST API 采集器"""

    source_type = "api"

    async def collect(self, source_config: Dict[str, Any], url: str) -> List[CollectedItemData]:
        """
        通过 REST API 采集数据。

        Args:
            source_config: 配置项：
                - method: HTTP 方法（默认 GET）
                - headers: 额外请求头
                - auth_type: 认证类型 (none/bearer/basic/api_key)
                - auth_token: 认证令牌/密钥
                - auth_header: API Key 的 Header 名称（默认 X-API-Key）
                - params: 查询参数
                - body: 请求体（POST 时使用）
                - data_path: JSON 响应中数据数组的路径（如 "data.items"）
                - title_field: 条目中标题的字段名
                - content_field: 条目中内容的字段名
                - url_field: 条目中 URL 的字段名
                - pagination_type: 分页类型 (none/offset/page_token/link_header)
                - page_size: 每页大小
                - max_pages: 最大页数（默认 10）
                - rate_limit: 每秒最大请求数（默认 5）
                - timeout: 请求超时秒数（默认 30）
            url: API URL

        Returns:
            List[CollectedItemData]
        """
        if httpx is None:
            logger.error("httpx 未安装，无法采集 API")
            return []

        method = source_config.get("method", "GET").upper()
        timeout = source_config.get("timeout", 30)
        max_pages = source_config.get("max_pages", 10)
        rate_limit = source_config.get("rate_limit", 5)
        data_path = source_config.get("data_path", "")
        title_field = source_config.get("title_field", "title")
        content_field = source_config.get("content_field", "content")
        url_field = source_config.get("url_field", "url")
        pagination_type = source_config.get("pagination_type", "none")

        headers = dict(source_config.get("headers", {}))
        auth_headers = self._build_auth_headers(source_config)
        headers.update(auth_headers)

        params = dict(source_config.get("params", {}))
        body = source_config.get("body")

        all_items: List[CollectedItemData] = []
        page = 0

        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                current_url = url
                current_params = dict(params)

                while page < max_pages:
                    # 速率限制
                    if page > 0 and rate_limit > 0:
                        await asyncio.sleep(1.0 / rate_limit)

                    if method == "GET":
                        resp = await client.get(current_url, headers=headers, params=current_params)
                    elif method == "POST":
                        resp = await client.post(current_url, headers=headers, params=current_params, json=body)
                    else:
                        logger.error(f"不支持的 HTTP 方法: {method}")
                        return []

                    if resp.status_code != 200:
                        logger.warning(f"API 请求失败 ({resp.status_code}): {current_url}")
                        break

                    data = resp.json()

                    # 提取数据数组
                    records = self._extract_data(data, data_path)
                    if not records:
                        break

                    for record in records:
                        item = self._build_item(
                            url=str(record.get(url_field, url)),
                            title=str(record.get(title_field, "")),
                            content=str(record.get(content_field, "")),
                            raw_record=record,
                        )
                        all_items.append(item)

                    # 分页处理
                    next_url, next_params = self._handle_pagination(
                        data, resp.headers, pagination_type, current_url, current_params, page
                    )

                    if next_url is None and next_params is None:
                        break

                    if next_url:
                        current_url = next_url
                    if next_params:
                        current_params = next_params

                    page += 1

        except Exception as e:
            logger.error(f"API 采集异常 {url}: {e}")

        logger.info(f"API 采集完成 {url}: {len(all_items)} 条")
        return all_items

    def _build_auth_headers(self, config: Dict[str, Any]) -> Dict[str, str]:
        """构建认证请求头"""
        auth_type = config.get("auth_type", "none")
        auth_token = config.get("auth_token", "")

        if auth_type == "none" or not auth_token:
            return {}

        if auth_type == "bearer":
            return {"Authorization": f"Bearer {auth_token}"}

        if auth_type == "basic":
            return {"Authorization": f"Basic {auth_token}"}

        if auth_type == "api_key":
            header_name = config.get("auth_header", "X-API-Key")
            return {header_name: auth_token}

        return {}

    @staticmethod
    def _extract_data(data: Any, data_path: str) -> List[Dict]:
        """从 JSON 响应中按路径提取数据数组"""
        if not data_path:
            if isinstance(data, list):
                return data
            # 尝试常见的 key
            for key in ("data", "items", "results", "records"):
                if isinstance(data, dict) and key in data and isinstance(data[key], list):
                    return data[key]
            return []

        # 按点号路径提取，如 "data.items"
        current = data
        for part in data_path.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return []

        return current if isinstance(current, list) else []

    @staticmethod
    def _handle_pagination(
        data: Any,
        headers: Dict[str, str],
        pagination_type: str,
        current_url: str,
        current_params: Dict[str, Any],
        page: int,
    ) -> tuple:
        """
        处理分页逻辑。

        Returns:
            (next_url, next_params) — 如果没有下一页，返回 (None, None)
        """
        if pagination_type == "none":
            return None, None

        if pagination_type == "offset":
            page_size = current_params.get("limit", current_params.get("per_page", 20))
            offset = (page + 1) * page_size
            if isinstance(data, dict):
                total = data.get("total", data.get("count", None))
                if total is not None and offset >= total:
                    return None, None
            new_params = dict(current_params)
            new_params["offset"] = offset
            return current_url, new_params

        if pagination_type == "page_token":
            next_token = None
            if isinstance(data, dict):
                next_token = data.get("next_page_token", data.get("nextToken", data.get("cursor")))
            if not next_token:
                return None, None
            new_params = dict(current_params)
            new_params["page_token"] = next_token
            return current_url, new_params

        if pagination_type == "link_header":
            link_header = headers.get("link", "")
            if 'rel="next"' in link_header:
                # 解析 Link header: <url>; rel="next"
                for part in link_header.split(","):
                    if 'rel="next"' in part:
                        next_url = part.split(";")[0].strip().strip("<>")
                        return next_url, current_params
            return None, None

        return None, None

    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证 API 采集器配置"""
        auth_type = config.get("auth_type", "none")
        if auth_type != "none" and not config.get("auth_token"):
            logger.warning("API 采集器认证类型为 {auth_type} 但未提供 auth_token")
            return False
        return True
