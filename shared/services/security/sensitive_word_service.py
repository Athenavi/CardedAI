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

    def reload_words(self) -> None:
        pass


# 全局单例
sensitive_word_service = SensitiveWordService()
