"""
通知频率限制服务 - 防止邮件轰炸
"""

import os
import time
from typing import Dict

from shared.utils.logger import get_logger

logger = get_logger(__name__)


class NotificationRateLimiter:
    """
    通知频率限制器
    
    功能：
    1. 限制同一用户接收通知的频率
    2. 限制同一文章的通知总数
    3. 支持多种限制策略
    """

    def __init__(self):
        # 从环境变量读取配置
        self.max_emails_per_user_per_hour = int(
            os.getenv('NOTIFICATION_MAX_EMAILS_PER_USER_PER_HOUR', '4')
        )
        self.min_email_interval_seconds = int(
            os.getenv('NOTIFICATION_MIN_EMAIL_INTERVAL_SECONDS', '900')  # 15分钟
        )
        self.max_inbox_notifications_per_user = int(
            os.getenv('NOTIFICATION_MAX_INBOX_PER_USER', '5')
        )

        # 内存存储（生产环境应使用Redis）
        self.user_email_times: Dict[str, list] = {}  # 用户邮件发送时间
        self.user_inbox_counts: Dict[int, int] = {}  # 用户站内信数量 {user_id: count}
        self.pending_notifications: Dict[str, list] = {}  # 待聚合通知 {user_email: [notifications]}

    def can_send_email(self, user_email: str) -> tuple:
        """
        检查是否可以给用户发送邮件通知
        
        Args:
            user_email: 用户邮箱
            
        Returns:
            tuple: (can_send: bool, reason: str, pending_count: int)
        """
        now = time.time()

        # 清理过期记录（1小时前）
        one_hour_ago = now - 3600
        if user_email in self.user_email_times:
            self.user_email_times[user_email] = [
                t for t in self.user_email_times[user_email]
                if t > one_hour_ago
            ]

        # 检查每小时限制（4封/小时）
        recent_count = len(self.user_email_times.get(user_email, []))
        if recent_count >= self.max_emails_per_user_per_hour:
            # 检查是否有待聚合的通知
            pending = self.pending_notifications.get(user_email, [])
            return False, f"已达到每小时{self.max_emails_per_user_per_hour}封邮件的限制", len(pending)

        # 检查最小间隔（15分钟）
        if user_email in self.user_email_times and self.user_email_times[user_email]:
            last_time = max(self.user_email_times[user_email])
            if now - last_time < self.min_email_interval_seconds:
                remaining = int(self.min_email_interval_seconds - (now - last_time))
                pending = self.pending_notifications.get(user_email, [])
                return False, f"发送过于频繁，请{remaining // 60}分钟后再试", len(pending)

        return True, "可以发送", 0

    def can_add_inbox_notification(self, user_id: int) -> tuple:
        """
        检查是否可以添加站内通知
        
        Args:
            user_id: 用户ID
            
        Returns:
            tuple: (can_add: bool, should_aggregate: bool, reason: str)
        """
        current_count = self.user_inbox_counts.get(user_id, 0)

        if current_count >= self.max_inbox_notifications_per_user:
            return False, True, f"已达到{self.max_inbox_notifications_per_user}条站内信限制，将聚合通知"

        return True, False, "可以添加"

    def can_notify_for_article(self, article_id: int) -> tuple:
        """
        检查是否可以给文章发送通知（已废弃，保留兼容）
        
        Args:
            article_id: 文章ID
            
        Returns:
            tuple: (can_send: bool, reason: str)
        """
        return True, "可以发送"

    def record_email_sent(self, user_email: str):
        """
        记录已发送的邮件
        
        Args:
            user_email: 用户邮箱
        """
        now = time.time()

        if user_email not in self.user_email_times:
            self.user_email_times[user_email] = []
        self.user_email_times[user_email].append(now)

        logger.info(f"记录邮件发送: {user_email}")

    def add_pending_notification(self, user_email: str, notification_data: dict):
        """
        添加待聚合的通知
        
        Args:
            user_email: 用户邮箱
            notification_data: 通知数据
        """
        if user_email not in self.pending_notifications:
            self.pending_notifications[user_email] = []

        self.pending_notifications[user_email].append({
            'data': notification_data,
            'timestamp': time.time()
        })

        logger.info(f"添加待聚合通知: {user_email}, 当前待聚合数量: {len(self.pending_notifications[user_email])}")

    def get_and_clear_pending(self, user_email: str) -> list:
        """
        获取并清除待聚合通知
        
        Args:
            user_email: 用户邮箱
            
        Returns:
            list: 待聚合通知列表
        """
        pending = self.pending_notifications.pop(user_email, [])
        return pending

    def increment_inbox_count(self, user_id: int):
        """
        增加站内信计数
        
        Args:
            user_id: 用户ID
        """
        if user_id not in self.user_inbox_counts:
            self.user_inbox_counts[user_id] = 0
        self.user_inbox_counts[user_id] += 1

    def reset_inbox_count(self, user_id: int):
        """
        重置站内信计数（当用户查看后）
        
        Args:
            user_id: 用户ID
        """
        self.user_inbox_counts[user_id] = 0

    def get_user_notification_count(self, user_email: str) -> int:
        """获取用户最近1小时的邮件数量"""
        now = time.time()
        one_hour_ago = now - 3600

        if user_email not in self.user_email_times:
            return 0

        return len([
            t for t in self.user_email_times[user_email]
            if t > one_hour_ago
        ])

    def get_pending_count(self, user_email: str) -> int:
        """获取待聚合通知数量"""
        return len(self.pending_notifications.get(user_email, []))

    def reset_limits(self, user_email: str = None):
        """
        重置限制（管理员功能）
        
        Args:
            user_email: 用户邮箱（可选）
        """
        if user_email:
            self.user_email_times.pop(user_email, None)
            self.pending_notifications.pop(user_email, None)
            logger.info(f"重置用户通知限制: {user_email}")
        else:
            self.user_email_times.clear()
            self.user_inbox_counts.clear()
            self.pending_notifications.clear()
            logger.info("重置所有通知限制")


# 全局实例
notification_rate_limiter = NotificationRateLimiter()
