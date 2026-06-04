"""
页面性能追踪服务

收集和记录前端页面加载性能数据
支持Core Web Vitals指标
"""

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional


class PagePerformanceTracker:
    """
    页面性能追踪服务
    
    收集和分析页面加载性能数据
    """

    def __init__(self):
        """初始化性能追踪器"""
        # 存储性能数据 {page_url: [performance_data]}
        self.performance_data: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # 聚合统计数据
        self.stats_cache: Dict[str, Dict[str, Any]] = {}

    def record_performance(
            self,
            url: str,
            user_agent: str,
            performance_metrics: Dict[str, Any],
            core_web_vitals: Optional[Dict[str, float]] = None,
            custom_timings: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        记录性能数据
        
        Args:
            url: 页面URL
            user_agent: 用户代理
            performance_metrics: 性能指标
            core_web_vitals: Core Web Vitals指标
            custom_timings: 自定义计时
        
        Returns:
            记录的性能数据
        """
        timestamp = datetime.now()

        record = {
            'url': url,
            'user_agent': user_agent,
            'timestamp': timestamp.isoformat(),
            'metrics': performance_metrics,
            'core_web_vitals': core_web_vitals or {},
            'custom_timings': custom_timings or {},
        }

        # 添加到数据列表
        self.performance_data[url].append(record)

        # 清除缓存
        if url in self.stats_cache:
            del self.stats_cache[url]

        return record

    def get_page_stats(self, url: str, hours: int = 24) -> Dict[str, Any]:
        """
        获取页面性能统计
        
        Args:
            url: 页面URL
            hours: 统计最近多少小时
        
        Returns:
            统计信息
        """
        # 检查缓存
        cache_key = f"{url}_{hours}"
        if cache_key in self.stats_cache:
            return self.stats_cache[cache_key]

        cutoff = datetime.now().timestamp() - (hours * 3600)

        # 过滤数据
        records = [
            r for r in self.performance_data.get(url, [])
            if datetime.fromisoformat(r['timestamp']).timestamp() > cutoff
        ]

        if not records:
            stats = {
                'url': url,
                'sample_count': 0,
                'time_range': f'Last {hours} hours',
            }
            self.stats_cache[cache_key] = stats
            return stats

        # 计算各项指标的统计
        metrics_stats = self._calculate_metrics_stats(records, 'metrics')
        cwv_stats = self._calculate_metrics_stats(records, 'core_web_vitals')

        # 设备分布
        device_distribution = self._get_device_distribution(records)

        # 浏览器分布
        browser_distribution = self._get_browser_distribution(records)

        stats = {
            'url': url,
            'sample_count': len(records),
            'time_range': f'Last {hours} hours',
            'load_time': metrics_stats.get('loadTime', {}),
            'dom_content_loaded': metrics_stats.get('domContentLoaded', {}),
            'first_paint': metrics_stats.get('firstPaint', {}),
            'core_web_vitals': cwv_stats,
            'device_distribution': device_distribution,
            'browser_distribution': browser_distribution,
        }

        self.stats_cache[cache_key] = stats
        return stats

    def get_overall_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取整体性能统计
        
        Args:
            hours: 统计最近多少小时
        
        Returns:
            整体统计
        """
        cutoff = datetime.now().timestamp() - (hours * 3600)

        all_records = []
        for records in self.performance_data.values():
            filtered = [
                r for r in records
                if datetime.fromisoformat(r['timestamp']).timestamp() > cutoff
            ]
            all_records.extend(filtered)

        if not all_records:
            return {
                'total_pages': 0,
                'total_samples': 0,
                'time_range': f'Last {hours} hours',
            }

        # 按URL分组
        pages = set(r['url'] for r in all_records)

        # 计算平均指标
        avg_load_time = self._calculate_average(all_records, 'metrics.loadTime')
        avg_fcp = self._calculate_average(all_records, 'core_web_vitals.fcp')
        avg_lcp = self._calculate_average(all_records, 'core_web_vitals.lcp')
        avg_fid = self._calculate_average(all_records, 'core_web_vitals.fid')
        avg_cls = self._calculate_average(all_records, 'core_web_vitals.cls')

        # Core Web Vitals达标率
        cwv_pass_rate = self._calculate_cwv_pass_rate(all_records)

        return {
            'total_pages': len(pages),
            'total_samples': len(all_records),
            'time_range': f'Last {hours} hours',
            'avg_load_time': round(avg_load_time, 2) if avg_load_time else 0,
            'avg_first_contentful_paint': round(avg_fcp, 2) if avg_fcp else 0,
            'avg_largest_contentful_paint': round(avg_lcp, 2) if avg_lcp else 0,
            'avg_first_input_delay': round(avg_fid, 2) if avg_fid else 0,
            'avg_cumulative_layout_shift': round(avg_cls, 4) if avg_cls else 0,
            'cwv_pass_rate': round(cwv_pass_rate, 2),
        }

    def get_slowest_pages(self, hours: int = 24, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取最慢的页面
        
        Args:
            hours: 统计最近多少小时
            limit: 返回数量
        
        Returns:
            最慢页面列表
        """
        cutoff = datetime.now().timestamp() - (hours * 3600)

        page_load_times = {}

        for url, records in self.performance_data.items():
            filtered = [
                r for r in records
                if datetime.fromisoformat(r['timestamp']).timestamp() > cutoff
            ]

            if filtered:
                avg_load_time = sum(
                    r['metrics'].get('loadTime', 0) for r in filtered
                ) / len(filtered)

                page_load_times[url] = {
                    'url': url,
                    'avg_load_time': round(avg_load_time, 2),
                    'sample_count': len(filtered),
                }

        # 按加载时间排序
        sorted_pages = sorted(
            page_load_times.values(),
            key=lambda x: x['avg_load_time'],
            reverse=True
        )

        return sorted_pages[:limit]

    def get_performance_trends(self, url: str, days: int = 7) -> List[Dict[str, Any]]:
        """
        获取性能趋势
        
        Args:
            url: 页面URL
            days: 统计天数
        
        Returns:
            趋势数据
        """
        trends = []

        for day_offset in range(days):
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            start_date = start_date.replace(day=start_date.day - day_offset)
            end_date = start_date.replace(day=start_date.day + 1)

            records = [
                r for r in self.performance_data.get(url, [])
                if start_date <= datetime.fromisoformat(r['timestamp']) < end_date
            ]

            if records:
                avg_load_time = sum(
                    r['metrics'].get('loadTime', 0) for r in records
                ) / len(records)

                trends.append({
                    'date': start_date.strftime('%Y-%m-%d'),
                    'avg_load_time': round(avg_load_time, 2),
                    'sample_count': len(records),
                })

        # 反转以按时间正序排列
        trends.reverse()
        return trends

    def _calculate_metrics_stats(
            self,
            records: List[Dict[str, Any]],
            metrics_key: str
    ) -> Dict[str, Any]:
        """
        计算指标统计
        
        Args:
            records: 性能记录
            metrics_key: 指标键名
        
        Returns:
            统计结果
        """
        values = []
        for record in records:
            value = record.get(metrics_key, {})
            if isinstance(value, dict):
                for k, v in value.items():
                    if isinstance(v, (int, float)):
                        values.append(v)
            elif isinstance(value, (int, float)):
                values.append(value)

        if not values:
            return {}

        values.sort()

        return {
            'min': min(values),
            'max': max(values),
            'avg': round(sum(values) / len(values), 2),
            'median': values[len(values) // 2],
            'p95': values[int(len(values) * 0.95)] if len(values) >= 20 else values[-1],
            'p99': values[int(len(values) * 0.99)] if len(values) >= 100 else values[-1],
        }

    def _get_device_distribution(self, records: List[Dict[str, Any]]) -> Dict[str, int]:
        """获取设备分布"""
        distribution = defaultdict(int)

        for record in records:
            ua = record.get('user_agent', '').lower()

            if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
                distribution['mobile'] += 1
            elif 'tablet' in ua or 'ipad' in ua:
                distribution['tablet'] += 1
            else:
                distribution['desktop'] += 1

        return dict(distribution)

    def _get_browser_distribution(self, records: List[Dict[str, Any]]) -> Dict[str, int]:
        """获取浏览器分布"""
        distribution = defaultdict(int)

        for record in records:
            ua = record.get('user_agent', '').lower()

            if 'chrome' in ua and 'edge' not in ua:
                distribution['Chrome'] += 1
            elif 'firefox' in ua:
                distribution['Firefox'] += 1
            elif 'safari' in ua and 'chrome' not in ua:
                distribution['Safari'] += 1
            elif 'edge' in ua:
                distribution['Edge'] += 1
            else:
                distribution['Other'] += 1

        return dict(distribution)

    def _calculate_average(
            self,
            records: List[Dict[str, Any]],
            metric_path: str
    ) -> Optional[float]:
        """
        计算平均值
        
        Args:
            records: 记录列表
            metric_path: 指标路径（如 'metrics.loadTime'）
        
        Returns:
            平均值
        """
        parts = metric_path.split('.')
        values = []

        for record in records:
            value = record
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    value = None
                    break

            if isinstance(value, (int, float)) and value > 0:
                values.append(value)

        if not values:
            return None

        return sum(values) / len(values)

    def _calculate_cwv_pass_rate(self, records: List[Dict[str, Any]]) -> float:
        """
        计算Core Web Vitals达标率
        
        标准：
        - FCP < 1.8s
        - LCP < 2.5s
        - FID < 100ms
        - CLS < 0.1
        
        Returns:
            达标率（0-100）
        """
        if not records:
            return 0.0

        passed = 0

        for record in records:
            cwv = record.get('core_web_vitals', {})

            fcp = cwv.get('fcp', 0)
            lcp = cwv.get('lcp', 0)
            fid = cwv.get('fid', 0)
            cls = cwv.get('cls', 0)

            # 检查是否所有指标都达标
            if fcp < 1.8 and lcp < 2.5 and fid < 100 and cls < 0.1:
                passed += 1

        return (passed / len(records)) * 100


# 全局实例
performance_tracker = PagePerformanceTracker()

# 导出
__all__ = ['PagePerformanceTracker', 'performance_tracker']
