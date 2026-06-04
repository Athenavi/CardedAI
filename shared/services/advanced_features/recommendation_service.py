"""
个性化推荐系统
基于用户行为和内容相似度的文章推荐服务
"""


from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter
import math

from src.unified_logger import default_logger as logger


class RecommendationService:
    """个性化推荐服务"""

    def __init__(self):
        # 用户阅读历史 {user_id: [(article_id, timestamp), ...]}
        self._reading_history = defaultdict(list)

        # 用户点赞历史 {user_id: [article_id, ...]}
        self._like_history = defaultdict(list)

        # 用户收藏历史 {user_id: [article_id, ...]}
        self._bookmark_history = defaultdict(list)

        # 文章特征 {article_id: {'tags': [], 'category': '', 'views': 0, ...}}
        self._article_features = {}

        #  trending 数据缓存
        self._trending_cache = {
            '24h': [],
            '7d': [],
            '30d': [],
            'last_updated': None,
        }

        # 配置参数
        self.trending_window_hours = [24, 168, 720]  # 24h, 7d, 30d
        self.recommendation_count = 10  # 默认推荐数量

    def record_user_action(self, user_id: int, article_id: int,
                           action_type: str = 'view'):
        """
        记录用户行为
        
        Args:
            user_id: 用户ID
            article_id: 文章ID
            action_type: 行为类型 (view, like, bookmark, comment)
        """
        now = datetime.now()

        if action_type == 'view':
            self._reading_history[user_id].append((article_id, now))
            # 保留最近100条记录
            if len(self._reading_history[user_id]) > 100:
                self._reading_history[user_id] = self._reading_history[user_id][-100:]

        elif action_type == 'like':
            if article_id not in self._like_history[user_id]:
                self._like_history[user_id].append(article_id)

        elif action_type == 'bookmark':
            if article_id not in self._bookmark_history[user_id]:
                self._bookmark_history[user_id].append(article_id)

        logger.debug(f"Recorded {action_type} for user {user_id} on article {article_id}")

    def update_article_features(self, article_id: int, features: Dict):
        """
        更新文章特征
        
        Args:
            article_id: 文章ID
            features: 文章特征字典
        """
        self._article_features[article_id] = features

    def get_personalized_recommendations(self, user_id: int,
                                         limit: int = None,
                                         exclude_articles: List[int] = None) -> List[Dict]:
        """
        获取个性化推荐
        
        Args:
            user_id: 用户ID
            limit: 返回数量
            exclude_articles: 要排除的文章ID列表
            
        Returns:
            推荐文章列表(带评分)
        """
        limit = limit or self.recommendation_count
        exclude_articles = exclude_articles or []

        # 获取用户兴趣标签
        user_interests = self._get_user_interests(user_id)

        if not user_interests:
            # 新用户或无历史,返回热门文章
            return self._get_popular_articles(limit, exclude_articles)

        # 计算所有文章的推荐分数
        scored_articles = []

        for article_id, features in self._article_features.items():
            if article_id in exclude_articles:
                continue

            score = self._calculate_recommendation_score(
                user_id, article_id, features, user_interests
            )

            if score > 0:
                scored_articles.append({
                    'article_id': article_id,
                    'score': score,
                    'features': features,
                })

        # 按分数排序
        scored_articles.sort(key=lambda x: x['score'], reverse=True)

        # 返回top N
        return scored_articles[:limit]

    def _get_user_interests(self, user_id: int) -> Dict[str, float]:
        """
        获取用户兴趣标签权重
        
        Args:
            user_id: 用户ID
            
        Returns:
            {tag: weight, ...}
        """
        tag_weights = Counter()

        # 从阅读历史提取兴趣
        for article_id, timestamp in self._reading_history.get(user_id, []):
            if article_id in self._article_features:
                features = self._article_features[article_id]
                tags = features.get('tags', [])

                # 时间衰减:越近的权重越高
                days_ago = (datetime.now() - timestamp).days
                time_weight = max(0.1, 1.0 - (days_ago / 30))  # 30天衰减到0.1

                for tag in tags:
                    tag_weights[tag] += time_weight

        # 从点赞历史提取兴趣(权重更高)
        for article_id in self._like_history.get(user_id, []):
            if article_id in self._article_features:
                features = self._article_features[article_id]
                tags = features.get('tags', [])

                for tag in tags:
                    tag_weights[tag] += 2.0  # 点赞权重是阅读的2倍

        # 从收藏历史提取兴趣(权重最高)
        for article_id in self._bookmark_history.get(user_id, []):
            if article_id in self._article_features:
                features = self._article_features[article_id]
                tags = features.get('tags', [])

                for tag in tags:
                    tag_weights[tag] += 3.0  # 收藏权重是阅读的3倍

        # 归一化权重
        total_weight = sum(tag_weights.values())
        if total_weight > 0:
            tag_weights = {tag: weight / total_weight for tag, weight in tag_weights.items()}

        return dict(tag_weights)

    def _calculate_recommendation_score(self, user_id: int, article_id: int,
                                        features: Dict, user_interests: Dict) -> float:
        """
        计算文章推荐分数
        
        Args:
            user_id: 用户ID
            article_id: 文章ID
            features: 文章特征
            user_interests: 用户兴趣
            
        Returns:
            推荐分数(0-1)
        """
        score = 0.0

        # 1. 标签匹配度 (权重 0.4)
        article_tags = features.get('tags', [])
        tag_match_score = sum(
            user_interests.get(tag, 0)
            for tag in article_tags
        )
        score += tag_match_score * 0.4

        # 2. 分类匹配度 (权重 0.2)
        user_categories = self._get_user_preferred_categories(user_id)
        article_category = features.get('category', '')
        if article_category in user_categories:
            score += 0.2

        # 3. 热度因子 (权重 0.2)
        views = features.get('views', 0)
        likes = features.get('likes', 0)
        popularity_score = min(1.0, (views + likes * 10) / 1000)
        score += popularity_score * 0.2

        # 4. 新鲜度因子 (权重 0.2)
        created_at = features.get('created_at')
        if created_at:
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))

            days_old = (datetime.now() - created_at).days
            freshness_score = max(0.1, 1.0 - (days_old / 90))  # 90天衰减到0.1
            score += freshness_score * 0.2

        return score

    def _get_user_preferred_categories(self, user_id: int) -> List[str]:
        """
        获取用户偏好的分类
        
        Args:
            user_id: 用户ID
            
        Returns:
            偏好分类列表
        """
        category_counts = Counter()

        for article_id, _ in self._reading_history.get(user_id, []):
            if article_id in self._article_features:
                category = self._article_features[article_id].get('category', '')
                if category:
                    category_counts[category] += 1

        # 返回top 3分类
        return [cat for cat, _ in category_counts.most_common(3)]

    def _get_popular_articles(self, limit: int,
                              exclude_articles: List[int] = None) -> List[Dict]:
        """
        获取热门文章(用于冷启动)
        
        Args:
            limit: 返回数量
            exclude_articles: 要排除的文章ID
            
        Returns:
            热门文章列表
        """
        exclude_articles = exclude_articles or []

        # 按浏览量和点赞数排序
        scored_articles = []

        for article_id, features in self._article_features.items():
            if article_id in exclude_articles:
                continue

            views = features.get('views', 0)
            likes = features.get('likes', 0)
            score = views + likes * 10

            scored_articles.append({
                'article_id': article_id,
                'score': score,
                'features': features,
            })

        scored_articles.sort(key=lambda x: x['score'], reverse=True)

        return scored_articles[:limit]

    def get_trending_articles(self, window: str = '24h',
                              limit: int = 10) -> List[Dict]:
        """
        获取Trending文章
        
        Args:
            window: 时间窗口 ('24h', '7d', '30d')
            limit: 返回数量
            
        Returns:
            Trending文章列表
        """
        # 检查缓存
        if window in self._trending_cache and self._trending_cache['last_updated']:
            cache_age = (datetime.now() - self._trending_cache['last_updated']).seconds
            if cache_age < 300:  # 5分钟缓存
                return self._trending_cache[window][:limit]

        # 计算时间范围
        if window == '24h':
            hours = 24
        elif window == '7d':
            hours = 168
        elif window == '30d':
            hours = 720
        else:
            hours = 24

        cutoff = datetime.now() - timedelta(hours=hours)

        # 统计近期热门
        article_scores = Counter()

        for article_id, features in self._article_features.items():
            created_at = features.get('created_at')
            if not created_at:
                continue

            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))

            # 只统计近期文章
            if created_at >= cutoff:
                views = features.get('views', 0)
                likes = features.get('likes', 0)

                # 时间加权:越近的文章权重越高
                hours_old = (datetime.now() - created_at).total_seconds() / 3600
                time_weight = max(0.1, 1.0 - (hours_old / (hours * 2)))

                score = (views + likes * 10) * time_weight
                article_scores[article_id] = score

        # 排序并返回
        trending = [
            {
                'article_id': article_id,
                'score': score,
                'features': self._article_features.get(article_id, {}),
            }
            for article_id, score in article_scores.most_common(limit)
        ]

        # 更新缓存
        self._trending_cache[window] = trending
        self._trending_cache['last_updated'] = datetime.now()

        return trending

    def get_rising_stars(self, limit: int = 10) -> List[Dict]:
        """
        获取Rising Stars(新锐博主)
        基于近期发文数量和互动增长
        
        Args:
            limit: 返回数量
            
        Returns:
            Rising Stars用户列表
        """
        from shared.models.article import Article
        from shared.models.user import User
        from sqlalchemy import select, func
        from datetime import datetime, timedelta

        # 统计最近30天的发文数据
        cutoff_date = datetime.now() - timedelta(days=30)

        try:
            # 查询每个用户的发文数
            result = self.db.execute(
                select(
                    Article.user,
                    func.count(Article.id).label('article_count'),
                    func.max(Article.created_at).label('last_article_date')
                ).filter(
                    Article.created_at >= cutoff_date
                ).group_by(
                    Article.user
                ).order_by(
                    func.count(Article.id).desc()
                ).limit(limit * 2)  # 获取更多以便筛选
            )

            user_stats = result.all()

            rising_stars = []
            for stat in user_stats:
                if stat.article_count >= 2:  # 至少发2篇文章
                    # 获取用户信息
                    user_result = self.db.execute(
                        select(User).where(User.id == stat.user)
                    )
                    user = user_result.scalar_one_or_none()

                    if user:
                        # 计算活跃度分数（发文数 + 最近活跃度）
                        days_since_last = (datetime.now() - stat.last_article_date).days
                        activity_score = stat.article_count * (1.0 / (1 + days_since_last * 0.1))

                        rising_stars.append({
                            'user_id': user.id,
                            'username': user.username,
                            'avatar': getattr(user, 'avatar', None),
                            'article_count': stat.article_count,
                            'last_article_date': stat.last_article_date.isoformat(),
                            'activity_score': round(activity_score, 2),
                        })

            # 按活跃度分数排序
            rising_stars.sort(key=lambda x: x['activity_score'], reverse=True)

            logger.info(f"Found {len(rising_stars)} rising stars")
            return rising_stars[:limit]

        except Exception as e:
            logger.error(f"Failed to get rising stars: {e}")
            return []

    def get_similar_articles(self, article_id: int,
                             limit: int = 5) -> List[Dict]:
        """
        获取相似文章(基于内容相似度)
        
        Args:
            article_id: 参考文章ID
            limit: 返回数量
            
        Returns:
            相似文章列表
        """
        if article_id not in self._article_features:
            return []

        target_features = self._article_features[article_id]
        target_tags = set(target_features.get('tags', []))
        target_category = target_features.get('category', '')

        scored_articles = []

        for other_id, features in self._article_features.items():
            if other_id == article_id:
                continue

            # 计算Jaccard相似度
            other_tags = set(features.get('tags', []))

            if not target_tags or not other_tags:
                tag_similarity = 0
            else:
                intersection = len(target_tags & other_tags)
                union = len(target_tags | other_tags)
                tag_similarity = intersection / union if union > 0 else 0

            # 分类匹配
            category_match = 1.0 if features.get('category') == target_category else 0.0

            # 综合相似度
            similarity = tag_similarity * 0.7 + category_match * 0.3

            if similarity > 0.1:  # 阈值
                scored_articles.append({
                    'article_id': other_id,
                    'similarity': similarity,
                    'features': features,
                })

        # 按相似度排序
        scored_articles.sort(key=lambda x: x['similarity'], reverse=True)

        return scored_articles[:limit]


# 全局实例
recommendation_service = RecommendationService()
