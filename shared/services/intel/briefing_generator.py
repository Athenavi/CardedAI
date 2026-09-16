"""
情报简报生成器

生成每日/自定义情报简报，调用 LLM 进行结构化内容生成。
"""

import json
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, and_, desc

logger = logging.getLogger(__name__)


class BriefingGenerator:
    """
    情报简报生成器

    功能：
    1. 生成每日情报简报
    2. 生成自定义主题简报
    3. 推送到配置的渠道
    """

    async def generate_daily_briefing(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        生成每日情报简报。

        Args:
            target_date: 目标日期（默认今天）

        Returns:
            dict: {
                "success": bool,
                "briefing_id": int | None,
                "title": str,
                "content": str,
                "intelligence_count": int,
            }
        """
        from shared.models import Intelligence, Briefing
        from shared.services.ai.llm_client import llm_client
        from src.extensions import get_db

        d = target_date or date.today()
        day_start = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)

        # 1. 查询当日所有情报
        with get_db() as db:
            items = db.execute(
                select(Intelligence).where(
                    and_(
                        Intelligence.created_at >= day_start,
                        Intelligence.created_at < day_end,
                    )
                ).order_by(desc(Intelligence.importance_score))
            ).scalars().all()

            if not items:
                return {
                    "success": False,
                    "briefing_id": None,
                    "title": f"{d.isoformat()} 情报简报",
                    "content": "当日无新增情报。",
                    "intelligence_count": 0,
                }

            # 2. 准备情报摘要列表
            intel_summaries = []
            intel_ids = []
            for item in items[:50]:  # 最多取 50 条
                intel_summaries.append({
                    "id": item.id,
                    "title": item.title or "",
                    "summary": item.summary or "",
                    "category": item.category or "",
                    "sentiment": item.sentiment or "",
                    "importance": float(item.importance_score) if item.importance_score else 0,
                })
                intel_ids.append(item.id)

        # 3. 调用 LLM 生成结构化简报
        title = f"{d.isoformat()} 每日情报简报"
        content = ""

        if llm_client.is_available:
            try:
                result = await llm_client.generate_text(
                    prompt=(
                        f"请根据以下 {len(intel_summaries)} 条情报，生成一份结构化的每日情报简报。\n\n"
                        f"要求：\n"
                        f"1. 使用 Markdown 格式\n"
                        f"2. 分为「今日要闻」、「重点关注」、「趋势分析」三个板块\n"
                        f"3. 每个板块选择 3-5 条最重要的情报\n"
                        f"4. 简明扼要，突出关键信息\n\n"
                        f"情报数据：\n{json.dumps(intel_summaries, ensure_ascii=False, indent=2)}"
                    ),
                    system_prompt="你是一个专业的情报分析师，擅长生成简洁、专业的情报简报。",
                    temperature=0.4,
                    max_tokens=2000,
                )

                if result.get("success") and result.get("content"):
                    content = result["content"]

            except Exception as e:
                logger.error(f"LLM 简报生成失败: {e}")

        if not content:
            # fallback：简单列表
            lines = [f"# {title}\n"]
            lines.append(f"共收录 {len(intel_summaries)} 条情报\n")
            lines.append("## 情报列表\n")
            for i, item in enumerate(intel_summaries[:20], 1):
                importance = f"⭐{int(item['importance'])}" if item["importance"] > 0.7 else ""
                lines.append(f"{i}. **{item['title']}** {importance}")
                if item["summary"]:
                    lines.append(f"   > {item['summary'][:100]}")
                lines.append("")
            content = "\n".join(lines)

        # 4. 存储简报
        briefing_id = None
        with get_db() as db:
            briefing = Briefing(
                title=title,
                content=content,
                briefing_type="daily",
                intelligence_ids=json.dumps(intel_ids),
                created_at=datetime.now(timezone.utc),
            )
            db.add(briefing)
            db.flush()
            briefing_id = briefing.id
            db.commit()

        return {
            "success": True,
            "briefing_id": briefing_id,
            "title": title,
            "content": content,
            "intelligence_count": len(intel_summaries),
        }

    async def generate_weekly_briefing(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        生成每周情报简报。

        Args:
            target_date: 所在周的某一天（默认今天）
        """
        d = target_date or date.today()
        # 计算周起始（周一）
        week_start = d - timedelta(days=d.weekday())
        week_end = week_start + timedelta(days=7)
        return await self._generate_period_briefing(
            period_start=datetime(week_start.year, week_start.month, week_start.day, tzinfo=timezone.utc),
            period_end=datetime(week_end.year, week_end.month, week_end.day, tzinfo=timezone.utc),
            briefing_type="weekly",
            title_prefix=f"{week_start.isoformat()} 至 {week_end.isoformat()} 每周情报简报",
            llm_prompt="请根据以下情报，生成一份每周情报简报。分为「本周要闻」、「重点分析」、「下周展望」三个板块。",
        )

    async def generate_monthly_briefing(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        生成每月情报简报。

        Args:
            target_date: 所在月的某一天（默认今天）
        """
        d = target_date or date.today()
        month_start = date(d.year, d.month, 1)
        if d.month == 12:
            month_end = date(d.year + 1, 1, 1)
        else:
            month_end = date(d.year, d.month + 1, 1)
        return await self._generate_period_briefing(
            period_start=datetime(month_start.year, month_start.month, month_start.day, tzinfo=timezone.utc),
            period_end=datetime(month_end.year, month_end.month, month_end.day, tzinfo=timezone.utc),
            briefing_type="monthly",
            title_prefix=f"{d.year}年{d.month}月 月度情报简报",
            llm_prompt="请根据以下情报，生成一份月度情报简报。分为「本月综述」、「重要事件回顾」、「趋势研判」三个板块。",
        )

    async def _generate_period_briefing(
        self,
        period_start: datetime,
        period_end: datetime,
        briefing_type: str,
        title_prefix: str,
        llm_prompt: str,
    ) -> Dict[str, Any]:
        """生成周期简报的通用逻辑"""
        from shared.models import Intelligence, Briefing
        from shared.services.ai.llm_client import llm_client
        from src.extensions import get_db

        with get_db() as db:
            items = db.execute(
                select(Intelligence).where(
                    and_(
                        Intelligence.created_at >= period_start,
                        Intelligence.created_at < period_end,
                    )
                ).order_by(desc(Intelligence.importance_score))
            ).scalars().all()

            if not items:
                return {
                    "success": False, "briefing_id": None,
                    "title": title_prefix, "content": "该周期内无新增情报。", "intelligence_count": 0,
                }

            intel_summaries = []
            intel_ids = []
            for item in items[:100]:
                intel_summaries.append({
                    "id": item.id, "title": item.title or "", "summary": item.summary or "",
                    "category": item.category or "", "sentiment": item.sentiment or "",
                    "importance": float(item.importance_score) if item.importance_score else 0,
                })
                intel_ids.append(item.id)

        title = title_prefix
        content = ""

        if llm_client.is_available:
            try:
                result = await llm_client.generate_text(
                    prompt=f"{llm_prompt}\n\n情报数据：\n{json.dumps(intel_summaries[:80], ensure_ascii=False, indent=2)}",
                    system_prompt="你是一个专业的情报分析师。",
                    temperature=0.4, max_tokens=2500,
                )
                if result.get("success") and result.get("content"):
                    content = result["content"]
            except Exception as e:
                logger.error(f"LLM {briefing_type} 简报生成失败: {e}")

        if not content:
            lines = [f"# {title}\n"]
            lines.append(f"共收录 {len(intel_summaries)} 条情报\n")
            for i, item in enumerate(intel_summaries[:30], 1):
                imp = f" ⭐{int(item['importance'])}" if item['importance'] > 0.7 else ""
                lines.append(f"{i}. **{item['title']}**{imp}")
                if item['summary']:
                    lines.append(f"   > {item['summary'][:100]}")
                lines.append("")
            content = "\n".join(lines)

        briefing_id = None
        with get_db() as db:
            briefing = Briefing(
                title=title, content=content,
                briefing_type=briefing_type,
                intelligence_ids=json.dumps(intel_ids),
                created_at=datetime.now(timezone.utc),
            )
            db.add(briefing)
            db.flush()
            briefing_id = briefing.id
            db.commit()

        return {"success": True, "briefing_id": briefing_id, "title": title,
                "content": content, "intelligence_count": len(intel_summaries)}

    async def generate_custom_briefing(self, topic: str, days: int = 7) -> Dict[str, Any]:
        """
        生成自定义主题简报。

        Args:
            topic: 主题/关键词
            days: 回溯天数（默认 7 天）

        Returns:
            dict: {
                "success": bool,
                "briefing_id": int | None,
                "title": str,
                "content": str,
                "intelligence_count": int,
            }
        """
        from shared.models import Intelligence, Briefing
        from shared.services.ai.llm_client import llm_client
        from src.extensions import get_db

        since = datetime.now(timezone.utc) - timedelta(days=days)

        # 1. 查询相关情报
        with get_db() as db:
            items = db.execute(
                select(Intelligence).where(Intelligence.created_at >= since)
                .order_by(desc(Intelligence.importance_score))
            ).scalars().all()

            # 过滤与主题相关的情报
            topic_lower = topic.lower()
            related = []
            for item in items:
                text = f"{item.title or ''} {item.summary or ''} {item.category or ''}".lower()
                if topic_lower in text:
                    related.append({
                        "id": item.id,
                        "title": item.title or "",
                        "summary": item.summary or "",
                        "category": item.category or "",
                        "importance": float(item.importance_score) if item.importance_score else 0,
                    })
                if len(related) >= 50:
                    break

            if not related:
                return {
                    "success": False,
                    "briefing_id": None,
                    "title": f"主题简报: {topic}",
                    "content": f"近 {days} 天内未找到与「{topic}」相关的情报。",
                    "intelligence_count": 0,
                }

            intel_ids = [r["id"] for r in related]

        # 2. LLM 生成
        title = f"主题简报: {topic}（近 {days} 天）"
        content = ""

        if llm_client.is_available:
            try:
                result = await llm_client.generate_text(
                    prompt=(
                        f"请根据以下与「{topic}」相关的情报，生成一份专题分析简报。\n\n"
                        f"要求：\n"
                        f"1. 使用 Markdown 格式\n"
                        f"2. 包含「概况总结」、「关键发现」、「趋势与建议」\n"
                        f"3. 统计分析（情感分布、重要性分布）\n\n"
                        f"情报数据（共 {len(related)} 条）：\n"
                        f"{json.dumps(related[:30], ensure_ascii=False, indent=2)}"
                    ),
                    system_prompt="你是一个专业的情报分析师，擅长生成专题分析报告。",
                    temperature=0.4,
                    max_tokens=2500,
                )

                if result.get("success") and result.get("content"):
                    content = result["content"]

            except Exception as e:
                logger.error(f"LLM 主题简报生成失败: {e}")

        if not content:
            lines = [f"# {title}\n"]
            lines.append(f"共找到 {len(related)} 条相关情报\n")
            for i, item in enumerate(related[:20], 1):
                lines.append(f"{i}. **{item['title']}**")
                if item["summary"]:
                    lines.append(f"   > {item['summary'][:100]}")
                lines.append("")
            content = "\n".join(lines)

        # 3. 存储
        briefing_id = None
        with get_db() as db:
            briefing = Briefing(
                title=title,
                content=content,
                briefing_type="custom",
                intelligence_ids=json.dumps(intel_ids),
                created_at=datetime.now(timezone.utc),
            )
            db.add(briefing)
            db.flush()
            briefing_id = briefing.id
            db.commit()

        return {
            "success": True,
            "briefing_id": briefing_id,
            "title": title,
            "content": content,
            "intelligence_count": len(related),
        }


# 全局实例
briefing_generator = BriefingGenerator()
