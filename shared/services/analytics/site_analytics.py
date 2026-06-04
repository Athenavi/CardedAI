"""
站内数据分析服务

提供页面浏览量统计、用户行为追踪、访问分析等功能
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict, Counter


class SiteAnalyticsService:
    """
    站内数据分析服务
    
    功能:
    1. 页面浏览量统计
    2. 用户行为追踪
    3. 访问来源分析
    4. 热门内容排行
    5. 用户留存分析
    """

    def __init__(self, data_dir: str = "storage/analytics"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 内存中的事件缓存
        self.events_buffer: List[Dict[str, Any]] = []
        self.max_buffer_size = 1000

        # 页面浏览量缓存 {page_path: count}
        self.page_views_cache: Counter = Counter()

        # 用户会话跟踪 {session_id: session_data}
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def track_page_view(
            self,
            page_path: str,
            page_title: str = "",
            user_id: Optional[str] = None,
            session_id: Optional[str] = None,
            referrer: Optional[str] = None,
            user_agent: Optional[str] = None,
            ip_address: Optional[str] = None,
            timestamp: Optional[datetime] = None
    ):
        """
        追踪页面浏览
        
        Args:
            page_path: 页面路径
            page_title: 页面标题
            user_id: 用户ID（如果已登录）
            session_id: 会话ID
            referrer: 来源页面
            user_agent: 用户代理
            ip_address: IP地址
            timestamp: 时间戳
        """
        if timestamp is None:
            timestamp = datetime.now()

        event = {
            "event_type": "page_view",
            "timestamp": timestamp.isoformat(),
            "page_path": page_path,
            "page_title": page_title,
            "user_id": user_id,
            "session_id": session_id,
            "referrer": referrer,
            "user_agent": user_agent,
            "ip_address": ip_address,
        }

        # 添加到缓冲区
        self.events_buffer.append(event)
        if len(self.events_buffer) >= self.max_buffer_size:
            self._flush_events()

        # 更新页面浏览量缓存
        self.page_views_cache[page_path] += 1

        # 更新会话数据
        if session_id:
            self._update_session(session_id, event)

    def track_event(
            self,
            event_name: str,
            user_id: Optional[str] = None,
            session_id: Optional[str] = None,
            properties: Optional[Dict[str, Any]] = None,
            timestamp: Optional[datetime] = None
    ):
        """
        追踪自定义事件
        
        Args:
            event_name: 事件名称
            user_id: 用户ID
            session_id: 会话ID
            properties: 事件属性
            timestamp: 时间戳
        """
        if timestamp is None:
            timestamp = datetime.now()

        event = {
            "event_type": "custom_event",
            "event_name": event_name,
            "timestamp": timestamp.isoformat(),
            "user_id": user_id,
            "session_id": session_id,
            "properties": properties or {},
        }

        # 添加到缓冲区
        self.events_buffer.append(event)
        if len(self.events_buffer) >= self.max_buffer_size:
            self._flush_events()

    def track_user_action(
            self,
            action: str,
            user_id: str,
            resource_type: Optional[str] = None,
            resource_id: Optional[str] = None,
            session_id: Optional[str] = None,
            timestamp: Optional[datetime] = None
    ):
        """
        追踪用户操作
        
        Args:
            action: 操作类型（click, scroll, form_submit等）
            user_id: 用户ID
            resource_type: 资源类型
            resource_id: 资源ID
            session_id: 会话ID
            timestamp: 时间戳
        """
        self.track_event(
            event_name=f"user_action:{action}",
            user_id=user_id,
            session_id=session_id,
            properties={
                "resource_type": resource_type,
                "resource_id": resource_id,
            },
            timestamp=timestamp
        )

    def get_page_views(
            self,
            page_path: Optional[str] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> Dict[str, int]:
        """
        获取页面浏览量
        
        Args:
            page_path: 页面路径过滤
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            页面浏览量字典
        """
        # 从缓存返回
        if page_path:
            return {page_path: self.page_views_cache.get(page_path, 0)}

        return dict(self.page_views_cache)

    def get_popular_pages(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取热门页面
        
        Args:
            limit: 返回数量
            
        Returns:
            热门页面列表
        """
        popular = self.page_views_cache.most_common(limit)

        return [
            {
                "page_path": path,
                "views": count,
            }
            for path, count in popular
        ]

    def get_traffic_sources(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取流量来源统计
        
        Args:
            limit: 返回数量
            
        Returns:
            流量来源列表
        """
        sources = Counter()

        for event in self.events_buffer:
            if event.get("event_type") == "page_view":
                referrer = event.get("referrer", "direct")
                if referrer:
                    # 提取域名
                    domain = self._extract_domain(referrer)
                    sources[domain] += 1

        top_sources = sources.most_common(limit)

        return [
            {
                "source": source,
                "visits": count,
            }
            for source, count in top_sources
        ]

    def get_user_activity(
            self,
            user_id: str,
            days: int = 30
    ) -> Dict[str, Any]:
        """
        获取用户活动统计
        
        Args:
            user_id: 用户ID
            days: 统计天数
            
        Returns:
            用户活动数据
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        user_events = [
            event for event in self.events_buffer
            if event.get("user_id") == user_id
               and datetime.fromisoformat(event["timestamp"]) >= cutoff_date
        ]

        # 统计页面浏览
        page_views = sum(1 for e in user_events if e.get("event_type") == "page_view")

        # 统计自定义事件
        custom_events = Counter(
            e.get("event_name", "unknown")
            for e in user_events
            if e.get("event_type") == "custom_event"
        )

        # 访问天数
        visit_dates = set(
            datetime.fromisoformat(e["timestamp"]).date()
            for e in user_events
        )

        return {
            "user_id": user_id,
            "period_days": days,
            "total_page_views": page_views,
            "unique_visit_days": len(visit_dates),
            "custom_events": dict(custom_events),
            "total_events": len(user_events),
        }

    def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话统计
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话统计数据
        """
        session = self.sessions.get(session_id)
        if not session:
            return None

        duration = session.get("duration_seconds", 0)
        page_views = session.get("page_views", 0)

        return {
            "session_id": session_id,
            "start_time": session.get("start_time"),
            "last_activity": session.get("last_activity"),
            "duration_seconds": duration,
            "page_views": page_views,
            "pages_visited": session.get("pages", []),
            "user_id": session.get("user_id"),
        }

    def get_daily_stats(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        获取每日统计数据
        
        Args:
            days: 统计天数
            
        Returns:
            每日统计数据列表
        """
        daily_stats = defaultdict(lambda: {
            "page_views": 0,
            "unique_visitors": set(),
            "events": 0,
        })

        cutoff_date = datetime.now() - timedelta(days=days)

        for event in self.events_buffer:
            timestamp = datetime.fromisoformat(event["timestamp"])
            if timestamp < cutoff_date:
                continue

            date_str = timestamp.strftime("%Y-%m-%d")

            if event.get("event_type") == "page_view":
                daily_stats[date_str]["page_views"] += 1

                # 统计独立访客
                visitor_id = event.get("user_id") or event.get("session_id")
                if visitor_id:
                    daily_stats[date_str]["unique_visitors"].add(visitor_id)

            else:
                daily_stats[date_str]["events"] += 1

        # 转换为列表格式
        result = []
        for date_str in sorted(daily_stats.keys()):
            stats = daily_stats[date_str]
            result.append({
                "date": date_str,
                "page_views": stats["page_views"],
                "unique_visitors": len(stats["unique_visitors"]),
                "events": stats["events"],
            })

        return result

    def _update_session(self, session_id: str, event: Dict[str, Any]):
        """更新会话数据"""
        if session_id not in self.sessions:
            # 创建新会话
            self.sessions[session_id] = {
                "session_id": session_id,
                "start_time": event["timestamp"],
                "last_activity": event["timestamp"],
                "user_id": event.get("user_id"),
                "page_views": 0,
                "pages": [],
                "duration_seconds": 0,
            }

        session = self.sessions[session_id]
        session["last_activity"] = event["timestamp"]

        # 更新页面浏览
        if event.get("event_type") == "page_view":
            session["page_views"] += 1
            page_path = event.get("page_path", "")
            if page_path and page_path not in session["pages"]:
                session["pages"].append(page_path)

        # 计算会话时长
        try:
            start = datetime.fromisoformat(session["start_time"])
            last = datetime.fromisoformat(session["last_activity"])
            session["duration_seconds"] = (last - start).total_seconds()
        except Exception:
            pass

    def _flush_events(self):
        """将事件缓冲区写入文件"""
        if not self.events_buffer:
            return

        try:
            # 按日期分文件存储
            date_str = datetime.now().strftime("%Y-%m-%d")
            events_file = self.data_dir / f"events_{date_str}.jsonl"

            with open(events_file, 'a', encoding='utf-8') as f:
                for event in self.events_buffer:
                    f.write(json.dumps(event, ensure_ascii=False) + '\n')

            # 清空缓冲区
            self.events_buffer.clear()

        except Exception as e:
            print(f"[Analytics] Failed to flush events: {e}")

    def _extract_domain(self, url: str) -> str:
        """从URL提取域名"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc or "direct"
        except Exception:
            return "direct"

    def load_events_from_file(self, date_str: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        从文件加载事件数据
        
        Args:
            date_str: 日期字符串（YYYY-MM-DD），默认为今天
            
        Returns:
            事件列表
        """
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")

        events_file = self.data_dir / f"events_{date_str}.jsonl"

        if not events_file.exists():
            return []

        events = []
        try:
            with open(events_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        events.append(json.loads(line))
        except Exception as e:
            print(f"[Analytics] Failed to load events: {e}")

        return events


# 全局实例
site_analytics = SiteAnalyticsService()
