"""
异常行为检测服务

检测和识别系统中的异常行为模式
包括异常登录、暴力破解、数据泄露等
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


class AnomalyDetector:
    """
    异常行为检测器
    
    使用基于规则的方法检测异常行为
    """

    def __init__(self):
        """初始化异常行为检测器"""
        # 登录尝试记录 {ip: [(timestamp, success), ...]}
        self.login_attempts: Dict[str, List[tuple]] = defaultdict(list)

        # 用户活动记录 {user_id: [(action, timestamp, details), ...]}
        self.user_activities: Dict[int, List[tuple]] = defaultdict(list)

        # 访问模式 {ip: [timestamps]}
        self.access_patterns: Dict[str, List[datetime]] = defaultdict(list)

        # 告警阈值配置
        self.thresholds = {
            'login_failures_per_hour': 10,  # 每小时失败登录次数
            'requests_per_minute': 100,  # 每分钟请求数
            'data_export_size_mb': 100,  # 数据导出大小(MB)
            'unusual_hours_start': 23,  # 非正常时间开始(23点)
            'unusual_hours_end': 6,  # 非正常时间结束(6点)
        }

        # 检测到的异常事件
        self.anomalies: List[Dict[str, Any]] = []

    def record_login_attempt(
            self,
            ip_address: str,
            username: str,
            success: bool,
            timestamp: Optional[datetime] = None
    ):
        """
        记录登录尝试
        
        Args:
            ip_address: IP地址
            username: 用户名
            success: 是否成功
            timestamp: 时间戳
        """
        if timestamp is None:
            timestamp = datetime.now()

        self.login_attempts[ip_address].append((timestamp, success, username))

        # 清理旧记录（保留24小时）
        cutoff = timestamp - timedelta(hours=24)
        self.login_attempts[ip_address] = [
            (t, s, u) for t, s, u in self.login_attempts[ip_address]
            if t > cutoff
        ]

        # 检测异常
        self._detect_brute_force(ip_address, timestamp)

    def record_user_activity(
            self,
            user_id: int,
            action: str,
            details: Optional[Dict[str, Any]] = None,
            timestamp: Optional[datetime] = None
    ):
        """
        记录用户活动
        
        Args:
            user_id: 用户ID
            action: 操作类型
            details: 详细信息
            timestamp: 时间戳
        """
        if timestamp is None:
            timestamp = datetime.now()

        self.user_activities[user_id].append((action, timestamp, details or {}))

        # 清理旧记录（保留7天）
        cutoff = timestamp - timedelta(days=7)
        self.user_activities[user_id] = [
            (a, t, d) for a, t, d in self.user_activities[user_id]
            if t > cutoff
        ]

        # 检测异常
        self._detect_unusual_activity(user_id, action, timestamp)

    def record_access(
            self,
            ip_address: str,
            timestamp: Optional[datetime] = None
    ):
        """
        记录访问
        
        Args:
            ip_address: IP地址
            timestamp: 时间戳
        """
        if timestamp is None:
            timestamp = datetime.now()

        self.access_patterns[ip_address].append(timestamp)

        # 清理旧记录（保留1小时）
        cutoff = timestamp - timedelta(hours=1)
        self.access_patterns[ip_address] = [
            t for t in self.access_patterns[ip_address]
            if t > cutoff
        ]

        # 检测异常
        self._detect_rate_abuse(ip_address, timestamp)

    def get_anomalies(
            self,
            hours: int = 24,
            anomaly_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取异常事件
        
        Args:
            hours: 最近多少小时
            anomaly_type: 异常类型过滤
        
        Returns:
            异常事件列表
        """
        cutoff = datetime.now() - timedelta(hours=hours)

        filtered = [
            anomaly for anomaly in self.anomalies
            if anomaly['timestamp'] > cutoff
        ]

        if anomaly_type:
            filtered = [
                anomaly for anomaly in filtered
                if anomaly['type'] == anomaly_type
            ]

        # 按时间排序
        filtered.sort(key=lambda x: x['timestamp'], reverse=True)

        return filtered

    def get_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取统计信息
        
        Args:
            hours: 统计最近多少小时
        
        Returns:
            统计信息
        """
        anomalies = self.get_anomalies(hours=hours)

        # 按类型统计
        by_type = defaultdict(int)
        for anomaly in anomalies:
            by_type[anomaly['type']] += 1

        # 按严重程度统计
        by_severity = defaultdict(int)
        for anomaly in anomalies:
            by_severity[anomaly['severity']] += 1

        return {
            'period_hours': hours,
            'total_anomalies': len(anomalies),
            'by_type': dict(by_type),
            'by_severity': dict(by_severity),
            'top_ips': self._get_top_suspicious_ips(hours),
        }

    def _detect_brute_force(self, ip_address: str, timestamp: datetime):
        """
        检测暴力破解
        
        Args:
            ip_address: IP地址
            timestamp: 当前时间
        """
        attempts = self.login_attempts[ip_address]

        # 统计最近1小时的失败尝试
        cutoff = timestamp - timedelta(hours=1)
        recent_failures = [
            (t, s, u) for t, s, u in attempts
            if t > cutoff and not s
        ]

        if len(recent_failures) >= self.thresholds['login_failures_per_hour']:
            anomaly = {
                'type': 'brute_force',
                'severity': 'high',
                'title': '检测到暴力破解',
                'message': f'IP {ip_address} 在1小时内有 {len(recent_failures)} 次失败登录',
                'ip_address': ip_address,
                'timestamp': timestamp,
                'details': {
                    'failure_count': len(recent_failures),
                    'threshold': self.thresholds['login_failures_per_hour'],
                    'usernames_tried': list(set(u for _, _, u in recent_failures)),
                }
            }

            # 避免重复告警
            if not self._is_duplicate_anomaly(anomaly):
                self.anomalies.append(anomaly)

    def _detect_unusual_activity(
            self,
            user_id: int,
            action: str,
            timestamp: datetime
    ):
        """
        检测异常活动
        
        Args:
            user_id: 用户ID
            action: 操作类型
            timestamp: 时间戳
        """
        # 检测非正常时间登录
        hour = timestamp.hour
        if (hour >= self.thresholds['unusual_hours_start'] or
                hour < self.thresholds['unusual_hours_end']):

            if action == 'login':
                anomaly = {
                    'type': 'unusual_time_login',
                    'severity': 'medium',
                    'title': '非正常时间登录',
                    'message': f'用户 {user_id} 在 {hour}:00 登录',
                    'user_id': user_id,
                    'timestamp': timestamp,
                    'details': {
                        'login_hour': hour,
                        'normal_range': f"{self.thresholds['unusual_hours_end']}:00 - {self.thresholds['unusual_hours_start']}:00",
                    }
                }

                if not self._is_duplicate_anomaly(anomaly):
                    self.anomalies.append(anomaly)

        # 检测大量数据导出
        if action == 'data_export':
            size_mb = (action.get('size_bytes', 0) / (1024 * 1024)) if isinstance(action, dict) else 0
            if size_mb > self.thresholds['data_export_size_mb']:
                anomaly = {
                    'type': 'large_data_export',
                    'severity': 'high',
                    'title': '大量数据导出',
                    'message': f'用户 {user_id} 导出了 {size_mb:.2f}MB 数据',
                    'user_id': user_id,
                    'timestamp': timestamp,
                    'details': {
                        'export_size_mb': size_mb,
                        'threshold_mb': self.thresholds['data_export_size_mb'],
                    }
                }

                if not self._is_duplicate_anomaly(anomaly):
                    self.anomalies.append(anomaly)

    def _detect_rate_abuse(self, ip_address: str, timestamp: datetime):
        """
        检测速率滥用
        
        Args:
            ip_address: IP地址
            timestamp: 时间戳
        """
        accesses = self.access_patterns[ip_address]

        # 统计最近1分钟的请求数
        cutoff = timestamp - timedelta(minutes=1)
        recent_requests = [t for t in accesses if t > cutoff]

        if len(recent_requests) >= self.thresholds['requests_per_minute']:
            anomaly = {
                'type': 'rate_abuse',
                'severity': 'medium',
                'title': '检测到速率滥用',
                'message': f'IP {ip_address} 在1分钟内有 {len(recent_requests)} 次请求',
                'ip_address': ip_address,
                'timestamp': timestamp,
                'details': {
                    'request_count': len(recent_requests),
                    'threshold': self.thresholds['requests_per_minute'],
                }
            }

            if not self._is_duplicate_anomaly(anomaly):
                self.anomalies.append(anomaly)

    def _is_duplicate_anomaly(self, new_anomaly: Dict[str, Any]) -> bool:
        """
        检查是否是重复的异常
        
        Args:
            new_anomaly: 新的异常
        
        Returns:
            是否重复
        """
        cutoff = new_anomaly['timestamp'] - timedelta(minutes=5)

        for existing in self.anomalies:
            if (existing['type'] == new_anomaly['type'] and
                    existing.get('ip_address') == new_anomaly.get('ip_address') and
                    existing.get('user_id') == new_anomaly.get('user_id') and
                    existing['timestamp'] > cutoff):
                return True

        return False

    def _get_top_suspicious_ips(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        获取最可疑的IP列表
        
        Args:
            hours: 时间范围
        
        Returns:
            可疑IP列表
        """
        cutoff = datetime.now() - timedelta(hours=hours)

        ip_scores = defaultdict(lambda: {'score': 0, 'anomalies': []})

        for anomaly in self.anomalies:
            if anomaly['timestamp'] > cutoff and 'ip_address' in anomaly:
                ip = anomaly['ip_address']
                ip_scores[ip]['score'] += 1
                ip_scores[ip]['anomalies'].append(anomaly['type'])

        # 按分数排序
        sorted_ips = sorted(
            ip_scores.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )

        return [
            {
                'ip': ip,
                'score': data['score'],
                'anomaly_types': list(set(data['anomalies'])),
            }
            for ip, data in sorted_ips[:10]
        ]

    def update_thresholds(self, **kwargs):
        """
        更新阈值配置
        
        Args:
            **kwargs: 阈值配置
        """
        self.thresholds.update(kwargs)


# 全局实例
anomaly_detector = AnomalyDetector()

# 导出
__all__ = ['AnomalyDetector', 'anomaly_detector']
