"""
搜索引擎数据采集器

通过搜索引擎 API（或模拟搜索）采集数据。
支持 Google Custom Search、Bing Search API 等。

配置示例 (config JSON):
    {
        "engine": "google",
        "api_key": "...",
        "cx": "...",
        "query": "AI news",
        "max_results": 10,
        "language": "zh"
    }
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from shared.services.intel.collectors.base import BaseCollector, CollectedItemData

logger = logging.getLogger(__name__)

SEARCH_ENGINES = {
    "google": {
        "url": "https://www.googleapis.com/customsearch/v1",
        "params": ["key", "cx", "q", "num", "lr", "start"],
    },
    "bing": {
        "url": "https://api.bing.microsoft.com/v7.0/search",
        "params": ["q", "count", "offset", "mkt"],
    },
}


class SearchCollector(BaseCollector):
    """搜索引擎数据采集器"""
    source_type = "search"

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        errors = []
        engine = config.get("engine", "google")
        if engine not in SEARCH_ENGINES:
            errors.append(f"不支持的搜索引擎: {engine} (支持: {', '.join(SEARCH_ENGINES.keys())})")
        if engine == "google" and not config.get("api_key"):
            errors.append("Google 搜索需要 api_key")
        if engine == "google" and not config.get("cx"):
            errors.append("Google 搜索需要 cx (Custom Search Engine ID)")
        if not config.get("query"):
            errors.append("需要搜索关键词 (query)")
        return errors

    async def collect(self, config: Dict[str, Any]) -> List[CollectedItemData]:
        engine_name = config.get("engine", "google")
        query = config.get("query", "")
        max_results = min(int(config.get("max_results", 10)), 50)
        language = config.get("language", "zh")
        engine = SEARCH_ENGINES[engine_name]

        items: List[CollectedItemData] = []

        try:
            if engine_name == "google":
                items = await self._collect_google(engine, config, query, max_results, language)
            elif engine_name == "bing":
                items = await self._collect_bing(engine, config, query, max_results, language)
        except Exception as e:
            logger.error(f"[SearchCollector] 采集失败: {e}")
            raise

        return items

    async def _collect_google(
        self, engine: Dict, config: Dict, query: str, max_results: int, language: str
    ) -> List[CollectedItemData]:
        items: List[CollectedItemData] = []
        params = {
            "key": config["api_key"],
            "cx": config["cx"],
            "q": query,
            "num": min(max_results, 10),
            "lr": f"lang_{language}" if language else None,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            for start in range(1, max_results, 10):
                params["start"] = start
                try:
                    resp = await client.get(engine["url"], params=params)
                    resp.raise_for_status()
                    data = resp.json()

                    for result in data.get("items", []):
                        link = result.get("link", "")
                        title = result.get("title", "")
                        snippet = result.get("snippet", "")
                        if link:
                            items.append(CollectedItemData(
                                url=link,
                                title=title,
                                content_raw=snippet,
                                metadata={
                                    "source": "google_search",
                                    "query": query,
                                    "display_link": result.get("displayLink", ""),
                                },
                            ))
                except Exception as e:
                    logger.warning(f"[SearchCollector] Google 分页 {start} 失败: {e}")

        return items

    async def _collect_bing(
        self, engine: Dict, config: Dict, query: str, max_results: int, language: str
    ) -> List[CollectedItemData]:
        items: List[CollectedItemData] = []
        headers = {"Ocp-Apim-Subscription-Key": config.get("api_key", "")}
        mkt = {"zh": "zh-CN", "en": "en-US", "ja": "ja-JP"}.get(language, "zh-CN")

        async with httpx.AsyncClient(timeout=30.0) as client:
            for offset in range(0, max_results, 10):
                params = {"q": query, "count": 10, "offset": offset, "mkt": mkt}
                try:
                    resp = await client.get(engine["url"], params=params, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()

                    for result in data.get("webPages", {}).get("value", []):
                        url = result.get("url", "")
                        title = result.get("name", "")
                        snippet = result.get("snippet", "")
                        if url:
                            items.append(CollectedItemData(
                                url=url,
                                title=title,
                                content_raw=snippet,
                                metadata={
                                    "source": "bing_search",
                                    "query": query,
                                },
                            ))
                except Exception as e:
                    logger.warning(f"[SearchCollector] Bing 分页 {offset} 失败: {e}")

        return items
