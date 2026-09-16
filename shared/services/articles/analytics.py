"""
数据分析服务（真实实现）

设计原则：
1. 所有指标均来自数据库真实聚合，**不再有任何硬编码/模拟值**
2. 依赖访问明细的指标（PV / UV / 停留时长 / 跳出率 / referrer 来源）在 Phase 1 明确返回
   0 或空数组（表示"暂无明细"），待 Phase 2 的 page_views 采集上线后由明细表提供真实值
3. 跨数据库兼容（SQLite / PostgreSQL）：按日期分组的聚合统一在 Python 侧完成
4. 可选数据源（会话/搜索/审计/媒体）在表为空或不可用时静默降级为空结果，绝不抛错

数据来源一览：
    文章指标    → articles（status / hidden / views / created_at / tags_list / category）
    正文长度    → article_content.content
    用户指标    → users（date_joined / last_login_at / is_staff）
    分类分布    → categories JOIN articles
    热门文章    → articles ORDER BY views DESC
    设备 / 地区 → user_sessions（device_info / location）
    搜索热词    → search_history.keyword
    后台活跃度  → audit_logs（action / created_at）
    媒体占用    → media（file_type / file_size）
"""

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.article import Article
from shared.models.article_content import ArticleContent
from shared.models.audit_log import AuditLog
from shared.models.category import Category
from shared.models.media import Media
from shared.models.search_history import SearchHistory
from shared.models.user import User
from shared.models.user_session import UserSession
from src.unified_logger import default_logger as logger

# 正文长度统计上限，避免超大正文拖慢聚合
MAX_CONTENT_SAMPLE = 20000


def _split_tags(tags_value) -> List[str]:
    """拆分 tags_list（兼容逗号/分号与中英文标点）"""
    if not tags_value:
        return []
    text = str(tags_value).replace('，', ',').replace('；', ';')
    return [chunk.strip() for chunk in text.split(',') if chunk.strip()]


class AnalyticsService:
    """
    数据分析服务（真实数据版）

    所有方法均为 async，直接使用 AsyncSession 查询；
    可选的统计维度在数据源缺失时返回空结果而不是抛错。
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ══════════════════════════════════════════════════
    # 内部工具
    # ══════════════════════════════════════════════════
    @staticmethod
    def _day_key(value) -> Optional[str]:
        if not value:
            return None
        try:
            return value.strftime("%Y-%m-%d")
        except Exception:
            return None

    async def _scalar(self, stmt, default: Any = 0) -> Any:
        """执行聚合查询并返回标量；异常时降级为默认值"""
        try:
            result = await self.db.execute(stmt)
            value = result.scalar()
            return default if value is None else value
        except Exception as exc:
            logger.warning(f"[Analytics] scalar query failed: {exc}")
            return default

    async def _count_by_day(self, column, days: int) -> Dict[str, int]:
        """按天统计某一时间列的记录数（Python 侧分组，跨库安全）"""
        cutoff = datetime.now() - timedelta(days=days)
        buckets: Dict[str, int] = {}
        try:
            result = await self.db.execute(select(column).where(column >= cutoff))
            for (value,) in result.all():
                key = self._day_key(value)
                if key:
                    buckets[key] = buckets.get(key, 0) + 1
        except Exception as exc:
            logger.warning(f"[Analytics] daily count failed: {exc}")
        return buckets

    @staticmethod
    def _series(buckets: Dict[str, int], days: int) -> List[Dict[str, Any]]:
        """把 {date: count} 补齐成连续 days 天的序列（旧 → 新）"""
        today = datetime.now()
        series = []
        for offset in range(days - 1, -1, -1):
            date = (today - timedelta(days=offset)).strftime("%Y-%m-%d")
            series.append({"date": date, "value": buckets.get(date, 0)})
        return series

    @staticmethod
    def _classify_referrer(referrer) -> str:
        """把 referrer 归类为可直接展示的来源渠道"""
        text = str(referrer or "").lower()
        if not text:
            return "直接访问"
        for keyword, label in (
                ("google.", "Google"),
                ("bing.", "Bing"),
                ("baidu.", "百度"),
                ("duckduckgo.", "DuckDuckGo"),
                ("yandex.", "Yandex"),
                ("github.", "GitHub"),
                ("twitter.", "Twitter / X"),
                ("x.com", "Twitter / X"),
                ("weibo.", "微博"),
                ("zhihu.", "知乎"),
                ("wechat", "微信"),
        ):
            if keyword in text:
                return label
        return "其它站点"

    @staticmethod
    def _classify_device(device_info) -> str:
        text = str(device_info or "").lower()
        if any(keyword in text for keyword in ("ipad", "tablet", "pad")):
            return "平板"
        if any(keyword in text for keyword in ("mobile", "android", "iphone", "ios", "phone")):
            return "移动端"
        if any(keyword in text for keyword in ("windows", "macintosh", "mac os", "linux", "desktop")):
            return "桌面端"
        return "未知"

    async def _tag_counts(self) -> List[Dict[str, Any]]:
        """标签分布（统计已发布文章的 tags_list）"""
        counter: Counter = Counter()
        try:
            result = await self.db.execute(
                select(Article.tags_list).where(Article.status == 1)
            )
            for (tags_value,) in result.all():
                for tag in _split_tags(tags_value):
                    counter[tag] += 1
        except Exception as exc:
            logger.warning(f"[Analytics] tag aggregation failed: {exc}")
        items = [{"name": name, "value": count} for name, count in counter.items()]
        items.sort(key=lambda item: (-item["value"], item["name"]))
        return items

    async def _pageview_trend(self, days: int):
        """
        Phase 2 接口位：page_views 明细表存在时返回按日 (PV, UV) 字典。

        Phase 1 尚未建立明细采集，这里返回空字典 —— 端点在序列中填 0，
        表示"暂无明细"而非伪造数字。
        """
        try:
            from shared.models.page_view import PageView  # Phase 2 才存在
        except Exception:
            return {}, {}

        cutoff = datetime.now() - timedelta(days=days)
        try:
            result = await self.db.execute(
                select(PageView.created_at, PageView.visitor_hash).where(PageView.created_at >= cutoff)
            )
            rows = result.all()
        except Exception as exc:
            logger.warning(f"[Analytics] pageview trend failed: {exc}")
            return {}, {}

        pv: Counter = Counter()
        uv_sets: Dict[str, set] = defaultdict(set)
        for created_at, visitor_hash in rows:
            key = self._day_key(created_at)
            if not key:
                continue
            pv[key] += 1
            if visitor_hash:
                uv_sets[key].add(visitor_hash)
        return pv, {day: len(visitors) for day, visitors in uv_sets.items()}

    # ══════════════════════════════════════════════════
    # 概览
    # ══════════════════════════════════════════════════
    async def get_overview_stats(self, days: int = 30) -> Dict:
        """概览统计（全部为真实聚合值）"""
        cutoff = datetime.now() - timedelta(days=days)

        total_articles = await self._scalar(select(func.count(Article.id)))
        published_articles = await self._scalar(
            select(func.count(Article.id)).where(Article.status == 1)
        )
        draft_articles = await self._scalar(
            select(func.count(Article.id)).where(
                or_(Article.status == 0, Article.status.is_(None))
            )
        )
        hidden_articles = await self._scalar(
            select(func.count(Article.id)).where(Article.hidden.is_(True))
        )
        featured_articles = await self._scalar(
            select(func.count(Article.id)).where(Article.is_featured.is_(True))
        )
        new_articles = await self._scalar(
            select(func.count(Article.id)).where(Article.created_at >= cutoff)
        )

        # 浏览量：真实累计值（article_view_stats 会把 Redis 计数批量回写到 articles.views）
        total_views = int(await self._scalar(select(func.coalesce(func.sum(Article.views), 0))))
        avg_views = round(total_views / total_articles, 2) if total_articles else 0.0

        total_users = await self._scalar(select(func.count(User.id)))
        new_users = await self._scalar(
            select(func.count(User.id)).where(User.date_joined >= cutoff)
        )
        active_users = await self._scalar(
            select(func.count(User.id)).where(User.last_login_at >= cutoff)
        )
        staff_users = await self._scalar(
            select(func.count(User.id)).where(User.is_staff.is_(True))
        )

        media_count = await self._scalar(select(func.count(Media.id)))
        media_bytes = int(await self._scalar(select(func.coalesce(func.sum(Media.file_size), 0))))

        searches = await self._scalar(
            select(func.count(SearchHistory.id)).where(SearchHistory.created_at >= cutoff)
        )

        tags = await self._tag_counts()
        pv_buckets, uv_buckets = await self._pageview_trend(days)

        # 平均停留时长：来自访问明细的 duration_ms（暂无明细时为 0）
        avg_duration = 0
        try:
            from shared.models.page_view import PageView
            result = await self.db.execute(
                select(func.avg(PageView.duration_ms)).where(
                    PageView.created_at >= cutoff, PageView.duration_ms.isnot(None)
                )
            )
            value = result.scalar()
            avg_duration = round(float(value) / 1000, 1) if value else 0
        except Exception:
            avg_duration = 0

        return {
            # 内容
            "total_articles": total_articles,
            "published_articles": published_articles,
            "draft_articles": draft_articles,
            "hidden_articles": hidden_articles,
            "featured_articles": featured_articles,
            "new_articles": new_articles,
            "total_views": total_views,
            "avg_views": avg_views,
            "total_tags": len(tags),
            # 用户
            "total_users": total_users,
            "new_users": new_users,
            "active_users": active_users,
            "staff_users": staff_users,
            # 媒体 / 搜索
            "media_count": media_count,
            "media_bytes": media_bytes,
            "searches": searches,
            # 访问明细（Phase 2 采集上线前恒为 0，代表「暂无明细」）
            "total_pv": sum(pv_buckets.values()) if pv_buckets else 0,
            "unique_visitors": sum(uv_buckets.values()) if uv_buckets else 0,
            "avg_duration": avg_duration,
            "bounce_rate": 0,
            "has_traffic_detail": bool(pv_buckets),
            "period_days": days,
        }

    # ══════════════════════════════════════════════════
    # 趋势（发布 / 注册 / PV·UV）
    # ══════════════════════════════════════════════════
    async def get_article_views_trend(self, days: int = 30) -> List[Dict]:
        """
        按日趋势：
        - articles：当日发布文章数（真实）
        - users：当日注册用户数（真实）
        - views / visitors：当日 PV / UV —— 需要访问明细（Phase 2）；
          暂无明细时恒为 0，前端应标注「待开启访问统计」
        """
        article_buckets = await self._count_by_day(Article.created_at, days)
        user_buckets = await self._count_by_day(User.date_joined, days)
        pv_buckets, uv_buckets = await self._pageview_trend(days)

        today = datetime.now()
        series = []
        for offset in range(days - 1, -1, -1):
            date = (today - timedelta(days=offset)).strftime("%Y-%m-%d")
            series.append({
                "date": date,
                "articles": article_buckets.get(date, 0),
                "users": user_buckets.get(date, 0),
                "views": pv_buckets.get(date, 0) if pv_buckets else 0,
                "visitors": uv_buckets.get(date, 0) if uv_buckets else 0,
            })
        return series

    # ══════════════════════════════════════════════════
    # 热门文章
    # ══════════════════════════════════════════════════
    async def get_popular_articles(self, limit: int = 10, days: int = 7) -> List[Dict]:
        """
        热门文章：按**累计浏览量**（articles.views，真实值）排序。

        注：暂无按日浏览明细（Phase 2 提供），因此 days 不参与浏览量过滤，
        仅用于标注「是否为统计窗口内新发布」。
        """
        cutoff = datetime.now() - timedelta(days=days)
        try:
            result = await self.db.execute(
                select(
                    Article.id, Article.title, Article.slug, Article.views,
                    Article.created_at, Article.category,
                )
                .where(Article.hidden.is_(False), Article.status == 1, Article.views > 0)
                .order_by(Article.views.desc())
                .limit(limit)
            )
            rows = result.all()
        except Exception as exc:
            logger.warning(f"[Analytics] popular articles failed: {exc}")
            return []

        category_names: Dict[int, str] = {}
        category_ids = [row.category for row in rows if row.category]
        if category_ids:
            try:
                cat_result = await self.db.execute(
                    select(Category.id, Category.name).where(Category.id.in_(category_ids))
                )
                category_names = {cid: name for cid, name in cat_result.all()}
            except Exception:
                category_names = {}

        return [
            {
                "id": row.id,
                "title": row.title,
                "slug": row.slug,
                "views": int(row.views or 0),
                "category_name": category_names.get(row.category),
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "created_within_period": bool(row.created_at and row.created_at >= cutoff),
            }
            for row in rows
        ]

    # ══════════════════════════════════════════════════
    # 分布：分类 / 标签
    # ══════════════════════════════════════════════════
    async def get_category_distribution(self) -> List[Dict]:
        """分类分布（含「未分类」）"""
        distribution: List[Dict] = []
        try:
            result = await self.db.execute(
                select(Category.name, func.count(Article.id).label("article_count"))
                .select_from(Article)
                .join(Category, Article.category == Category.id, isouter=True)
                .group_by(Category.name)
                .order_by(func.count(Article.id).desc())
            )
            for name, count in result.all():
                distribution.append({"name": name or "未分类", "value": count})
        except Exception as exc:
            logger.warning(f"[Analytics] category distribution failed: {exc}")

        if not distribution:
            total = await self._scalar(select(func.count(Article.id)))
            if total:
                distribution = [{"name": "未分类", "value": total}]
        return distribution

    async def get_tag_distribution(self, limit: int = 15) -> List[Dict]:
        """标签分布（Top N）"""
        tags = await self._tag_counts()
        return tags[:limit]

    # ══════════════════════════════════════════════════
    # 用户活动
    # ══════════════════════════════════════════════════
    async def get_user_activity(self, days: int = 30) -> Dict:
        """用户活动：活跃作者 / 新注册 / 近期登录 / 注册趋势"""
        cutoff = datetime.now() - timedelta(days=days)

        active_authors = await self._scalar(
            select(func.count(func.distinct(Article.user))).where(
                Article.created_at >= cutoff, Article.user.isnot(None)
            )
        )
        new_users = await self._scalar(
            select(func.count(User.id)).where(User.date_joined >= cutoff)
        )
        active_users = await self._scalar(
            select(func.count(User.id)).where(User.last_login_at >= cutoff)
        )
        returning_users = await self._scalar(
            select(func.count(User.id)).where(
                User.last_login_at >= cutoff, User.date_joined < cutoff
            )
        )

        register_buckets = await self._count_by_day(User.date_joined, days)

        return {
            "active_authors": active_authors,
            "active_users": active_users,
            "returning_users": returning_users,
            "new_users": new_users,
            "register_trend": self._series(register_buckets, days),
            "period_days": days,
        }

    # ══════════════════════════════════════════════════
    # 内容表现
    # ══════════════════════════════════════════════════
    async def get_content_performance(self, days: int = 30) -> Dict:
        """内容表现：真实浏览统计 + 正文长度（article_content）"""
        cutoff = datetime.now() - timedelta(days=days)

        total_articles = await self._scalar(select(func.count(Article.id)))
        published_articles = await self._scalar(
            select(func.count(Article.id)).where(Article.status == 1)
        )
        total_views = int(await self._scalar(select(func.coalesce(func.sum(Article.views), 0))))
        zero_view_articles = await self._scalar(
            select(func.count(Article.id)).where(
                or_(Article.views == 0, Article.views.is_(None))
            )
        )
        published_in_period = await self._scalar(
            select(func.count(Article.id)).where(Article.created_at >= cutoff)
        )
        max_views = int(await self._scalar(select(func.coalesce(func.max(Article.views), 0))))

        lengths: List[int] = []
        try:
            result = await self.db.execute(
                select(ArticleContent.content).limit(MAX_CONTENT_SAMPLE)
            )
            for (content,) in result.all():
                if content:
                    lengths.append(len(str(content)))
        except Exception as exc:
            logger.warning(f"[Analytics] content length failed: {exc}")

        measured = len(lengths)
        avg_length = round(sum(lengths) / measured) if measured else 0

        return {
            "total_articles": total_articles,
            "published_articles": published_articles,
            "published_in_period": published_in_period,
            "total_views": total_views,
            "avg_views_per_article": round(total_views / total_articles, 2) if total_articles else 0.0,
            "max_views": max_views,
            "zero_view_articles": zero_view_articles,
            "measured_articles": measured,
            "avg_content_length": avg_length,
            "max_content_length": max(lengths) if lengths else 0,
            "period_days": days,
        }

    # ══════════════════════════════════════════════════
    # 设备 / 来源
    # ══════════════════════════════════════════════════
    async def get_device_stats(self, days: int = 30) -> List[Dict]:
        """
        设备分布：基于登录会话 device_info（user_sessions）。
        无会话数据时返回空数组（前端显示空态），不再抛错。
        """
        cutoff = datetime.now() - timedelta(days=days)
        buckets: Counter = Counter()

        # 优先使用访问明细的 User-Agent（Phase 2 采集），无明细时回退登录会话 device_info
        try:
            from shared.models.page_view import PageView
            result = await self.db.execute(
                select(PageView.user_agent).where(PageView.created_at >= cutoff)
            )
            for (user_agent,) in result.all():
                buckets[self._classify_device(user_agent)] += 1
        except Exception:
            buckets = Counter()

        if not buckets:
            try:
                result = await self.db.execute(
                    select(UserSession.device_info).where(UserSession.created_at >= cutoff)
                )
                for (device_info,) in result.all():
                    buckets[self._classify_device(device_info)] += 1
            except Exception as exc:
                logger.warning(f"[Analytics] device stats failed: {exc}")

        return [{"name": name, "value": value} for name, value in buckets.most_common()]

    async def get_traffic_sources(self, days: int = 30) -> List[Dict]:
        """
        流量来源：
        - Phase 1：基于登录会话地区（user_sessions.location），有数据时为真实值；
          referrer 归类的来源统计将在 Phase 2 由 page_views 提供
        - 无数据返回空数组
        """
        cutoff = datetime.now() - timedelta(days=days)
        buckets: Counter = Counter()

        # 优先按访问明细的 referrer 归类（Phase 2 采集）
        try:
            from shared.models.page_view import PageView
            result = await self.db.execute(
                select(PageView.referrer).where(PageView.created_at >= cutoff)
            )
            for (referrer,) in result.all():
                buckets[self._classify_referrer(referrer)] += 1
        except Exception:
            buckets = Counter()

        if not buckets:
            try:
                result = await self.db.execute(
                    select(UserSession.location).where(UserSession.created_at >= cutoff)
                )
                for (location,) in result.all():
                    buckets[str(location).strip() if location else "未知"] += 1
            except Exception as exc:
                logger.warning(f"[Analytics] traffic sources failed: {exc}")

        return [{"name": name, "value": value} for name, value in buckets.most_common(10)]

    # ══════════════════════════════════════════════════
    # 搜索 / 审计 / 媒体
    # ══════════════════════════════════════════════════
    async def get_search_keywords(self, limit: int = 10, days: int = 30) -> List[Dict]:
        """搜索热词（search_history 聚合）"""
        cutoff = datetime.now() - timedelta(days=days)
        counter: Counter = Counter()
        try:
            result = await self.db.execute(
                select(SearchHistory.keyword).where(SearchHistory.created_at >= cutoff)
            )
            for (keyword,) in result.all():
                text = (keyword or "").strip()
                if text:
                    counter[text] += 1
        except Exception as exc:
            logger.warning(f"[Analytics] search keywords failed: {exc}")
        return [{"name": name, "value": value} for name, value in counter.most_common(limit)]

    async def get_audit_activity(self, days: int = 30, limit: int = 8) -> Dict:
        """后台操作活跃度（audit_logs：按日 + 按动作 Top）"""
        cutoff = datetime.now() - timedelta(days=days)
        by_day: Counter = Counter()
        by_action: Counter = Counter()
        try:
            result = await self.db.execute(
                select(AuditLog.action, AuditLog.created_at).where(AuditLog.created_at >= cutoff)
            )
            for action, created_at in result.all():
                key = self._day_key(created_at)
                if key:
                    by_day[key] += 1
                by_action[str(action or "unknown")] += 1
        except Exception as exc:
            logger.warning(f"[Analytics] audit activity failed: {exc}")

        return {
            "daily": self._series(by_day, days),
            "top_actions": [{"name": name, "value": value} for name, value in by_action.most_common(limit)],
            "total": sum(by_day.values()),
            "period_days": days,
        }

    async def get_media_stats(self) -> Dict:
        """媒体库统计：数量 / 总占用 / 按类型分布"""
        by_type: Counter = Counter()
        total_bytes = 0
        count = 0
        try:
            result = await self.db.execute(select(Media.file_type, Media.file_size))
            for file_type, file_size in result.all():
                count += 1
                total_bytes += int(file_size or 0)
                by_type[str(file_type or "other")] += 1
        except Exception as exc:
            logger.warning(f"[Analytics] media stats failed: {exc}")

        return {
            "count": count,
            "bytes": total_bytes,
            "by_type": [{"name": name, "value": value} for name, value in by_type.most_common()],
        }


# 工厂函数（保持既有签名，端点无需改动）
def create_analytics_service(db: AsyncSession) -> AnalyticsService:
    return AnalyticsService(db)
