"""
文章分析服务
提供文章阅读量趋势、来源渠道、读者分布等分析功能
"""


from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List

from src.unified_logger import default_logger as logger


class ArticleAnalyticsService:
    """文章分析服务"""

    def __init__(self):
        # 文章访问记录 {article_id: [visit_record, ...]}
        self._article_visits = defaultdict(list)

        # 文章每日统计 {article_id: {date: stats}}
        self._article_daily_stats = defaultdict(lambda: defaultdict(lambda: {
            'views': 0,
            'unique_visitors': set(),
            'avg_read_time': 0,
            'bounce_rate': 0,
        }))

        # 来源渠道统计 {article_id: {source: count}}
        self._traffic_sources = defaultdict(lambda: defaultdict(int))

        # 读者地域统计 {article_id: {region: count}}
        self._reader_regions = defaultdict(lambda: defaultdict(int))

    def record_view(self, article_id: int, user_id: int = None,
                    ip_address: str = None, referer: str = None,
                    read_time_seconds: int = 0, region: str = None):
        """
        记录文章访问
        
        Args:
            article_id: 文章ID
            user_id: 用户ID(可选)
            ip_address: IP地址
            referer: 来源URL
            read_time_seconds: 阅读时长(秒)
            region: 读者地域
        """
        now = datetime.now()
        today = now.strftime('%Y-%m-%d')

        # 记录访问
        visit = {
            'timestamp': now,
            'user_id': user_id,
            'ip_address': ip_address,
            'referer': referer,
            'read_time': read_time_seconds,
            'region': region,
        }

        self._article_visits[article_id].append(visit)

        # 更新每日统计
        daily_stats = self._article_daily_stats[article_id][today]
        daily_stats['views'] += 1

        if user_id:
            daily_stats['unique_visitors'].add(user_id)
        elif ip_address:
            daily_stats['unique_visitors'].add(ip_address)

        # 更新平均阅读时长
        if read_time_seconds > 0:
            total_views = daily_stats['views']
            old_avg = daily_stats['avg_read_time']
            daily_stats['avg_read_time'] = (
                    (old_avg * (total_views - 1) + read_time_seconds) / total_views
            )

        # 更新跳出率(阅读时间<10秒视为跳出)
        if read_time_seconds < 10:
            total_views = daily_stats['views']
            old_bounce = daily_stats['bounce_rate']
            daily_stats['bounce_rate'] = (
                    (old_bounce * (total_views - 1) + 1) / total_views * 100
            )

        # 记录来源渠道
        if referer:
            source = self._classify_source(referer)
            self._traffic_sources[article_id][source] += 1

        # 记录地域
        if region:
            self._reader_regions[article_id][region] += 1

    def _classify_source(self, referer: str) -> str:
        """
        分类流量来源
        
        Args:
            referer: 来源URL
            
        Returns:
            来源类型
        """
        referer_lower = referer.lower()

        if 'google.com' in referer_lower:
            return 'Google'
        elif 'baidu.com' in referer_lower:
            return 'Baidu'
        elif 'bing.com' in referer_lower:
            return 'Bing'
        elif 'facebook.com' in referer_lower:
            return 'Facebook'
        elif 'twitter.com' in referer_lower or 'x.com' in referer_lower:
            return 'Twitter'
        elif 'weibo.com' in referer_lower:
            return 'Weibo'
        elif 'zhihu.com' in referer_lower:
            return 'Zhihu'
        elif 'reddit.com' in referer_lower:
            return 'Reddit'
        elif any(social in referer_lower for social in ['linkedin', 'instagram', 'tiktok']):
            return 'Social Media'
        else:
            return 'Direct'  # 直接访问或其他

    def get_article_stats(self, article_id: int,
                          days: int = 30) -> Dict:
        """
        获取文章统计数据
        
        Args:
            article_id: 文章ID
            days: 统计天数
            
        Returns:
            统计数据
        """
        now = datetime.now()
        start_date = now - timedelta(days=days)

        # 过滤指定时间范围的访问
        recent_visits = [
            v for v in self._article_visits.get(article_id, [])
            if v['timestamp'] >= start_date
        ]

        total_views = len(recent_visits)
        unique_visitors = len(set(
            v['user_id'] or v['ip_address']
            for v in recent_visits
            if v['user_id'] or v['ip_address']
        ))

        # 计算平均阅读时长
        read_times = [v['read_time'] for v in recent_visits if v['read_time'] > 0]
        avg_read_time = sum(read_times) / len(read_times) if read_times else 0

        # 计算跳出率
        bounces = len([v for v in recent_visits if v['read_time'] < 10])
        bounce_rate = (bounces / total_views * 100) if total_views > 0 else 0

        return {
            'article_id': article_id,
            'period_days': days,
            'total_views': total_views,
            'unique_visitors': unique_visitors,
            'avg_read_time_seconds': round(avg_read_time, 2),
            'bounce_rate_percent': round(bounce_rate, 2),
            'views_per_day': round(total_views / days, 2),
        }

    def get_views_trend(self, article_id: int,
                        days: int = 30) -> List[Dict]:
        """
        获取文章阅读量趋势
        
        Args:
            article_id: 文章ID
            days: 统计天数
            
        Returns:
            每日数据列表
        """
        trend = []
        now = datetime.now()

        for i in range(days - 1, -1, -1):
            date = (now - timedelta(days=i)).strftime('%Y-%m-%d')
            daily_stats = self._article_daily_stats[article_id].get(date, {
                'views': 0,
                'unique_visitors': set(),
                'avg_read_time': 0,
                'bounce_rate': 0,
            })

            trend.append({
                'date': date,
                'views': daily_stats['views'],
                'unique_visitors': len(daily_stats['unique_visitors']),
                'avg_read_time': round(daily_stats['avg_read_time'], 2),
                'bounce_rate': round(daily_stats['bounce_rate'], 2),
            })

        return trend

    def get_traffic_sources(self, article_id: int) -> Dict[str, int]:
        """
        获取文章流量来源分布
        
        Args:
            article_id: 文章ID
            
        Returns:
            来源分布字典
        """
        return dict(self._traffic_sources.get(article_id, {}))

    def get_reader_regions(self, article_id: int) -> Dict[str, int]:
        """
        获取文章读者地域分布
        
        Args:
            article_id: 文章ID
            
        Returns:
            地域分布字典
        """
        return dict(self._reader_regions.get(article_id, {}))

    def get_article_analytics(self, article_id: int,
                              days: int = 30) -> Dict:
        """
        获取文章完整分析报告
        
        Args:
            article_id: 文章ID
            days: 统计天数
            
        Returns:
            完整分析数据
        """
        stats = self.get_article_stats(article_id, days)
        trend = self.get_views_trend(article_id, days)
        sources = self.get_traffic_sources(article_id)
        regions = self.get_reader_regions(article_id)

        return {
            'summary': stats,
            'trend': trend,
            'traffic_sources': sources,
            'reader_regions': regions,
        }

    def get_top_articles(self, days: int = 7,
                         limit: int = 10,
                         sort_by: str = 'views') -> List[Dict]:
        """
        获取热门文章排行
        
        Args:
            days: 统计天数
            limit: 返回数量
            sort_by: 排序字段(views/unique_visitors/avg_read_time)
            
        Returns:
            文章排行榜
        """
        now = datetime.now()
        start_date = now - timedelta(days=days)

        article_stats = {}

        for article_id in self._article_visits.keys():
            visits = [
                v for v in self._article_visits[article_id]
                if v['timestamp'] >= start_date
            ]

            if not visits:
                continue

            total_views = len(visits)
            unique_visitors = len(set(
                v['user_id'] or v['ip_address']
                for v in visits
                if v['user_id'] or v['ip_address']
            ))

            read_times = [v['read_time'] for v in visits if v['read_time'] > 0]
            avg_read_time = sum(read_times) / len(read_times) if read_times else 0

            article_stats[article_id] = {
                'article_id': article_id,
                'total_views': total_views,
                'unique_visitors': unique_visitors,
                'avg_read_time': round(avg_read_time, 2),
            }

        # 排序
        sorted_articles = sorted(
            article_stats.values(),
            key=lambda x: x.get(sort_by, 0),
            reverse=True
        )

        return sorted_articles[:limit]


# 全局实例
article_analytics_service = ArticleAnalyticsService()
