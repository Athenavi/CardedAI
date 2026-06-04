"""
用户积分系统服务
提供积分获取、消耗、排行榜等功能
"""


from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

from src.unified_logger import default_logger as logger


class PointsSystem:
    """用户积分系统"""

    def __init__(self):
        # 用户积分 {user_id: points}
        self._user_points = defaultdict(int)

        # 积分历史记录 {user_id: [(points, reason, timestamp), ...]}
        self._points_history = defaultdict(list)

        # 积分规则配置
        self._rules = {
            'article_published': 10,  # 发布文章
            'comment_created': 2,  # 发表评论
            'article_liked': 1,  # 文章被点赞
            'comment_liked': 1,  # 评论被点赞
            'daily_login': 1,  # 每日登录
            'profile_completed': 5,  # 完善资料
            'first_article': 20,  # 首篇文章奖励
            'continuous_posting_7d': 50,  # 连续发文7天
            'continuous_posting_30d': 200,  # 连续发文30天
        }

        # 兑换配置
        self._exchange_rules = {
            'vip_1_month': 1000,  # VIP会员1个月
            'vip_3_months': 2800,  # VIP会员3个月(优惠)
            'featured_article': 500,  # 文章置顶推荐
            'custom_domain': 5000,  # 自定义域名
        }

        # 每日登录追踪 {user_id: last_login_date}
        self._daily_logins = {}

        # 连续发文追踪 {user_id: [date1, date2, ...]}
        self._posting_streaks = defaultdict(list)

    def add_points(self, user_id: int, points: int, reason: str = '') -> bool:
        """
        增加用户积分
        
        Args:
            user_id: 用户ID
            points: 积分数量
            reason: 原因说明
            
        Returns:
            是否成功
        """
        if points <= 0:
            return False

        self._user_points[user_id] += points

        # 记录历史
        self._points_history[user_id].append({
            'points': points,
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
            'type': 'earned',
        })

        logger.info(f"User {user_id} earned {points} points: {reason}")
        return True

    def deduct_points(self, user_id: int, points: int, reason: str = '') -> bool:
        """
        扣除用户积分
        
        Args:
            user_id: 用户ID
            points: 积分数量
            reason: 原因说明
            
        Returns:
            是否成功
        """
        if points <= 0:
            return False

        if self._user_points[user_id] < points:
            logger.warning(f"User {user_id} has insufficient points")
            return False

        self._user_points[user_id] -= points

        # 记录历史
        self._points_history[user_id].append({
            'points': -points,
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
            'type': 'spent',
        })

        logger.info(f"User {user_id} spent {points} points: {reason}")
        return True

    def get_user_points(self, user_id: int) -> int:
        """
        获取用户积分
        
        Args:
            user_id: 用户ID
            
        Returns:
            当前积分
        """
        return self._user_points.get(user_id, 0)

    def get_points_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """
        获取用户积分历史
        
        Args:
            user_id: 用户ID
            limit: 返回数量
            
        Returns:
            积分历史记录列表
        """
        history = self._points_history.get(user_id, [])
        return history[-limit:]

    def record_action(self, user_id: int, action: str, **kwargs) -> bool:
        """
        记录用户行为并自动发放积分
        
        Args:
            user_id: 用户ID
            action: 行为类型
            **kwargs: 额外参数
            
        Returns:
            是否成功发放积分
        """
        points = self._rules.get(action, 0)

        if points == 0:
            logger.warning(f"Unknown action: {action}")
            return False

        # 特殊处理某些行为
        if action == 'daily_login':
            return self._handle_daily_login(user_id, points)

        elif action == 'article_published':
            return self._handle_article_published(user_id, points, **kwargs)

        elif action in ['comment_created', 'article_liked', 'comment_liked']:
            return self.add_points(user_id, points, f"Action: {action}")

        else:
            return self.add_points(user_id, points, f"Action: {action}")

    def _handle_daily_login(self, user_id: int, points: int) -> bool:
        """
        处理每日登录
        
        Args:
            user_id: 用户ID
            points: 积分数量
            
        Returns:
            是否成功
        """
        today = datetime.now().date()
        last_login = self._daily_logins.get(user_id)

        # 检查今天是否已登录
        if last_login and last_login == today:
            logger.info(f"User {user_id} already logged in today")
            return False

        # 更新登录记录
        self._daily_logins[user_id] = today

        return self.add_points(user_id, points, "Daily login bonus")

    def _handle_article_published(self, user_id: int, points: int,
                                  is_first: bool = False) -> bool:
        """
        处理文章发布
        
        Args:
            user_id: 用户ID
            points: 基础积分
            is_first: 是否首篇文章
            
        Returns:
            是否成功
        """
        total_points = points

        # 首篇文章额外奖励
        if is_first:
            total_points += self._rules.get('first_article', 0)

        # 记录发文日期
        today = datetime.now().date()
        self._posting_streaks[user_id].append(today)

        # 检查连续发文
        streak_days = self._calculate_posting_streak(user_id)

        if streak_days >= 30:
            total_points += self._rules.get('continuous_posting_30d', 0)
            reason = f"Article published + 30-day streak bonus"
        elif streak_days >= 7:
            total_points += self._rules.get('continuous_posting_7d', 0)
            reason = f"Article published + 7-day streak bonus"
        else:
            reason = "Article published"

        return self.add_points(user_id, total_points, reason)

    def _calculate_posting_streak(self, user_id: int) -> int:
        """
        计算连续发文天数
        
        Args:
            user_id: 用户ID
            
        Returns:
            连续天数
        """
        dates = sorted(set(self._posting_streaks.get(user_id, [])))

        if not dates:
            return 0

        streak = 1
        max_streak = 1

        for i in range(1, len(dates)):
            if (dates[i] - dates[i - 1]).days == 1:
                streak += 1
                max_streak = max(max_streak, streak)
            else:
                streak = 1

        return max_streak

    def exchange_points(self, user_id: int, item: str) -> Dict:
        """
        积分兑换
        
        Args:
            user_id: 用户ID
            item: 兑换物品
            
        Returns:
            兑换结果
        """
        cost = self._exchange_rules.get(item)

        if not cost:
            return {
                'success': False,
                'message': f'未知的兑换物品: {item}',
            }

        current_points = self.get_user_points(user_id)

        if current_points < cost:
            return {
                'success': False,
                'message': f'积分不足，需要 {cost} 积分，当前有 {current_points} 积分',
                'required': cost,
                'current': current_points,
            }

        # 扣除积分
        success = self.deduct_points(user_id, cost, f"Exchange: {item}")

        if success:
            return {
                'success': True,
                'message': f'兑换成功: {item}',
                'item': item,
                'cost': cost,
                'remaining_points': self.get_user_points(user_id),
            }
        else:
            return {
                'success': False,
                'message': '兑换失败',
            }

    def get_leaderboard(self, limit: int = 100,
                        period: str = 'all') -> List[Dict]:
        """
        获取积分排行榜
        
        Args:
            limit: 返回数量
            period: 时间周期 ('all', 'week', 'month')
            
        Returns:
            排行榜列表
        """
        # 简化实现：返回所有用户按积分排序
        leaderboard = [
            {
                'user_id': user_id,
                'points': points,
                'rank': 0,
            }
            for user_id, points in self._user_points.items()
            if points > 0
        ]

        # 按积分降序排序
        leaderboard.sort(key=lambda x: x['points'], reverse=True)

        # 添加排名
        for i, entry in enumerate(leaderboard[:limit]):
            entry['rank'] = i + 1

        return leaderboard[:limit]

    def get_exchange_rules(self) -> Dict[str, int]:
        """
        获取兑换规则
        
        Returns:
            兑换规则字典
        """
        return self._exchange_rules.copy()

    def get_points_rules(self) -> Dict[str, int]:
        """
        获取积分规则
        
        Returns:
            积分规则字典
        """
        return self._rules.copy()

    def get_user_stats(self, user_id: int) -> Dict:
        """
        获取用户积分统计
        
        Args:
            user_id: 用户ID
            
        Returns:
            统计数据
        """
        current_points = self.get_user_points(user_id)
        history = self._points_history.get(user_id, [])

        total_earned = sum(h['points'] for h in history if h['points'] > 0)
        total_spent = sum(abs(h['points']) for h in history if h['points'] < 0)

        streak_days = self._calculate_posting_streak(user_id)

        return {
            'current_points': current_points,
            'total_earned': total_earned,
            'total_spent': total_spent,
            'transaction_count': len(history),
            'posting_streak_days': streak_days,
        }

    def cleanup_old_data(self, days: int = 365):
        """
        清理旧数据
        
        Args:
            days: 保留天数
        """
        cutoff = datetime.now() - timedelta(days=days)

        for user_id in list(self._points_history.keys()):
            self._points_history[user_id] = [
                h for h in self._points_history[user_id]
                if datetime.fromisoformat(h['timestamp']) > cutoff
            ]

        logger.info("Cleaned up old points data")


# 全局实例
points_system = PointsSystem()
