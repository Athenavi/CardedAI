"""
实时监控系统服务
提供系统性能、在线用户、访问量等实时监控数据
"""


from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List

import psutil

from src.unified_logger import default_logger as logger


class RealTimeMonitorService:
    """实时监控系统服务"""

    def __init__(self):
        # 在线用户追踪 {user_id: last_activity_timestamp}
        self._online_users = {}

        # 访问统计 {endpoint: [timestamp, ...]}
        self._access_log = defaultdict(list)

        # 热门文章缓存
        self._trending_articles = []
        self._last_trending_update = None

        # 系统指标缓存
        self._system_metrics_cache = None
        self._cache_timestamp = None

        # 配置参数
        self.online_timeout_seconds = 300  # 5分钟无活动视为离线
        self.cache_ttl_seconds = 10  # 缓存10秒

    def record_user_activity(self, user_id: int):
        """
        记录用户活动
        
        Args:
            user_id: 用户ID
        """
        now = datetime.now()
        self._online_users[user_id] = now

    def record_page_view(self, endpoint: str, article_id: int = None):
        """
        记录页面访问
        
        Args:
            endpoint: 访问的端点
            article_id: 文章ID(可选)
        """
        now = datetime.now()
        self._access_log[endpoint].append(now)

        # 清理旧记录(保留最近1小时)
        cutoff = now - timedelta(hours=1)
        self._access_log[endpoint] = [
            ts for ts in self._access_log[endpoint] if ts > cutoff
        ]

    def get_online_users_count(self) -> int:
        """
        获取在线用户数
        
        Returns:
            在线用户数量
        """
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.online_timeout_seconds)

        # 清理过期用户
        expired_users = [
            uid for uid, last_active in self._online_users.items()
            if last_active < cutoff
        ]

        for uid in expired_users:
            del self._online_users[uid]

        return len(self._online_users)

    def get_online_users_list(self, limit: int = 50) -> List[Dict]:
        """
        获取在线用户列表
        
        Args:
            limit: 返回数量
            
        Returns:
            在线用户列表
        """
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.online_timeout_seconds)

        online_users = []
        for user_id, last_active in self._online_users.items():
            if last_active >= cutoff:
                online_users.append({
                    'user_id': user_id,
                    'last_active': last_active.isoformat(),
                    'duration_seconds': (now - last_active).seconds,
                })

        # 按最后活动时间排序
        online_users.sort(key=lambda x: x['last_active'], reverse=True)

        return online_users[:limit]

    def get_today_visits(self) -> int:
        """
        获取今日访问量
        
        Returns:
            今日访问次数
        """
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        total_visits = 0
        for endpoint, timestamps in self._access_log.items():
            today_visits = [ts for ts in timestamps if ts >= today_start]
            total_visits += len(today_visits)

        return total_visits

    def get_realtime_visits(self, window_minutes: int = 5) -> int:
        """
        获取实时访问量(最近N分钟)
        
        Args:
            window_minutes: 时间窗口(分钟)
            
        Returns:
            访问量
        """
        now = datetime.now()
        cutoff = now - timedelta(minutes=window_minutes)

        total_visits = 0
        for timestamps in self._access_log.values():
            recent_visits = [ts for ts in timestamps if ts >= cutoff]
            total_visits += len(recent_visits)

        return total_visits

    def get_popular_endpoints(self, limit: int = 10,
                              window_minutes: int = 60) -> List[Dict]:
        """
        获取热门访问端点
        
        Args:
            limit: 返回数量
            window_minutes: 时间窗口(分钟)
            
        Returns:
            热门端点列表
        """
        now = datetime.now()
        cutoff = now - timedelta(minutes=window_minutes)

        endpoint_counts = {}
        for endpoint, timestamps in self._access_log.items():
            recent_visits = [ts for ts in timestamps if ts >= cutoff]
            if recent_visits:
                endpoint_counts[endpoint] = len(recent_visits)

        # 排序
        sorted_endpoints = sorted(
            endpoint_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [
            {
                'endpoint': endpoint,
                'visits': count,
            }
            for endpoint, count in sorted_endpoints[:limit]
        ]

    def get_system_metrics(self) -> Dict:
        """
        获取系统指标(CPU、内存、磁盘等)
        
        Returns:
            系统指标字典
        """
        now = datetime.now()

        # 检查缓存
        if (self._system_metrics_cache and
                self._cache_timestamp and
                (now - self._cache_timestamp).seconds < self.cache_ttl_seconds):
            return self._system_metrics_cache

        try:
            # CPU信息
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()

            # 内存信息
            memory = psutil.virtual_memory()

            # 磁盘信息
            disk = psutil.disk_usage('/')

            # 网络信息
            net_io = psutil.net_io_counters()

            metrics = {
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'frequency': cpu_freq.current if cpu_freq else 0,
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'used': memory.used,
                    'percent': memory.percent,
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': disk.percent,
                },
                'network': {
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv,
                },
                'timestamp': now.isoformat(),
            }

            # 更新缓存
            self._system_metrics_cache = metrics
            self._cache_timestamp = now

            return metrics

        except Exception as e:
            logger.error(f"Failed to get system metrics: {str(e)}")
            return {
                'error': str(e),
                'timestamp': now.isoformat(),
            }

    def get_trending_articles(self, limit: int = 10) -> List[Dict]:
        """
        获取实时热门文章
        
        Args:
            limit: 返回数量
            
        Returns:
            热门文章列表
        """
        now = datetime.now()

        # 检查缓存(5分钟)
        if (self._trending_articles and
                self._last_trending_update and
                (now - self._last_trending_update).seconds < 300):
            return self._trending_articles[:limit]

        # Query trending articles from database
        # Example implementation:
        # from shared.models.article import Article
        # from sqlalchemy import select, desc
        # from datetime import datetime, timedelta
        # 
        # seven_days_ago = datetime.now() - timedelta(days=7)
        # stmt = (
        #     select(Article)
        #     .where(Article.status == 'published')
        #     .where(Article.published_at >= seven_days_ago)
        #     .order_by(desc(Article.view_count))
        #     .limit(limit * 2)  # Get more for filtering
        # )
        # result = await db.execute(stmt)
        # articles = result.scalars().all()
        # 
        # trending = [{
        #     'id': article.id,
        #     'title': article.title,
        #     'slug': article.slug,
        #     'view_count': article.view_count,
        #     'like_count': article.like_count,
        #     'comment_count': article.comment_count,
        #     'published_at': article.published_at.isoformat(),
        # } for article in articles]

        # For now, return empty list (will be populated when DB is connected)
        trending = []

        # 更新缓存
        self._trending_articles = trending
        self._last_trending_update = now

        return trending[:limit]

    def get_health_status(self) -> Dict:
        """
        获取系统健康状态
        
        Returns:
            健康状态字典
        """
        metrics = self.get_system_metrics()

        # 判断健康状态
        health_issues = []

        # CPU检查
        if metrics.get('cpu', {}).get('percent', 0) > 90:
            health_issues.append({
                'component': 'CPU',
                'status': 'warning',
                'message': f"CPU使用率过高: {metrics['cpu']['percent']}%",
            })

        # 内存检查
        if metrics.get('memory', {}).get('percent', 0) > 90:
            health_issues.append({
                'component': 'Memory',
                'status': 'critical',
                'message': f"内存使用率过高: {metrics['memory']['percent']}%",
            })

        # 磁盘检查
        if metrics.get('disk', {}).get('percent', 0) > 90:
            health_issues.append({
                'component': 'Disk',
                'status': 'warning',
                'message': f"磁盘使用率过高: {metrics['disk']['percent']}%",
            })

        # 总体状态
        if not health_issues:
            overall_status = 'healthy'
        elif any(issue['status'] == 'critical' for issue in health_issues):
            overall_status = 'critical'
        else:
            overall_status = 'warning'

        return {
            'overall_status': overall_status,
            'issues': health_issues,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat(),
        }

    def get_dashboard_data(self) -> Dict:
        """
        获取仪表板完整数据
        
        Returns:
            仪表板数据
        """
        return {
            'online_users': {
                'count': self.get_online_users_count(),
                'list': self.get_online_users_list(limit=10),
            },
            'visits': {
                'today': self.get_today_visits(),
                'realtime_5min': self.get_realtime_visits(window_minutes=5),
                'popular_endpoints': self.get_popular_endpoints(limit=5),
            },
            'trending_articles': self.get_trending_articles(limit=10),
            'system_health': self.get_health_status(),
            'timestamp': datetime.now().isoformat(),
        }

    def cleanup_old_data(self):
        """清理旧数据"""
        now = datetime.now()
        cutoff = now - timedelta(hours=24)

        # 清理24小时前的访问日志
        for endpoint in list(self._access_log.keys()):
            self._access_log[endpoint] = [
                ts for ts in self._access_log[endpoint] if ts > cutoff
            ]
            if not self._access_log[endpoint]:
                del self._access_log[endpoint]

        logger.info("Cleaned up old monitoring data")


# 全局实例
realtime_monitor_service = RealTimeMonitorService()
