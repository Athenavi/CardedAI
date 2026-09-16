"""
分析引擎

编排情感分析、摘要生成、分类器，将清洗后的采集条目转化为情报。
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select

logger = logging.getLogger(__name__)


class AnalysisEngine:
    """
    分析引擎

    对清洗后的采集条目执行 AI 分析，生成 Intelligence 记录。
    流程：SentimentAnalyzer -> ContentSummarizer -> ContentClassifier -> AlertEngine
    """

    def __init__(self):
        self._sentiment = None
        self._summarizer = None
        self._classifier = None

    @property
    def sentiment_analyzer(self):
        if self._sentiment is None:
            from shared.services.intel.analyzers.sentiment import SentimentAnalyzer
            self._sentiment = SentimentAnalyzer()
        return self._sentiment

    @property
    def content_summarizer(self):
        if self._summarizer is None:
            from shared.services.intel.analyzers.summarizer import ContentSummarizer
            self._summarizer = ContentSummarizer()
        return self._summarizer

    @property
    def content_classifier(self):
        if self._classifier is None:
            from shared.services.intel.analyzers.classifier import ContentClassifier
            self._classifier = ContentClassifier()
        return self._classifier

    async def analyze_item(self, item_id: int) -> Dict[str, Any]:
        """
        分析单条采集条目，生成情报。

        Args:
            item_id: CollectedItem 的 ID

        Returns:
            dict: {
                "success": bool,
                "intelligence_id": int | None,
                "sentiment": str,
                "category": str,
                "summary": str,
                "alert_events": list,
            }
        """
        from shared.models import CollectedItem, Intelligence
        from shared.services.intel.alert_engine import alert_engine
        from src.extensions import get_db

        # 1. 读取采集条目
        with get_db() as db:
            item = db.get(CollectedItem, item_id)
            if not item:
                return {"success": False, "error": f"条目不存在: {item_id}"}

            content = item.content_cleaned or item.content_raw or ""
            title = item.title or ""

            if not content:
                return {"success": False, "error": "条目内容为空"}

        # 2. 并行执行分析
        sentiment_result = await self.sentiment_analyzer.analyze(content)
        summary_result = await self.content_summarizer.summarize(content)
        classify_result = await self.content_classifier.classify(content)

        sentiment = sentiment_result.get("sentiment", "neutral")
        summary = summary_result.get("summary", "")
        category = classify_result.get("category", "其他")
        tags = classify_result.get("tags", [])
        confidence = sentiment_result.get("confidence", 0.0)
        importance = classify_result.get("confidence", 0.0)

        # 3. 创建 Intelligence 记录
        intelligence_id = None
        with get_db() as db:
            intel = Intelligence(
                title=title[:500] if title else "",
                summary=summary,
                sentiment=sentiment,
                category=category,
                importance_score=importance,
                item_ids=json.dumps([item_id]),
                tags=json.dumps(tags, ensure_ascii=False) if tags else None,
                source_urls=json.dumps([item.url]) if hasattr(item, "url") and item.url else None,
                created_at=datetime.now(timezone.utc),
            )
            db.add(intel)
            db.flush()
            intelligence_id = intel.id
            db.commit()

            # 更新采集条目状态
            item = db.get(CollectedItem, item_id)
            if item:
                item.status = "analyzed"
                item.analyzed_at = datetime.now(timezone.utc)

        # 4. 触发预警评估
        alert_events = await alert_engine.evaluate(
            intelligence_id=intelligence_id,
            title=title,
            summary=summary,
            category=category,
            sentiment=sentiment,
            importance_score=importance,
        )

        # 5. 分发预警
        if alert_events:
            await alert_engine.dispatch_alerts(alert_events)

        return {
            "success": True,
            "intelligence_id": intelligence_id,
            "sentiment": sentiment,
            "category": category,
            "summary": summary[:100] + "..." if len(summary) > 100 else summary,
            "alert_events": len(alert_events),
        }

    async def analyze_source(self, source_id: int) -> Dict[str, int]:
        """
        分析指定数据源下所有已清洗的采集条目。

        Args:
            source_id: 数据源 ID

        Returns:
            dict: {"total", "success", "errors"}
        """
        from shared.models import CollectedItem
        from src.extensions import get_db

        stats = {"total": 0, "success": 0, "errors": 0}

        with get_db() as db:
            items = db.execute(
                select(CollectedItem).where(
                    CollectedItem.source_id == source_id,
                    CollectedItem.status == "cleaned",
                )
            ).scalars().all()

            stats["total"] = len(items)

        for item in items:
            try:
                result = await self.analyze_item(item.id)
                if result.get("success"):
                    stats["success"] += 1
                else:
                    stats["errors"] += 1
                    logger.warning(f"分析条目 {item.id} 失败: {result.get('error')}")
            except Exception as e:
                logger.error(f"分析条目 {item.id} 异常: {e}")
                stats["errors"] += 1

        logger.info(
            f"分析引擎完成 source_id={source_id}: "
            f"total={stats['total']} success={stats['success']} errors={stats['errors']}"
        )
        return stats

    async def analyze_pending(self) -> Dict[str, int]:
        """
        分析所有状态为 cleaned 的采集条目。

        Returns:
            dict: {"total", "success", "errors"}
        """
        from shared.models import CollectedItem
        from src.extensions import get_db

        stats = {"total": 0, "success": 0, "errors": 0}

        with get_db() as db:
            items = db.execute(
                select(CollectedItem).where(CollectedItem.status == "cleaned")
            ).scalars().all()

            stats["total"] = len(items)

        for item in items:
            try:
                result = await self.analyze_item(item.id)
                if result.get("success"):
                    stats["success"] += 1
                else:
                    stats["errors"] += 1
            except Exception as e:
                logger.error(f"分析条目 {item.id} 异常: {e}")
                stats["errors"] += 1

        logger.info(
            f"分析引擎全局完成: total={stats['total']} success={stats['success']} errors={stats['errors']}"
        )
        return stats


# 全局实例
analysis_engine = AnalysisEngine()
