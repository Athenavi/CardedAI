"""
插件行为审计系统

记录插件的所有关键操作，用于安全审计和异常检测
"""

import json
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List


class AuditActionType(str, Enum):
    """审计动作类型"""
    # 数据访问
    DATA_READ = "data_read"
    DATA_WRITE = "data_write"
    DATA_DELETE = "data_delete"

    # 文件系统
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"

    # 网络请求
    NETWORK_REQUEST = "network_request"

    # 邮件发送
    EMAIL_SEND = "email_send"

    # 数据库操作
    DB_QUERY = "db_query"
    DB_EXECUTE = "db_execute"

    # 权限相关
    PERMISSION_CHECK = "permission_check"
    PERMISSION_DENIED = "permission_denied"

    # 插件生命周期
    PLUGIN_ACTIVATE = "plugin_activate"
    PLUGIN_DEACTIVATE = "plugin_deactivate"
    PLUGIN_INSTALL = "plugin_install"
    PLUGIN_UNINSTALL = "plugin_uninstall"

    # 其他
    CONFIG_CHANGE = "config_change"
    CUSTOM = "custom"


class AuditStatus(str, Enum):
    """审计状态"""
    SUCCESS = "success"
    FAILURE = "failure"
    DENIED = "denied"
    WARNING = "warning"


class AuditLogger:
    """
    插件行为审计日志器
    
    记录插件的所有关键操作，支持多种存储后端
    """

    def __init__(self, storage_backend: str = "file", log_dir: str = "logs/plugin_audit"):
        """
        初始化审计日志器
        
        Args:
            storage_backend: 存储后端类型 (file, database)
            log_dir: 日志文件目录（当使用 file 后端时）
        """
        print(f"[AuditLogger] Initialized with {storage_backend} backend")

    def log(
            self,
            plugin_slug: str,
            action_type: AuditActionType,
            resource: str,
            status: AuditStatus = AuditStatus.SUCCESS,
            details: Optional[Dict[str, Any]] = None,
            severity: str = "info"
    ):
        """
        记录审计日志
        
        Args:
            plugin_slug: 插件标识
            action_type: 动作类型
            resource: 操作的资源
            status: 操作状态
            details: 详细信息
            severity: 严重级别 (info, warning, error, critical)
        """
        timestamp = datetime.now().isoformat()

        log_entry = {
            "timestamp": timestamp,
            "plugin_slug": plugin_slug,
            "action_type": action_type.value if isinstance(action_type, AuditActionType) else action_type,
            "resource": resource,
            "status": status.value if isinstance(status, AuditStatus) else status,
            "details": details or {},
            "severity": severity
        }

        # 根据严重级别选择日志方法
        log_method = getattr(self.logger, severity, self.logger.info)
        log_method(json.dumps(log_entry, ensure_ascii=False))

        # 如果是 denied 或 failure，额外输出到控制台
        if status in [AuditStatus.DENIED, AuditStatus.FAILURE]:
            print(f"[AUDIT ALERT] {plugin_slug}: {action_type} on {resource} - {status}")

        return log_entry

    def log_permission_check(self, plugin_slug: str, capability: str, granted: bool):
        """记录权限检查"""
        status = AuditStatus.SUCCESS if granted else AuditStatus.DENIED
        severity = "warning" if not granted else "info"

        return self.log(
            plugin_slug=plugin_slug,
            action_type=AuditActionType.PERMISSION_CHECK,
            resource=capability,
            status=status,
            details={"granted": granted},
            severity=severity
        )

    def log_data_access(self, plugin_slug: str, operation: str, resource: str, success: bool = True):
        """记录数据访问"""
        action_map = {
            "read": AuditActionType.DATA_READ,
            "write": AuditActionType.DATA_WRITE,
            "delete": AuditActionType.DATA_DELETE
        }

        action_type = action_map.get(operation, AuditActionType.CUSTOM)
        status = AuditStatus.SUCCESS if success else AuditStatus.FAILURE

        return self.log(
            plugin_slug=plugin_slug,
            action_type=action_type,
            resource=resource,
            status=status
        )

    def log_file_access(self, plugin_slug: str, operation: str, filepath: str, success: bool = True):
        """记录文件访问"""
        action_map = {
            "read": AuditActionType.FILE_READ,
            "write": AuditActionType.FILE_WRITE,
            "delete": AuditActionType.FILE_DELETE
        }

        action_type = action_map.get(operation, AuditActionType.CUSTOM)
        status = AuditStatus.SUCCESS if success else AuditStatus.FAILURE

        return self.log(
            plugin_slug=plugin_slug,
            action_type=action_type,
            resource=filepath,
            status=status,
            details={"filepath": filepath}
        )

    def log_network_request(self, plugin_slug: str, url: str, method: str = "GET", success: bool = True):
        """记录网络请求"""
        status = AuditStatus.SUCCESS if success else AuditStatus.FAILURE

        return self.log(
            plugin_slug=plugin_slug,
            action_type=AuditActionType.NETWORK_REQUEST,
            resource=url,
            status=status,
            details={"url": url, "method": method}
        )

    def get_logs(
            self,
            plugin_slug: Optional[str] = None,
            action_type: Optional[str] = None,
            start_time: Optional[str] = None,
            end_time: Optional[str] = None,
            limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        查询审计日志
        
        Args:
            plugin_slug: 插件标识过滤
            action_type: 动作类型过滤
            start_time: 开始时间 (ISO format)
            end_time: 结束时间 (ISO format)
            limit: 返回数量限制
            
        Returns:
            日志条目列表
        """
        logs = []

        # 读取最近的日志文件
        log_files = sorted(self.log_dir.glob("audit_*.log"), reverse=True)

        for log_file in log_files[:7]:  # 最近7天
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if not line.strip():
                            continue

                        try:
                            # 解析日志行（跳过前面的时间戳和级别信息）
                            parts = line.split(' - ', 3)
                            if len(parts) >= 4:
                                log_json = parts[3].strip()
                                log_entry = json.loads(log_json)

                                # 应用过滤器
                                if plugin_slug and log_entry.get('plugin_slug') != plugin_slug:
                                    continue
                                if action_type and log_entry.get('action_type') != action_type:
                                    continue

                                logs.append(log_entry)

                                if len(logs) >= limit:
                                    return logs
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                print(f"[AuditLogger] Error reading {log_file}: {e}")

        return logs

    def generate_report(self, plugin_slug: str, days: int = 7) -> Dict[str, Any]:
        """
        生成插件审计报告
        
        Args:
            plugin_slug: 插件标识
            days: 报告天数
            
        Returns:
            审计报告
        """
        logs = self.get_logs(plugin_slug=plugin_slug, limit=10000)

        # 统计分析
        total_actions = len(logs)
        denied_count = sum(1 for log in logs if log.get('status') == 'denied')
        failure_count = sum(1 for log in logs if log.get('status') == 'failure')

        # 按动作类型统计
        action_stats = {}
        for log in logs:
            action = log.get('action_type', 'unknown')
            action_stats[action] = action_stats.get(action, 0) + 1

        # 按严重级别统计
        severity_stats = {}
        for log in logs:
            severity = log.get('severity', 'info')
            severity_stats[severity] = severity_stats.get(severity, 0) + 1

        report = {
            "plugin_slug": plugin_slug,
            "period_days": days,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_actions": total_actions,
                "denied_count": denied_count,
                "failure_count": failure_count,
                "success_rate": ((
                                         total_actions - denied_count - failure_count) / total_actions * 100) if total_actions > 0 else 100
            },
            "action_statistics": action_stats,
            "severity_statistics": severity_stats,
            "risk_level": self._calculate_risk_level(denied_count, failure_count, total_actions)
        }

        return report

    def _calculate_risk_level(self, denied: int, failures: int, total: int) -> str:
        """计算风险级别"""
        if total == 0:
            return "low"

        risk_ratio = (denied + failures) / total

        if risk_ratio > 0.1 or denied > 100:
            return "high"
        elif risk_ratio > 0.05 or denied > 50:
            return "medium"
        else:
            return "low"


# 全局审计日志器实例
audit_logger = AuditLogger()


def audit_action(
        action_type: AuditActionType,
        resource: str,
        details: Optional[Dict[str, Any]] = None
):
    """
    装饰器：自动审计插件操作
    
    用法:
        @audit_action(AuditActionType.DATA_READ, "articles")
        def read_articles(self):
            ...
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            # 尝试从第一个参数获取插件实例
            plugin_slug = "unknown"
            if args and hasattr(args[0], 'slug'):
                plugin_slug = args[0].slug

            try:
                result = func(*args, **kwargs)
                audit_logger.log(
                    plugin_slug=plugin_slug,
                    action_type=action_type,
                    resource=resource,
                    status=AuditStatus.SUCCESS,
                    details=details
                )
                return result
            except Exception as e:
                audit_logger.log(
                    plugin_slug=plugin_slug,
                    action_type=action_type,
                    resource=resource,
                    status=AuditStatus.FAILURE,
                    details={"error": str(e), **(details or {})}
                )
                raise

        return wrapper

    return decorator
