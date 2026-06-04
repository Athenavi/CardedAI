"""
文本清洗器

HTML 去标签、编码修复、空白规范化。
"""

import html
import logging
import re
from typing import Optional

from shared.services.intel.cleaners.base import BaseCleaner

logger = logging.getLogger(__name__)

# HTML 标签正则
_HTML_TAG_RE = re.compile(r"<[^>]+>")
# 多余空白正则
_MULTI_SPACE_RE = re.compile(r"[ \t]+")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
# 控制字符
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class TextCleaner(BaseCleaner):
    """文本清洗：HTML 去标签、编码修复、空白规范化"""

    name = "text_cleaner"

    def __init__(
        self,
        strip_html: bool = True,
        normalize_whitespace: bool = True,
        fix_encoding: bool = True,
        max_length: int = 0,
    ):
        """
        Args:
            strip_html: 是否去除 HTML 标签
            normalize_whitespace: 是否规范化空白字符
            fix_encoding: 是否修复 HTML 实体编码
            max_length: 最大内容长度（0 表示不限制）
        """
        self.strip_html = strip_html
        self.normalize_whitespace = normalize_whitespace
        self.fix_encoding = fix_encoding
        self.max_length = max_length

    async def clean(
        self,
        item_id: int,
        content: str,
        title: str = "",
        metadata: Optional[dict] = None,
    ) -> dict:
        original_content = content
        original_title = title

        if not content:
            return {
                "content": content,
                "title": title,
                "metadata": metadata or {},
                "changed": False,
            }

        # 1. 去除控制字符
        content = _CONTROL_CHAR_RE.sub("", content)
        title = _CONTROL_CHAR_RE.sub("", title)

        # 2. 修复 HTML 实体编码
        if self.fix_encoding:
            content = html.unescape(content)
            title = html.unescape(title)

        # 3. 去除 HTML 标签
        if self.strip_html:
            content = _HTML_TAG_RE.sub("", content)
            title = _HTML_TAG_RE.sub("", title)

        # 4. 规范化空白
        if self.normalize_whitespace:
            content = _MULTI_SPACE_RE.sub(" ", content)
            content = _MULTI_NEWLINE_RE.sub("\n\n", content)
            content = content.strip()

            title = _MULTI_SPACE_RE.sub(" ", title)
            title = title.strip()

        # 5. 截断
        if self.max_length > 0 and len(content) > self.max_length:
            content = content[: self.max_length]

        changed = (content != original_content) or (title != original_title)

        return {
            "content": content,
            "title": title,
            "metadata": metadata or {},
            "changed": changed,
        }
