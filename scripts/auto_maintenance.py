#!/usr/bin/env python3
"""
FastBlog 企业版自动化运维脚本
提供系统监控、健康检查、自动修复等功能
"""
import os
import sys
import json
import time
import psutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional


class SystemMonitor:
    """系统监控器"""

    def __init__(self):
        self.metrics = {}

    def check_cpu_usage(self) -> float:
        """检查CPU使用率"""
        return psutil.cpu_percent(interval=1)

    def check_memory_usage(self) -> Dict[str, Any]:
        """检查内存使用情况"""
        memory = psutil.virtual_memory()
        return {
            'total': memory.total,
            'available': memory.available,
            'used': memory.used,
            'percent': memory.percent
        }

    def check_disk_usage(self, path: str = '/') -> Dict[str, Any]:
        """检查磁盘使用情况"""
        disk = psutil.disk_usage(path)
        return {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': disk.percent
        }

    def check_process_status(self, process_name: str) -> bool:
        """检查进程状态"""
        for proc in psutil.process_iter(['name']):
            if process_name in proc.info['name']:
                return True
        return False

    def check_port_status(self, port: int) -> bool:
        """检查端口状态"""
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == 'LISTEN':
                return True
        return False

    def collect_all_metrics(self) -> Dict[str, Any]:
        """收集所有指标"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'cpu': {
                'usage_percent': self.check_cpu_usage()
            },
            'memory': self.check_memory_usage(),
            'disk': self.check_disk_usage('/'),
            'processes': {
                'nginx': self.check_process_status('nginx'),
                'postgres': self.check_process_status('postgres'),
                'redis': self.check_process_status('redis'),
                'python': self.check_process_status('python')
            },
            'ports': {
                '80': self.check_port_status(80),
                '443': self.check_port_status(443),
                '5432': self.check_port_status(5432),
                '6379': self.check_port_status(6379),
                '8000': self.check_port_status(8000)
            }
        }

        self.metrics = metrics
        return metrics


class HealthChecker:
    """健康检查器"""

    def __init__(self):
        self.monitor = SystemMonitor()

    def check_application_health(self) -> Dict[str, Any]:
        """检查应用健康状态"""
        health = {
            'status': 'healthy',
            'checks': {},
            'timestamp': datetime.now().isoformat()
        }

        # 检查进程
        if not self.monitor.check_process_status('python'):
            health['status'] = 'unhealthy'
            health['checks']['process'] = 'failed'
        else:
            health['checks']['process'] = 'ok'

        # 检查端口
        if not self.monitor.check_port_status(8000):
            health['status'] = 'unhealthy'
            health['checks']['port'] = 'failed'
        else:
            health['checks']['port'] = 'ok'

        # 检查数据库连接
        try:
            import subprocess
            result = subprocess.run(
                ['pg_isready', '-h', 'localhost', '-U', 'fastblog'],
                capture_output=True,
                timeout=5
            )
            health['checks']['database'] = 'ok' if result.returncode == 0 else 'failed'
        except Exception as e:
            health['status'] = 'unhealthy'
            health['checks']['database'] = f'failed: {str(e)}'

        # 检查Redis连接
        try:
            import subprocess
            result = subprocess.run(
                ['redis-cli', 'ping'],
                capture_output=True,
                timeout=5
            )
            health['checks']['redis'] = 'ok' if result.returncode == 0 else 'failed'
        except Exception as e:
            health['status'] = 'unhealthy'
            health['checks']['redis'] = f'failed: {str(e)}'

        return health

    def check_system_resources(self) -> Dict[str, Any]:
        """检查系统资源"""
        metrics = self.monitor.collect_all_metrics()

        status = 'healthy'
        warnings = []

        # CPU检查
        if metrics['cpu']['usage_percent'] > 90:
            status = 'critical'
            warnings.append(f"CPU使用率过高: {metrics['cpu']['usage_percent']}%")
        elif metrics['cpu']['usage_percent'] > 70:
            warnings.append(f"CPU使用率较高: {metrics['cpu']['usage_percent']}%")

        # 内存检查
        if metrics['memory']['percent'] > 90:
            status = 'critical'
            warnings.append(f"内存使用率过高: {metrics['memory']['percent']}%")
        elif metrics['memory']['percent'] > 70:
            warnings.append(f"内存使用率较高: {metrics['memory']['percent']}%")

        # 磁盘检查
        if metrics['disk']['percent'] > 90:
            status = 'critical'
            warnings.append(f"磁盘使用率过高: {metrics['disk']['percent']}%")
        elif metrics['disk']['percent'] > 70:
            warnings.append(f"磁盘使用率较高: {metrics['disk']['percent']}%")

        return {
            'status': status,
            'warnings': warnings,
            'metrics': metrics
        }


class AutoHealer:
    """自动修复器"""

    def __init__(self):
        self.health_checker = HealthChecker()

    def restart_service(self, service_name: str) -> bool:
        """重启服务"""
        try:
            subprocess.run(['sudo', 'systemctl', 'restart', service_name],
                           check=True, timeout=30)
            print(f"✓ 服务 {service_name} 已重启")
            return True
        except Exception as e:
            print(f"✗ 重启服务 {service_name} 失败: {e}")
            return False

    def heal_application(self) -> bool:
        """修复应用问题"""
        health = self.health_checker.check_application_health()

        if health['status'] == 'healthy':
            print("✓ 应用健康，无需修复")
            return True

        print("检测到应用问题，尝试自动修复...")

        # 尝试重启应用
        if health['checks'].get('process') == 'failed':
            print("应用进程未运行，尝试启动...")
            return self.restart_service('fastblog')

        if health['checks'].get('port') == 'failed':
            print("应用端口未监听，尝试重启...")
            return self.restart_service('fastblog')

        return False

    def cleanup_old_files(self, days: int = 7) -> int:
        """清理旧文件"""
        backup_dir = Path('/opt/fastblog/backups')
        if not backup_dir.exists():
            return 0

        cleaned_count = 0
        cutoff_date = datetime.now() - timedelta(days=days)

        for file_path in backup_dir.glob('*'):
            if file_path.is_file():
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mtime < cutoff_date:
                    file_path.unlink()
                    cleaned_count += 1
                    print(f"已删除: {file_path.name}")

        print(f"✓ 清理了 {cleaned_count} 个旧文件")
        return cleaned_count

    def optimize_database(self) -> bool:
        """优化数据库"""
        try:
            # VACUUM ANALYZE
            subprocess.run([
                'sudo', '-u', 'postgres', 'psql', '-d', 'fastblog',
                '-c', 'VACUUM ANALYZE;'
            ], check=True, timeout=300)

            print("✓ 数据库优化完成")
            return True
        except Exception as e:
            print(f"✗ 数据库优化失败: {e}")
            return False


class MaintenanceManager:
    """维护管理器"""

    def __init__(self):
        self.auto_healer = AutoHealer()
        self.health_checker = HealthChecker()

    def daily_maintenance(self):
        """执行日常维护"""
        print("=" * 60)
        print("开始日常维护")
        print("=" * 60)

        # 1. 健康检查
        print("\n[1/4] 执行健康检查...")
        health = self.health_checker.check_application_health()
        print(f"应用状态: {health['status']}")

        # 2. 自动修复
        print("\n[2/4] 检查并修复问题...")
        if health['status'] != 'healthy':
            self.auto_healer.heal_application()

        # 3. 清理旧文件
        print("\n[3/4] 清理旧备份文件...")
        self.auto_healer.cleanup_old_files(days=7)

        # 4. 数据库优化
        print("\n[4/4] 优化数据库...")
        self.auto_healer.optimize_database()

        print("\n" + "=" * 60)
        print("日常维护完成")
        print("=" * 60)

    def generate_report(self) -> Dict[str, Any]:
        """生成维护报告"""
        health = self.health_checker.check_application_health()
        resources = self.health_checker.check_system_resources()
        metrics = self.health_checker.monitor.collect_all_metrics()

        report = {
            'timestamp': datetime.now().isoformat(),
            'application_health': health,
            'system_resources': resources,
            'metrics': metrics
        }

        return report


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='FastBlog 企业版自动化运维工具')
    parser.add_argument('command', choices=['health', 'maintain', 'report', 'cleanup'],
                        help='执行的命令')
    parser.add_argument('--days', type=int, default=7,
                        help='清理天数（用于cleanup命令）')

    args = parser.parse_args()

    manager = MaintenanceManager()

    if args.command == 'health':
        print("执行健康检查...")
        health = manager.health_checker.check_application_health()
        print(json.dumps(health, indent=2))

    elif args.command == 'maintain':
        manager.daily_maintenance()

    elif args.command == 'report':
        print("生成维护报告...")
        report = manager.generate_report()
        print(json.dumps(report, indent=2))

    elif args.command == 'cleanup':
        print(f"清理 {args.days} 天前的文件...")
        count = manager.auto_healer.cleanup_old_files(days=args.days)
        print(f"清理完成，共删除 {count} 个文件")


if __name__ == '__main__':
    main()
