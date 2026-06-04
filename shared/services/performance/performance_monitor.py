"""
性能监控服务

提供系统性能指标收集和监控功能
包括页面加载时间、服务器指标、数据库性能等
"""

from collections import deque
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import psutil


class PerformanceMonitor:
    """
    性能监控服务
    
    收集和监控系统各项性能指标
    """

    def __init__(self, max_history: int = 1000):
        """
        初始化性能监控
        
        Args:
            max_history: 最大历史记录数
        """
        self.max_history = max_history

        # 页面加载时间历史
        self.page_load_times = deque(maxlen=max_history)

        # 数据库查询历史
        self.db_query_times = deque(maxlen=max_history)

        # API响应时间历史
        self.api_response_times = deque(maxlen=max_history)

        # 内存使用历史
        self.memory_usage_history = deque(maxlen=max_history)

        # CPU使用历史
        self.cpu_usage_history = deque(maxlen=max_history)

        # 启动时间
        self.start_time = datetime.now()

    def record_page_load(self, url: str, load_time: float,
                         user_agent: Optional[str] = None):
        """
        记录页面加载时间
        
        Args:
            url: 页面URL
            load_time: 加载时间(秒)
            user_agent: 用户代理
        """
        self.page_load_times.append({
            'url': url,
            'load_time': load_time,
            'user_agent': user_agent,
            'timestamp': datetime.now().isoformat(),
        })

    def record_db_query(self, query_type: str, duration: float,
                        table: Optional[str] = None):
        """
        记录数据库查询时间
        
        Args:
            query_type: 查询类型 (SELECT, INSERT, UPDATE, DELETE)
            duration: 查询耗时(秒)
            table: 表名
        """
        self.db_query_times.append({
            'query_type': query_type,
            'duration': duration,
            'table': table,
            'timestamp': datetime.now().isoformat(),
        })

    def record_api_response(self, endpoint: str, method: str,
                            response_time: float, status_code: int):
        """
        记录API响应时间
        
        Args:
            endpoint: API端点
            method: HTTP方法
            response_time: 响应时间(秒)
            status_code: 状态码
        """
        self.api_response_times.append({
            'endpoint': endpoint,
            'method': method,
            'response_time': response_time,
            'status_code': status_code,
            'timestamp': datetime.now().isoformat(),
        })

    def get_server_metrics(self) -> Dict[str, Any]:
        """
        获取服务器指标
        
        Returns:
            服务器指标字典
        """
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)

        # 内存使用
        memory = psutil.virtual_memory()

        # 磁盘使用
        disk = psutil.disk_usage('/')

        # 网络IO
        net_io = psutil.net_io_counters()

        # 进程数
        process_count = len(psutil.pids())
        
        return {
            'cpu': {
                'percent': cpu_percent,
                'count': psutil.cpu_count(),
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
            'processes': process_count,
            'uptime': (datetime.now() - self.start_time).total_seconds(),
        }

    def get_page_load_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取页面加载统计
        
        Args:
            hours: 统计最近多少小时的数据
        
        Returns:
            统计信息
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # 过滤指定时间范围内的数据
        recent_loads = [
            load for load in self.page_load_times
            if datetime.fromisoformat(load['timestamp']) > cutoff_time
        ]

        if not recent_loads:
            return {
                'total_requests': 0,
                'avg_load_time': 0,
                'min_load_time': 0,
                'max_load_time': 0,
                'p95_load_time': 0,
                'slow_pages': [],
            }

        load_times = [load['load_time'] for load in recent_loads]
        load_times.sort()

        # 计算百分位数
        p95_index = int(len(load_times) * 0.95)
        p95_load_time = load_times[p95_index] if p95_index < len(load_times) else load_times[-1]

        # 找出最慢的页面
        slow_pages = sorted(recent_loads, key=lambda x: x['load_time'], reverse=True)[:10]

        return {
            'total_requests': len(recent_loads),
            'avg_load_time': sum(load_times) / len(load_times),
            'min_load_time': min(load_times),
            'max_load_time': max(load_times),
            'p95_load_time': p95_load_time,
            'slow_pages': slow_pages,
        }

    def get_db_query_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取数据库查询统计
        
        Args:
            hours: 统计最近多少小时的数据
        
        Returns:
            统计信息
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # 过滤指定时间范围内的数据
        recent_queries = [
            query for query in self.db_query_times
            if datetime.fromisoformat(query['timestamp']) > cutoff_time
        ]

        if not recent_queries:
            return {
                'total_queries': 0,
                'avg_query_time': 0,
                'slow_queries': [],
                'by_type': {},
                'by_table': {},
            }

        query_times = [query['duration'] for query in recent_queries]

        # 按类型统计
        by_type = {}
        for query in recent_queries:
            qtype = query['query_type']
            if qtype not in by_type:
                by_type[qtype] = {'count': 0, 'total_time': 0}
            by_type[qtype]['count'] += 1
            by_type[qtype]['total_time'] += query['duration']

        # 按表统计
        by_table = {}
        for query in recent_queries:
            table = query.get('table', 'unknown')
            if table not in by_table:
                by_table[table] = {'count': 0, 'total_time': 0, 'avg_time': 0}
            by_table[table]['count'] += 1
            by_table[table]['total_time'] += query['duration']
            by_table[table]['avg_time'] = by_table[table]['total_time'] / by_table[table]['count']

        # 找出慢查询 (>100ms)
        slow_queries = [
            query for query in recent_queries
            if query['duration'] > 0.1
        ]
        slow_queries = sorted(slow_queries, key=lambda x: x['duration'], reverse=True)[:20]
        
        return {
            'total_queries': len(recent_queries),
            'avg_query_time': sum(query_times) / len(query_times) if query_times else 0,
            'slow_queries': slow_queries,
            'by_type': by_type,
            'by_table': by_table,
        }

    def get_api_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取API统计
        
        Args:
            hours: 统计最近多少小时的数据
        
        Returns:
            统计信息
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # 过滤指定时间范围内的数据
        recent_responses = [
            resp for resp in self.api_response_times
            if datetime.fromisoformat(resp['timestamp']) > cutoff_time
        ]

        if not recent_responses:
            return {
                'total_requests': 0,
                'avg_response_time': 0,
                'error_rate': 0,
                'by_endpoint': {},
                'by_status': {},
            }

        response_times = [resp['response_time'] for resp in recent_responses]

        # 按端点统计
        by_endpoint = {}
        for resp in recent_responses:
            endpoint = resp['endpoint']
            if endpoint not in by_endpoint:
                by_endpoint[endpoint] = {
                    'count': 0,
                    'total_time': 0,
                    'avg_time': 0,
                    'errors': 0,
                }
            by_endpoint[endpoint]['count'] += 1
            by_endpoint[endpoint]['total_time'] += resp['response_time']
            by_endpoint[endpoint]['avg_time'] = (
                    by_endpoint[endpoint]['total_time'] / by_endpoint[endpoint]['count']
            )
            if resp['status_code'] >= 400:
                by_endpoint[endpoint]['errors'] += 1

        # 按状态码统计
        by_status = {}
        for resp in recent_responses:
            status = str(resp['status_code'])
            if status not in by_status:
                by_status[status] = 0
            by_status[status] += 1

        # 计算错误率
        error_count = sum(1 for resp in recent_responses if resp['status_code'] >= 400)
        error_rate = (error_count / len(recent_responses)) * 100
        
        return {
            'total_requests': len(recent_responses),
            'avg_response_time': sum(response_times) / len(response_times) if response_times else 0,
            'error_rate': error_rate,
            'by_endpoint': by_endpoint,
            'by_status': by_status,
        }

    def get_comprehensive_report(self) -> Dict[str, Any]:
        """
        获取综合性能报告
        
        Returns:
            综合报告
        """
        server_metrics = self.get_server_metrics()
        page_stats = self.get_page_load_stats()
        db_stats = self.get_db_query_stats()
        api_stats = self.get_api_stats()
        
        return {
            'generated_at': datetime.now().isoformat(),
            'server': server_metrics,
            'page_load': page_stats,
            'database': db_stats,
            'api': api_stats,
            'recommendations': self._generate_recommendations(
                server_metrics, page_stats, db_stats, api_stats
            ),
        }

    def _generate_recommendations(self, server_metrics: Dict,
                                  page_stats: Dict, db_stats: Dict,
                                  api_stats: Dict) -> List[Dict[str, str]]:
        """
        生成优化建议
        
        Returns:
            建议列表
        """
        recommendations = []

        # CPU使用率检查
        if server_metrics['cpu']['percent'] > 80:
            recommendations.append({
                'type': 'warning',
                'category': 'server',
                'title': 'CPU使用率过高',
                'message': f"当前CPU使用率为{server_metrics['cpu']['percent']}%",
                'suggestion': '考虑优化代码或增加服务器资源',
            })

        # 内存使用率检查
        if server_metrics['memory']['percent'] > 85:
            recommendations.append({
                'type': 'warning',
                'category': 'server',
                'title': '内存使用率过高',
                'message': f"当前内存使用率为{server_metrics['memory']['percent']}%",
                'suggestion': '检查是否有内存泄漏，考虑增加内存',
            })

        # 页面加载时间检查
        if page_stats['p95_load_time'] > 3:
            recommendations.append({
                'type': 'warning',
                'category': 'performance',
                'title': '页面加载时间过长',
                'message': f"P95加载时间为{page_stats['p95_load_time']:.2f}秒",
                'suggestion': '优化资源加载，启用缓存，压缩资源',
            })

        # 数据库慢查询检查
        if db_stats['slow_queries']:
            recommendations.append({
                'type': 'warning',
                'category': 'database',
                'title': '存在慢查询',
                'message': f"发现{len(db_stats['slow_queries'])}个慢查询(>100ms)",
                'suggestion': '添加索引，优化查询语句，使用缓存',
            })

        # API错误率检查
        if api_stats['error_rate'] > 5:
            recommendations.append({
                'type': 'critical',
                'category': 'api',
                'title': 'API错误率过高',
                'message': f"当前错误率为{api_stats['error_rate']:.2f}%",
                'suggestion': '检查API日志，修复错误原因',
            })
        
        return recommendations


# 全局实例
performance_monitor = PerformanceMonitor()

# 导出
__all__ = ['PerformanceMonitor', 'performance_monitor']
