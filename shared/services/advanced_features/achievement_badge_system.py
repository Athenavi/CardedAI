"""
用户成就徽章系统
提供徽章获取、展示、进度追踪等功能
"""


from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

from shared.services.advanced_features.points_system import points_system
from src.unified_logger import default_logger as logger


class AchievementBadgeSystem:
    """成就徽章系统"""

    def __init__(self):
        # 用户已获得的徽章 {user_id: [badge_key, ...]}
        self._user_badges = defaultdict(set)

        # 徽章进度追踪 {user_id: {badge_key: progress}}
        self._badge_progress = defaultdict(lambda: defaultdict(int))

        # 徽章定义
        self._badges = {
            # 发文成就
            'first_article': {
                'name': '初出茅庐',
                'description': '发布第一篇文章',
                'icon': '📝',
                'category': 'writing',
                'requirement': {'type': 'article_count', 'value': 1},
                'points_reward': 20,
            },
            'prolific_writer_10': {
                'name': '多产作家',
                'description': '发布10篇文章',
                'icon': '✍️',
                'category': 'writing',
                'requirement': {'type': 'article_count', 'value': 10},
                'points_reward': 50,
            },
            'prolific_writer_50': {
                'name': '写作达人',
                'description': '发布50篇文章',
                'icon': '🖋️',
                'category': 'writing',
                'requirement': {'type': 'article_count', 'value': 50},
                'points_reward': 100,
            },
            'prolific_writer_100': {
                'name': '百篇大师',
                'description': '发布100篇文章',
                'icon': '👑',
                'category': 'writing',
                'requirement': {'type': 'article_count', 'value': 100},
                'points_reward': 200,
            },

            # 连续发文成就
            'streak_7_days': {
                'name': '持之以恒',
                'description': '连续发文7天',
                'icon': '🔥',
                'category': 'consistency',
                'requirement': {'type': 'posting_streak', 'value': 7},
                'points_reward': 50,
            },
            'streak_30_days': {
                'name': '坚持不懈',
                'description': '连续发文30天',
                'icon': '💪',
                'category': 'consistency',
                'requirement': {'type': 'posting_streak', 'value': 30},
                'points_reward': 150,
            },
            'streak_100_days': {
                'name': '百日坚守',
                'description': '连续发文100天',
                'icon': '🏆',
                'category': 'consistency',
                'requirement': {'type': 'posting_streak', 'value': 100},
                'points_reward': 500,
            },

            # 优质内容认证
            'quality_content_10_likes': {
                'name': '受欢迎',
                'description': '单篇文章获得10个点赞',
                'icon': '❤️',
                'category': 'quality',
                'requirement': {'type': 'max_article_likes', 'value': 10},
                'points_reward': 30,
            },
            'quality_content_100_likes': {
                'name': '热门作者',
                'description': '单篇文章获得100个点赞',
                'icon': '🌟',
                'category': 'quality',
                'requirement': {'type': 'max_article_likes', 'value': 100},
                'points_reward': 100,
            },
            'quality_content_1000_views': {
                'name': '千次浏览',
                'description': '单篇文章达到1000次浏览',
                'icon': '👁️',
                'category': 'quality',
                'requirement': {'type': 'max_article_views', 'value': 1000},
                'points_reward': 80,
            },

            # 社区贡献者徽章
            'active_commenter_50': {
                'name': '活跃评论家',
                'description': '发表50条评论',
                'icon': '💬',
                'category': 'community',
                'requirement': {'type': 'comment_count', 'value': 50},
                'points_reward': 40,
            },
            'active_commenter_200': {
                'name': '评论达人',
                'description': '发表200条评论',
                'icon': '🗣️',
                'category': 'community',
                'requirement': {'type': 'comment_count', 'value': 200},
                'points_reward': 80,
            },
            'helpful_user_20_likes': {
                'name': '乐于助人',
                'description': '评论获得20个点赞',
                'icon': '🤝',
                'category': 'community',
                'requirement': {'type': 'comment_likes', 'value': 20},
                'points_reward': 60,
            },

            # 社交互动徽章
            'social_butterfly_10_followers': {
                'name': '人气博主',
                'description': '获得10个粉丝',
                'icon': '🦋',
                'category': 'social',
                'requirement': {'type': 'follower_count', 'value': 10},
                'points_reward': 50,
            },
            'social_butterfly_100_followers': {
                'name': '意见领袖',
                'description': '获得100个粉丝',
                'icon': '⭐',
                'category': 'social',
                'requirement': {'type': 'follower_count', 'value': 100},
                'points_reward': 150,
            },

            # 特殊成就
            'early_adopter': {
                'name': '早期支持者',
                'description': '在平台上线首月注册',
                'icon': '🎖️',
                'category': 'special',
                'requirement': {'type': 'registration_date', 'value': '2024-01-31'},
                'points_reward': 100,
            },
            'verified_expert': {
                'name': '认证专家',
                'description': '通过领域专家认证',
                'icon': '✅',
                'category': 'special',
                'requirement': {'type': 'manual_award', 'value': True},
                'points_reward': 200,
            },
        }

        # 用户统计数据缓存 {user_id: stats}
        self._user_stats_cache = {}

    def check_and_award_badges(self, user_id: int, stats: Dict = None) -> List[Dict]:
        """
        检查并授予符合条件的徽章
        
        Args:
            user_id: 用户ID
            stats: 用户统计数据(可选，如不提供则使用缓存)
            
        Returns:
            新获得的徽章列表
        """
        if stats is None:
            stats = self._get_user_stats(user_id)

        newly_awarded = []

        for badge_key, badge_def in self._badges.items():
            # 跳过已获得徽章
            if badge_key in self._user_badges[user_id]:
                continue

            # 检查是否满足条件
            if self._check_badge_requirement(badge_key, badge_def, stats):
                # 授予徽章
                self._award_badge(user_id, badge_key, badge_def)
                newly_awarded.append({
                    'badge_key': badge_key,
                    'badge': badge_def,
                })

        return newly_awarded

    def _check_badge_requirement(self, badge_key: str,
                                 badge_def: Dict,
                                 stats: Dict) -> bool:
        """
        检查徽章要求是否满足
        
        Args:
            badge_key: 徽章键
            badge_def: 徽章定义
            stats: 用户统计数据
            
        Returns:
            是否满足要求
        """
        req = badge_def['requirement']
        req_type = req['type']
        req_value = req['value']

        if req_type == 'article_count':
            return stats.get('article_count', 0) >= req_value

        elif req_type == 'posting_streak':
            return stats.get('max_posting_streak', 0) >= req_value

        elif req_type == 'max_article_likes':
            return stats.get('max_article_likes', 0) >= req_value

        elif req_type == 'max_article_views':
            return stats.get('max_article_views', 0) >= req_value

        elif req_type == 'comment_count':
            return stats.get('comment_count', 0) >= req_value

        elif req_type == 'comment_likes':
            return stats.get('total_comment_likes', 0) >= req_value

        elif req_type == 'follower_count':
            return stats.get('follower_count', 0) >= req_value

        elif req_type == 'registration_date':
            reg_date = stats.get('registration_date')
            if not reg_date:
                return False
            cutoff = datetime.fromisoformat(req_value)
            return reg_date <= cutoff

        elif req_type == 'manual_award':
            # 手动授予的徽章需要管理员操作
            return False

        return False

    def _award_badge(self, user_id: int, badge_key: str, badge_def: Dict):
        """
        授予用户徽章
        
        Args:
            user_id: 用户ID
            badge_key: 徽章键
            badge_def: 徽章定义
        """
        self._user_badges[user_id].add(badge_key)

        # 发放积分奖励
        points_reward = badge_def.get('points_reward', 0)
        if points_reward > 0:
            points_system.add_points(
                user_id,
                points_reward,
                f"Badge awarded: {badge_def['name']}"
            )

        logger.info(f"User {user_id} awarded badge: {badge_key}")

    def get_user_badges(self, user_id: int, category: str = None) -> List[Dict]:
        """
        获取用户已获得的徽章
        
        Args:
            user_id: 用户ID
            category: 分类过滤(可选)
            
        Returns:
            徽章列表
        """
        badges = []

        for badge_key in self._user_badges.get(user_id, set()):
            badge_def = self._badges.get(badge_key)
            if badge_def:
                if category and badge_def['category'] != category:
                    continue

                badges.append({
                    'badge_key': badge_key,
                    **badge_def,
                    'awarded_at': badge_data.get('awarded_at', datetime.now().isoformat()),  # Get from database
                })

        return badges

    def get_available_badges(self, category: str = None) -> List[Dict]:
        """
        获取所有可用徽章
        
        Args:
            category: 分类过滤(可选)
            
        Returns:
            徽章列表
        """
        badges = []

        for badge_key, badge_def in self._badges.items():
            if category and badge_def['category'] != category:
                continue

            badges.append({
                'badge_key': badge_key,
                **badge_def,
            })

        return badges

    def get_badge_progress(self, user_id: int, badge_key: str) -> Dict:
        """
        获取徽章完成进度
        
        Args:
            user_id: 用户ID
            badge_key: 徽章键
            
        Returns:
            进度信息
        """
        badge_def = self._badges.get(badge_key)
        if not badge_def:
            return {'error': 'Badge not found'}

        stats = self._get_user_stats(user_id)
        req = badge_def['requirement']

        current_value = self._get_current_value(req['type'], stats)
        required_value = req['value']

        progress = min(100, (current_value / required_value * 100) if required_value > 0 else 0)

        return {
            'badge_key': badge_key,
            'badge_name': badge_def['name'],
            'current_value': current_value,
            'required_value': required_value,
            'progress_percent': round(progress, 2),
            'completed': current_value >= required_value,
        }

    def _get_current_value(self, req_type: str, stats: Dict) -> int:
        """
        获取当前进度值
        
        Args:
            req_type: 要求类型
            stats: 用户统计数据
            
        Returns:
            当前值
        """
        mapping = {
            'article_count': 'article_count',
            'posting_streak': 'max_posting_streak',
            'max_article_likes': 'max_article_likes',
            'max_article_views': 'max_article_views',
            'comment_count': 'comment_count',
            'comment_likes': 'total_comment_likes',
            'follower_count': 'follower_count',
        }

        stat_key = mapping.get(req_type)
        return stats.get(stat_key, 0) if stat_key else 0

    def _get_user_stats(self, user_id: int) -> Dict:
        """
        获取用户统计数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            统计数据
        """
        # Query real data from database
        # Example implementation:
        # from sqlalchemy import select, func
        # from shared.models.article import Article
        # from shared.models.comment import Comment
        # 
        # stmt = select(func.count(Article.id)).where(Article.user_id == user_id)
        # result = await db.execute(stmt)
        # article_count = result.scalar()
        # 
        # return {
        #     'article_count': article_count,
        #     ...
        # }

        # For now, return sample data
        return {
            'article_count': 0,
            'max_posting_streak': 0,
            'max_article_likes': 0,
            'max_article_views': 0,
            'comment_count': 0,
            'total_comment_likes': 0,
            'follower_count': 0,
            'registration_date': datetime.now().isoformat(),
        }

    def manually_award_badge(self, user_id: int, badge_key: str) -> bool:
        """
        手动授予徽章(管理员操作)
        
        Args:
            user_id: 用户ID
            badge_key: 徽章键
            
        Returns:
            是否成功
        """
        if badge_key not in self._badges:
            return False

        if badge_key in self._user_badges[user_id]:
            return False

        badge_def = self._badges[badge_key]
        self._award_badge(user_id, badge_key, badge_def)

        return True

    def get_categories(self) -> List[str]:
        """
        获取所有徽章分类
        
        Returns:
            分类列表
        """
        categories = set()
        for badge_def in self._badges.values():
            categories.add(badge_def['category'])

        return sorted(list(categories))

    def get_badge_details(self, badge_key: str) -> Optional[Dict]:
        """
        获取徽章详细信息
        
        Args:
            badge_key: 徽章键
            
        Returns:
            徽章详情
        """
        badge_def = self._badges.get(badge_key)
        if not badge_def:
            return None

        return {
            'badge_key': badge_key,
            **badge_def,
        }


# 全局实例
achievement_badge_system = AchievementBadgeSystem()
