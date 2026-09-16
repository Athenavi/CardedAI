"""
通知推送节点执行器

支持多种通知渠道：email / webhook / log。
复用 notification_service 的邮件发送能力。
"""

from typing import Any, Dict, List

from src.unified_logger import default_logger as logger
from shared.services.workflow.node_executors.base import BaseNodeExecutor


class NotifyNodeExecutor(BaseNodeExecutor):
    """通知推送节点"""

    @property
    def node_type(self) -> str:
        return "notify"

    async def execute(self, node: Dict, inputs: Dict) -> Dict:
        """
        发送通知

        config 参数:
            channels: List[str] - 通知渠道列表 ("email" / "webhook" / "log")
            message_template: str - 消息模板，支持 {key} 占位符
            subject: str - 邮件主题（email 渠道用）
            recipients: List[str] - 收件人列表（email 渠道用）
            webhook_url: str - Webhook URL（webhook 渠道用）
        """
        config = node.get("config", {})
        channels: List[str] = config.get("channels", ["log"])
        message_template = config.get("message_template", "")
        subject = config.get("subject", "Workflow Notification")

        # 渲染消息
        message = self._render_template(message_template, inputs)
        if not message:
            # 回退：使用 inputs 的摘要
            message = str(inputs)[:500]

        results = {}
        for channel in channels:
            try:
                if channel == "email":
                    await self._send_email(config, subject, message)
                    results["email"] = "sent"
                elif channel == "webhook":
                    await self._send_webhook(config, message)
                    results["webhook"] = "sent"
                elif channel == "log":
                    logger.info(f"[NotifyNode] 消息: {message[:200]}")
                    results["log"] = "sent"
                else:
                    results[channel] = f"unknown channel: {channel}"
            except Exception as exc:
                logger.error(f"[NotifyNode] 通知发送失败 ({channel}): {exc}")
                results[channel] = f"error: {exc}"

        return {
            "success": all(v == "sent" for v in results.values()),
            "sent_to": results,
            "message": message[:200],
        }

    @staticmethod
    async def _send_email(config: Dict, subject: str, message: str) -> None:
        """发送邮件通知"""
        from shared.services.notifications.email_service import email_service

        recipients = config.get("recipients", [])
        if not recipients:
            raise ValueError("email 渠道需要配置 recipients")

        for recipient in recipients:
            await email_service.send_email(
                to=recipient,
                subject=subject,
                body=message,
            )

    @staticmethod
    async def _send_webhook(config: Dict, message: str) -> None:
        """发送 Webhook 通知"""
        import json
        try:
            import httpx
        except ImportError:
            raise ImportError("Webhook 通知需要 httpx: pip install httpx")

        webhook_url = config.get("webhook_url")
        if not webhook_url:
            raise ValueError("webhook 渠道需要配置 webhook_url")

        payload = {
            "text": message,
            "content": message,
        }

        # 允许自定义 payload 格式
        custom_payload = config.get("payload_template")
        if custom_payload:
            try:
                payload = json.loads(custom_payload)
                # 替换 {message} 占位符
                for k, v in payload.items():
                    if isinstance(v, str) and "{message}" in v:
                        payload[k] = v.replace("{message}", message)
            except json.JSONDecodeError:
                pass

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(webhook_url, json=payload)
            resp.raise_for_status()

    @staticmethod
    def _render_template(template: str, inputs: Dict) -> str:
        """渲染模板"""
        import json

        result = template
        for key, value in inputs.items():
            placeholder = "{" + key + "}"
            if placeholder in result:
                if isinstance(value, (dict, list)):
                    result = result.replace(placeholder, json.dumps(value, ensure_ascii=False))
                else:
                    result = result.replace(placeholder, str(value))
        return result
