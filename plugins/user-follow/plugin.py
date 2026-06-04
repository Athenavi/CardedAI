"""
用户关注系统插件
用户关注功能，支持关注作者、获取动态推送
"""

import time
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any

from shared.services.plugins.plugin_manager.core import BasePlugin, plugin_hooks


class UserFollowPlugin(BasePlugin):
    """
    用户关注系统插件
    
    功能:
    1. 关注/取消关注
    2. 粉丝列表管理
    3. 关注动态推送
    4. 关注数量统计
    5. 推荐关注用户
    6. 私信功能基础
    """

    def __init__(self):
        super().__init__(
            plugin_id=0,
            name="用户关注系统",
            slug="user-follow",
            version="1.0.0"
        )

        # 默认设置
        self.settings = {
            'enable_follow': True,
            'enable_notifications': True,
            'enable_feed': True,
            'max_follow_per_day': 50,  # 每天最大关注数
            'enable_recommendations': True,
            'recommendation_count': 10,
            'allow_private_messages': False,
        }

        # 关注关系 {follower_id: {following_id: timestamp}}
        self.follows: Dict[str, Dict[str, float]] = defaultdict(dict)

        # 粉丝关系 {user_id: {follower_id: timestamp}}
        self.followers: Dict[str, Dict[str, float]] = defaultdict(dict)

        # 关注计数 {user_id: {'following': count, 'followers': count}}
        self.follow_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: {'following': 0, 'followers': 0})

        # 动态推送 {user_id: [activity, ...]}
        self.feed: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # 今日关注计数 {user_id: count}
        self.daily_follow_counts: Dict[str, int] = defaultdict(int)
        self.last_reset_date = datetime.now().strftime('%Y-%m-%d')

    def register_hooks(self):
        """注册钩子"""
        # 用户发布文章时推送到粉丝动态
        plugin_hooks.add_action(
            "article_published",
            self.on_article_published,
            priority=10
        )

        # 用户发表评论时推送到粉丝动态
        plugin_hooks.add_action(
            "comment_created",
            self.on_comment_created,
            priority=10
        )

        # 每日清理任务
        plugin_hooks.add_action(
            "daily_cleanup",
            self.reset_daily_counts,
            priority=10
        )

    def activate(self):
        """激活插件"""
        super().activate()
        print("[UserFollow] Plugin activated")

    def deactivate(self):
        """停用插件"""
        super().deactivate()
        print("[UserFollow] Plugin deactivated")

    async def follow_user(self, follower_id: str, following_id: str) -> Dict[str, Any]:
        """
        关注用户
        
        Args:
            follower_id: 关注者ID
            following_id: 被关注者ID
            
        Returns:
            结果 {success: bool, message: str}
        """
        if not self.settings.get('enable_follow'):
            return {'success': False, 'message': '关注功能已禁用'}

        # 不能关注自己
        if follower_id == following_id:
            return {'success': False, 'message': '不能关注自己'}

        # 检查是否已经关注
        if following_id in self.follows.get(follower_id, {}):
            return {'success': False, 'message': '已经关注了该用户'}

        # 检查每日限制
        if not self._check_daily_limit(follower_id):
            return {'success': False, 'message': '今日关注数已达上限'}

        current_time = time.time()

        # 添加关注关系
        self.follows[follower_id][following_id] = current_time
        self.followers[following_id][follower_id] = current_time

        # 更新计数
        self.follow_counts[follower_id]['following'] += 1
        self.follow_counts[following_id]['followers'] += 1

        # 增加今日计数
        self.daily_follow_counts[follower_id] += 1

        # 发送通知
        if self.settings.get('enable_notifications'):
            await self._send_notification(following_id, {
                'type': 'new_follower',
                'follower_id': follower_id,
                'timestamp': datetime.now().isoformat(),
            })

        print(f"[UserFollow] User {follower_id} followed {following_id}")

        return {
            'success': True,
            'message': '关注成功',
            'counts': self.get_follow_counts(follower_id)
        }

    def unfollow_user(self, follower_id: str, following_id: str) -> Dict[str, Any]:
        """
        取消关注
        
        Args:
            follower_id: 关注者ID
            following_id: 被关注者ID
            
        Returns:
            结果
        """
        if following_id not in self.follows.get(follower_id, {}):
            return {'success': False, 'message': '未关注该用户'}

        # 移除关注关系
        del self.follows[follower_id][following_id]
        if following_id in self.followers:
            if follower_id in self.followers[following_id]:
                del self.followers[following_id][follower_id]

        # 更新计数
        self.follow_counts[follower_id]['following'] -= 1
        self.follow_counts[following_id]['followers'] -= 1

        return {
            'success': True,
            'message': '取消关注成功',
            'counts': self.get_follow_counts(follower_id)
        }

    def is_following(self, follower_id: str, following_id: str) -> bool:
        """
        检查是否关注
        
        Args:
            follower_id: 关注者ID
            following_id: 被关注者ID
            
        Returns:
            是否关注
        """
        return following_id in self.follows.get(follower_id, {})

    def get_following_list(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取关注列表
        
        Args:
            user_id: 用户ID
            limit: 返回数量
            offset: 偏移量
            
        Returns:
            关注的用户列表
        """
        following_ids = list(self.follows.get(user_id, {}).keys())

        result = []
        for following_id in following_ids[offset:offset + limit]:
            result.append({
                'user_id': following_id,
                'followed_at': datetime.fromtimestamp(self.follows[user_id][following_id]).isoformat(),
            })

        return result

    def get_followers_list(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取粉丝列表
        
        Args:
            user_id: 用户ID
            limit: 返回数量
            offset: 偏移量
            
        Returns:
            粉丝列表
        """
        follower_ids = list(self.followers.get(user_id, {}).keys())

        result = []
        for follower_id in follower_ids[offset:offset + limit]:
            result.append({
                'user_id': follower_id,
                'followed_at': datetime.fromtimestamp(self.followers[user_id][follower_id]).isoformat(),
            })

        return result

    def get_follow_counts(self, user_id: str) -> Dict[str, int]:
        """
        获取关注计数
        
        Args:
            user_id: 用户ID
            
        Returns:
            计数 {following, followers}
        """
        return self.follow_counts.get(user_id, {'following': 0, 'followers': 0})

    def get_user_feed(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取用户动态
        
        Args:
            user_id: 用户ID
            limit: 返回数量
            offset: 偏移量
            
        Returns:
            动态列表
        """
        if not self.settings.get('enable_feed'):
            return []

        activities = self.feed.get(user_id, [])

        # 按时间排序
        sorted_activities = sorted(activities, key=lambda x: x['timestamp'], reverse=True)

        return sorted_activities[offset:offset + limit]

    def on_article_published(self, article_data: Dict[str, Any]):
        """
        文章发布时的处理
        
        Args:
            article_data: 文章数据 {author_id, title, url}
        """
        if not self.settings.get('enable_feed'):
            return

        author_id = article_data.get('author_id') or article_data.get('user_id')
        if not author_id:
            return

        # 获取作者的粉丝
        fans = self.followers.get(author_id, {})

        # 为每个粉丝添加动态
        activity = {
            'type': 'article_published',
            'author_id': author_id,
            'article_title': article_data.get('title', ''),
            'article_url': article_data.get('url', ''),
            'timestamp': time.time(),
            'created_at': datetime.now().isoformat(),
        }

        for fan_id in fans.keys():
            self.feed[fan_id].append(activity)

            # 限制动态数量（保留最近100条）
            if len(self.feed[fan_id]) > 100:
                self.feed[fan_id] = self.feed[fan_id][-100:]

        print(f"[UserFollow] Pushed article to {len(fans)} followers")

    async def on_comment_created(self, comment_data: Dict[str, Any]):
        """
        评论创建时的处理
        
        Args:
            comment_data: 评论数据 {user_id, article_id, article_title, content}
        """
        if not self.settings.get('enable_feed'):
            return

        user_id = comment_data.get('user_id') or comment_data.get('author_id')
        if not user_id:
            return

        # 获取用户的粉丝
        fans = self.followers.get(str(user_id), {})

        # 为每个粉丝添加动态
        activity = {
            'type': 'comment_created',
            'user_id': user_id,
            'article_id': comment_data.get('article_id'),
            'article_title': comment_data.get('article_title', ''),
            'comment_preview': comment_data.get('content', '')[:100],
            'timestamp': time.time(),
            'created_at': datetime.now().isoformat(),
        }

        for fan_id in fans.keys():
            self.feed[fan_id].append(activity)

            # 限制动态数量（保留最近100条）
            if len(self.feed[fan_id]) > 100:
                self.feed[fan_id] = self.feed[fan_id][-100:]

            # 发送通知
            if self.settings.get('enable_notifications'):
                await self._send_notification(fan_id, {
                    'type': 'comment_created',
                    'user_id': user_id,
                    'article_title': comment_data.get('article_title', ''),
                    'comment_preview': comment_data.get('content', '')[:50],
                })

        print(f"[UserFollow] Pushed comment to {len(fans)} followers")

    def get_recommendations(self, user_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """
        获取推荐关注的用户
        
        Args:
            user_id: 用户ID
            limit: 返回数量
            
        Returns:
            推荐用户列表
        """
        if not self.settings.get('enable_recommendations'):
            return []

        limit = limit or self.settings.get('recommendation_count', 10)

        # 简单的推荐算法：关注了你关注的人也关注的用户
        following = set(self.follows.get(user_id, {}).keys())

        # 统计共同关注
        candidate_scores = defaultdict(int)

        for following_id in following:
            # 获取此人关注的人
            their_following = self.follows.get(following_id, {})

            for candidate_id in their_following.keys():
                if candidate_id != user_id and candidate_id not in following:
                    candidate_scores[candidate_id] += 1

        # 按分数排序
        sorted_candidates = sorted(
            candidate_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        result = []
        for candidate_id, score in sorted_candidates[:limit]:
            result.append({
                'user_id': candidate_id,
                'score': score,
                'reason': f'{score} 个你关注的人也关注了他',
            })

        return result

    def reset_daily_counts(self):
        """重置每日计数"""
        current_date = datetime.now().strftime('%Y-%m-%d')

        if current_date != self.last_reset_date:
            self.daily_follow_counts.clear()
            self.last_reset_date = current_date
            print("[UserFollow] Daily follow counts reset")

    def _check_daily_limit(self, user_id: str) -> bool:
        """检查每日关注限制"""
        max_follow = self.settings.get('max_follow_per_day', 50)
        return self.daily_follow_counts.get(user_id, 0) < max_follow

    async def _send_notification(self, user_id: str, notification: Dict[str, Any]):
        """
        发送通知
        
        Args:
            user_id: 接收者用户ID
            notification: 通知数据
        """
        try:
            from src.notification import create_notification

            # 根据通知类型创建不同的通知
            notif_type = notification.get('type', 'info')

            if notif_type == 'new_follower':
                follower_id = notification.get('follower_id', '')
                title = '新粉丝'
                content = f'用户 {follower_id} 开始关注你'
                severity = 'info'
            elif notif_type == 'article_published':
                author_id = notification.get('author_id', '')
                article_title = notification.get('article_title', '')
                title = '关注的作者发布了新文章'
                content = f'{author_id} 发布了新文章: {article_title}'
                severity = 'info'
            elif notif_type == 'comment_created':
                user_id = notification.get('user_id', '')
                article_title = notification.get('article_title', '')
                comment_preview = notification.get('comment_preview', '')
                title = '关注的用户发表了评论'
                content = f'{user_id} 在《{article_title}》中评论: {comment_preview}'
                severity = 'info'
            else:
                title = '新通知'
                content = str(notification)
                severity = 'info'

            # 创建通知
            await create_notification(
                recipient_id=int(user_id),
                title=title,
                content=content,
                notification_type=severity,
                data=notification
            )

            print(f"[UserFollow] Notification sent to user {user_id}: {title}")

        except ImportError:
            # 如果通知系统不可用，只打印日志
            print(f"[UserFollow] Notification system not available. Notification: {notification}")
        except Exception as e:
            print(f"[UserFollow] Failed to send notification: {e}")
            import traceback
            traceback.print_exc()

    def get_settings_ui(self) -> Dict[str, Any]:
        """返回设置界面配置"""
        return {
            'fields': [
                {
                    'key': 'enable_follow',
                    'type': 'boolean',
                    'label': '启用关注功能',
                },
                {
                    'key': 'enable_notifications',
                    'type': 'boolean',
                    'label': '启用通知',
                },
                {
                    'key': 'enable_feed',
                    'type': 'boolean',
                    'label': '启用动态推送',
                },
                {
                    'key': 'max_follow_per_day',
                    'type': 'number',
                    'label': '每日最大关注数',
                    'min': 10,
                    'max': 200,
                },
                {
                    'key': 'enable_recommendations',
                    'type': 'boolean',
                    'label': '启用推荐关注',
                },
                {
                    'key': 'allow_private_messages',
                    'type': 'boolean',
                    'label': '允许私信',
                },
            ],
            'actions': [
                {
                    'type': 'button',
                    'label': '查看统计',
                    'action': 'view_stats',
                    'variant': 'outline',
                },
            ]
        }


# 插件实例
plugin_instance = UserFollowPlugin()
