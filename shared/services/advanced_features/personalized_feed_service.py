"""
个性化动态流服务
提供基于关注的个性化内容推荐和动态流
"""


from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List

from src.unified_logger import default_logger as logger


class PersonalizedFeedService:
    """个性化动态流服务"""

    def __init__(self):
        # 用户关注关系 {follower_id: [following_id, ...]}
        self._followings = defaultdict(set)

        # 用户粉丝关系 {following_id: [follower_id, ...]}
        self._followers = defaultdict(set)

        # 动态事件 {event_id: event_info}
        self._events = {}

        # 用户动态流缓存 {user_id: [event_id, ...]}
        self._user_feeds = defaultdict(list)

        # 事件ID计数器
        self._event_counter = 0

    def follow_user(self, follower_id: int, following_id: int) -> bool:
        """
        关注用户
        
        Args:
            follower_id: 关注者ID
            following_id: 被关注者ID
            
        Returns:
            是否成功
        """
        if follower_id == following_id:
            return False

        self._followings[follower_id].add(following_id)
        self._followers[following_id].add(follower_id)

        logger.info(f"User {follower_id} followed user {following_id}")
        return True

    def unfollow_user(self, follower_id: int, following_id: int) -> bool:
        """
        取消关注
        
        Args:
            follower_id: 关注者ID
            following_id: 被关注者ID
            
        Returns:
            是否成功
        """
        if following_id in self._followings[follower_id]:
            self._followings[follower_id].discard(following_id)
            self._followers[following_id].discard(follower_id)

            logger.info(f"User {follower_id} unfollowed user {following_id}")
            return True

        return False

    def is_following(self, follower_id: int, following_id: int) -> bool:
        """
        检查是否关注
        
        Args:
            follower_id: 关注者ID
            following_id: 被关注者ID
            
        Returns:
            是否关注
        """
        return following_id in self._followings.get(follower_id, set())

    def get_followings(self, user_id: int) -> List[int]:
        """
        获取关注列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            关注的用户ID列表
        """
        return list(self._followings.get(user_id, set()))

    def get_followers(self, user_id: int) -> List[int]:
        """
        获取粉丝列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            粉丝用户ID列表
        """
        return list(self._followers.get(user_id, set()))

    def create_event(self, event_type: str, actor_id: int,
                     target_id: int = None, content: Dict = None) -> str:
        """
        创建动态事件
        
        Args:
            event_type: 事件类型(article_published/commented/liked/followed)
            actor_id: 发起者ID
            target_id: 目标ID(文章ID/评论ID/用户ID等)
            content: 事件内容
            
        Returns:
            事件ID
        """
        self._event_counter += 1
        event_id = f"event_{self._event_counter}_{int(datetime.now().timestamp())}"

        now = datetime.now()
        event = {
            'event_id': event_id,
            'event_type': event_type,
            'actor_id': actor_id,
            'target_id': target_id,
            'content': content or {},
            'created_at': now,
        }

        self._events[event_id] = event

        # 推送到粉丝的动态流
        self._push_to_followers(event_id, actor_id)

        logger.info(f"Created event {event_id}: {event_type} by user {actor_id}")
        return event_id

    def _push_to_followers(self, event_id: str, actor_id: int):
        """
        将事件推送到粉丝的动态流
        
        Args:
            event_id: 事件ID
            actor_id: 发起者ID
        """
        followers = self._followers.get(actor_id, set())

        for follower_id in followers:
            # 插入到动态流开头(最新的在前)
            self._user_feeds[follower_id].insert(0, event_id)

            # 限制动态流长度(最多保留500条)
            if len(self._user_feeds[follower_id]) > 500:
                self._user_feeds[follower_id] = self._user_feeds[follower_id][:500]

    def get_user_feed(self, user_id: int, limit: int = 50,
                      offset: int = 0, event_type: str = None) -> List[Dict]:
        """
        获取用户个性化动态流
        
        Args:
            user_id: 用户ID
            limit: 返回数量
            offset: 偏移量
            event_type: 事件类型过滤(可选)
            
        Returns:
            动态流列表
        """
        event_ids = self._user_feeds.get(user_id, [])

        # 分页
        paginated_ids = event_ids[offset:offset + limit]

        # 获取事件详情
        feed = []
        for event_id in paginated_ids:
            event = self._events.get(event_id)
            if not event:
                continue

            # 类型过滤
            if event_type and event['event_type'] != event_type:
                continue

            feed.append({
                'event_id': event['event_id'],
                'event_type': event['event_type'],
                'actor_id': event['actor_id'],
                'target_id': event['target_id'],
                'content': event['content'],
                'created_at': event['created_at'].isoformat(),
                'time_ago': self._get_time_ago(event['created_at']),
            })

        return feed

    def _get_time_ago(self, dt: datetime) -> str:
        """
        计算相对时间
        
        Args:
            dt: 日期时间
            
        Returns:
            相对时间字符串
        """
        now = datetime.now()
        diff = now - dt
        seconds = int(diff.total_seconds())

        if seconds < 60:
            return '刚刚'
        elif seconds < 3600:
            minutes = seconds // 60
            return f'{minutes}分钟前'
        elif seconds < 86400:
            hours = seconds // 3600
            return f'{hours}小时前'
        elif seconds < 604800:
            days = seconds // 86400
            return f'{days}天前'
        else:
            return dt.strftime('%Y-%m-%d')

    def get_mutual_followings(self, user_id: int, other_user_id: int) -> List[int]:
        """
        获取共同关注
        
        Args:
            user_id: 用户ID
            other_user_id: 另一个用户ID
            
        Returns:
            共同关注的用户ID列表
        """
        my_followings = self._followings.get(user_id, set())
        their_followings = self._followings.get(other_user_id, set())

        return list(my_followings & their_followings)

    def get_feed_stats(self, user_id: int) -> Dict:
        """
        获取动态流统计
        
        Args:
            user_id: 用户ID
            
        Returns:
            统计数据
        """
        event_ids = self._user_feeds.get(user_id, [])

        # 统计各类型事件数量
        type_counts = defaultdict(int)
        for event_id in event_ids:
            event = self._events.get(event_id)
            if event:
                type_counts[event['event_type']] += 1

        return {
            'total_events': len(event_ids),
            'type_distribution': dict(type_counts),
            'following_count': len(self._followings.get(user_id, set())),
            'follower_count': len(self._followers.get(user_id, set())),
        }

    def clear_old_events(self, days: int = 90):
        """
        清理旧事件
        
        Args:
            days: 保留天数
        """
        cutoff = datetime.now() - timedelta(days=days)

        # 清理过期事件
        expired_events = [
            event_id for event_id, event in self._events.items()
            if event['created_at'] < cutoff
        ]

        for event_id in expired_events:
            del self._events[event_id]

        # 清理用户动态流中的引用
        for user_id in self._user_feeds.keys():
            self._user_feeds[user_id] = [
                eid for eid in self._user_feeds[user_id]
                if eid in self._events
            ]

        logger.info(f"Cleared {len(expired_events)} old events")


# 全局实例
personalized_feed_service = PersonalizedFeedService()
