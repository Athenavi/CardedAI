"""
垃圾评论检测策略
每个策略独立实现一种检测方法
"""

import hashlib
import re
from datetime import datetime
from typing import Dict, Any, List


class DetectionStrategy:
    """检测策略基类"""

    def check(self, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError


class KeywordStrategy(DetectionStrategy):
    """关键词检测策略"""

    def __init__(self):
        self.spam_keywords = [
            'viagra', 'cialis', 'casino', 'poker', 'lottery',
            'cheap meds', 'buy now', 'click here', 'free money',
            'earn money', 'work from home', 'make money fast',
            'weight loss', 'diet pill', 'sex enhancement',
            'replica watch', 'fake id', 'counterfeit'
        ]
        self.spam_keywords_cn = [
            '代开发票', '赌博', '博彩', '彩票', '色情',
            '刷单', '兼职', '赚钱', '贷款', '信用卡套现',
            '高仿', 'A货', '假证', '迷药', '枪支'
        ]

    def check(self, content: str, **kwargs) -> Dict[str, Any]:
        reasons = []
        confidence = 0.0
        content_lower = content.lower()

        spam_count = 0
        for keyword in self.spam_keywords:
            if keyword in content_lower:
                spam_count += 1
                reasons.append(f"包含敏感关键词: {keyword}")

        for keyword in self.spam_keywords_cn:
            if keyword in content:
                spam_count += 1
                reasons.append(f"包含敏感关键词: {keyword}")

        if spam_count > 0:
            confidence = min(0.3 * spam_count, 0.9)

        return {
            "is_spam": spam_count > 0,
            "confidence": confidence,
            "reasons": reasons
        }


class LinkDensityStrategy(DetectionStrategy):
    """链接密度检测策略"""

    def __init__(self, max_links: int = 3):
        self.max_links = max_links
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )

    def check(self, content: str, **kwargs) -> Dict[str, Any]:
        reasons = []
        confidence = 0.0

        urls = self.url_pattern.findall(content)
        url_count = len(urls)

        if url_count > self.max_links:
            reasons.append(f"包含过多链接({url_count}个)")
            confidence += 0.4

        if len(content) > 0:
            url_length = sum(len(url) for url in urls)
            url_ratio = url_length / len(content)

            if url_ratio > 0.5:
                reasons.append(f"链接密度过高({url_ratio:.0%})")
                confidence += 0.3

        return {
            "is_spam": confidence > 0,
            "confidence": confidence,
            "reasons": reasons
        }


class DuplicateStrategy(DetectionStrategy):
    """重复内容检测策略"""

    def __init__(self, time_window: int = 60):
        self.time_window = time_window
        self.recent_submissions: Dict[str, datetime] = {}

    def check(self, content: str, **kwargs) -> Dict[str, Any]:
        reasons = []
        confidence = 0.0

        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()

        if content_hash in self.recent_submissions:
            last_submit = self.recent_submissions[content_hash]
            time_diff = (datetime.now() - last_submit).total_seconds()

            if time_diff < self.time_window:
                reasons.append(f"短时间内重复提交相同内容({time_diff:.0f}秒前)")
                confidence += 0.7

        return {
            "is_spam": confidence > 0,
            "confidence": confidence,
            "reasons": reasons
        }

    def record_submission(self, content: str):
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        self.recent_submissions[content_hash] = datetime.now()

        # 清理过期记录
        now = datetime.now()
        expired = [h for h, t in self.recent_submissions.items()
                   if (now - t).total_seconds() > 300]
        for h in expired:
            del self.recent_submissions[h]


class FrequencyStrategy(DetectionStrategy):
    """IP频率检测策略"""

    def __init__(self, max_per_minute: int = 5):
        self.max_per_minute = max_per_minute
        self.ip_submissions: Dict[str, List[datetime]] = {}

    def check(self, ip_address: str, **kwargs) -> Dict[str, Any]:
        reasons = []
        confidence = 0.0

        if ip_address in self.ip_submissions:
            now = datetime.now()
            recent = [t for t in self.ip_submissions[ip_address]
                      if (now - t).total_seconds() < 60]

            if len(recent) >= self.max_per_minute:
                reasons.append(f"IP提交频率过高({len(recent)}次/分钟)")
                confidence += 0.6

        return {
            "is_spam": confidence > 0,
            "confidence": confidence,
            "reasons": reasons
        }

    def record_submission(self, ip_address: str):
        now = datetime.now()
        if ip_address not in self.ip_submissions:
            self.ip_submissions[ip_address] = []

        self.ip_submissions[ip_address].append(now)

        # 清理过旧记录
        self.ip_submissions[ip_address] = [
            t for t in self.ip_submissions[ip_address]
            if (now - t).total_seconds() < 600
        ]


class HoneypotStrategy(DetectionStrategy):
    """蜜罐检测策略"""

    def __init__(self, honeypot_fields: List[str] = None):
        self.honeypot_fields = honeypot_fields or [
            'website_url', 'phone_field', 'comment_extra'
        ]

    def check(self, honeypot_data: Dict[str, str], **kwargs) -> Dict[str, Any]:
        reasons = []
        confidence = 0.0

        for field_name in self.honeypot_fields:
            if field_name in honeypot_data and honeypot_data[field_name]:
                reasons.append(f"蜜罐字段 '{field_name}' 被填写(疑似机器人)")
                confidence = 1.0
                break

        return {
            "is_spam": confidence > 0,
            "confidence": confidence,
            "reasons": reasons
        }


class UserAgentStrategy(DetectionStrategy):
    """User-Agent检测策略"""

    def __init__(self):
        self.suspicious_patterns = [
            r'bot', r'crawler', r'spider', r'scraper',
            r'curl', r'wget', r'python-requests',
            r'java/', r'libwww', r'httpclient'
        ]

    def check(self, user_agent: str, **kwargs) -> Dict[str, Any]:
        reasons = []
        confidence = 0.0

        if not user_agent or len(user_agent.strip()) == 0:
            reasons.append("User-Agent为空")
            confidence += 0.4
            return {
                "is_spam": confidence > 0,
                "confidence": confidence,
                "reasons": reasons
            }

        ua_lower = user_agent.lower()
        for pattern in self.suspicious_patterns:
            if re.search(pattern, ua_lower, re.IGNORECASE):
                reasons.append(f"可疑User-Agent: 匹配模式 '{pattern}'")
                confidence += 0.5
                break

        return {
            "is_spam": confidence > 0,
            "confidence": confidence,
            "reasons": reasons
        }
