"""简化的敏感词服务（个人站长轻量版）"""
from typing import Optional


class SensitiveWordService:
    """敏感词过滤服务"""

    def __init__(self):
        self._words: list[str] = []

    def check_text(self, text: str) -> tuple[bool, Optional[str]]:
        """检查文本是否含敏感词"""
        for word in self._words:
            if word in text:
                return True, word
        return False, None

    async def check_content(self, content: str) -> dict:
        """
        检查内容是否含敏感词（异步，兼容原有调用方）。
        返回: {has_sensitive: bool, actions: list[str], words_found: list[str]}
        """
        found_words = []
        for word in self._words:
            if word in content:
                found_words.append(word)
        has = len(found_words) > 0
        return {
            "has_sensitive": has,
            "actions": ["block"] if has else [],
            "words_found": found_words,
        }

    async def filter_content(self, content: str) -> tuple[str, list[str]]:
        """过滤内容中的敏感词（替换为 ***）"""
        result = content
        found = []
        for word in self._words:
            if word in result:
                result = result.replace(word, "***")
                found.append(word)
        return result, found

    def reload_words(self) -> None:
        pass


# 全局单例
sensitive_word_service = SensitiveWordService()
