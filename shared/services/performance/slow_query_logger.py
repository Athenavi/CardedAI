"""
慢查询日志服务

记录和分析数据库慢查询
提供查询优化建议
"""

from collections import deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


class SlowQueryLogger:
    """
    慢查询日志服务
    
    记录和监控数据库慢查询
    支持阈值配置和日志分析
    """

    def __init__(self, threshold: float = 0.1, max_logs: int = 1000):
        """
        初始化慢查询日志
        
        Args:
            threshold: 慢查询阈值(秒)，默认100ms
            max_logs: 最大日志数量
        """
        self.threshold = threshold
        self.max_logs = max_logs
        self.queries = deque(maxlen=max_logs)

        # 统计信息
        self.stats = {
            'total_queries': 0,
            'slow_queries': 0,
            'total_time': 0.0,
            'slowest_query_time': 0.0,
        }

    def log_query(
            self,
            sql: str,
            duration: float,
            params: Optional[Dict[str, Any]] = None,
            table: Optional[str] = None,
            query_type: Optional[str] = None,
    ):
        """
        记录查询
        
        Args:
            sql: SQL语句
            duration: 执行时间(秒)
            params: 查询参数
            table: 表名
            query_type: 查询类型 (SELECT, INSERT, UPDATE, DELETE)
        """
        self.stats['total_queries'] += 1
        self.stats['total_time'] += duration

        if duration > self.stats['slowest_query_time']:
            self.stats['slowest_query_time'] = duration

        # 只记录慢查询
        if duration >= self.threshold:
            self.stats['slow_queries'] += 1

            query_log = {
                'sql': sql[:2000],  # 限制SQL长度
                'duration': duration,
                'params': params,
                'table': table,
                'query_type': query_type or self._detect_query_type(sql),
                'timestamp': datetime.now().isoformat(),
            }

            self.queries.append(query_log)

    def get_slow_queries(
            self,
            limit: int = 50,
            hours: int = 24,
            table: Optional[str] = None,
            query_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取慢查询列表
        
        Args:
            limit: 返回数量限制
            hours: 最近多少小时的数据
            table: 表名过滤
            query_type: 查询类型过滤
        
        Returns:
            慢查询列表
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # 过滤数据
        filtered = []
        for query in self.queries:
            query_time = datetime.fromisoformat(query['timestamp'])

            if query_time < cutoff_time:
                continue

            if table and query.get('table') != table:
                continue

            if query_type and query.get('query_type') != query_type:
                continue

            filtered.append(query)

        # 按执行时间排序
        sorted_queries = sorted(filtered, key=lambda x: x['duration'], reverse=True)

        return sorted_queries[:limit]

    def get_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取统计信息
        
        Args:
            hours: 统计最近多少小时
        
        Returns:
            统计信息字典
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # 过滤数据
        recent_queries = [
            q for q in self.queries
            if datetime.fromisoformat(q['timestamp']) >= cutoff_time
        ]

        if not recent_queries:
            return {
                'period_hours': hours,
                'total_queries': 0,
                'slow_queries': 0,
                'avg_duration': 0,
                'max_duration': 0,
                'by_table': {},
                'by_type': {},
            }

        durations = [q['duration'] for q in recent_queries]

        # 按表统计
        by_table = {}
        for query in recent_queries:
            table = query.get('table', 'unknown')
            if table not in by_table:
                by_table[table] = {
                    'count': 0,
                    'total_time': 0,
                    'avg_time': 0,
                    'max_time': 0,
                }
            by_table[table]['count'] += 1
            by_table[table]['total_time'] += query['duration']
            by_table[table]['avg_time'] = by_table[table]['total_time'] / by_table[table]['count']
            if query['duration'] > by_table[table]['max_time']:
                by_table[table]['max_time'] = query['duration']

        # 按类型统计
        by_type = {}
        for query in recent_queries:
            qtype = query.get('query_type', 'UNKNOWN')
            if qtype not in by_type:
                by_type[qtype] = {'count': 0, 'total_time': 0}
            by_type[qtype]['count'] += 1
            by_type[qtype]['total_time'] += query['duration']

        return {
            'period_hours': hours,
            'total_queries': len(recent_queries),
            'slow_queries': len(recent_queries),
            'avg_duration': sum(durations) / len(durations),
            'max_duration': max(durations),
            'by_table': by_table,
            'by_type': by_type,
        }

    def get_optimization_suggestions(self) -> List[Dict[str, str]]:
        """
        生成优化建议
        
        Returns:
            优化建议列表
        """
        suggestions = []

        if not self.queries:
            return suggestions

        # 分析最慢的查询
        slowest_queries = sorted(self.queries, key=lambda x: x['duration'], reverse=True)[:10]

        for query in slowest_queries:
            suggestion = self._analyze_query(query)
            if suggestion:
                suggestions.append(suggestion)

        # 检查重复查询模式
        pattern_counts = {}
        for query in self.queries:
            pattern = self._normalize_sql(query['sql'])
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

        for pattern, count in pattern_counts.items():
            if count >= 10:  # 相同模式出现10次以上
                suggestions.append({
                    'type': 'warning',
                    'title': '重复查询模式',
                    'message': f'查询模式出现 {count} 次，考虑缓存结果',
                    'pattern': pattern[:200],
                    'recommendation': '使用对象缓存或页面缓存减少数据库访问',
                })

        return suggestions

    def _analyze_query(self, query: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        分析单个查询并生成建议
        
        Args:
            query: 查询日志
        
        Returns:
            优化建议
        """
        sql = query['sql'].upper()
        duration = query['duration']
        table = query.get('table', 'unknown')

        suggestion = {
            'table': table,
            'duration': duration,
            'sql': query['sql'][:200],
        }

        # 检查是否缺少WHERE子句
        if 'SELECT' in sql and 'WHERE' not in sql:
            suggestion['type'] = 'critical'
            suggestion['title'] = '全表扫描'
            suggestion['message'] = f'表 "{table}" 的查询缺少WHERE条件'
            suggestion['recommendation'] = '添加WHERE条件或使用LIMIT限制返回行数'
            return suggestion

        # 检查是否使用LIKE前缀通配符
        if 'LIKE' in sql and "'%" in query['sql']:
            suggestion['type'] = 'warning'
            suggestion['title'] = '低效的LIKE查询'
            suggestion['message'] = '使用前缀通配符 % 会导致索引失效'
            suggestion['recommendation'] = '考虑使用全文搜索或重构查询'
            return suggestion

        # 检查是否使用SELECT *
        if 'SELECT *' in sql:
            suggestion['type'] = 'info'
            suggestion['title'] = '使用 SELECT *'
            suggestion['message'] = 'SELECT * 会返回所有列，可能包含不必要的数据'
            suggestion['recommendation'] = '明确指定需要的列名'
            return suggestion

        # 检查执行时间
        if duration > 1.0:
            suggestion['type'] = 'critical'
            suggestion['title'] = '超慢查询'
            suggestion['message'] = f'查询执行时间 {duration:.2f}秒，超过1秒'
            suggestion['recommendation'] = '添加索引、优化查询逻辑或使用缓存'
            return suggestion
        elif duration > 0.5:
            suggestion['type'] = 'warning'
            suggestion['title'] = '慢查询'
            suggestion['message'] = f'查询执行时间 {duration:.2f}秒'
            suggestion['recommendation'] = '考虑添加索引或优化查询'
            return suggestion

        return None

    def _normalize_sql(self, sql: str) -> str:
        """
        标准化SQL用于模式匹配
        
        Args:
            sql: 原始SQL
        
        Returns:
            标准化的SQL
        """
        import re

        # 替换数字为占位符
        normalized = re.sub(r'\b\d+\b', '?', sql)

        # 替换字符串值为占位符
        normalized = re.sub(r"'[^']*'", '?', normalized)

        # 移除多余空格
        normalized = ' '.join(normalized.split())

        return normalized

    def _detect_query_type(self, sql: str) -> str:
        """
        检测查询类型
        
        Args:
            sql: SQL语句
        
        Returns:
            查询类型
        """
        sql_upper = sql.strip().upper()

        if sql_upper.startswith('SELECT'):
            return 'SELECT'
        elif sql_upper.startswith('INSERT'):
            return 'INSERT'
        elif sql_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif sql_upper.startswith('DELETE'):
            return 'DELETE'

        return 'OTHER'

    def clear_logs(self):
        """清空日志"""
        self.queries.clear()
        self.stats = {
            'total_queries': 0,
            'slow_queries': 0,
            'total_time': 0.0,
            'slowest_query_time': 0.0,
        }

    def update_threshold(self, new_threshold: float):
        """
        更新慢查询阈值
        
        Args:
            new_threshold: 新的阈值(秒)
        """
        self.threshold = new_threshold


# 全局实例
slow_query_logger = SlowQueryLogger(threshold=0.1)

# 导出
__all__ = ['SlowQueryLogger', 'slow_query_logger']
