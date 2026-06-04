"""
安全报告生成服务

生成日报、周报、月报等安全报告
提供趋势分析和可视化数据
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


class SecurityReportGenerator:
    """
    安全报告生成器
    
    生成各种周期的安全报告
    """

    def __init__(self):
        """初始化报告生成器"""
        self.report_history: List[Dict[str, Any]] = []

    def generate_daily_report(
            self,
            anomalies: List[Dict[str, Any]],
            alerts: List[Dict[str, Any]],
            audit_logs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        生成日报
        
        Args:
            anomalies: 异常事件列表
            alerts: 告警列表
            audit_logs: 审计日志列表
        
        Returns:
            日报数据
        """
        today = datetime.now().date()

        # 过滤今天的数据
        today_anomalies = [
            a for a in anomalies
            if datetime.fromisoformat(a['timestamp']).date() == today
        ]

        today_alerts = [
            a for a in alerts
            if datetime.fromisoformat(a['timestamp']).date() == today
        ]

        today_logs = [
            log for log in audit_logs
            if datetime.fromisoformat(log['timestamp']).date() == today
        ]

        report = {
            'report_type': 'daily',
            'date': today.isoformat(),
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_anomalies': len(today_anomalies),
                'total_alerts': len(today_alerts),
                'total_audit_events': len(today_logs),
            },
            'anomalies': self._summarize_anomalies(today_anomalies),
            'alerts': self._summarize_alerts(today_alerts),
            'top_actions': self._get_top_actions(today_logs),
            'recommendations': self._generate_recommendations(today_anomalies, today_alerts),
        }

        self.report_history.append(report)

        return report

    def generate_weekly_report(
            self,
            anomalies: List[Dict[str, Any]],
            alerts: List[Dict[str, Any]],
            audit_logs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        生成周报
        
        Args:
            anomalies: 异常事件列表
            alerts: 告警列表
            audit_logs: 审计日志列表
        
        Returns:
            周报数据
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)

        # 过滤本周数据
        week_anomalies = [
            a for a in anomalies
            if start_date <= datetime.fromisoformat(a['timestamp']).date() <= end_date
        ]

        week_alerts = [
            a for a in alerts
            if start_date <= datetime.fromisoformat(a['timestamp']).date() <= end_date
        ]

        week_logs = [
            log for log in audit_logs
            if start_date <= datetime.fromisoformat(log['timestamp']).date() <= end_date
        ]

        # 按天统计趋势
        daily_trend = self._calculate_daily_trend(week_anomalies, week_alerts, 7)

        report = {
            'report_type': 'weekly',
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            },
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_anomalies': len(week_anomalies),
                'total_alerts': len(week_alerts),
                'total_audit_events': len(week_logs),
                'avg_anomalies_per_day': len(week_anomalies) / 7,
                'avg_alerts_per_day': len(week_alerts) / 7,
            },
            'trend': daily_trend,
            'anomalies': self._summarize_anomalies(week_anomalies),
            'alerts': self._summarize_alerts(week_alerts),
            'comparison': self._compare_with_previous_week(week_anomalies, week_alerts),
            'recommendations': self._generate_recommendations(week_anomalies, week_alerts),
        }

        self.report_history.append(report)

        return report

    def generate_monthly_report(
            self,
            anomalies: List[Dict[str, Any]],
            alerts: List[Dict[str, Any]],
            audit_logs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        生成月报
        
        Args:
            anomalies: 异常事件列表
            alerts: 告警列表
            audit_logs: 审计日志列表
        
        Returns:
            月报数据
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)

        # 过滤本月数据
        month_anomalies = [
            a for a in anomalies
            if start_date <= datetime.fromisoformat(a['timestamp']).date() <= end_date
        ]

        month_alerts = [
            a for a in alerts
            if start_date <= datetime.fromisoformat(a['timestamp']).date() <= end_date
        ]

        month_logs = [
            log for log in audit_logs
            if start_date <= datetime.fromisoformat(log['timestamp']).date() <= end_date
        ]

        # 按周统计趋势
        weekly_trend = self._calculate_weekly_trend(month_anomalies, month_alerts, 4)

        report = {
            'report_type': 'monthly',
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            },
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_anomalies': len(month_anomalies),
                'total_alerts': len(month_alerts),
                'total_audit_events': len(month_logs),
                'avg_anomalies_per_day': len(month_anomalies) / 30,
                'avg_alerts_per_day': len(month_alerts) / 30,
            },
            'trend': weekly_trend,
            'anomalies': self._summarize_anomalies(month_anomalies),
            'alerts': self._summarize_alerts(month_alerts),
            'security_score': self._calculate_security_score(month_anomalies, month_alerts),
            'recommendations': self._generate_recommendations(month_anomalies, month_alerts),
        }

        self.report_history.append(report)

        return report

    def _summarize_anomalies(self, anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """总结异常事件"""
        by_type = defaultdict(int)
        by_severity = defaultdict(int)

        for anomaly in anomalies:
            by_type[anomaly.get('type', 'unknown')] += 1
            by_severity[anomaly.get('severity', 'unknown')] += 1

        return {
            'by_type': dict(by_type),
            'by_severity': dict(by_severity),
            'total': len(anomalies),
        }

    def _summarize_alerts(self, alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """总结告警"""
        by_type = defaultdict(int)
        by_severity = defaultdict(int)
        delivery_stats = {'success': 0, 'failed': 0}

        for alert in alerts:
            by_type[alert.get('type', 'unknown')] += 1
            by_severity[alert.get('severity', 'unknown')] += 1

            # 统计发送结果
            results = alert.get('results', {})
            if any(results.values()):
                delivery_stats['success'] += 1
            else:
                delivery_stats['failed'] += 1

        return {
            'by_type': dict(by_type),
            'by_severity': dict(by_severity),
            'delivery_stats': delivery_stats,
            'total': len(alerts),
        }

    def _get_top_actions(self, logs: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        """获取最常见的操作"""
        action_counts = defaultdict(int)

        for log in logs:
            action = log.get('action', 'unknown')
            action_counts[action] += 1

        sorted_actions = sorted(
            action_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [
            {'action': action, 'count': count}
            for action, count in sorted_actions[:limit]
        ]

    def _calculate_daily_trend(
            self,
            anomalies: List[Dict[str, Any]],
            alerts: List[Dict[str, Any]],
            days: int
    ) -> List[Dict[str, Any]]:
        """计算每日趋势"""
        trend = []
        end_date = datetime.now().date()

        for i in range(days):
            date = end_date - timedelta(days=days - 1 - i)

            day_anomalies = len([
                a for a in anomalies
                if datetime.fromisoformat(a['timestamp']).date() == date
            ])

            day_alerts = len([
                a for a in alerts
                if datetime.fromisoformat(a['timestamp']).date() == date
            ])

            trend.append({
                'date': date.isoformat(),
                'anomalies': day_anomalies,
                'alerts': day_alerts,
            })

        return trend

    def _calculate_weekly_trend(
            self,
            anomalies: List[Dict[str, Any]],
            alerts: List[Dict[str, Any]],
            weeks: int
    ) -> List[Dict[str, Any]]:
        """计算每周趋势"""
        trend = []
        end_date = datetime.now().date()

        for i in range(weeks):
            week_end = end_date - timedelta(days=(weeks - 1 - i) * 7)
            week_start = week_end - timedelta(days=6)

            week_anomalies = len([
                a for a in anomalies
                if week_start <= datetime.fromisoformat(a['timestamp']).date() <= week_end
            ])

            week_alerts = len([
                a for a in alerts
                if week_start <= datetime.fromisoformat(a['timestamp']).date() <= week_end
            ])

            trend.append({
                'week_start': week_start.isoformat(),
                'week_end': week_end.isoformat(),
                'anomalies': week_anomalies,
                'alerts': week_alerts,
            })

        return trend

    def _compare_with_previous_week(
            self,
            current_anomalies: List[Dict[str, Any]],
            current_alerts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """与上一周对比"""
        # 这里简化实现，实际应该查询历史数据
        return {
            'anomalies_change': 'N/A',
            'alerts_change': 'N/A',
            'note': '需要更多历史数据进行对比',
        }

    def _calculate_security_score(
            self,
            anomalies: List[Dict[str, Any]],
            alerts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """计算安全评分"""
        # 基础分100分
        score = 100

        # 扣分规则
        severity_weights = {
            'critical': 10,
            'high': 5,
            'medium': 2,
            'low': 1,
        }

        for anomaly in anomalies:
            severity = anomaly.get('severity', 'low')
            score -= severity_weights.get(severity, 1)

        score = max(0, min(100, score))

        # 评级
        if score >= 90:
            grade = 'A'
            level = '优秀'
        elif score >= 80:
            grade = 'B'
            level = '良好'
        elif score >= 70:
            grade = 'C'
            level = '一般'
        elif score >= 60:
            grade = 'D'
            level = '较差'
        else:
            grade = 'F'
            level = '危险'

        return {
            'score': score,
            'grade': grade,
            'level': level,
        }

    def _generate_recommendations(
            self,
            anomalies: List[Dict[str, Any]],
            alerts: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """生成建议"""
        recommendations = []

        # 分析异常类型
        anomaly_types = defaultdict(int)
        for anomaly in anomalies:
            anomaly_types[anomaly.get('type', 'unknown')] += 1

        # 根据异常类型生成建议
        if anomaly_types.get('brute_force', 0) > 0:
            recommendations.append({
                'priority': 'high',
                'category': 'authentication',
                'title': '加强登录安全',
                'description': '检测到暴力破解尝试，建议启用双因素认证或IP白名单',
            })

        if anomaly_types.get('unusual_time_login', 0) > 0:
            recommendations.append({
                'priority': 'medium',
                'category': 'monitoring',
                'title': '加强非工作时间监控',
                'description': '检测到非正常时间登录，建议审查相关账户活动',
            })

        if anomaly_types.get('rate_abuse', 0) > 0:
            recommendations.append({
                'priority': 'medium',
                'category': 'rate_limiting',
                'title': '优化速率限制',
                'description': '检测到速率滥用，建议调整速率限制策略',
            })

        if not recommendations:
            recommendations.append({
                'priority': 'low',
                'category': 'general',
                'title': '保持当前安全措施',
                'description': '未发现明显安全问题，继续保持现有安全策略',
            })

        return recommendations

    def get_report_history(
            self,
            report_type: Optional[str] = None,
            limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取报告历史
        
        Args:
            report_type: 报告类型过滤
            limit: 返回数量限制
        
        Returns:
            报告历史列表
        """
        filtered = self.report_history

        if report_type:
            filtered = [r for r in filtered if r['report_type'] == report_type]

        # 按时间排序
        filtered.sort(key=lambda x: x['generated_at'], reverse=True)

        return filtered[:limit]


# 全局实例
report_generator = SecurityReportGenerator()

# 导出
__all__ = ['SecurityReportGenerator', 'report_generator']
