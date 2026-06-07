"""
RSS/Atom 采集器

使用 feedparser 解析 RSS/Atom 源，支持增量采集（基于 etag/last-modified）。
"""

import importlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from shared.services.intel.collectors.base import BaseCollector, CollectedItemData

logger = logging.getLogger(__name__)


def _get_feedparser():
    """运行时懒导入 feedparser（支持安装后无需重启服务器即可生效）"""
    try:
        return importlib.import_module("feedparser")
    except ImportError:
        return None


def _get_httpx():
    """运行时懒导入 httpx（支持安装后无需重启服务器即可生效）"""
    try:
        return importlib.import_module("httpx")
    except ImportError:
        return None


class RSSCollector(BaseCollector):
    """RSS/Atom 采集器"""

    source_type = "rss"

    async def collect(self, source_config: Dict[str, Any], url: str) -> List[CollectedItemData]:
        """
        采集 RSS/Atom 源。

        Args:
            source_config: 配置项：
                - etag: 上次采集的 ETag（用于增量采集）
                - last_modified: 上次采集的 Last-Modified（用于增量采集）
                - max_entries: 最大条目数（默认 100）
                - timeout: 请求超时秒数（默认 30）
            url: RSS/Atom Feed URL

        Returns:
            List[CollectedItemData]
        """
        fp = _get_feedparser()
        if fp is None:
            logger.error("feedparser 未安装，无法采集 RSS 源（请执行: pip install feedparser）")
            return []

        hx = _get_httpx()
        if hx is None:
            logger.error("httpx 未安装，无法发起 HTTP 请求（请执行: pip install httpx）")
            return []

        etag = source_config.get("etag")
        last_modified = source_config.get("last_modified")
        max_entries = source_config.get("max_entries", 100)
        timeout = source_config.get("timeout", 30)

        headers = {}
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified

        try:
            async with hx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)

                # 304 Not Modified — 无新内容
                if resp.status_code == 304:
                    logger.info(f"RSS 源无新内容 (304): {url}")
                    return []

                if resp.status_code != 200:
                    logger.warning(f"RSS 源请求失败 ({resp.status_code}): {url}")
                    return []

                feed = fp.parse(resp.text)

        except Exception as e:
            logger.error(f"RSS 采集异常 {url}: {e}")
            return []

        items: List[CollectedItemData] = []
        for entry in feed.entries[:max_entries]:
            entry_url = entry.get("link", "")
            title = entry.get("title", "")
            # 优先使用 content，否则 summary
            content = ""
            if entry.get("content"):
                content = entry.content[0].get("value", "")
            if not content:
                content = entry.get("summary", "")

            published = entry.get("published_parsed") or entry.get("updated_parsed")
            published_str = ""
            if published:
                try:
                    published_str = datetime(*published[:6], tzinfo=timezone.utc).isoformat()
                except Exception:
                    published_str = str(published)

            item = self._build_item(
                url=entry_url,
                title=title,
                content=content,
                published=published_str,
                author=entry.get("author", ""),
                categories=[t.get("term", "") for t in entry.get("tags", [])],
            )
            items.append(item)

        logger.info(f"RSS 采集完成 {url}: {len(items)} 条")
        return items

    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """RSS 采集器配置验证 — URL 已在外层校验，此处无特殊配置"""
        return True
