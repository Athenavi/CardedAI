"""
用户画像服务
提供用户活跃度分级、兴趣标签提取、流失预警等功能
"""


from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List

from src.unified_logger import default_logger as logger


class UserProfileService:
    """用户画像服务"""

    def __init__(self):
        # 用户活动记录 {user_id: [activity]}
        self._user_activities = defaultdict(list)

        # 用户阅读历史 {user_id: [(article_id, timestamp, tags)]}
        self._reading_history = defaultdict(list)

        # 用户互动历史 {user_id: {action_type: count}}
        self._interaction_stats = defaultdict(lambda: {
            'likes': 0,
            'comments': 0,
            'shares': 0,
            'bookmarks': 0,
        })

        # 用户登录记录 {user_id: [timestamp]}
        self._login_history = defaultdict(list)

        # 用户兴趣标签 {user_id: {tag: weight}}
        self._user_interests = defaultdict(Counter)

        # 用户活跃度缓存 {user_id: {level, score, last_updated}}
        self._activity_cache = {}

    def record_activity(self, user_id: int, activity_type: str,
                        article_id: int = None, tags: List[str] = None,
                        timestamp: datetime = None):
        """
        记录用户活动
        
        Args:
            user_id: 用户ID
            activity_type: 活动类型 (view/like/comment/share/bookmark/login)
            article_id: 文章ID（可选）
            tags: 文章标签（可选）
            timestamp: 时间戳
        """
        if not timestamp:
            timestamp = datetime.now()

        activity = {
            'type': activity_type,
            'article_id': article_id,
            'tags': tags or [],
            'timestamp': timestamp,
        }

        self._user_activities[user_id].append(activity)

        # 更新特定统计
        if activity_type == 'view' and article_id:
            self._reading_history[user_id].append((article_id, timestamp, tags or []))
            # 更新兴趣标签
            if tags:
                for tag in tags:
                    self._user_interests[user_id][tag] += 1.0

        elif activity_type == 'like':
            self._interaction_stats[user_id]['likes'] += 1

        elif activity_type == 'comment':
            self._interaction_stats[user_id]['comments'] += 1

        elif activity_type == 'share':
            self._interaction_stats[user_id]['shares'] += 1

        elif activity_type == 'bookmark':
            self._interaction_stats[user_id]['bookmarks'] += 1

        elif activity_type == 'login':
            self._login_history[user_id].append(timestamp)

        # 清除活跃度缓存
        if user_id in self._activity_cache:
            del self._activity_cache[user_id]

    def calculate_activity_score(self, user_id: int, days: int = 30) -> float:
        """
        计算用户活跃度评分（0-100）
        
        评分维度：
        - 登录频率（20%）
        - 阅读数量（30%）
        - 互动行为（30%）
        - 内容创作（20%）
        
        Args:
            user_id: 用户ID
            days: 统计天数
            
        Returns:
            活跃度评分（0-100）
        """
        now = datetime.now()
        cutoff = now - timedelta(days=days)

        # 获取近期活动
        recent_activities = [
            act for act in self._user_activities.get(user_id, [])
            if act['timestamp'] >= cutoff
        ]

        if not recent_activities:
            return 0.0

        # 1. 登录频率评分（0-20分）
        login_count = len([
            ts for ts in self._login_history.get(user_id, [])
            if ts >= cutoff
        ])
        login_score = min(20, (login_count / max(days / 3, 1)) * 20)

        # 2. 阅读数量评分（0-30分）
        view_count = len([
            act for act in recent_activities
            if act['type'] == 'view'
        ])
        view_score = min(30, (view_count / 50) * 30)  # 30天看50篇得满分

        # 3. 互动行为评分（0-30分）
        stats = self._interaction_stats.get(user_id, {})
        interaction_count = (
                stats.get('likes', 0) +
                stats.get('comments', 0) * 2 +  # 评论权重更高
                stats.get('shares', 0) * 3 +  # 分享权重最高
                stats.get('bookmarks', 0)
        )
        interaction_score = min(30, (interaction_count / 20) * 30)  # 20次互动得满分

        # 4. Content creation score (0-20 points)
        # Query user's published articles from database
        # Example implementation:
        # from shared.models.article import Article
        # from sqlalchemy import select, func
        # 
        # stmt = select(func.count(Article.id)).where(
        #     (Article.user_id == user_id) & (Article.status == 'published')
        # )
        # result = await db.execute(stmt)
        # article_count = result.scalar() or 0
        # 
        # # Score based on article count (10 articles = full score)
        # creation_score = min(20, (article_count / 10) * 20)

        # For now, use placeholder value
        creation_score = 0

        total_score = login_score + view_score + interaction_score + creation_score

        return round(min(100, total_score), 2)

    def get_activity_level(self, user_id: int, days: int = 30) -> Dict:
        """
        获取用户活跃度等级
        
        等级划分：
        - 超级活跃 (90-100): 每天登录，大量阅读和互动
        - 活跃 (70-89): 经常登录，定期阅读和互动
        - 一般 (50-69): 偶尔登录，少量阅读
        - 不活跃 (30-49): 很少登录
        - 沉睡 (0-29): 长期未登录
        
        Args:
            user_id: 用户ID
            days: 统计天数
            
        Returns:
            活跃度信息 {score, level, level_name, description}
        """
        # 检查缓存
        cache_key = f"{user_id}_{days}"
        if cache_key in self._activity_cache:
            cached = self._activity_cache[cache_key]
            # 缓存有效期5分钟
            if (datetime.now() - cached['last_updated']).seconds < 300:
                return cached

        score = self.calculate_activity_score(user_id, days)

        # 确定等级
        if score >= 90:
            level = 'super_active'
            level_name = '超级活跃'
            description = '每日登录，大量阅读和互动'
        elif score >= 70:
            level = 'active'
            level_name = '活跃'
            description = '经常登录，定期阅读和互动'
        elif score >= 50:
            level = 'moderate'
            level_name = '一般'
            description = '偶尔登录，少量阅读'
        elif score >= 30:
            level = 'inactive'
            level_name = '不活跃'
            description = '很少登录'
        else:
            level = 'dormant'
            level_name = '沉睡'
            description = '长期未登录'

        result = {
            'score': score,
            'level': level,
            'level_name': level_name,
            'description': description,
            'period_days': days,
        }

        # 更新缓存
        self._activity_cache[cache_key] = {
            **result,
            'last_updated': datetime.now(),
        }

        return result

    def get_user_interests(self, user_id: int, top_n: int = 10) -> List[Dict]:
        """
        获取用户兴趣标签
        
        基于用户的阅读历史、点赞、收藏等行为，
        使用TF-IDF思想计算标签权重。
        
        Args:
            user_id: 用户ID
            top_n: 返回前N个标签
            
        Returns:
            兴趣标签列表 [{tag, weight, article_count}]
        """
        interests = self._user_interests.get(user_id, Counter())

        if not interests:
            return []

        # 应用时间衰减（最近的行为权重更高）
        now = datetime.now()
        weighted_interests = Counter()

        for article_id, timestamp, tags in self._reading_history.get(user_id, []):
            # 计算时间衰减因子（30天衰减到0.3）
            days_ago = (now - timestamp).days
            time_weight = max(0.3, 1.0 - (days_ago / 30))

            for tag in tags:
                weighted_interests[tag] += time_weight

        # 结合互动行为（点赞*2, 收藏*1.5）
        stats = self._interaction_stats.get(user_id, {})
        interaction_multiplier = 1 + (
                stats.get('likes', 0) * 0.1 +
                stats.get('bookmarks', 0) * 0.15
        )

        for tag in weighted_interests:
            weighted_interests[tag] *= interaction_multiplier

        # 返回Top N
        result = []
        for tag, weight in weighted_interests.most_common(top_n):
            # 计算该标签相关的文章数
            article_count = len([
                (aid, ts, tgs)
                for aid, ts, tgs in self._reading_history.get(user_id, [])
                if tag in tgs
            ])

            result.append({
                'tag': tag,
                'weight': round(weight, 2),
                'article_count': article_count,
            })

        return result

    def predict_churn_risk(self, user_id: int) -> Dict:
        """
        预测用户流失风险
        
        基于以下指标：
        - 最后登录时间
        - 近期活跃度趋势
        - 互动频率变化
        
        Args:
            user_id: 用户ID
            
        Returns:
            流失风险信息 {risk_level, risk_score, reasons, suggestions}
        """
        now = datetime.now()

        # 1. 检查最后登录时间
        logins = self._login_history.get(user_id, [])
        if not logins:
            last_login = None
            days_since_login = 999  # 从未登录
        else:
            last_login = max(logins)
            days_since_login = (now - last_login).days

        # 2. 计算近期活跃度趋势
        recent_7d = self.calculate_activity_score(user_id, 7)
        recent_30d = self.calculate_activity_score(user_id, 30)

        # 活跃度下降比例
        if recent_30d > 0:
            activity_decline = (recent_30d - recent_7d * 4.28) / recent_30d  # 预期7天是30天的7/30
        else:
            activity_decline = 0

        # 3. 计算风险评分（0-100，越高风险越大）
        risk_score = 0

        # 最后登录时间权重（40%）
        if days_since_login > 30:
            risk_score += 40
        elif days_since_login > 14:
            risk_score += 25
        elif days_since_login > 7:
            risk_score += 10

        # 活跃度下降权重（30%）
        if activity_decline > 0.5:  # 下降超过50%
            risk_score += 30
        elif activity_decline > 0.3:
            risk_score += 20
        elif activity_decline > 0.1:
            risk_score += 10

        # 互动频率权重（30%）
        stats = self._interaction_stats.get(user_id, {})
        total_interactions = sum(stats.values())
        if total_interactions == 0:
            risk_score += 30
        elif total_interactions < 5:
            risk_score += 15

        risk_score = min(100, risk_score)

        # 确定风险等级
        if risk_score >= 70:
            risk_level = 'high'
            risk_name = '高流失风险'
        elif risk_score >= 40:
            risk_level = 'medium'
            risk_name = '中等流失风险'
        elif risk_score >= 20:
            risk_level = 'low'
            risk_name = '低流失风险'
        else:
            risk_level = 'minimal'
            risk_name = '极低风险'

        # 生成原因和建议
        reasons = []
        suggestions = []

        if days_since_login > 14:
            reasons.append(f'已{days_since_login}天未登录')
            suggestions.append('发送召回邮件或推送通知')

        if activity_decline > 0.3:
            reasons.append('活跃度明显下降')
            suggestions.append('推荐个性化内容')

        if total_interactions < 5:
            reasons.append('互动行为较少')
            suggestions.append('引导参与社区互动')

        if not reasons:
            reasons.append('用户状态良好')
            suggestions.append('继续保持优质内容推荐')

        return {
            'risk_level': risk_level,
            'risk_name': risk_name,
            'risk_score': round(risk_score, 2),
            'days_since_login': days_since_login,
            'last_login': last_login.isoformat() if last_login else None,
            'activity_decline': round(activity_decline * 100, 2),
            'reasons': reasons,
            'suggestions': suggestions,
        }

    def get_user_profile(self, user_id: int) -> Dict:
        """
        获取完整用户画像
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户画像数据
        """
        activity = self.get_activity_level(user_id)
        interests = self.get_user_interests(user_id, top_n=10)
        churn_risk = self.predict_churn_risk(user_id)

        # 统计总活动数
        total_activities = len(self._user_activities.get(user_id, []))

        # 统计各类型活动
        activity_breakdown = Counter([
            act['type'] for act in self._user_activities.get(user_id, [])
        ])

        return {
            'user_id': user_id,
            'activity': activity,
            'interests': interests,
            'churn_risk': churn_risk,
            'statistics': {
                'total_activities': total_activities,
                'activity_breakdown': dict(activity_breakdown),
                'total_interactions': sum(self._interaction_stats.get(user_id, {}).values()),
                'total_articles_read': len(self._reading_history.get(user_id, [])),
            },
            'generated_at': datetime.now().isoformat(),
        }


# 全局实例
user_profile_service = UserProfileService()
