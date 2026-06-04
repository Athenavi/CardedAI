"""
数据库查询监控服务
提供查询分析、N+1检测、性能统计等功能
类似WordPress的Query Monitor插件
"""
import re
import time
from collections import defaultdict
from typing import Dict, List, Any, Optional


class QueryMonitorService:
    """查询监控服务"""
    
    def __init__(self):
        self.queries: List[Dict[str, Any]] = []
        self.start_time: Optional[float] = None
        self.enabled = False
    
    def start_recording(self):
        """开始记录查询"""
        self.enabled = True
        self.start_time = time.time()
        self.queries = []
    
    def stop_recording(self) -> Dict[str, Any]:
        """停止记录并返回分析报告"""
        self.enabled = False
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        analysis = self._analyze_queries()
        
        return {
            'total_time': round(elapsed, 4),
            'query_count': len(self.queries),
            'analysis': analysis,
            'queries': self.queries[-50:],  # 只返回最近50条
        }
    
    def record_query(self, sql: str, duration: float, caller: str = ''):
        """记录单条查询"""
        if not self.enabled:
            return
        
        query_info = {
            'sql': sql,
            'duration': round(duration, 4),
            'caller': caller,
            'timestamp': time.time(),
            'type': self._get_query_type(sql),
            'table': self._extract_table(sql),
        }
        
        self.queries.append(query_info)
    
    def _analyze_queries(self) -> Dict[str, Any]:
        """分析查询模式"""
        if not self.queries:
            return {
                'slow_queries': [],
                'duplicate_queries': [],
                'n_plus_one_patterns': [],
                'table_stats': {},
                'type_distribution': {},
            }
        
        # 慢查询 (>100ms)
        slow_queries = [q for q in self.queries if q['duration'] > 0.1]
        
        # 重复查询检测
        query_counts = defaultdict(list)
        for i, q in enumerate(self.queries):
            simplified = self._simplify_sql(q['sql'])
            query_counts[simplified].append(i)
        
        duplicate_queries = []
        for sql_pattern, indices in query_counts.items():
            if len(indices) > 3:  # 出现3次以上视为重复
                duplicate_queries.append({
                    'pattern': sql_pattern[:200],
                    'count': len(indices),
                    'total_time': sum(self.queries[i]['duration'] for i in indices),
                })
        
        # N+1检测 (相同模式在短时间内多次执行)
        n_plus_one_patterns = self._detect_n_plus_one()
        
        # 表统计
        table_stats = defaultdict(lambda: {'count': 0, 'total_time': 0})
        for q in self.queries:
            if q['table']:
                table_stats[q['table']]['count'] += 1
                table_stats[q['table']]['total_time'] += q['duration']
        
        # 查询类型分布
        type_dist = defaultdict(int)
        for q in self.queries:
            type_dist[q['type']] += 1
        
        return {
            'slow_queries': sorted(slow_queries, key=lambda x: x['duration'], reverse=True)[:10],
            'duplicate_queries': sorted(duplicate_queries, key=lambda x: x['count'], reverse=True)[:10],
            'n_plus_one_patterns': n_plus_one_patterns[:10],
            'table_stats': dict(table_stats),
            'type_distribution': dict(type_dist),
        }
    
    def _detect_n_plus_one(self) -> List[Dict[str, Any]]:
        """检测N+1查询模式"""
        patterns = defaultdict(list)
        
        for q in self.queries:
            simplified = self._simplify_sql(q['sql'])
            patterns[simplified].append(q)
        
        n_plus_one = []
        for pattern, queries in patterns.items():
            if len(queries) >= 5:  # 5次以上可能是N+1
                # 检查是否在短时间内连续执行
                timestamps = [q['timestamp'] for q in queries]
                time_span = max(timestamps) - min(timestamps)
                
                if time_span < 2.0:  # 2秒内执行5次以上
                    n_plus_one.append({
                        'pattern': pattern[:200],
                        'count': len(queries),
                        'time_span': round(time_span, 3),
                        'total_time': round(sum(q['duration'] for q in queries), 4),
                        'avg_time': round(sum(q['duration'] for q in queries) / len(queries), 4),
                        'suggestion': f'考虑使用 select_related 或 prefetch_related 优化',
                    })
        
        return sorted(n_plus_one, key=lambda x: x['count'], reverse=True)
    
    def _simplify_sql(self, sql: str) -> str:
        """简化SQL以检测模式"""
        if not sql:
            return ''
        
        # 移除具体值
        simplified = re.sub(r"'[^']*'", "'?'", sql)
        simplified = re.sub(r'\b\d+\b', '?', simplified)
        
        # 标准化空格
        simplified = re.sub(r'\s+', ' ', simplified).strip()
        
        return simplified
    
    def _get_query_type(self, sql: str) -> str:
        """获取查询类型"""
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
    
    def _extract_table(self, sql: str) -> Optional[str]:
        """提取表名"""
        if not sql:
            return None
        
        # SELECT ... FROM table
        match = re.search(r'\bFROM\s+(\w+)', sql, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # INSERT INTO table
        match = re.search(r'\bINTO\s+(\w+)', sql, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # UPDATE table
        match = re.search(r'\bUPDATE\s+(\w+)', sql, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None
    
    def get_summary(self) -> Dict[str, Any]:
        """获取查询摘要"""
        if not self.queries:
            return {
                'total_queries': 0,
                'total_time': 0,
                'avg_time': 0,
                'slowest_query': None,
            }
        
        total_time = sum(q['duration'] for q in self.queries)
        slowest = max(self.queries, key=lambda x: x['duration'])
        
        return {
            'total_queries': len(self.queries),
            'total_time': round(total_time, 4),
            'avg_time': round(total_time / len(self.queries), 4),
            'slowest_query': {
                'sql': slowest['sql'][:200],
                'duration': slowest['duration'],
            },
        }


# 全局实例
query_monitor_service = QueryMonitorService()
