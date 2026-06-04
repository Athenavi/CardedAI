"""
内容表现分析服务
追踪文章阅读量、分享数、转化率等内容相关指标
"""


from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.unified_logger import default_logger as logger


class ContentAnalytics:
    """内容表现分析器"""

    def __init__(self):
        # 文章统计 {article_id: stats}
        self._article_stats = defaultdict(lambda: {
            'views': 0,
            'unique_visitors': set(),
            'shares': 0,
            'likes': 0,
            'comments': 0,
            'bookmarks': 0,
            'completion_rate': 0,  # 阅读完成率
            'avg_read_time': 0,
            'bounce_rate': 0,
            'conversion_events': [],
        })

        # 每日统计 {date: {article_id: stats}}
        self._daily_stats = defaultdict(lambda: defaultdict(lambda: {
            'views': 0,
            'shares': 0,
            'likes': 0,
        }))

        # 来源统计 {article_id: {source: count}}
        self._traffic_sources = defaultdict(lambda: defaultdict(int))

        # 设备统计 {article_id: {device_type: count}}
        self._device_stats = defaultdict(lambda: defaultdict(int))

        # 分享记录 {article_id: [share_event]}
        self._share_events = defaultdict(list)

    def track_article_view(self, article_id: int, user_id: Optional[int] = None,
                           source: str = 'direct', device_type: str = 'desktop',
                           read_time: int = 0, scroll_depth: int = 0):
        """
        追踪文章浏览
        
        Args:
            article_id: 文章ID
            user_id: 用户ID（可选）
            source: 流量来源（direct/search/social/referral）
            device_type: 设备类型（desktop/mobile/tablet）
            read_time: 阅读时间（秒）
            scroll_depth: 滚动深度百分比
        """
        now = datetime.now()
        today = now.strftime('%Y-%m-%d')

        stats = self._article_stats[article_id]
        stats['views'] += 1

        if user_id:
            stats['unique_visitors'].add(user_id)

        # 更新阅读时间
        if read_time > 0:
            total_read_time = stats['avg_read_time'] * (stats['views'] - 1) + read_time
            stats['avg_read_time'] = total_read_time / stats['views']

        # 更新阅读完成率（基于滚动深度）
        if scroll_depth > 0:
            current_completion = stats['completion_rate'] * (stats['views'] - 1) + scroll_depth
            stats['completion_rate'] = current_completion / stats['views']

        # 记录每日统计
        daily = self._daily_stats[today][article_id]
        daily['views'] += 1

        # 记录来源
        self._traffic_sources[article_id][source] += 1

        # 记录设备
        self._device_stats[article_id][device_type] += 1

        logger.debug(f"Article {article_id} viewed by user {user_id} from {source}")

    def track_share(self, article_id: int, platform: str = '',
                    user_id: Optional[int] = None):
        """
        追踪文章分享
        
        Args:
            article_id: 文章ID
            platform: 分享平台（wechat/weibo/twitter/facebook等）
            user_id: 用户ID
        """
        stats = self._article_stats[article_id]
        stats['shares'] += 1

        # 记录分享事件
        share_event = {
            'platform': platform,
            'user_id': user_id,
            'timestamp': datetime.now(),
        }
        self._share_events[article_id].append(share_event)

        # 更新每日统计
        today = datetime.now().strftime('%Y-%m-%d')
        self._daily_stats[today][article_id]['shares'] += 1

        logger.info(f"Article {article_id} shared on {platform}")

    def track_like(self, article_id: int, user_id: Optional[int] = None):
        """
        追踪文章点赞
        
        Args:
            article_id: 文章ID
            user_id: 用户ID
        """
        stats = self._article_stats[article_id]
        stats['likes'] += 1

        today = datetime.now().strftime('%Y-%m-%d')
        self._daily_stats[today][article_id]['likes'] += 1

    def track_comment(self, article_id: int, user_id: Optional[int] = None):
        """
        追踪文章评论
        
        Args:
            article_id: 文章ID
            user_id: 用户ID
        """
        self._article_stats[article_id]['comments'] += 1

    def track_bookmark(self, article_id: int, user_id: Optional[int] = None):
        """
        追踪文章收藏
        
        Args:
            article_id: 文章ID
            user_id: 用户ID
        """
        self._article_stats[article_id]['bookmarks'] += 1

    def track_conversion(self, article_id: int, conversion_type: str,
                         value: float = 0, metadata: Dict = None):
        """
        追踪转化事件
        
        Args:
            article_id: 文章ID
            conversion_type: 转化类型（tip/subscribe/purchase等）
            value: 转化价值
            metadata: 额外元数据
        """
        stats = self._article_stats[article_id]

        conversion_event = {
            'type': conversion_type,
            'value': value,
            'metadata': metadata or {},
            'timestamp': datetime.now(),
        }
        stats['conversion_events'].append(conversion_event)

    def get_article_stats(self, article_id: int) -> Dict:
        """
        获取文章统计数据
        
        Args:
            article_id: 文章ID
            
        Returns:
            统计数据
        """
        stats = self._article_stats[article_id]

        return {
            'article_id': article_id,
            'total_views': stats['views'],
            'unique_visitors': len(stats['unique_visitors']),
            'shares': stats['shares'],
            'likes': stats['likes'],
            'comments': stats['comments'],
            'bookmarks': stats['bookmarks'],
            'avg_read_time': round(stats['avg_read_time'], 2),
            'completion_rate': round(stats['completion_rate'], 2),
            'bounce_rate': round(stats['bounce_rate'], 2),
            'engagement_score': self._calculate_engagement_score(stats),
        }

    def _calculate_engagement_score(self, stats: Dict) -> float:
        """
        计算参与度评分
        
        Args:
            stats: 统计数据
            
        Returns:
            参与度评分（0-100）
        """
        if stats['views'] == 0:
            return 0

        # 权重配置
        weights = {
            'likes': 2,
            'comments': 3,
            'shares': 4,
            'bookmarks': 2,
            'completion_rate': 5,
        }

        score = 0
        score += (stats['likes'] / stats['views']) * 100 * weights['likes']
        score += (stats['comments'] / stats['views']) * 100 * weights['comments']
        score += (stats['shares'] / stats['views']) * 100 * weights['shares']
        score += (stats['bookmarks'] / stats['views']) * 100 * weights['bookmarks']
        score += stats['completion_rate'] * weights['completion_rate']

        # 归一化到0-100
        max_score = sum(weights.values()) * 100
        normalized_score = (score / max_score) * 100

        return round(min(normalized_score, 100), 2)

    def get_trending_articles(self, period: str = 'week',
                              limit: int = 10) -> List[Dict]:
        """
        获取热门文章
        
        Args:
            period: 时间周期（day/week/month）
            limit: 返回数量
            
        Returns:
            热门文章列表
        """
        cutoff = None
        now = datetime.now()

        if period == 'day':
            cutoff = now - timedelta(days=1)
        elif period == 'week':
            cutoff = now - timedelta(days=7)
        elif period == 'month':
            cutoff = now - timedelta(days=30)

        articles = []
        for article_id, stats in self._article_stats.items():
            # 简化：这里应该根据时间过滤
            engagement = self._calculate_engagement_score(stats)

            articles.append({
                'article_id': article_id,
                'views': stats['views'],
                'engagement_score': engagement,
                'trend_score': self._calculate_trend_score(article_id, period),
            })

        # 按趋势分数排序
        articles.sort(key=lambda x: x['trend_score'], reverse=True)

        return articles[:limit]

    def _calculate_trend_score(self, article_id: int, period: str) -> float:
        """
        计算文章趋势分数
        
        Args:
            article_id: 文章ID
            period: 时间周期
            
        Returns:
            趋势分数
        """
        # 简化实现：基于最近浏览量
        stats = self._article_stats[article_id]
        return stats['views'] * 0.5 + stats['shares'] * 2 + stats['likes']

    def get_traffic_sources(self, article_id: int) -> Dict:
        """
        获取流量来源分布
        
        Args:
            article_id: 文章ID
            
        Returns:
            流量来源统计
        """
        sources = dict(self._traffic_sources[article_id])
        total = sum(sources.values())

        # 计算百分比
        distribution = {}
        for source, count in sources.items():
            distribution[source] = {
                'count': count,
                'percentage': round((count / total * 100) if total > 0 else 0, 2)
            }

        return {
            'article_id': article_id,
            'total_views': total,
            'distribution': distribution,
        }

    def get_device_breakdown(self, article_id: int) -> Dict:
        """
        获取设备类型分布
        
        Args:
            article_id: 文章ID
            
        Returns:
            设备统计
        """
        devices = dict(self._device_stats[article_id])
        total = sum(devices.values())

        breakdown = {}
        for device, count in devices.items():
            breakdown[device] = {
                'count': count,
                'percentage': round((count / total * 100) if total > 0 else 0, 2)
            }

        return {
            'article_id': article_id,
            'total_views': total,
            'breakdown': breakdown,
        }

    def get_share_analytics(self, article_id: int) -> Dict:
        """
        获取分享分析
        
        Args:
            article_id: 文章ID
            
        Returns:
            分享统计
        """
        events = self._share_events.get(article_id, [])

        # 按平台统计
        platform_stats = defaultdict(int)
        for event in events:
            platform = event.get('platform', 'unknown')
            platform_stats[platform] += 1

        total_shares = len(events)

        return {
            'article_id': article_id,
            'total_shares': total_shares,
            'by_platform': dict(platform_stats),
            'recent_shares': events[-10:],  # 最近10次分享
        }

    def get_daily_trends(self, article_id: int,
                         days: int = 30) -> List[Dict]:
        """
        获取每日趋势
        
        Args:
            article_id: 文章ID
            days: 天数
            
        Returns:
            每日数据列表
        """
        trends = []
        now = datetime.now()

        for i in range(days):
            date = (now - timedelta(days=i)).strftime('%Y-%m-%d')
            daily = self._daily_stats[date].get(article_id, {})

            trends.append({
                'date': date,
                'views': daily.get('views', 0),
                'shares': daily.get('shares', 0),
                'likes': daily.get('likes', 0),
            })

        # 按日期排序
        trends.sort(key=lambda x: x['date'])

        return trends

    def get_conversion_analytics(self, article_id: int) -> Dict:
        """
        获取转化分析
        
        Args:
            article_id: 文章ID
            
        Returns:
            转化统计
        """
        stats = self._article_stats[article_id]
        conversions = stats['conversion_events']

        # 按类型统计
        type_stats = defaultdict(lambda: {'count': 0, 'total_value': 0})
        for conv in conversions:
            conv_type = conv['type']
            type_stats[conv_type]['count'] += 1
            type_stats[conv_type]['total_value'] += conv.get('value', 0)

        total_value = sum(c.get('value', 0) for c in conversions)
        conversion_rate = (len(conversions) / stats['views'] * 100) if stats['views'] > 0 else 0

        return {
            'article_id': article_id,
            'total_conversions': len(conversions),
            'total_value': total_value,
            'conversion_rate': round(conversion_rate, 2),
            'by_type': dict(type_stats),
        }


# 全局实例
content_analytics = ContentAnalytics()
