"""
文章评分系统插件
允许用户对文章进行星级评分和评论，显示平均评分
"""

import time
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any, Optional

from shared.services.plugins.plugin_manager.core import BasePlugin, plugin_hooks


class ArticleRatingPlugin(BasePlugin):
    """
    文章评分系统插件
    
    功能:
    1. 星级评分组件（1-5星）
    2. 用户评分记录
    3. 平均评分计算
    4. 评分分布统计
    5. 防刷分机制
    6. 评分排序功能
    """

    def __init__(self):
        super().__init__(
            plugin_id=0,
            name="文章评分系统",
            slug="article-rating",
            version="1.0.0"
        )

        # 默认设置
        self.settings = {
            'enable_rating': True,
            'max_rating': 5,  # 最大评分
            'min_rating': 1,  # 最小评分
            'allow_anonymous': False,  # 允许匿名用户评分
            'one_vote_per_user': True,  # 每用户只能投票一次
            'require_comment': False,  # 评分时必须填写评论
            'show_rating_count': True,  # 显示评分人数
            'show_average_rating': True,  # 显示平均评分
            'enable_sorting': True,  # 启用按评分排序
            'anti_spam_enabled': True,  # 启用防刷
            'min_interval_seconds': 3600,  # 最小评分间隔（秒）
        }

        # 评分记录 {article_id: [{user_id, rating, comment, timestamp}]}
        self.ratings: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # 用户评分历史 {user_id: {article_id: timestamp}}
        self.user_rating_history: Dict[str, Dict[str, float]] = defaultdict(dict)

        # 统计缓存 {article_id: {average, count, distribution}}
        self.stats_cache: Dict[str, Dict[str, Any]] = {}

    def register_hooks(self):
        """注册钩子"""
        # 提交评分
        plugin_hooks.add_action(
            "submit_rating",
            self.handle_rating_submission,
            priority=10
        )

        # 获取文章时附加评分信息
        plugin_hooks.add_filter(
            "article_data",
            self.attach_rating_info,
            priority=10
        )

    def activate(self):
        """激活插件"""
        super().activate()
        print("[ArticleRating] Plugin activated")

    def deactivate(self):
        """停用插件"""
        super().deactivate()
        print("[ArticleRating] Plugin deactivated")

    def handle_rating_submission(self, rating_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理评分提交
        
        Args:
            rating_data: 评分数据 {article_id, user_id, rating, comment, ip}
            
        Returns:
            结果 {success: bool, message: str, data: ...}
        """
        if not self.settings.get('enable_rating'):
            return {'success': False, 'message': '评分功能已禁用'}

        article_id = rating_data.get('article_id')
        user_id = rating_data.get('user_id')
        rating = rating_data.get('rating')
        comment = rating_data.get('comment', '')
        ip = rating_data.get('ip', '')

        # 验证参数
        validation = self._validate_rating(rating_data)
        if not validation['valid']:
            return {'success': False, 'message': validation['error']}

        # 防刷检查
        if self.settings.get('anti_spam_enabled'):
            spam_check = self._check_spam(user_id, article_id, ip)
            if not spam_check['allowed']:
                return {'success': False, 'message': spam_check['reason']}

        # 检查是否已经评分
        if self.settings.get('one_vote_per_user') and user_id:
            existing = self._get_user_rating(user_id, article_id)
            if existing:
                # 更新评分
                self._update_rating(user_id, article_id, rating, comment)
                message = '评分已更新'
            else:
                # 新增评分
                self._add_rating(user_id, article_id, rating, comment)
                message = '评分成功'
        else:
            # 允许匿名或多次评分
            self._add_rating(user_id or f"anonymous_{ip}", article_id, rating, comment)
            message = '评分成功'

        # 清除统计缓存
        if article_id in self.stats_cache:
            del self.stats_cache[article_id]

        # 返回更新后的统计
        stats = self.get_article_stats(article_id)

        return {
            'success': True,
            'message': message,
            'data': stats
        }

    def get_article_stats(self, article_id: str) -> Dict[str, Any]:
        """
        获取文章评分统计
        
        Args:
            article_id: 文章ID
            
        Returns:
            统计数据
        """
        # 检查缓存
        if article_id in self.stats_cache:
            return self.stats_cache[article_id]

        ratings = self.ratings.get(article_id, [])
        
        if not ratings:
            stats = {
                'average': 0,
                'count': 0,
                'distribution': {str(i): 0 for i in range(1, self.settings.get('max_rating', 5) + 1)},
                'percentage': 0,
            }
        else:
            # 计算平均分
            total = sum(r['rating'] for r in ratings)
            count = len(ratings)
            average = total / count

            # 计算分布
            distribution = defaultdict(int)
            for r in ratings:
                distribution[str(r['rating'])] += 1

            # 确保所有星级都有
            max_rating = self.settings.get('max_rating', 5)
            full_distribution = {str(i): distribution.get(str(i), 0) for i in range(1, max_rating + 1)}

            # 计算百分比（5星制）
            percentage = (average / max_rating) * 100

            stats = {
                'average': round(average, 2),
                'count': count,
                'distribution': full_distribution,
                'percentage': round(percentage, 2),
            }

        # 缓存统计
        self.stats_cache[article_id] = stats

        return stats

    def get_user_rating(self, user_id: str, article_id: str) -> Optional[Dict[str, Any]]:
        """
        获取用户对文章的评分
        
        Args:
            user_id: 用户ID
            article_id: 文章ID
            
        Returns:
            评分记录
        """
        return self._get_user_rating(user_id, article_id)

    def get_top_rated_articles(self, limit: int = 10, min_votes: int = 5) -> List[Dict[str, Any]]:
        """
        获取评分最高的文章
        
        Args:
            limit: 返回数量
            min_votes: 最少投票数
            
        Returns:
            文章列表 [{article_id, average, count}]
        """
        results = []

        for article_id in self.ratings.keys():
            stats = self.get_article_stats(article_id)
            
            if stats['count'] >= min_votes:
                results.append({
                    'article_id': article_id,
                    'average': stats['average'],
                    'count': stats['count'],
                })

        # 按平均分排序
        results.sort(key=lambda x: x['average'], reverse=True)

        return results[:limit]

    def get_recent_ratings(self, article_id: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近的评分
        
        Args:
            article_id: 文章ID（可选）
            limit: 返回数量
            
        Returns:
            评分列表
        """
        all_ratings = []

        if article_id:
            all_ratings = self.ratings.get(article_id, [])
        else:
            for ratings in self.ratings.values():
                all_ratings.extend(ratings)

        # 按时间排序
        sorted_ratings = sorted(all_ratings, key=lambda x: x['timestamp'], reverse=True)

        # 格式化返回
        result = []
        for r in sorted_ratings[:limit]:
            result.append({
                'user_id': r.get('user_id'),
                'rating': r['rating'],
                'comment': r.get('comment', ''),
                'timestamp': r['timestamp'],
                'formatted_time': datetime.fromtimestamp(r['timestamp']).strftime('%Y-%m-%d %H:%M')
            })

        return result

    def delete_rating(self, user_id: str, article_id: str) -> bool:
        """
        删除评分
        
        Args:
            user_id: 用户ID
            article_id: 文章ID
            
        Returns:
            是否成功删除
        """
        if article_id not in self.ratings:
            return False

        initial_count = len(self.ratings[article_id])
        self.ratings[article_id] = [
            r for r in self.ratings[article_id]
            if r.get('user_id') != user_id
        ]

        if len(self.ratings[article_id]) < initial_count:
            # 清除缓存
            if article_id in self.stats_cache:
                del self.stats_cache[article_id]
            return True

        return False

    def attach_rating_info(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        为文章附加评分信息
        
        Args:
            article_data: 文章数据
            
        Returns:
            包含评分信息的文章数据
        """
        if not self.settings.get('enable_rating'):
            return article_data

        article_id = article_data.get('id') or article_data.get('article_id')
        if not article_id:
            return article_data

        stats = self.get_article_stats(str(article_id))
        
        article_data['rating_stats'] = stats
        article_data['user_rating'] = None

        # 如果用户已登录，获取其评分
        user_id = article_data.get('current_user_id')
        if user_id:
            user_rating = self._get_user_rating(user_id, str(article_id))
            if user_rating:
                article_data['user_rating'] = user_rating['rating']

        return article_data

    def _validate_rating(self, rating_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证评分数据
        
        Args:
            rating_data: 评分数据
            
        Returns:
            验证结果
        """
        # 检查必需字段
        if not rating_data.get('article_id'):
            return {'valid': False, 'error': '缺少文章ID'}

        if not rating_data.get('rating'):
            return {'valid': False, 'error': '缺少评分'}

        # 检查评分范围
        rating = rating_data['rating']
        min_rating = self.settings.get('min_rating', 1)
        max_rating = self.settings.get('max_rating', 5)

        if not isinstance(rating, (int, float)):
            return {'valid': False, 'error': '评分必须是数字'}

        if rating < min_rating or rating > max_rating:
            return {'valid': False, 'error': f'评分必须在{min_rating}-{max_rating}之间'}

        # 检查是否需要登录
        if not self.settings.get('allow_anonymous') and not rating_data.get('user_id'):
            return {'valid': False, 'error': '需要登录后才能评分'}

        # 检查是否需要评论
        if self.settings.get('require_comment') and not rating_data.get('comment'):
            return {'valid': False, 'error': '评分时必须填写评论'}

        return {'valid': True, 'error': ''}

    def _check_spam(self, user_id: str, article_id: str, ip: str) -> Dict[str, Any]:
        """
        防刷检查
        
        Args:
            user_id: 用户ID
            article_id: 文章ID
            ip: IP地址
            
        Returns:
            检查结果
        """
        identifier = user_id or ip
        
        if identifier in self.user_rating_history:
            history = self.user_rating_history[identifier]
            
            if article_id in history:
                last_rating_time = history[article_id]
                current_time = time.time()
                min_interval = self.settings.get('min_interval_seconds', 3600)
                
                if current_time - last_rating_time < min_interval:
                    remaining = int(min_interval - (current_time - last_rating_time))
                    return {
                        'allowed': False,
                        'reason': f'请稍后再试，剩余 {remaining} 秒'
                    }

        return {'allowed': True}

    def _add_rating(self, user_id: str, article_id: str, rating: float, comment: str = ''):
        """添加评分"""
        rating_record = {
            'user_id': user_id,
            'rating': rating,
            'comment': comment,
            'timestamp': time.time(),
        }

        self.ratings[article_id].append(rating_record)

        # 更新用户历史
        if user_id:
            self.user_rating_history[user_id][article_id] = time.time()

    def _update_rating(self, user_id: str, article_id: str, rating: float, comment: str = ''):
        """更新评分"""
        if article_id not in self.ratings:
            return

        for r in self.ratings[article_id]:
            if r.get('user_id') == user_id:
                r['rating'] = rating
                r['comment'] = comment
                r['timestamp'] = time.time()
                break

        # 更新用户历史
        if user_id:
            self.user_rating_history[user_id][article_id] = time.time()

    def _get_user_rating(self, user_id: str, article_id: str) -> Optional[Dict[str, Any]]:
        """获取用户评分"""
        if article_id not in self.ratings:
            return None

        for r in self.ratings[article_id]:
            if r.get('user_id') == user_id:
                return r

        return None

    def get_settings_ui(self) -> Dict[str, Any]:
        """返回设置界面配置"""
        return {
            'fields': [
                {
                    'key': 'enable_rating',
                    'type': 'boolean',
                    'label': '启用评分功能',
                },
                {
                    'key': 'max_rating',
                    'type': 'number',
                    'label': '最大评分',
                    'min': 3,
                    'max': 10,
                    'help': '推荐使用5星制',
                },
                {
                    'key': 'allow_anonymous',
                    'type': 'boolean',
                    'label': '允许匿名评分',
                    'help': '不推荐，容易被刷分',
                },
                {
                    'key': 'one_vote_per_user',
                    'type': 'boolean',
                    'label': '每用户只能投票一次',
                },
                {
                    'key': 'require_comment',
                    'type': 'boolean',
                    'label': '评分时必须填写评论',
                },
                {
                    'key': 'show_rating_count',
                    'type': 'boolean',
                    'label': '显示评分人数',
                },
                {
                    'key': 'show_average_rating',
                    'type': 'boolean',
                    'label': '显示平均评分',
                },
                {
                    'key': 'anti_spam_enabled',
                    'type': 'boolean',
                    'label': '启用防刷机制',
                },
                {
                    'key': 'min_interval_seconds',
                    'type': 'number',
                    'label': '最小评分间隔（秒）',
                    'min': 60,
                    'max': 86400,
                    'show_if': {'anti_spam_enabled': True},
                },
            ],
            'actions': [
                {
                    'type': 'button',
                    'label': '查看热门评分',
                    'action': 'view_top_rated',
                    'variant': 'outline',
                },
                {
                    'type': 'button',
                    'label': '导出评分数据',
                    'action': 'export_ratings',
                    'variant': 'outline',
                },
            ]
        }


# 插件实例
plugin_instance = ArticleRatingPlugin()
