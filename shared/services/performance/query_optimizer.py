"""
数据库查询优化服务
提供查询分析、慢查询检测、索引建议等功能
"""


import time
from contextlib import asynccontextmanager
from typing import Dict, List, Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.unified_logger import default_logger as logger


class QueryOptimizer:
    """
    数据库查询优化器
    
    功能：
    1. 慢查询检测
    2. 查询统计
    3. N+1查询检测
    4. 索引使用分析
    5. 查询计划分析
    """

    def __init__(self, slow_query_threshold: float = 1.0):
        """
        初始化查询优化器
        
        Args:
            slow_query_threshold: 慢查询阈值（秒）
        """
        self.slow_query_threshold = slow_query_threshold
        self.query_stats: Dict[str, Dict] = {}
        self.slow_queries: List[Dict] = []
        self.n_plus_one_warnings: List[Dict] = []

    @asynccontextmanager
    async def track_query(self, query_name: str = "unnamed"):
        """
        上下文管理器：跟踪查询性能
        
        Usage:
            async with query_optimizer.track_query("get_articles"):
                result = await db.execute(query)
        """
        start_time = time.time()

        try:
            yield
        finally:
            duration = time.time() - start_time

            # 记录统计
            if query_name not in self.query_stats:
                self.query_stats[query_name] = {
                    'count': 0,
                    'total_time': 0,
                    'avg_time': 0,
                    'max_time': 0,
                    'min_time': float('inf'),
                }

            stats = self.query_stats[query_name]
            stats['count'] += 1
            stats['total_time'] += duration
            stats['avg_time'] = stats['total_time'] / stats['count']
            stats['max_time'] = max(stats['max_time'], duration)
            stats['min_time'] = min(stats['min_time'], duration)

            # 检测慢查询
            if duration > self.slow_query_threshold:
                slow_query_info = {
                    'query_name': query_name,
                    'duration': duration,
                    'timestamp': time.time(),
                }
                self.slow_queries.append(slow_query_info)

                logger.warning(
                    f"Slow query detected: {query_name} took {duration:.3f}s "
                    f"(threshold: {self.slow_query_threshold}s)"
                )

    def detect_n_plus_one(self, query_pattern: str, execution_count: int, threshold: int = 10):
        """
        检测N+1查询问题
        
        Args:
            query_pattern: 查询模式
            execution_count: 执行次数
            threshold: 触发警告的阈值
        """
        if execution_count > threshold:
            warning = {
                'pattern': query_pattern,
                'count': execution_count,
                'threshold': threshold,
                'timestamp': time.time(),
            }
            self.n_plus_one_warnings.append(warning)

            logger.warning(
                f"Potential N+1 query detected: {query_pattern} "
                f"executed {execution_count} times (threshold: {threshold})"
            )

    async def analyze_query_plan(self, db: AsyncSession, sql_query: str) -> Dict:
        """
        分析查询计划（PostgreSQL EXPLAIN）
        
        Args:
            db: 数据库会话
            sql_query: SQL查询语句
            
        Returns:
            查询计划分析结果
        """
        try:
            # 执行EXPLAIN ANALYZE
            explain_query = f"EXPLAIN (ANALYZE, FORMAT JSON) {sql_query}"
            result = await db.execute(text(explain_query))
            plan = result.scalar()

            return {
                'success': True,
                'plan': plan,
                'recommendations': self._analyze_plan(plan),
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }

    def _analyze_plan(self, plan: Any) -> List[str]:
        """分析查询计划并给出建议"""
        recommendations = []

        # 这里可以添加更复杂的分析逻辑
        # 简化版本：检查是否使用了全表扫描

        plan_str = str(plan).lower()

        if 'seq scan' in plan_str:
            recommendations.append(
                "考虑添加索引以避免全表扫描（Sequential Scan）"
            )

        if 'nested loop' in plan_str and 'seq scan' in plan_str:
            recommendations.append(
                "嵌套循环 + 全表扫描可能导致性能问题，建议添加索引"
            )

        if 'sort' in plan_str and 'disk' in plan_str:
            recommendations.append(
                "排序操作使用了磁盘，考虑增加work_mem或添加索引"
            )

        return recommendations

    def get_optimization_report(self) -> Dict:
        """
        生成优化报告
        
        Returns:
            包含所有统计和建议的报告
        """
        # 找出最慢的查询
        top_slow_queries = sorted(
            self.slow_queries,
            key=lambda x: x['duration'],
            reverse=True
        )[:10]

        # 找出最频繁的查询
        frequent_queries = sorted(
            self.query_stats.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:10]

        return {
            'summary': {
                'total_queries_tracked': len(self.query_stats),
                'total_slow_queries': len(self.slow_queries),
                'total_n_plus_one_warnings': len(self.n_plus_one_warnings),
            },
            'slow_query_threshold': self.slow_query_threshold,
            'top_slow_queries': top_slow_queries,
            'most_frequent_queries': [
                {'name': name, **stats}
                for name, stats in frequent_queries
            ],
            'n_plus_one_warnings': self.n_plus_one_warnings[-10:],
            'recommendations': self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []

        # 检查是否有大量慢查询
        if len(self.slow_queries) > 10:
            recommendations.append(
                f"检测到 {len(self.slow_queries)} 个慢查询，建议审查数据库索引和查询逻辑"
            )

        # 检查N+1问题
        if self.n_plus_one_warnings:
            recommendations.append(
                f"检测到 {len(self.n_plus_one_warnings)} 个潜在N+1查询问题，"
                f"建议使用eager loading（joinedload/selectinload）"
            )

        # 检查高频查询
        for name, stats in self.query_stats.items():
            if stats['count'] > 1000 and stats['avg_time'] > 0.1:
                recommendations.append(
                    f"查询 '{name}' 执行频繁({stats['count']}次)且平均耗时较长"
                    f"({stats['avg_time']:.3f}s)，建议添加缓存"
                )

        return recommendations

    def reset_stats(self):
        """重置统计数据"""
        self.query_stats.clear()
        self.slow_queries.clear()
        self.n_plus_one_warnings.clear()


# 全局实例
query_optimizer = QueryOptimizer(slow_query_threshold=1.0)


def optimize_query(func):
    """
    装饰器：自动跟踪查询性能
    
    Usage:
        @optimize_query
        async def get_articles():
            ...
    """
    import functools

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        query_name = func.__name__

        async with query_optimizer.track_query(query_name):
            result = await func(*args, **kwargs)

        return result

    return wrapper
