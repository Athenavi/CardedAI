"""
综合性能优化插件
整合页面缓存、性能监控、图片优化、懒加载等功能

功能模块:
1. 页面缓存 - 静态页面缓存、智能失效
2. 性能监控 - 页面加载时间、数据库查询监控
3. 图片优化 - 压缩、WebP转换、尺寸调整
4. 懒加载 - 图片和内容延迟加载

注意: CDN功能已移至 cloud-cdn 插件
"""

import hashlib
import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

from shared.services.plugins.plugin_manager.core import BasePlugin, plugin_hooks


class OptimizationPlugin(BasePlugin):
    """
    综合性能优化插件
    
    整合了以下原有插件的功能:
    - page-cache: 页面缓存
    - performance-monitor: 性能监控
    - image-optimizer: 图片优化
    - image-lazy-load: 图片懒加载
    
    注意: CDN功能已移至 cloud-cdn 插件
    """

    def __init__(self):
        super().__init__(
            plugin_id=0,
            name="性能优化中心",
            slug="opt",
            version="2.0.0"
        )

        # ==================== 全局设置 ====================
        self.settings = {
            # 页面缓存设置
            'enable_page_cache': True,
            'cache_ttl': 3600,
            'max_cache_size': 1000,
            'cache_path': 'storage/cache/page_cache',
            'excluded_paths': ['/admin', '/api', '/login'],

            # 性能监控设置
            'enable_performance_monitor': True,
            'slow_query_threshold': 100,  # 毫秒
            'page_load_threshold': 2,  # 秒
            'sampling_rate': 100,

            # 图片优化设置
            'enable_image_optimization': True,
            'auto_compress': True,
            'compression_quality': 80,
            'convert_to_webp': True,
            'max_width': 1920,
            'max_height': 1080,

            # 图片优化设置
            # 懒加载设置
            'enable_lazy_load': True,
            'lazy_load_threshold': 300,  # 像素
        }

        # ==================== 页面缓存相关 ====================
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'writes': 0,
        }

        # ==================== 性能监控相关 ====================
        self.page_metrics: List[Dict[str, Any]] = []
        self.db_queries: List[Dict[str, Any]] = []
        self.performance_alerts: List[Dict[str, Any]] = []

        # ==================== 图片优化统计 ====================
        self.image_stats = {
            'total_images_optimized': 0,
            'total_size_before': 0,
            'total_size_after': 0,
            'webp_conversions': 0,
        }

    def register_hooks(self):
        """注册钩子"""
        # 页面缓存钩子
        if self.settings.get('enable_page_cache'):
            plugin_hooks.add_filter(
                "before_response",
                self.serve_cached_page,
                priority=1
            )
            plugin_hooks.add_action(
                "after_response",
                self.cache_page,
                priority=10
            )

        # 性能监控钩子
        if self.settings.get('enable_performance_monitor'):
            plugin_hooks.add_action(
                "request_started",
                self.on_request_start,
                priority=5
            )
            plugin_hooks.add_action(
                "request_finished",
                self.on_request_end,
                priority=10
            )
            plugin_hooks.add_action(
                "db_query_executed",
                self.on_db_query,
                priority=10
            )

        # 内容更新时清除缓存
        plugin_hooks.add_action(
            "article_published",
            self.on_content_update,
            priority=10
        )
        plugin_hooks.add_action(
            "article_updated",
            self.on_content_update,
            priority=10
        )

    def activate(self):
        """激活插件"""
        super().activate()
        self._init_cache_dir()
        print("[Opt] Plugin activated - All optimization modules initialized")

    def deactivate(self):
        """停用插件"""
        super().deactivate()
        print("[Opt] Plugin deactivated")

    def _init_cache_dir(self):
        """初始化缓存目录"""
        cache_path = Path(self.settings.get('cache_path', 'storage/cache/page_cache'))
        cache_path.mkdir(parents=True, exist_ok=True)

    # ==================== 页面缓存功能 ====================

    def serve_cached_page(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """提供缓存的页面"""
        if not self.settings.get('enable_page_cache'):
            return {'cached': False}

        # 检查是否应该缓存
        url = request_data.get('url', '')
        for excluded in self.settings.get('excluded_paths', []):
            if url.startswith(excluded):
                return {'cached': False}

        # 生成缓存键
        cache_key = self._generate_cache_key(request_data)

        # 尝试从内存缓存获取
        cached_data = self._get_from_memory(cache_key)
        if cached_data:
            self.cache_stats['hits'] += 1
            return {
                'cached': True,
                'data': cached_data,
                'source': 'memory',
            }

        # 尝试从文件缓存获取
        cached_data = self._get_from_file(cache_key)
        if cached_data:
            self.cache_stats['hits'] += 1
            # 加载到内存
            ttl = self.settings.get('cache_ttl', 3600)
            self._save_to_memory(cache_key, cached_data, ttl)
            return {
                'cached': True,
                'data': cached_data,
                'source': 'file',
            }

        self.cache_stats['misses'] += 1
        return {'cached': False}

    def cache_page(self, response_data: Dict[str, Any]):
        """缓存页面"""
        if not self.settings.get('enable_page_cache'):
            return

        request_data = response_data.get('request_data', {})

        # 检查是否应该缓存
        url = request_data.get('url', '')
        for excluded in self.settings.get('excluded_paths', []):
            if url.startswith(excluded):
                return

        # 生成缓存键
        cache_key = self._generate_cache_key(request_data)

        # 准备缓存数据
        cache_entry = {
            'url': response_data.get('url'),
            'status_code': response_data.get('status_code', 200),
            'headers': response_data.get('headers', {}),
            'body': response_data.get('body'),
            'cached_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(seconds=self.settings.get('cache_ttl', 3600))).isoformat(),
        }

        # 保存到内存和文件
        ttl = self.settings.get('cache_ttl', 3600)
        self._save_to_memory(cache_key, cache_entry, ttl)
        self._save_to_file(cache_key, cache_entry)
        self.cache_stats['writes'] += 1

    def _generate_cache_key(self, request_data: Dict[str, Any]) -> str:
        """生成缓存键"""
        url = request_data.get('url', '')
        query_string = request_data.get('query_string', '')

        key_string = f"{url}?{query_string}" if query_string else url
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_from_memory(self, key: str) -> Optional[Dict[str, Any]]:
        """从内存获取缓存"""
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            expires_at = datetime.fromisoformat(entry.get('expires_at', ''))
            if datetime.now() < expires_at:
                return entry.get('data')
            else:
                del self.memory_cache[key]
        return None

    def _save_to_memory(self, key: str, data: Any, ttl: int):
        """保存到内存缓存"""
        # 检查缓存大小限制
        max_size = self.settings.get('max_cache_size', 1000)
        if len(self.memory_cache) >= max_size:
            # 删除最旧的条目
            oldest_key = min(self.memory_cache.keys(),
                             key=lambda k: self.memory_cache[k].get('cached_at', ''))
            del self.memory_cache[oldest_key]

        self.memory_cache[key] = {
            'data': data,
            'cached_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(seconds=ttl)).isoformat(),
        }

    def _get_from_file(self, key: str) -> Optional[Dict[str, Any]]:
        """从文件获取缓存"""
        cache_file = Path(self.settings.get('cache_path', 'storage/cache/page_cache')) / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except:
                return None
        return None

    def _save_to_file(self, key: str, data: Dict[str, Any]):
        """保存到文件缓存"""
        cache_file = Path(self.settings.get('cache_path', 'storage/cache/page_cache')) / f"{key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            print(f"[Opt] Failed to save cache to file: {e}")

    def on_content_update(self, article_data: Dict[str, Any]):
        """内容更新时清除缓存"""
        if not self.settings.get('enable_page_cache'):
            return

        # 清除所有缓存（简化实现）
        self.memory_cache.clear()

        # 清除文件缓存
        cache_path = Path(self.settings.get('cache_path', 'storage/cache/page_cache'))
        if cache_path.exists():
            for cache_file in cache_path.glob('*.json'):
                cache_file.unlink()

        print("[Opt] Cache cleared due to content update")

    # ==================== 性能监控功能 ====================

    def on_request_start(self, request_data: Dict[str, Any]):
        """请求开始时记录"""
        if not self.settings.get('enable_performance_monitor'):
            return

        request_data['_perf_start_time'] = time.time()

    def on_request_end(self, request_data: Dict[str, Any], response_data: Dict[str, Any]):
        """请求结束时记录性能数据"""
        if not self.settings.get('enable_performance_monitor'):
            return

        start_time = request_data.get('_perf_start_time')
        if not start_time:
            return

        # 计算加载时间
        load_time = time.time() - start_time

        # 记录页面性能
        metric = {
            'timestamp': datetime.now().isoformat(),
            'url': request_data.get('path', ''),
            'method': request_data.get('method', 'GET'),
            'load_time': round(load_time, 3),
            'status_code': response_data.get('status_code', 200),
        }

        self.page_metrics.append(metric)

        # 检查是否超过阈值
        threshold = self.settings.get('page_load_threshold', 2)
        if load_time > threshold:
            self._create_alert(
                alert_type='slow_page',
                severity='warning',
                message=f'Slow page load: {metric["url"]} took {load_time:.2f}s',
                details=metric
            )

        # 清理旧数据（保留最近1000条）
        if len(self.page_metrics) > 1000:
            self.page_metrics = self.page_metrics[-1000:]

    def on_db_query(self, query_data: Dict[str, Any]):
        """记录数据库查询"""
        if not self.settings.get('enable_performance_monitor'):
            return

        execution_time = query_data.get('execution_time', 0) * 1000  # 转换为毫秒

        # 记录查询
        query_record = {
            'timestamp': datetime.now().isoformat(),
            'query': query_data.get('sql', ''),
            'execution_time_ms': round(execution_time, 2),
            'rows_affected': query_data.get('rows', 0),
        }

        self.db_queries.append(query_record)

        # 检查是否是慢查询
        slow_threshold = self.settings.get('slow_query_threshold', 100)
        if execution_time > slow_threshold:
            self._create_alert(
                alert_type='slow_query',
                severity='warning',
                message=f'Slow query detected: {execution_time:.0f}ms',
                details=query_record
            )

        # 清理旧数据（保留最近1000条）
        if len(self.db_queries) > 1000:
            self.db_queries = self.db_queries[-1000:]

    def _create_alert(self, alert_type: str, severity: str, message: str, details: Dict[str, Any]):
        """创建性能告警"""
        alert = {
            'type': alert_type,
            'severity': severity,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat(),
        }

        self.performance_alerts.append(alert)

        # 保留最近100条告警
        if len(self.performance_alerts) > 100:
            self.performance_alerts = self.performance_alerts[-100:]

        print(f"[Opt] Alert: {message}")

    # ==================== 懒加载功能 ====================

    def add_lazy_load_to_images(self, html_content: str) -> str:
        """为HTML中的图片添加懒加载"""
        if not self.settings.get('enable_lazy_load'):
            return html_content

        def add_lazy_attr(match):
            img_tag = match.group(0)

            # 如果已经有loading属性，跳过
            if 'loading=' in img_tag:
                return img_tag

            # 添加loading="lazy"属性
            img_tag = img_tag.replace('<img', '<img loading="lazy"')
            return img_tag

        pattern = r'<img[^>]+>'
        lazy_html = re.sub(pattern, add_lazy_attr, html_content)
        return lazy_html

    # ==================== 管理API ====================

    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表板数据"""
        # 计算缓存命中率
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        # 计算平均页面加载时间
        avg_load_time = 0
        if self.page_metrics:
            avg_load_time = sum(m['load_time'] for m in self.page_metrics) / len(self.page_metrics)

        # 计算图片优化节省空间
        total_saved = self.image_stats['total_size_before'] - self.image_stats['total_size_after']

        return {
            'cache_stats': {
                **self.cache_stats,
                'hit_rate': round(hit_rate, 2),
            },
            'performance_stats': {
                'avg_load_time': round(avg_load_time, 3),
                'total_requests_monitored': len(self.page_metrics),
                'total_queries_monitored': len(self.db_queries),
                'active_alerts': len(self.performance_alerts),
            },
            'image_stats': self.image_stats,
            'lazy_load_enabled': self.settings.get('enable_lazy_load', False),
        }

    def clear_all_cache(self):
        """清除所有缓存"""
        self.memory_cache.clear()

        cache_path = Path(self.settings.get('cache_path', 'storage/cache/page_cache'))
        if cache_path.exists():
            for cache_file in cache_path.glob('*.json'):
                cache_file.unlink()

        print("[Opt] All cache cleared")

    def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """获取性能报告"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        recent_metrics = [
            m for m in self.page_metrics
            if datetime.fromisoformat(m['timestamp']) > cutoff_time
        ]

        if not recent_metrics:
            return {'message': 'No data available'}

        # 计算统计数据
        load_times = [m['load_time'] for m in recent_metrics]
        load_times.sort()

        avg_load_time = sum(load_times) / len(load_times)
        p95_index = int(len(load_times) * 0.95)
        p99_index = int(len(load_times) * 0.99)

        return {
            'period_hours': hours,
            'total_requests': len(recent_metrics),
            'avg_load_time': round(avg_load_time, 3),
            'p95_load_time': round(load_times[p95_index] if p95_index < len(load_times) else 0, 3),
            'p99_load_time': round(load_times[p99_index] if p99_index < len(load_times) else 0, 3),
            'slowest_pages': sorted(recent_metrics, key=lambda x: x['load_time'], reverse=True)[:10],
            'alerts': self.performance_alerts[-20:],
        }

    def get_admin_ui_config(self) -> Dict[str, Any]:
        """获取管理界面配置"""
        return {
            'title': '性能优化中心',
            'icon': '⚡',
            'sections': [
                {
                    'title': '性能概览',
                    'widgets': [
                        {'type': 'stat', 'label': '缓存命中率',
                         'value': f"{self.get_dashboard_data()['cache_stats']['hit_rate']}%"},
                        {'type': 'stat', 'label': '平均加载时间',
                         'value': f"{self.get_dashboard_data()['performance_stats']['avg_load_time']}s"},
                        {'type': 'stat', 'label': '活跃告警',
                         'value': self.get_dashboard_data()['performance_stats']['active_alerts']},
                        {'type': 'stat', 'label': '已优化图片', 'value': self.image_stats['total_images_optimized']},
                    ],
                },
                {
                    'title': '缓存设置',
                    'fields': [
                        {
                            'key': 'enable_page_cache',
                            'label': '启用页面缓存',
                            'type': 'boolean',
                        },
                        {
                            'key': 'cache_ttl',
                            'label': '缓存时长（秒）',
                            'type': 'number',
                            'min': 60,
                            'max': 86400,
                        },
                    ],
                },
                {
                    'title': '监控设置',
                    'fields': [
                        {
                            'key': 'enable_performance_monitor',
                            'label': '启用性能监控',
                            'type': 'boolean',
                        },
                        {
                            'key': 'page_load_threshold',
                            'label': '页面加载阈值（秒）',
                            'type': 'number',
                            'min': 0.5,
                            'max': 10,
                        },
                        {
                            'key': 'slow_query_threshold',
                            'label': '慢查询阈值（毫秒）',
                            'type': 'number',
                            'min': 10,
                            'max': 5000,
                        },
                    ],
                },
                {
                    'title': '操作',
                    'actions': [
                        {
                            'type': 'button',
                            'label': '清除所有缓存',
                            'action': 'clear_cache',
                            'variant': 'danger',
                            'confirm': '确定要清除所有缓存吗？',
                        },
                        {
                            'type': 'button',
                            'label': '查看性能报告',
                            'action': 'view_report',
                            'variant': 'outline',
                        },
                    ],
                },
            ],
        }


# 导出插件实例
plugin = OptimizationPlugin()
