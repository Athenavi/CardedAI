"""
插件权限审计服务

提供插件权限使用的审计、监控和告警功能
记录插件的权限检查、API调用和资源访问
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict


class PluginAuditLogger:
    """
    插件权限审计日志服务
    
    功能:
    1. 记录插件权限使用
    2. 异常行为检测
    3. 权限滥用告警
    4. 审计日志查询和分析
    """

    def __init__(self, log_dir: str = "logs/plugin_audit", max_logs: int = 10000):
        self.log_dir = Path(log_dir)
        self.max_logs = max_logs

        # 确保日志目录存在
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 内存中的审计日志（最近的操作）
        self.audit_logs: List[Dict[str, Any]] = []

        # 权限使用统计
        self.permission_stats: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"granted": 0, "denied": 0}
        )

        # 异常行为检测阈值
        self.thresholds = {
            "max_permission_checks_per_minute": 100,  # 每分钟最大权限检查次数
            "max_denied_ratio": 0.5,  # 最大拒绝率
            "max_api_calls_per_minute": 200,  # 每分钟最大API调用次数
        }

    def log_permission_check(
            self,
            plugin_slug: str,
            capability: str,
            granted: bool,
            context: Optional[Dict[str, Any]] = None
    ):
        """
        记录权限检查
        
        Args:
            plugin_slug: 插件标识
            capability: 权限代码
            granted: 是否授权
            context: 上下文信息
        """
        timestamp = datetime.now()

        log_entry = {
            "timestamp": timestamp.isoformat(),
            "plugin_slug": plugin_slug,
            "action_type": "permission_check",
            "capability": capability,
            "granted": granted,
            "context": context or {},
        }

        # 添加到内存日志
        self.audit_logs.append(log_entry)
        if len(self.audit_logs) > self.max_logs:
            self.audit_logs = self.audit_logs[-self.max_logs:]

        # 更新统计
        stats_key = f"{plugin_slug}:{capability}"
        if granted:
            self.permission_stats[stats_key]["granted"] += 1
        else:
            self.permission_stats[stats_key]["denied"] += 1

        # 写入文件日志
        self._write_log_to_file(plugin_slug, log_entry)

        # 检查异常行为
        self._check_anomalies(plugin_slug)

    def log_api_call(
            self,
            plugin_slug: str,
            api_endpoint: str,
            method: str = "GET",
            success: bool = True,
            duration_ms: float = 0,
            context: Optional[Dict[str, Any]] = None
    ):
        """
        记录API调用
        
        Args:
            plugin_slug: 插件标识
            api_endpoint: API端点
            method: HTTP方法
            success: 是否成功
            duration_ms: 执行时间（毫秒）
            context: 上下文信息
        """
        timestamp = datetime.now()

        log_entry = {
            "timestamp": timestamp.isoformat(),
            "plugin_slug": plugin_slug,
            "action_type": "api_call",
            "api_endpoint": api_endpoint,
            "method": method,
            "success": success,
            "duration_ms": round(duration_ms, 2),
            "context": context or {},
        }

        # 添加到内存日志
        self.audit_logs.append(log_entry)
        if len(self.audit_logs) > self.max_logs:
            self.audit_logs = self.audit_logs[-self.max_logs:]

        # 写入文件日志
        self._write_log_to_file(plugin_slug, log_entry)

        # 检查异常行为
        self._check_anomalies(plugin_slug)

    def log_resource_access(
            self,
            plugin_slug: str,
            resource_type: str,
            resource_id: str,
            action: str,
            success: bool = True,
            context: Optional[Dict[str, Any]] = None
    ):
        """
        记录资源访问
        
        Args:
            plugin_slug: 插件标识
            resource_type: 资源类型（article, user, media等）
            resource_id: 资源ID
            action: 操作类型（read, write, delete）
            success: 是否成功
            context: 上下文信息
        """
        timestamp = datetime.now()

        log_entry = {
            "timestamp": timestamp.isoformat(),
            "plugin_slug": plugin_slug,
            "action_type": "resource_access",
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "success": success,
            "context": context or {},
        }

        # 添加到内存日志
        self.audit_logs.append(log_entry)
        if len(self.audit_logs) > self.max_logs:
            self.audit_logs = self.audit_logs[-self.max_logs:]

        # 写入文件日志
        self._write_log_to_file(plugin_slug, log_entry)

    def get_audit_logs(
            self,
            plugin_slug: Optional[str] = None,
            action_type: Optional[str] = None,
            start_time: Optional[datetime] = None,
            end_time: Optional[datetime] = None,
            limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取审计日志
        
        Args:
            plugin_slug: 插件标识过滤
            action_type: 操作类型过滤
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量限制
            
        Returns:
            审计日志列表
        """
        filtered_logs = self.audit_logs

        # 按插件过滤
        if plugin_slug:
            filtered_logs = [
                log for log in filtered_logs
                if log.get("plugin_slug") == plugin_slug
            ]

        # 按操作类型过滤
        if action_type:
            filtered_logs = [
                log for log in filtered_logs
                if log.get("action_type") == action_type
            ]

        # 按时间范围过滤
        if start_time:
            filtered_logs = [
                log for log in filtered_logs
                if datetime.fromisoformat(log["timestamp"]) >= start_time
            ]

        if end_time:
            filtered_logs = [
                log for log in filtered_logs
                if datetime.fromisoformat(log["timestamp"]) <= end_time
            ]

        # 按时间倒序排列并限制数量
        filtered_logs = sorted(
            filtered_logs,
            key=lambda x: x["timestamp"],
            reverse=True
        )[:limit]

        return filtered_logs

    def get_permission_statistics(
            self,
            plugin_slug: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取权限使用统计
        
        Args:
            plugin_slug: 插件标识（可选）
            
        Returns:
            权限统计数据
        """
        stats = {}

        for key, data in self.permission_stats.items():
            parts = key.split(":", 1)
            if len(parts) != 2:
                continue

            slug, capability = parts

            # 如果指定了插件，只返回该插件的统计
            if plugin_slug and slug != plugin_slug:
                continue

            total = data["granted"] + data["denied"]
            denied_ratio = data["denied"] / total if total > 0 else 0

            if slug not in stats:
                stats[slug] = {
                    "total_checks": 0,
                    "total_granted": 0,
                    "total_denied": 0,
                    "capabilities": {}
                }

            stats[slug]["total_checks"] += total
            stats[slug]["total_granted"] += data["granted"]
            stats[slug]["total_denied"] += data["denied"]
            stats[slug]["capabilities"][capability] = {
                "granted": data["granted"],
                "denied": data["denied"],
                "denied_ratio": round(denied_ratio, 3)
            }

        return stats

    def detect_anomalies(self, plugin_slug: str) -> List[Dict[str, Any]]:
        """
        检测插件的异常行为
        
        Args:
            plugin_slug: 插件标识
            
        Returns:
            异常行为列表
        """
        anomalies = []
        now = datetime.now()

        # 获取最近1分钟的日志
        recent_logs = [
            log for log in self.audit_logs
            if log.get("plugin_slug") == plugin_slug
               and datetime.fromisoformat(log["timestamp"]) >= now - timedelta(minutes=1)
        ]

        # 检查权限检查频率
        permission_checks = [
            log for log in recent_logs
            if log.get("action_type") == "permission_check"
        ]

        if len(permission_checks) > self.thresholds["max_permission_checks_per_minute"]:
            anomalies.append({
                "type": "high_permission_check_frequency",
                "severity": "warning",
                "message": f"插件 '{plugin_slug}' 在1分钟内进行了 {len(permission_checks)} 次权限检查，超过阈值 {self.thresholds['max_permission_checks_per_minute']}",
                "count": len(permission_checks),
                "threshold": self.thresholds["max_permission_checks_per_minute"],
            })

        # 检查权限拒绝率
        denied_checks = [log for log in permission_checks if not log.get("granted", True)]
        if len(permission_checks) > 10:
            denied_ratio = len(denied_checks) / len(permission_checks)
            if denied_ratio > self.thresholds["max_denied_ratio"]:
                anomalies.append({
                    "type": "high_permission_denial_rate",
                    "severity": "critical",
                    "message": f"插件 '{plugin_slug}' 的权限拒绝率为 {denied_ratio:.1%}，超过阈值 {self.thresholds['max_denied_ratio']:.1%}",
                    "denied_ratio": round(denied_ratio, 3),
                    "threshold": self.thresholds["max_denied_ratio"],
                })

        # 检查API调用频率
        api_calls = [
            log for log in recent_logs
            if log.get("action_type") == "api_call"
        ]

        if len(api_calls) > self.thresholds["max_api_calls_per_minute"]:
            anomalies.append({
                "type": "high_api_call_frequency",
                "severity": "warning",
                "message": f"插件 '{plugin_slug}' 在1分钟内调用了 {len(api_calls)} 次API，超过阈值 {self.thresholds['max_api_calls_per_minute']}",
                "count": len(api_calls),
                "threshold": self.thresholds["max_api_calls_per_minute"],
            })

        return anomalies

    def _check_anomalies(self, plugin_slug: str):
        """检查并记录异常行为（内部方法）"""
        anomalies = self.detect_anomalies(plugin_slug)

        for anomaly in anomalies:
            # 记录异常到日志
            anomaly_log = {
                "timestamp": datetime.now().isoformat(),
                "plugin_slug": plugin_slug,
                "action_type": "anomaly_detected",
                "anomaly_type": anomaly["type"],
                "severity": anomaly["severity"],
                "message": anomaly["message"],
            }

            self.audit_logs.append(anomaly_log)
            self._write_log_to_file(plugin_slug, anomaly_log)

            # 打印告警
            print(f"[PLUGIN AUDIT ALERT] {anomaly['message']}")

    def _write_log_to_file(self, plugin_slug: str, log_entry: Dict[str, Any]):
        """
        将日志写入文件
        
        Args:
            plugin_slug: 插件标识
            log_entry: 日志条目
        """
        try:
            # 按日期分文件存储
            date_str = datetime.now().strftime("%Y-%m-%d")
            log_file = self.log_dir / f"{plugin_slug}_{date_str}.jsonl"

            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

        except Exception as e:
            print(f"[Plugin Audit] Failed to write log: {e}")

    def clear_old_logs(self, days: int = 30):
        """
        清理旧日志
        
        Args:
            days: 保留天数
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        for log_file in self.log_dir.glob("*.jsonl"):
            # 从文件名提取日期
            try:
                date_str = log_file.stem.split('_')[-1]
                file_date = datetime.strptime(date_str, "%Y-%m-%d")

                if file_date < cutoff_date:
                    log_file.unlink()
            except Exception:
                continue


# 全局实例
plugin_audit_logger = PluginAuditLogger()
