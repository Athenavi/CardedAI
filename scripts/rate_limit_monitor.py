#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 速率限制监控工具

监控和分析 API 请求的速率限制使用情况
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List
from collections import defaultdict


class RateLimitMonitor:
    """速率限制监控器"""

    def __init__(self, log_file: str = "logs/rate_limit.log"):
        """
        初始化监控器
        
        Args:
            log_file: 速率限制日志文件路径
        """
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.stats_file = Path("logs/rate_limit_stats.json")

    def parse_log(self) -> List[dict]:
        """
        解析速率限制日志
        
        Returns:
            日志条目列表
        """
        if not self.log_file.exists():
            print(f"⚠️  日志文件不存在: {self.log_file}")
            return []

        entries = []

        with open(self.log_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue

        return entries

    def analyze_stats(self, entries: List[dict]) -> dict:
        """
        分析统计数据
        
        Args:
            entries: 日志条目列表
            
        Returns:
            统计结果
        """
        stats = {
            "total_requests": len(entries),
            "blocked_requests": 0,
            "allowed_requests": 0,
            "by_endpoint": defaultdict(int),
            "by_ip": defaultdict(int),
            "by_hour": defaultdict(int),
            "top_blocked_ips": defaultdict(int),
            "top_blocked_endpoints": defaultdict(int),
        }

        for entry in entries:
            endpoint = entry.get("endpoint", "unknown")
            ip = entry.get("ip", "unknown")
            timestamp = entry.get("timestamp", "")
            blocked = entry.get("blocked", False)

            # 统计总数
            if blocked:
                stats["blocked_requests"] += 1
                stats["top_blocked_ips"][ip] += 1
                stats["top_blocked_endpoints"][endpoint] += 1
            else:
                stats["allowed_requests"] += 1

            # 按端点统计
            stats["by_endpoint"][endpoint] += 1

            # 按 IP 统计
            stats["by_ip"][ip] += 1

            # 按小时统计
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    hour_key = dt.strftime("%Y-%m-%d %H:00")
                    stats["by_hour"][hour_key] += 1
                except (ValueError, TypeError):
                    pass

        # 转换为普通字典
        stats["by_endpoint"] = dict(stats["by_endpoint"])
        stats["by_ip"] = dict(stats["by_ip"])
        stats["by_hour"] = dict(stats["by_hour"])
        stats["top_blocked_ips"] = dict(
            sorted(stats["top_blocked_ips"].items(), key=lambda x: x[1], reverse=True)[:10]
        )
        stats["top_blocked_endpoints"] = dict(
            sorted(stats["top_blocked_endpoints"].items(), key=lambda x: x[1], reverse=True)[:10]
        )

        return stats

    def show_report(self, stats: dict):
        """
        显示报告
        
        Args:
            stats: 统计结果
        """
        print("=" * 80)
        print("API 速率限制监控报告")
        print("=" * 80)

        # 总体统计
        total = stats["total_requests"]
        blocked = stats["blocked_requests"]
        allowed = stats["allowed_requests"]
        block_rate = (blocked / total * 100) if total > 0 else 0

        print(f"\n📊 总体统计:")
        print(f"   总请求数: {total:,}")
        print(f"   允许请求: {allowed:,} ({100 - block_rate:.2f}%)")
        print(f"   阻止请求: {blocked:,} ({block_rate:.2f}%)")

        # 热门端点
        if stats["by_endpoint"]:
            print(f"\n🔗 热门 API 端点 (Top 10):")
            sorted_endpoints = sorted(stats["by_endpoint"].items(), key=lambda x: x[1], reverse=True)[:10]
            for endpoint, count in sorted_endpoints:
                bar = "█" * min(count // 10, 50)
                print(f"   {endpoint:<40} {count:>6,} {bar}")

        # 被阻止最多的 IP
        if stats["top_blocked_ips"]:
            print(f"\n🚫 被阻止最多的 IP (Top 10):")
            for ip, count in stats["top_blocked_ips"].items():
                bar = "█" * min(count, 50)
                print(f"   {ip:<20} {count:>6,} {bar}")

        # 被阻止最多的端点
        if stats["top_blocked_endpoints"]:
            print(f"\n⚠️  被阻止最多的端点 (Top 10):")
            for endpoint, count in stats["top_blocked_endpoints"].items():
                bar = "█" * min(count, 50)
                print(f"   {endpoint:<40} {count:>6,} {bar}")

        # 时间分布
        if stats["by_hour"]:
            print(f"\n📅 请求时间分布 (最近24小时):")
            sorted_hours = sorted(stats["by_hour"].items())[-24:]
            max_count = max(count for _, count in sorted_hours) if sorted_hours else 1

            for hour, count in sorted_hours:
                bar_length = int((count / max_count) * 50)
                bar = "█" * bar_length
                print(f"   {hour}  {count:>6,} {bar}")

        print("\n" + "=" * 80)

    def save_stats(self, stats: dict):
        """保存统计数据"""
        stats["generated_at"] = datetime.now().isoformat()

        with open(self.stats_file, 'w') as f:
            json.dump(stats, f, indent=2, default=str)

        print(f"✅ 统计数据已保存到: {self.stats_file}")

    def generate_alert(self, stats: dict, threshold: float = 20.0) -> list:
        """
        生成告警
        
        Args:
            stats: 统计结果
            threshold: 阻止率阈值 (%)
            
        Returns:
            告警列表
        """
        alerts = []

        total = stats["total_requests"]
        blocked = stats["blocked_requests"]
        block_rate = (blocked / total * 100) if total > 0 else 0

        # 检查阻止率
        if block_rate > threshold:
            alerts.append({
                "type": "HIGH_BLOCK_RATE",
                "level": "WARNING",
                "message": f"API 阻止率过高: {block_rate:.2f}% (阈值: {threshold}%)",
                "value": block_rate,
                "threshold": threshold
            })

        # 检查异常 IP
        for ip, count in stats["top_blocked_ips"].items():
            if count > 100:
                alerts.append({
                    "type": "SUSPICIOUS_IP",
                    "level": "CRITICAL",
                    "message": f"可疑 IP 大量请求: {ip} ({count} 次被阻止)",
                    "ip": ip,
                    "count": count
                })

        # 检查热点端点
        for endpoint, count in stats["top_blocked_endpoints"].items():
            if count > 50:
                alerts.append({
                    "type": "HOT_ENDPOINT",
                    "level": "WARNING",
                    "message": f"端点被频繁限流: {endpoint} ({count} 次)",
                    "endpoint": endpoint,
                    "count": count
                })

        return alerts

    def watch_realtime(self, interval: int = 5):
        """
        实时监控
        
        Args:
            interval: 刷新间隔（秒）
        """
        print("开始实时监控 API 速率限制...")
        print(f"刷新间隔: {interval} 秒")
        print("按 Ctrl+C 停止\n")

        try:
            while True:
                entries = self.parse_log()

                if entries:
                    stats = self.analyze_stats(entries)
                    self.show_report(stats)

                    # 生成告警
                    alerts = self.generate_alert(stats)
                    if alerts:
                        print(f"\n🚨 发现 {len(alerts)} 个告警:")
                        for alert in alerts:
                            print(f"   [{alert['level']}] {alert['message']}")

                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n监控已停止")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="FastBlog API 速率限制监控工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # report 命令
    report_parser = subparsers.add_parser("report", help="生成报告")
    report_parser.add_argument("--save", action="store_true", help="保存统计数据")

    # watch 命令
    watch_parser = subparsers.add_parser("watch", help="实时监控")
    watch_parser.add_argument("-i", "--interval", type=int, default=5, help="刷新间隔（秒）")

    # alert 命令
    alert_parser = subparsers.add_parser("alert", help="检查告警")
    alert_parser.add_argument("--threshold", type=float, default=20.0, help="阻止率阈值 (%)")

    args = parser.parse_args()

    monitor = RateLimitMonitor()

    if args.command == "report":
        entries = monitor.parse_log()

        if not entries:
            print("没有找到日志数据")
            return

        stats = monitor.analyze_stats(entries)
        monitor.show_report(stats)

        if args.save:
            monitor.save_stats(stats)

    elif args.command == "watch":
        monitor.watch_realtime(args.interval)

    elif args.command == "alert":
        entries = monitor.parse_log()

        if not entries:
            print("没有找到日志数据")
            return

        stats = monitor.analyze_stats(entries)
        alerts = monitor.generate_alert(stats, args.threshold)

        if alerts:
            print(f"🚨 发现 {len(alerts)} 个告警:\n")
            for alert in alerts:
                print(f"[{alert['level']}] {alert['message']}")
        else:
            print("✅ 没有发现告警")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
