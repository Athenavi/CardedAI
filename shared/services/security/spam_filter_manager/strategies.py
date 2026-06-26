"""简化的垃圾评论过滤策略（个人站长轻量版）"""
import re
from typing import Optional


class SpamStrategy:
    """基础垃圾评论检测策略"""

    @staticmethod
    def check_content(content: str) -> tuple[bool, Optional[str]]:
        """检查内容是否含垃圾信息"""
        if not content:
            return False, None

        # 常见垃圾关键词（中文）
        spam_keywords = [
            '免费领取', '点击这里', '立即购买', '加微信', '微信号',
            '兼职', '日赚', '月入', '彩票', '赌博', '色情',
        ]
        for kw in spam_keywords:
            if kw in content:
                return True, f'包含垃圾关键词: {kw}'

        # 过多URL链接
        url_count = len(re.findall(r'https?://', content))
        if url_count > 3:
            return True, f'链接过多: {url_count}个'

        # 纯英文垃圾评论（俄语/阿拉伯语等非中文非英文也被拦截）
        non_chinese_ratio = sum(1 for c in content if ord(c) > 127 and not (0x4e00 <= ord(c) <= 0x9fff)) / max(len(content), 1)
        if non_chinese_ratio > 0.8 and len(content) > 10:
            return True, '非中文内容占比过高'

        return False, None


class RateLimitStrategy:
    """频率限制策略"""

    @staticmethod
    def is_rate_limited(ip: str, max_per_minute: int = 5) -> bool:
        """简单频率检查（由调用方维护计数器）"""
        return False  # 简化版不做频率限制
