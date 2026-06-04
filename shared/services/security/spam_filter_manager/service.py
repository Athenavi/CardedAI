"""
垃圾评论过滤服务核心逻辑
组合多种检测策略进行综合判断
"""

from datetime import datetime
from typing import Dict, Any, Optional

from shared.services.security.spam_filter_manager.strategies import (
    KeywordStrategy,
    LinkDensityStrategy,
    DuplicateStrategy,
    FrequencyStrategy,
    HoneypotStrategy,
    UserAgentStrategy
)


class SpamFilterService:
    """
    垃圾评论过滤服务
    
    使用多种策略检测垃圾评论:
    1. 关键词过滤
    2. 链接密度检测
    3. 重复内容检测
    4. IP频率限制
    5. 用户行为分析
    6. 蜜罐检测
    7. User-Agent检测
    """

    def __init__(self):
        # 初始化检测策略
        self.keyword_strategy = KeywordStrategy()
        self.link_strategy = LinkDensityStrategy(max_links=3)
        self.duplicate_strategy = DuplicateStrategy(time_window=60)
        self.frequency_strategy = FrequencyStrategy(max_per_minute=5)
        self.honeypot_strategy = HoneypotStrategy()
        self.ua_strategy = UserAgentStrategy()

        # IP黑白名单
        self.ip_blacklist: set = set()
        self.ip_whitelist: set = set()

        # 配置参数
        self.min_comment_length = 5
        self.max_comment_length = 5000
        self.min_comment_interval = 10
        self.enable_honeypot = True
        self.enable_ua_check = True

    def check_spam(
            self,
            content: str,
            user_id: Optional[int] = None,
            ip_address: Optional[str] = None,
            user_agent: Optional[str] = None,
            honeypot_data: Optional[Dict[str, str]] = None,
            submit_time: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        检查评论是否为垃圾评论
        
        Returns:
            {
                "is_spam": bool,
                "confidence": float (0-1),
                "reasons": List[str],
                "action": "approve" | "moderate" | "reject"
            }
        """
        reasons = []
        confidence = 0.0

        # 0. 检查IP黑名单/白名单
        if ip_address:
            if ip_address in self.ip_blacklist:
                return {
                    "is_spam": True,
                    "confidence": 1.0,
                    "reasons": [f"IP地址 {ip_address} 在黑名单中"],
                    "action": "reject",
                    "timestamp": datetime.now().isoformat()
                }
            if ip_address in self.ip_whitelist:
                return {
                    "is_spam": False,
                    "confidence": 0.0,
                    "reasons": [],
                    "action": "approve",
                    "timestamp": datetime.now().isoformat()
                }

        # 1. 蜜罐检测
        if self.enable_honeypot and honeypot_data:
            result = self.honeypot_strategy.check(honeypot_data=honeypot_data)
            reasons.extend(result['reasons'])
            confidence += result['confidence']

        # 2. User-Agent检测
        if self.enable_ua_check and user_agent:
            result = self.ua_strategy.check(user_agent=user_agent)
            reasons.extend(result['reasons'])
            confidence += result['confidence']

        # 3. 内容长度检查
        length_result = self._check_content_length(content)
        reasons.extend(length_result['reasons'])
        confidence += length_result['confidence']

        # 4. 关键词检测
        result = self.keyword_strategy.check(content=content)
        reasons.extend(result['reasons'])
        confidence += result['confidence']

        # 5. 链接密度检测
        result = self.link_strategy.check(content=content)
        reasons.extend(result['reasons'])
        confidence += result['confidence']

        # 6. 重复内容检测
        if ip_address:
            result = self.duplicate_strategy.check(content=content)
            reasons.extend(result['reasons'])
            confidence += result['confidence']

        # 7. IP频率检测
        if ip_address:
            result = self.frequency_strategy.check(ip_address=ip_address)
            reasons.extend(result['reasons'])
            confidence += result['confidence']

        # 8. 提交间隔检测
        if ip_address and submit_time:
            result = self._check_submit_interval(ip_address, submit_time)
            reasons.extend(result['reasons'])
            confidence += result['confidence']

        # 9. 未登录用户增加风险
        if user_id is None:
            confidence += 0.1
            reasons.append("未登录用户")

        # 确定最终结果
        is_spam = confidence >= 0.6
        action = self._determine_action(confidence)

        # 记录提交
        if ip_address:
            self.duplicate_strategy.record_submission(content)
            self.frequency_strategy.record_submission(ip_address)

        return {
            "is_spam": is_spam,
            "confidence": min(confidence, 1.0),
            "reasons": reasons,
            "action": action,
            "timestamp": datetime.now().isoformat()
        }

    def _check_content_length(self, content: str) -> Dict[str, Any]:
        """检查内容长度"""
        reasons = []
        confidence = 0.0

        if len(content) < self.min_comment_length:
            reasons.append(f"评论内容过短({len(content)}字符)")
            confidence += 0.3

        if len(content) > self.max_comment_length:
            reasons.append(f"评论内容过长({len(content)}字符)")
            confidence += 0.2

        return {"is_spam": confidence > 0, "confidence": confidence, "reasons": reasons}

    def _check_submit_interval(self, ip_address: str, submit_time: float) -> Dict[str, Any]:
        """检查提交时间间隔"""
        reasons = []
        confidence = 0.0

        if ip_address in self.frequency_strategy.ip_submissions:
            last_submit_time = self.frequency_strategy.ip_submissions[ip_address][-1]
            interval = submit_time - last_submit_time.timestamp()

            if 0 < interval < self.min_comment_interval:
                reasons.append(f"提交间隔过短({interval:.1f}秒, 最小{self.min_comment_interval}秒)")
                confidence += 0.5

        return {"is_spam": confidence > 0, "confidence": confidence, "reasons": reasons}

    def _determine_action(self, confidence: float) -> str:
        """根据置信度决定操作"""
        if confidence >= 0.8:
            return "reject"
        elif confidence >= 0.6:
            return "moderate"
        else:
            return "approve"

    def get_stats(self) -> Dict[str, Any]:
        """获取过滤器统计信息"""
        return {
            "cached_hashes": len(self.duplicate_strategy.recent_submissions),
            "tracked_ips": len(self.frequency_strategy.ip_submissions),
            "blacklisted_ips": len(self.ip_blacklist),
            "whitelisted_ips": len(self.ip_whitelist),
            "spam_keywords_count": len(self.keyword_strategy.spam_keywords) +
                                   len(self.keyword_strategy.spam_keywords_cn),
            "config": {
                "max_links_per_comment": self.link_strategy.max_links,
                "duplicate_time_window": self.duplicate_strategy.time_window,
                "max_submissions_per_minute": self.frequency_strategy.max_per_minute,
                "min_comment_length": self.min_comment_length,
                "max_comment_length": self.max_comment_length,
                "min_comment_interval": self.min_comment_interval,
                "enable_honeypot": self.enable_honeypot,
                "enable_ua_check": self.enable_ua_check
            }
        }

    def add_ip_to_blacklist(self, ip_address: str) -> bool:
        """添加IP到黑名单"""
        self.ip_blacklist.add(ip_address)
        self.ip_whitelist.discard(ip_address)
        return True

    def remove_ip_from_blacklist(self, ip_address: str) -> bool:
        """从黑名单移除IP"""
        self.ip_blacklist.discard(ip_address)
        return True

    def add_ip_to_whitelist(self, ip_address: str) -> bool:
        """添加IP到白名单"""
        self.ip_whitelist.add(ip_address)
        self.ip_blacklist.discard(ip_address)
        return True

    def remove_ip_from_whitelist(self, ip_address: str) -> bool:
        """从白名单移除IP"""
        self.ip_whitelist.discard(ip_address)
        return True

    def update_config(self, config: Dict[str, Any]) -> bool:
        """更新过滤器配置"""
        try:
            if 'max_links_per_comment' in config:
                self.link_strategy.max_links = int(config['max_links_per_comment'])
            if 'duplicate_time_window' in config:
                self.duplicate_strategy.time_window = int(config['duplicate_time_window'])
            if 'max_submissions_per_minute' in config:
                self.frequency_strategy.max_per_minute = int(config['max_submissions_per_minute'])
            if 'min_comment_length' in config:
                self.min_comment_length = int(config['min_comment_length'])
            if 'max_comment_length' in config:
                self.max_comment_length = int(config['max_comment_length'])
            if 'min_comment_interval' in config:
                self.min_comment_interval = int(config['min_comment_interval'])
            if 'enable_honeypot' in config:
                self.enable_honeypot = bool(config['enable_honeypot'])
            if 'enable_ua_check' in config:
                self.enable_ua_check = bool(config['enable_ua_check'])
            return True
        except Exception as e:
            print(f"更新配置失败: {e}")
            return False
