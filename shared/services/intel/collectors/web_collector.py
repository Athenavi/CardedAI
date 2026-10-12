"""
网页爬虫采集器

使用 httpx + BeautifulSoup/selectolax 提取网页内容，
支持 CSS 选择器提取、JavaScript 渲染（Playwright 可选）。
"""

import logging
from typing import Any, Dict, List, Optional

try:
    import httpx
except ImportError:
    httpx = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    from selectolax.parser import HTMLParser as SelectolaxParser
except ImportError:
    SelectolaxParser = None

from shared.services.intel.collectors.base import BaseCollector, CollectedItemData

logger = logging.getLogger(__name__)


class WebCollector(BaseCollector):
    """网页爬虫采集器"""

    source_type = "web"

    async def collect(self, source_config: Dict[str, Any], url: str) -> List[CollectedItemData]:
        """
        采集网页内容。

        Args:
            source_config: 配置项：
                - selector: CSS 选择器（提取文章列表容器）
                - item_selector: 条目选择器（在容器内提取每篇文章链接）
                - title_selector: 标题选择器（文章详情页内）
                - content_selector: 内容选择器（文章详情页内）
                - follow_links: 是否跟踪链接采集详情页（默认 False）
                - max_pages: 最大采集页数（默认 1）
                - timeout: 请求超时秒数（默认 30）
                - user_agent: 自定义 User-Agent
            url: 网页 URL

        Returns:
            List[CollectedItemData]
        """
        if httpx is None:
            logger.error("httpx 未安装，无法采集网页")
            return []

        timeout = source_config.get("timeout", 30)
        user_agent = source_config.get("user_agent", "CardedAI-Collector/1.0")
        headers = {"User-Agent": user_agent}

        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers) as client:
                resp = await client.get(url)

                if resp.status_code != 200:
                    logger.warning(f"网页请求失败 ({resp.status_code}): {url}")
                    return []

                html = resp.text

        except Exception as e:
            logger.error(f"网页采集异常 {url}: {e}")
            return []

        follow_links = source_config.get("follow_links", False)

        if follow_links:
            # 从列表页提取链接，再逐个采集详情页
            return await self._collect_detail_pages(client=None, html=html, source_config=source_config, base_url=url)
        else:
            # 直接从当前页面提取内容
            item = self._extract_from_html(url, html, source_config)
            return [item] if item else []

    async def _collect_detail_pages(
        self,
        client: Optional[Any],
        html: str,
        source_config: Dict[str, Any],
        base_url: str,
    ) -> List[CollectedItemData]:
        """从列表页提取链接并采集详情页"""
        item_selector = source_config.get("item_selector", "a")
        max_pages = source_config.get("max_pages", 10)
        timeout = source_config.get("timeout", 30)
        user_agent = source_config.get("user_agent", "CardedAI-Collector/1.0")

        links = self._extract_links(html, item_selector, base_url)
        links = links[:max_pages]

        items: List[CollectedItemData] = []
        headers = {"User-Agent": user_agent}

        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers) as http_client:
                for link in links:
                    try:
                        resp = await http_client.get(link)
                        if resp.status_code == 200:
                            item = self._extract_from_html(link, resp.text, source_config)
                            if item:
                                items.append(item)
                    except Exception as e:
                        logger.warning(f"详情页采集失败 {link}: {e}")

        except Exception as e:
            logger.error(f"详情页采集批量异常: {e}")

        logger.info(f"网页采集完成 {base_url}: {len(items)} 条（跟踪链接模式）")
        return items

    def _extract_from_html(self, url: str, html: str, config: Dict[str, Any]) -> Optional[CollectedItemData]:
        """从 HTML 中提取标题和内容"""
        title_selector = config.get("title_selector", "title")
        content_selector = config.get("content_selector", "body")

        title = ""
        content = ""

        # 优先使用 BeautifulSoup
        if BeautifulSoup is not None:
            soup = BeautifulSoup(html, "html.parser")
            title_el = soup.select_one(title_selector)
            if title_el:
                title = title_el.get_text(strip=True)
            content_el = soup.select_one(content_selector)
            if content_el:
                content = content_el.get_text(separator="\n", strip=True)
        elif SelectolaxParser is not None:
            tree = SelectolaxParser(html)
            title_node = tree.css_first(title_selector)
            if title_node:
                title = title_node.text(strip=True)
            content_node = tree.css_first(content_selector)
            if content_node:
                content = content_node.text(separator="\n", strip=True)
        else:
            logger.warning("未安装 BeautifulSoup 或 selectolax，无法解析 HTML")
            return None

        if not content:
            return None

        return self._build_item(url=url, title=title, content=content)

    def _extract_links(self, html: str, selector: str, base_url: str) -> List[str]:
        """从 HTML 中提取链接"""
        links: List[str] = []
        if BeautifulSoup is not None:
            soup = BeautifulSoup(html, "html.parser")
            for el in soup.select(selector):
                href = el.get("href", "")
                if href:
                    if href.startswith("/"):
                        # 拼接为绝对 URL
                        from urllib.parse import urljoin
                        href = urljoin(base_url, href)
                    if href.startswith("http"):
                        links.append(href)
        return links

    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证网页采集器配置"""
        # follow_links 模式下需要 item_selector
        if config.get("follow_links") and not config.get("item_selector"):
            logger.warning("网页采集器 follow_links 模式需要 item_selector")
            return False
        return True
