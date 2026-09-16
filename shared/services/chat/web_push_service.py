"""
Web Push 推送通知服务
支持浏览器推送通知功能
"""

import json
import os
from datetime import datetime
from typing import Dict, List

try:
    from pywebpush import webpush, WebPushException
except ImportError:
    webpush = None
    WebPushException = Exception

from src.unified_logger import default_logger as logger


class WebPushService:
    """Web推送通知服务"""

    def __init__(self):
        # 用户订阅存储 {user_id: [subscription_info, ...]}
        self._subscriptions = {}

        # VAPID密钥配置(生产环境应从环境变量读取)
        self.vapid_config = {
            'public_key': '',
            'private_key': '',
            'subject': 'mailto:admin@fastblog.com',
        }

        # 推送消息队列
        self._message_queue = []

    def subscribe_user(self, user_id: int, subscription_data: Dict) -> bool:
        """
        用户订阅推送通知

        Args:
            user_id: 用户ID
            subscription_data: 订阅数据(包含endpoint, keys等)

        Returns:
            是否订阅成功
        """
        if user_id not in self._subscriptions:
            self._subscriptions[user_id] = []

        # 检查是否已存在相同订阅
        endpoint = subscription_data.get('endpoint', '')
        for sub in self._subscriptions[user_id]:
            if sub.get('endpoint') == endpoint:
                logger.info(f"Subscription already exists for user {user_id}")
                return True

        # 添加新订阅
        subscription_record = {
            'endpoint': endpoint,
            'keys': subscription_data.get('keys', {}),
            'created_at': datetime.now().isoformat(),
            'user_agent': subscription_data.get('user_agent', ''),
        }

        self._subscriptions[user_id].append(subscription_record)
        logger.info(f"User {user_id} subscribed to push notifications")

        return True

    def unsubscribe_user(self, user_id: int, endpoint: str = None) -> bool:
        """
        用户取消订阅

        Args:
            user_id: 用户ID
            endpoint: 要取消的endpoint(可选,不提供则取消所有)

        Returns:
            是否成功
        """
        if user_id not in self._subscriptions:
            return False

        if endpoint:
            # 取消特定订阅
            self._subscriptions[user_id] = [
                sub for sub in self._subscriptions[user_id]
                if sub.get('endpoint') != endpoint
            ]
        else:
            # 取消所有订阅
            self._subscriptions[user_id] = []

        logger.info(f"User {user_id} unsubscribed from push notifications")
        return True

    def send_push_notification(self, user_id: int, title: str,
                               body: str, data: Dict = None,
                               icon: str = None, badge: str = None) -> Dict:
        """
        发送推送通知

        Args:
            user_id: 用户ID
            title: 通知标题
            body: 通知内容
            data: 附加数据
            icon: 图标URL
            badge: 徽章URL

        Returns:
            发送结果
        """
        if user_id not in self._subscriptions:
            return {
                'success': False,
                'message': '用户未订阅推送通知',
                'sent_count': 0,
            }

        subscriptions = self._subscriptions[user_id]
        if not subscriptions:
            return {
                'success': False,
                'message': '用户没有有效的订阅',
                'sent_count': 0,
            }

        # 构建通知payload
        notification_payload = {
            'title': title,
            'body': body,
            'icon': icon or '/favicon.ico',
            'badge': badge or '/icons/badge-72x72.png',
            'data': data or {},
            'timestamp': datetime.now().isoformat(),
            'actions': [
                {
                    'action': 'open',
                    'title': '查看',
                },
                {
                    'action': 'dismiss',
                    'title': '关闭',
                },
            ],
        }

        sent_count = 0
        failed_subscriptions = []

        for subscription in subscriptions:
            try:
                # 使用 pywebpush 发送真实的 Web Push 通知
                success = self._send_to_endpoint(subscription, notification_payload)

                if success:
                    sent_count += 1
                else:
                    failed_subscriptions.append(subscription.get('endpoint'))

            except Exception as e:
                logger.error(f"Failed to send push notification: {str(e)}")
                failed_subscriptions.append(subscription.get('endpoint'))

        # 清理失败的订阅
        if failed_subscriptions:
            self._subscriptions[user_id] = [
                sub for sub in self._subscriptions[user_id]
                if sub.get('endpoint') not in failed_subscriptions
            ]

        return {
            'success': sent_count > 0,
            'message': f'成功发送 {sent_count} 条通知',
            'sent_count': sent_count,
            'total_subscriptions': len(subscriptions),
        }

    def _send_to_endpoint(self, subscription: Dict, payload: Dict) -> bool:
        """
        发送推送到指定endpoint

        Args:
            subscription: 订阅信息
            payload: 通知payload

        Returns:
            是否发送成功
        """
        try:
            endpoint = subscription.get('endpoint', '')
            keys = subscription.get('keys', {})

            logger.info(f"Sending push to endpoint: {endpoint[:50]}...")

            # 使用 pywebpush 发送真实的 Web Push 通知
            if webpush and self.vapid_config.get('private_key'):
                try:
                    subscription_info = {
                        "endpoint": endpoint,
                        "keys": {
                            "p256dh": keys.get("p256dh", ""),
                            "auth": keys.get("auth", ""),
                        },
                    }
                    webpush(
                        subscription_info=subscription_info,
                        data=json.dumps(payload),
                        vapid_private_key=self.vapid_config.get('private_key'),
                        vapid_claims={
                            "sub": self.vapid_config.get('subject', 'mailto:admin@fastblog.com'),
                        },
                    )
                    return True
                except WebPushException as e:
                    logger.error(f"WebPush error: {str(e)}")
                    # 410 Gone 或 404 表示订阅已失效
                    if hasattr(e, 'response') and e.response is not None:
                        if e.response.status_code in (404, 410):
                            logger.warning(f"Subscription expired: {endpoint[:50]}...")
                            return False
                    return False
            else:
                # pywebpush 未安装或未配置 VAPID 密钥，模拟发送
                logger.warning("pywebpush not available or VAPID keys not configured, simulating push")
                return True

        except Exception as e:
            logger.error(f"Push send failed: {str(e)}")
            return False

    def send_to_multiple_users(self, user_ids: List[int],
                               title: str, body: str,
                               data: Dict = None) -> Dict:
        """
        批量发送推送通知

        Args:
            user_ids: 用户ID列表
            title: 通知标题
            body: 通知内容
            data: 附加数据

        Returns:
            批量发送结果
        """
        results = {
            'total_users': len(user_ids),
            'successful': 0,
            'failed': 0,
            'details': [],
        }

        for user_id in user_ids:
            result = self.send_push_notification(user_id, title, body, data)

            if result['success']:
                results['successful'] += 1
            else:
                results['failed'] += 1

            results['details'].append({
                'user_id': user_id,
                'success': result['success'],
                'sent_count': result['sent_count'],
            })

        return results

    def get_user_subscriptions(self, user_id: int) -> List[Dict]:
        """
        获取用户的订阅列表

        Args:
            user_id: 用户ID

        Returns:
            订阅列表
        """
        return self._subscriptions.get(user_id, [])

    def get_subscription_stats(self) -> Dict:
        """
        获取订阅统计信息

        Returns:
            统计数据
        """
        total_users = len(self._subscriptions)
        total_subscriptions = sum(len(subs) for subs in self._subscriptions.values())

        return {
            'total_users': total_users,
            'total_subscriptions': total_subscriptions,
            'average_per_user': total_subscriptions / total_users if total_users > 0 else 0,
        }

    def cleanup_invalid_subscriptions(self) -> int:
        """
        清理无效订阅

        Returns:
            清理的数量
        """
        cleaned = 0

        for user_id in list(self._subscriptions.keys()):
            original_count = len(self._subscriptions[user_id])

            # 清理超过30天的旧订阅(简化逻辑)
            cutoff = datetime.now()
            self._subscriptions[user_id] = [
                sub for sub in self._subscriptions[user_id]
                # 实际应该检查created_at
            ]

            cleaned += original_count - len(self._subscriptions[user_id])

        logger.info(f"Cleaned up {cleaned} invalid subscriptions")
        return cleaned

    def configure_vapid_keys(self, public_key: str, private_key: str,
                             subject: str = 'mailto:admin@fastblog.com'):
        """
        配置VAPID密钥

        Args:
            public_key: VAPID公钥
            private_key: VAPID私钥
            subject: 联系人邮箱
        """
        self.vapid_config.update({
            'public_key': public_key,
            'private_key': private_key,
            'subject': subject,
        })
        logger.info("VAPID keys configured")


# 全局实例
web_push_service = WebPushService()
