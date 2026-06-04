#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统监控工具

监控系统资源使用情况，发送告警通知
"""

import json
import os
import smtplib
import time
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path

import psutil


class SystemMonitor:
    """系统监控器"""

    def __init__(self, config_file: str = "config/monitor.json"):
        """
        初始化监控器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = Path(config_file)
        self.config = self.load_config()
        self.alert_log = Path("logs/alerts.log")
        self.alert_log.parent.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> dict:
        """加载配置文件"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)

        # 默认配置
        return {
            "thresholds": {
                "cpu_percent": 80,
                "memory_percent": 85,
                "disk_percent": 90,
                "load_average": 4.0
            },
            "alert_channels": {
                "email": {
                    "enabled": False,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "from_addr": "",
                    "to_addrs": []
                },
                "webhook": {
                    "enabled": False,
                    "url": "",
                    "method": "POST"
                }
            },
            "check_interval": 60,
            "cooldown_period": 300
        }

    def save_config(self):
        """保存配置文件"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def get_system_metrics(self) -> dict:
        """
        获取系统指标
        
        Returns:
            系统指标字典
        """
        # CPU 使用率
        cpu_percent = psutil.cpu_percent(interval=1)

        # 内存使用
        memory = psutil.virtual_memory()

        # 磁盘使用
        disk = psutil.disk_usage('/')

        # 负载平均值（仅 Linux/Mac）
        try:
            load_avg = os.getloadavg()
        except (AttributeError, OSError):
            load_avg = (0, 0, 0)

        # 网络统计
        net_io = psutil.net_io_counters()

        return {
            "timestamp": datetime.now().isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "cores": psutil.cpu_count()
            },
            "memory": {
                "total": memory.total,
                "used": memory.used,
                "available": memory.available,
                "percent": memory.percent
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            },
            "load_average": {
                "1min": load_avg[0],
                "5min": load_avg[1],
                "15min": load_avg[2]
            },
            "network": {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            }
        }

    def check_thresholds(self, metrics: dict) -> list:
        """
        检查是否超过阈值
        
        Args:
            metrics: 系统指标
            
        Returns:
            告警列表
        """
        alerts = []
        thresholds = self.config["thresholds"]

        # CPU 检查
        if metrics["cpu"]["percent"] > thresholds["cpu_percent"]:
            alerts.append({
                "type": "CPU",
                "level": "WARNING",
                "message": f"CPU 使用率过高: {metrics['cpu']['percent']}%",
                "value": metrics["cpu"]["percent"],
                "threshold": thresholds["cpu_percent"]
            })

        # 内存检查
        if metrics["memory"]["percent"] > thresholds["memory_percent"]:
            alerts.append({
                "type": "MEMORY",
                "level": "WARNING",
                "message": f"内存使用率过高: {metrics['memory']['percent']}%",
                "value": metrics["memory"]["percent"],
                "threshold": thresholds["memory_percent"]
            })

        # 磁盘检查
        if metrics["disk"]["percent"] > thresholds["disk_percent"]:
            alerts.append({
                "type": "DISK",
                "level": "CRITICAL",
                "message": f"磁盘使用率过高: {metrics['disk']['percent']}%",
                "value": metrics["disk"]["percent"],
                "threshold": thresholds["disk_percent"]
            })

        # 负载检查
        if metrics["load_average"]["1min"] > thresholds["load_average"]:
            alerts.append({
                "type": "LOAD",
                "level": "WARNING",
                "message": f"系统负载过高: {metrics['load_average']['1min']}",
                "value": metrics["load_average"]["1min"],
                "threshold": thresholds["load_average"]
            })

        return alerts

    def send_alert(self, alert: dict):
        """
        发送告警
        
        Args:
            alert: 告警信息
        """
        # 记录告警日志
        log_entry = f"[{datetime.now().isoformat()}] [{alert['level']}] {alert['message']}\n"
        with open(self.alert_log, 'a') as f:
            f.write(log_entry)

        print(f"🚨 告警: {alert['message']}")

        # 发送邮件告警
        if self.config["alert_channels"]["email"]["enabled"]:
            self.send_email_alert(alert)

        # 发送 Webhook 告警
        if self.config["alert_channels"]["webhook"]["enabled"]:
            self.send_webhook_alert(alert)

    def send_email_alert(self, alert: dict):
        """发送邮件告警"""
        try:
            email_config = self.config["alert_channels"]["email"]

            subject = f"[FastBlog Alert] {alert['level']}: {alert['type']}"
            body = f"""
告警类型: {alert['type']}
告警级别: {alert['level']}
告警信息: {alert['message']}
当前值: {alert['value']}
阈值: {alert['threshold']}
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()

            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = email_config["from_addr"]
            msg['To'] = ", ".join(email_config["to_addrs"])

            server = smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"])
            server.starttls()
            server.login(email_config["username"], email_config["password"])
            server.sendmail(email_config["from_addr"], email_config["to_addrs"], msg.as_string())
            server.quit()

            print("✅ 邮件告警已发送")

        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")

    def send_webhook_alert(self, alert: dict):
        """发送 Webhook 告警"""
        try:
            import requests

            webhook_config = self.config["alert_channels"]["webhook"]

            payload = {
                "text": f"🚨 FastBlog 告警\n"
                        f"类型: {alert['type']}\n"
                        f"级别: {alert['level']}\n"
                        f"信息: {alert['message']}\n"
                        f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }

            response = requests.post(
                webhook_config["url"],
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                print("✅ Webhook 告警已发送")
            else:
                print(f"❌ Webhook 发送失败: {response.status_code}")

        except ImportError:
            print("⚠️  需要安装 requests: pip install requests")
        except Exception as e:
            print(f"❌ Webhook 发送失败: {e}")

    def show_status(self):
        """显示系统状态"""
        metrics = self.get_system_metrics()

        print("=" * 70)
        print("系统监控状态")
        print("=" * 70)

        # CPU
        cpu_color = "🟢" if metrics["cpu"]["percent"] < 70 else "🟡" if metrics["cpu"]["percent"] < 90 else "🔴"
        print(f"\n{cpu_color} CPU 使用率: {metrics['cpu']['percent']}%")
        print(f"   核心数: {metrics['cpu']['cores']}")

        # 内存
        mem_color = "🟢" if metrics["memory"]["percent"] < 70 else "🟡" if metrics["memory"]["percent"] < 90 else "🔴"
        mem_used_gb = metrics["memory"]["used"] / (1024 ** 3)
        mem_total_gb = metrics["memory"]["total"] / (1024 ** 3)
        print(f"\n{mem_color} 内存使用: {metrics['memory']['percent']}%")
        print(f"   已用: {mem_used_gb:.2f} GB / {mem_total_gb:.2f} GB")

        # 磁盘
        disk_color = "🟢" if metrics["disk"]["percent"] < 70 else "🟡" if metrics["disk"]["percent"] < 90 else "🔴"
        disk_used_gb = metrics["disk"]["used"] / (1024 ** 3)
        disk_total_gb = metrics["disk"]["total"] / (1024 ** 3)
        print(f"\n{disk_color} 磁盘使用: {metrics['disk']['percent']}%")
        print(f"   已用: {disk_used_gb:.2f} GB / {disk_total_gb:.2f} GB")

        # 负载
        load_color = "🟢" if metrics["load_average"]["1min"] < 2 else "🟡" if metrics["load_average"][
                                                                                "1min"] < 4 else "🔴"
        print(f"\n{load_color} 系统负载:")
        print(f"   1分钟: {metrics['load_average']['1min']:.2f}")
        print(f"   5分钟: {metrics['load_average']['5min']:.2f}")
        print(f"   15分钟: {metrics['load_average']['15min']:.2f}")

        # 网络
        net_sent_mb = metrics["network"]["bytes_sent"] / (1024 ** 2)
        net_recv_mb = metrics["network"]["bytes_recv"] / (1024 ** 2)
        print(f"\n📡 网络流量:")
        print(f"   发送: {net_sent_mb:.2f} MB")
        print(f"   接收: {net_recv_mb:.2f} MB")

        print("\n" + "=" * 70)

    def monitor_loop(self):
        """持续监控循环"""
        print("开始监控系统...")
        print(f"检查间隔: {self.config['check_interval']} 秒")
        print("按 Ctrl+C 停止\n")

        last_alert_time = {}

        try:
            while True:
                metrics = self.get_system_metrics()
                alerts = self.check_thresholds(metrics)

                for alert in alerts:
                    alert_key = alert["type"]
                    now = time.time()

                    # 冷却期检查
                    if alert_key in last_alert_time:
                        if now - last_alert_time[alert_key] < self.config["cooldown_period"]:
                            continue

                    # 发送告警
                    self.send_alert(alert)
                    last_alert_time[alert_key] = now

                time.sleep(self.config["check_interval"])

        except KeyboardInterrupt:
            print("\n\n监控已停止")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="FastBlog 系统监控工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # status 命令
    subparsers.add_parser("status", help="显示系统状态")

    # watch 命令
    watch_parser = subparsers.add_parser("watch", help="持续监控")
    watch_parser.add_argument("-i", "--interval", type=int, help="检查间隔（秒）")

    # config 命令
    config_parser = subparsers.add_parser("config", help="配置监控")
    config_parser.add_argument("--cpu-threshold", type=int, help="CPU 阈值")
    config_parser.add_argument("--memory-threshold", type=int, help="内存阈值")
    config_parser.add_argument("--disk-threshold", type=int, help="磁盘阈值")

    args = parser.parse_args()

    monitor = SystemMonitor()

    if args.command == "status":
        monitor.show_status()

    elif args.command == "watch":
        if args.interval:
            monitor.config["check_interval"] = args.interval
        monitor.monitor_loop()

    elif args.command == "config":
        if args.cpu_threshold:
            monitor.config["thresholds"]["cpu_percent"] = args.cpu_threshold
        if args.memory_threshold:
            monitor.config["thresholds"]["memory_percent"] = args.memory_threshold
        if args.disk_threshold:
            monitor.config["thresholds"]["disk_percent"] = args.disk_threshold

        monitor.save_config()
        print("✅ 配置已保存")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
