"""
预警引擎

评估情报是否触发预警规则，并分发预警通知。
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, and_

logger = logging.getLogger(__name__)


class AlertEvent:
    """预警事件数据类"""

    def __init__(
        self,
        rule_id: int,
        rule_name: str,
        intelligence_id: int,
        severity: str,
        message: str,
        matched_keywords: List[str] = None,
        actions: List[Dict] = None,
    ):
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.intelligence_id = intelligence_id
        self.severity = severity
        self.message = message
        self.matched_keywords = matched_keywords or []
        self.actions = actions or []
        self.triggered_at = datetime.now(timezone.utc)


class AlertEngine:
    """
    预警引擎

    功能：
    1. 评估情报是否匹配预警规则（关键词、条件）
    2. 生成预警事件
    3. 分发预警到各渠道（邮件、Webhook 等）
    """

    def __init__(self):
        self._action_handlers = {
            "email": self._send_email_alert,
            "webhook": self._send_webhook_alert,
            "log": self._log_alert,
        }

    async def evaluate(self, intelligence_id: int, title: str, summary: str, category: str = "",
                       sentiment: str = "", importance_score: float = 0.0) -> List[AlertEvent]:
        """
        评估单条情报是否触发预警规则。

        Args:
            intelligence_id: 情报 ID
            title: 情报标题
            summary: 情报摘要
            category: 情报分类
            sentiment: 情感倾向
            importance_score: 重要性评分

        Returns:
            List[AlertEvent]: 触发的预警事件列表
        """
        from shared.models import AlertRule
        from src.extensions import get_db

        events: List[AlertEvent] = []

        with get_db() as db:
            rules = db.execute(
                select(AlertRule).where(AlertRule.is_active == True)
            ).scalars().all()

            for rule in rules:
                event = self._evaluate_rule(
                    rule=rule,
                    intelligence_id=intelligence_id,
                    title=title,
                    summary=summary,
                    category=category,
                    sentiment=sentiment,
                    importance_score=importance_score,
                )
                if event:
                    events.append(event)

                    # 更新规则的最后触发时间
                    try:
                        rule.last_triggered_at = datetime.now(timezone.utc)
                    except Exception:
                        pass

            db.commit()

        return events

    def _evaluate_rule(
        self,
        rule: Any,
        intelligence_id: int,
        title: str,
        summary: str,
        category: str,
        sentiment: str,
        importance_score: float,
    ) -> Optional[AlertEvent]:
        """评估单条规则"""
        matched_keywords: List[str] = []

        # 1. 关键词匹配
        keywords = []
        if rule.keywords:
            try:
                keywords = json.loads(rule.keywords) if isinstance(rule.keywords, str) else rule.keywords
            except (json.JSONDecodeError, TypeError):
                pass

        text = f"{title} {summary}".lower()

        if keywords:
            keyword_matched = False
            for kw in keywords:
                if kw.lower() in text:
                    matched_keywords.append(kw)
                    keyword_matched = True

            if not keyword_matched:
                return None

        # 2. 条件匹配
        conditions = {}
        if rule.conditions:
            try:
                conditions = json.loads(rule.conditions) if isinstance(rule.conditions, str) else rule.conditions
            except (json.JSONDecodeError, TypeError):
                pass

        if conditions:
            # 分类条件
            if "category" in conditions and conditions["category"] != category:
                return None

            # 情感条件
            if "sentiment" in conditions and conditions["sentiment"] != sentiment:
                return None

            # 最低重要性评分
            if "min_importance" in conditions:
                min_imp = float(conditions["min_importance"])
                if importance_score < min_imp:
                    return None

        # 3. 触发 — 构建预警事件
        actions = []
        if rule.actions:
            try:
                actions = json.loads(rule.actions) if isinstance(rule.actions, str) else rule.actions
            except (json.JSONDecodeError, TypeError):
                pass

        message = f"预警规则 [{rule.name}] 被触发"
        if matched_keywords:
            message += f"，匹配关键词: {', '.join(matched_keywords)}"

        return AlertEvent(
            rule_id=rule.id,
            rule_name=rule.name or "",
            intelligence_id=intelligence_id,
            severity=rule.severity or "medium",
            message=message,
            matched_keywords=matched_keywords,
            actions=actions,
        )

    async def dispatch_alerts(self, events: List[AlertEvent]) -> Dict[str, int]:
        """
        分发预警事件到各渠道。

        Args:
            events: 预警事件列表

        Returns:
            dict: {"dispatched": int, "errors": int}
        """
        stats = {"dispatched": 0, "errors": 0}

        for event in events:
            if not event.actions:
                # 默认使用日志
                await self._log_alert(event)
                stats["dispatched"] += 1
                continue

            for action in event.actions:
                action_type = action.get("type", "log") if isinstance(action, dict) else str(action)
                handler = self._action_handlers.get(action_type)

                if handler:
                    try:
                        await handler(event, action if isinstance(action, dict) else {})
                        stats["dispatched"] += 1
                    except Exception as e:
                        logger.error(f"预警分发失败 ({action_type}): {e}")
                        stats["errors"] += 1
                else:
                    logger.warning(f"未知预警动作类型: {action_type}")
                    stats["errors"] += 1

        return stats

    async def _send_email_alert(self, event: AlertEvent, action_config: Dict) -> None:
        """通过邮件发送预警"""
        recipients = action_config.get("recipients", [])
        if not recipients:
            logger.warning(f"预警邮件无收件人: rule_id={event.rule_id}")
            return

        # 复用现有的邮件服务
        try:
            from src.utils.send_email import send_notification_email
            await send_notification_email(
                to=recipients,
                subject=f"[{event.severity.upper()}] 情报预警: {event.rule_name}",
                body=event.message,
            )
        except ImportError:
            logger.warning("邮件服务不可用，使用日志替代")
            await self._log_alert(event)

    async def _send_webhook_alert(self, event: AlertEvent, action_config: Dict) -> None:
        """通过 Webhook 发送预警"""
        url = action_config.get("url")
        if not url:
            return

        try:
            import httpx
            payload = {
                "rule_id": event.rule_id,
                "rule_name": event.rule_name,
                "intelligence_id": event.intelligence_id,
                "severity": event.severity,
                "message": event.message,
                "matched_keywords": event.matched_keywords,
                "triggered_at": event.triggered_at.isoformat(),
            }
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code >= 400:
                    logger.warning(f"Webhook 预警发送失败 ({resp.status_code}): {url}")
        except Exception as e:
            logger.error(f"Webhook 预警异常: {e}")
            raise

    async def _log_alert(self, event: AlertEvent, action_config: Dict = None) -> None:
        """通过日志记录预警"""
        logger.warning(
            f"[ALERT][{event.severity.upper()}] {event.rule_name} "
            f"(intelligence_id={event.intelligence_id}): {event.message}"
        )


# 全局实例
alert_engine = AlertEngine()
