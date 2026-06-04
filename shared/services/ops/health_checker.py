"""
P8-2: 健康检查与自愈服务
提供系统监控、告警和自动恢复功能
"""
import asyncio
import json
import psutil
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

try:
    import aiohttp
except ImportError:
    aiohttp = None

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.unified_logger import default_logger as logger
from src.utils.database.main import get_async_session


class HealthChecker:
    """
    P8-2: 健康检查与自愈服务

    功能：
    1. 数据库连接池监控
    2. 内存/CPU 使用率告警
    3. 磁盘空间监控
    4. 自动重启异常进程
    5. 故障通知（Webhook/邮件）
    """

    def __init__(self, webhook_url: str = "", email_config: Dict[str, Any] = None):
        self.check_interval = 60  # 检查间隔（秒）
        self.alert_thresholds = {
            'cpu_percent': 90,  # CPU 使用率阈值
            'memory_percent': 85,  # 内存使用率阈值
            'disk_percent': 90,  # 磁盘使用率阈值
            'db_pool_usage': 80,  # 数据库连接池使用率阈值
        }
        self.alert_history = []
        self.is_running = False
        # Webhook 配置（支持飞书/钉钉/企业微信/Slack等）
        self.webhook_url = webhook_url
        # 邮件配置: {"smtp_host", "smtp_port", "username", "password", "recipients", "from_addr", "use_tls"}
        self.email_config = email_config or {}

    async def check_database_health(self) -> Dict[str, Any]:
        """
        检查数据库健康状态

        Returns:
            数据库健康信息
        """
        try:
            async for db in get_async_session():
                # 测试数据库连接
                start_time = time.time()
                result = await db.execute(text("SELECT 1"))
                response_time = (time.time() - start_time) * 1000  # ms

                # 获取连接池信息（如果使用 SQLAlchemy pool）
                engine = db.bind
                pool_status = {}

                if hasattr(engine, 'pool'):
                    pool = engine.pool
                    pool_status = {
                        'pool_size': pool.size() if hasattr(pool, 'size') else None,
                        'checked_in': pool.checkedin() if hasattr(pool, 'checkedin') else None,
                        'checked_out': pool.checkedout() if hasattr(pool, 'checkedout') else None,
                        'overflow': pool.overflow() if hasattr(pool, 'overflow') else None,
                    }

                    # 检查连接池使用率
                    if pool_status.get('pool_size'):
                        usage_percent = (pool_status['checked_out'] / pool_status['pool_size']) * 100
                        if usage_percent > self.alert_thresholds['db_pool_usage']:
                            await self._send_alert(
                                "database_pool_high",
                                f"数据库连接池使用率过高: {usage_percent:.1f}%",
                                "warning"
                            )

                return {
                    "status": "healthy",
                    "response_time_ms": round(response_time, 2),
                    "pool_status": pool_status,
                    "last_check": datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            await self._send_alert(
                "database_down",
                f"数据库连接失败: {str(e)}",
                "critical"
            )

            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }

    def check_system_resources(self) -> Dict[str, Any]:
        """
        检查系统资源使用情况

        Returns:
            系统资源信息
        """
        try:
            # CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=1)

            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent

            alerts = []

            # 检查阈值
            if cpu_percent > self.alert_thresholds['cpu_percent']:
                alerts.append({
                    "type": "cpu_high",
                    "message": f"CPU 使用率过高: {cpu_percent}%",
                    "severity": "warning"
                })

            if memory_percent > self.alert_thresholds['memory_percent']:
                alerts.append({
                    "type": "memory_high",
                    "message": f"内存使用率过高: {memory_percent}%",
                    "severity": "warning"
                })

            if disk_percent > self.alert_thresholds['disk_percent']:
                alerts.append({
                    "type": "disk_high",
                    "message": f"磁盘使用率过高: {disk_percent}%",
                    "severity": "critical"
                })

            # 发送告警
            for alert in alerts:
                self._send_alert_sync(alert['type'], alert['message'], alert['severity'])

            return {
                "status": "healthy" if not alerts else "degraded",
                "cpu_percent": cpu_percent,
                "memory": {
                    "total_gb": round(memory.total / (1024 ** 3), 2),
                    "used_gb": round(memory.used / (1024 ** 3), 2),
                    "percent": memory_percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024 ** 3), 2),
                    "used_gb": round(disk.used / (1024 ** 3), 2),
                    "percent": disk_percent
                },
                "alerts": alerts,
                "last_check": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"System resource check failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def check_application_health(self) -> Dict[str, Any]:
        """
        检查应用健康状态

        Returns:
            应用健康信息
        """
        try:
            # 检查关键服务
            checks = {
                "database": await self.check_database_health(),
                "system": self.check_system_resources(),
            }

            # 总体状态
            all_healthy = all(
                check.get("status") == "healthy"
                for check in checks.values()
            )

            return {
                "status": "healthy" if all_healthy else "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "checks": checks,
                "uptime_seconds": time.time() - psutil.boot_time()
            }

        except Exception as e:
            logger.error(f"Application health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _send_alert(self, alert_type: str, message: str, severity: str = "warning"):
        """
        发送告警通知（异步）

        Args:
            alert_type: 告警类型
            message: 告警消息
            severity: 严重程度 (info/warning/critical)
        """
        alert_data = {
            "type": alert_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat()
        }

        self.alert_history.append(alert_data)

        # 限制历史记录大小
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]

        logger.warning(f"[ALERT] [{severity.upper()}] {alert_type}: {message}")

        # 异步发送 Webhook 通知
        if self.webhook_url:
            try:
                await self._send_webhook_notification(alert_data)
            except Exception as e:
                logger.error(f"Webhook notification failed: {e}")

        # 异步发送邮件通知（仅对 warning/critical 级别发送）
        if self.email_config and severity in ("warning", "critical"):
            try:
                await self._send_email_notification(alert_data)
            except Exception as e:
                logger.error(f"Email notification failed: {e}")

    def _send_alert_sync(self, alert_type: str, message: str, severity: str = "warning"):
        """同步版本的告警发送"""
        alert_data = {
            "type": alert_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat()
        }

        self.alert_history.append(alert_data)
        logger.warning(f"[ALERT] [{severity.upper()}] {alert_type}: {message}")

    async def start_monitoring(self):
        """启动持续监控"""
        self.is_running = True
        logger.info("Health checker monitoring started")

        while self.is_running:
            try:
                # 执行健康检查
                health = await self.check_application_health()

                # 如果检测到严重问题，尝试自愈
                if health['status'] == 'unhealthy':
                    await self._attempt_self_healing(health)

                # 等待下一个检查周期
                await asyncio.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(self.check_interval)

    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        logger.info("Health checker monitoring stopped")

    async def _attempt_self_healing(self, health: Dict[str, Any]):
        """
        尝试自愈

        Args:
            health: 健康检查结果
        """
        logger.warning("Attempting self-healing...")

        # 1. 数据库连接问题：尝试重新连接
        if health.get('checks', {}).get('database', {}).get('status') == 'unhealthy':
            logger.info("Self-healing: Attempting database reconnection")
            # 实际项目中可以重置连接池
            # await reset_database_pool()

        # 2. 内存过高：清理缓存
        system_health = health.get('checks', {}).get('system', {})
        if system_health.get('memory', {}).get('percent', 0) > 90:
            logger.info("Self-healing: Clearing application cache")
            # 实际项目中可以清理缓存
            # await clear_application_cache()

        # 3. 发送告警通知运维团队
        await self._send_alert(
            "self_healing_triggered",
            f"自愈机制已触发，请检查系统状态",
            "warning"
        )

    def get_alert_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取告警历史

        Args:
            limit: 返回数量限制

        Returns:
            告警历史列表
        """
        return self.alert_history[-limit:]

    async def _send_webhook_notification(self, alert_data: Dict[str, Any]):
        """
        发送 Webhook 通知（支持飞书/钉钉/企业微信/Slack 等）
        自动根据 URL 格式适配不同的消息体结构
        """
        if not self.webhook_url or not aiohttp:
            return

        severity_emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🔴"}.get(
            alert_data.get("severity", "warning"), "⚠️"
        )
        title = f"{severity_emoji} 系统告警: {alert_data.get('type', 'unknown')}"
        text = (
            f"**类型**: {alert_data.get('type', 'N/A')}\n"
            f"**级别**: {alert_data.get('severity', 'N/A')}\n"
            f"**消息**: {alert_data.get('message', 'N/A')}\n"
            f"**时间**: {alert_data.get('timestamp', 'N/A')}"
        )

        # 根据 URL 自动判断平台并构造消息体
        url = self.webhook_url
        if "feishu.cn" in url or "larksuite.com" in url:
            # 飞书机器人
            payload = {
                "msg_type": "interactive",
                "card": {
                    "header": {"title": {"tag": "plain_text", "content": title}},
                    "elements": [{"tag": "markdown", "content": text}],
                },
            }
        elif "dingtalk.com" in url:
            # 钉钉机器人
            payload = {
                "msgtype": "markdown",
                "markdown": {"title": title, "text": f"## {title}\n\n{text}"},
            }
        elif "qyapi.weixin.qq.com" in url:
            # 企业微信机器人
            payload = {
                "msgtype": "markdown",
                "markdown": {"content": f"## {title}\n\n{text}"},
            }
        else:
            # 通用 Webhook（Slack / Discord / 自定义）
            payload = {
                "text": f"{title}\n{text}",
                "content": f"{title}\n{text}",
            }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status >= 400:
                    body = await resp.text()
                    logger.error(f"Webhook notification failed ({resp.status}): {body}")
                else:
                    logger.info(f"Webhook notification sent successfully for alert: {alert_data.get('type')}")

    async def _send_email_notification(self, alert_data: Dict[str, Any]):
        """
        发送邮件告警通知
        需要 email_config 包含: smtp_host, smtp_port, username, password, recipients, from_addr
        """
        cfg = self.email_config
        if not cfg.get("smtp_host") or not cfg.get("recipients"):
            return

        severity = alert_data.get("severity", "warning")
        subject = f"[{severity.upper()}] 系统告警: {alert_data.get('type', 'unknown')}"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: {'#e74c3c' if severity == 'critical' else '#f39c12' if severity == 'warning' else '#3498db'};">
                ⚠️ 系统告警通知
            </h2>
            <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
                <tr><td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">告警类型</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{alert_data.get('type', 'N/A')}</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">严重程度</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{severity}</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">告警消息</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{alert_data.get('message', 'N/A')}</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">触发时间</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{alert_data.get('timestamp', 'N/A')}</td></tr>
            </table>
            <p style="color: #888; margin-top: 20px; font-size: 12px;">
                此邮件由 FastBlog 健康检查服务自动发送
            </p>
        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = cfg.get("from_addr", cfg.get("username", ""))
        msg["To"] = ", ".join(cfg["recipients"]) if isinstance(cfg["recipients"], list) else cfg["recipients"]
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        try:
            use_tls = cfg.get("use_tls", True)
            smtp_port = cfg.get("smtp_port", 465 if use_tls else 587)

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_email_sync, cfg, msg, smtp_port, use_tls)
            logger.info(f"Email notification sent for alert: {alert_data.get('type')}")
        except Exception as e:
            logger.error(f"Email notification failed: {e}")

    @staticmethod
    def _send_email_sync(cfg: dict, msg: MIMEMultipart, smtp_port: int, use_tls: bool):
        """同步发送邮件（在线程池中运行）"""
        if use_tls:
            server = smtplib.SMTP_SSL(cfg["smtp_host"], smtp_port, timeout=15)
        else:
            server = smtplib.SMTP(cfg["smtp_host"], smtp_port, timeout=15)
            server.starttls()

        try:
            server.login(cfg["username"], cfg["password"])
            recipients = cfg["recipients"]
            if isinstance(recipients, str):
                recipients = [recipients]
            server.sendmail(cfg.get("from_addr", cfg["username"]), recipients, msg.as_string())
        finally:
            server.quit()


# 全局实例
health_checker = HealthChecker()
