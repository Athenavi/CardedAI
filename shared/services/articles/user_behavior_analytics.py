"""
用户行为分析服务
追踪页面浏览、停留时间、点击事件等用户行为数据
"""


from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.unified_logger import default_logger as logger


class UserBehaviorTracker:
    """用户行为追踪器"""

    def __init__(self):
        # 页面浏览记录 {session_id: [page_view, ...]}
        self._page_views = defaultdict(list)

        # 用户会话 {session_id: session_info}
        self._sessions = {}

        # 点击事件 {event_type: [event, ...]}
        self._click_events = defaultdict(list)

        # 滚动深度 {page_url: max_scroll_depth}
        self._scroll_depth = defaultdict(int)

        # 会话ID计数器
        self._session_counter = 0

    def create_session(self, user_id: Optional[int] = None,
                       user_agent: str = '', ip_address: str = '') -> str:
        """
        创建用户会话
        
        Args:
            user_id: 用户ID（可选）
            user_agent: 浏览器UA
            ip_address: IP地址
            
        Returns:
            会话ID
        """
        self._session_counter += 1
        session_id = f"sess_{self._session_counter}_{int(datetime.now().timestamp())}"

        now = datetime.now()
        self._sessions[session_id] = {
            'session_id': session_id,
            'user_id': user_id,
            'user_agent': user_agent,
            'ip_address': ip_address,
            'start_time': now,
            'last_activity': now,
            'page_views': 0,
            'total_duration': 0,
            'bounce': True,  # 是否跳出（只访问一个页面）
        }

        logger.info(f"Created session {session_id} for user {user_id}")
        return session_id

    def track_page_view(self, session_id: str, page_url: str,
                        page_title: str = '', referrer: str = ''):
        """
        追踪页面浏览
        
        Args:
            session_id: 会话ID
            page_url: 页面URL
            page_title: 页面标题
            referrer: 来源页面
        """
        if session_id not in self._sessions:
            logger.warning(f"Session {session_id} not found")
            return

        now = datetime.now()
        session = self._sessions[session_id]

        # 记录页面浏览
        page_view = {
            'url': page_url,
            'title': page_title,
            'referrer': referrer,
            'timestamp': now,
            'duration': 0,  # 将在下一个页面浏览时计算
        }

        self._page_views[session_id].append(page_view)
        session['page_views'] += 1
        session['last_activity'] = now

        # 如果不是第一个页面，则不是跳出
        if session['page_views'] > 1:
            session['bounce'] = False

        # 计算上一个页面的停留时间
        if len(self._page_views[session_id]) > 1:
            previous_view = self._page_views[session_id][-2]
            duration = (now - previous_view['timestamp']).total_seconds()
            previous_view['duration'] = duration
            session['total_duration'] += duration

        logger.debug(f"Page view tracked: {page_url} in session {session_id}")

    def track_click_event(self, session_id: str, event_type: str,
                          element_selector: str = '', page_url: str = '',
                          metadata: Dict = None):
        """
        追踪点击事件
        
        Args:
            session_id: 会话ID
            event_type: 事件类型（如：button_click, link_click, cta_click）
            element_selector: CSS选择器
            page_url: 页面URL
            metadata: 额外元数据
        """
        now = datetime.now()
        event = {
            'session_id': session_id,
            'event_type': event_type,
            'element_selector': element_selector,
            'page_url': page_url,
            'metadata': metadata or {},
            'timestamp': now,
        }

        self._click_events[event_type].append(event)

        if session_id in self._sessions:
            self._sessions[session_id]['last_activity'] = now

    def track_scroll_depth(self, page_url: str, scroll_percentage: int):
        """
        追踪滚动深度
        
        Args:
            page_url: 页面URL
            scroll_percentage: 滚动百分比（0-100）
        """
        current_max = self._scroll_depth[page_url]
        if scroll_percentage > current_max:
            self._scroll_depth[page_url] = scroll_percentage

    def end_session(self, session_id: str):
        """
        结束会话
        
        Args:
            session_id: 会话ID
        """
        if session_id not in self._sessions:
            return

        session = self._sessions[session_id]
        now = datetime.now()

        # 计算最后一个页面的停留时间
        if self._page_views[session_id]:
            last_view = self._page_views[session_id][-1]
            duration = (now - last_view['timestamp']).total_seconds()
            last_view['duration'] = duration
            session['total_duration'] += duration

        session['end_time'] = now
        logger.info(f"Session {session_id} ended. Duration: {session['total_duration']}s")

    def get_session_stats(self, session_id: str) -> Dict:
        """
        获取会话统计
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话统计数据
        """
        if session_id not in self._sessions:
            return {}

        session = self._sessions[session_id]
        page_views = self._page_views.get(session_id, [])

        return {
            'session_id': session_id,
            'user_id': session.get('user_id'),
            'start_time': session['start_time'].isoformat(),
            'end_time': session.get('end_time', '').isoformat() if session.get('end_time') else None,
            'duration': session['total_duration'],
            'page_views': session['page_views'],
            'pages_visited': [pv['url'] for pv in page_views],
            'bounce': session['bounce'],
            'referrer': page_views[0]['referrer'] if page_views else '',
        }

    def get_page_analytics(self, page_url: str,
                           period: str = 'all') -> Dict:
        """
        获取页面分析数据
        
        Args:
            page_url: 页面URL
            period: 时间周期（all/day/week/month）
            
        Returns:
            页面统计数据
        """
        total_views = 0
        total_duration = 0
        unique_sessions = set()

        cutoff = None
        now = datetime.now()

        if period == 'day':
            cutoff = now - timedelta(days=1)
        elif period == 'week':
            cutoff = now - timedelta(days=7)
        elif period == 'month':
            cutoff = now - timedelta(days=30)

        for session_id, views in self._page_views.items():
            for view in views:
                if view['url'] != page_url:
                    continue

                if cutoff and view['timestamp'] < cutoff:
                    continue

                total_views += 1
                total_duration += view['duration']
                unique_sessions.add(session_id)

        avg_duration = total_duration / total_views if total_views > 0 else 0

        return {
            'page_url': page_url,
            'total_views': total_views,
            'unique_visitors': len(unique_sessions),
            'avg_duration': round(avg_duration, 2),
            'total_duration': round(total_duration, 2),
            'period': period,
        }

    def get_user_journey(self, session_id: str) -> List[Dict]:
        """
        获取用户旅程（页面浏览路径）
        
        Args:
            session_id: 会话ID
            
        Returns:
            页面浏览序列
        """
        views = self._page_views.get(session_id, [])
        journey = []

        for i, view in enumerate(views):
            journey.append({
                'step': i + 1,
                'url': view['url'],
                'title': view['title'],
                'timestamp': view['timestamp'].isoformat(),
                'duration': view['duration'],
                'referrer': view['referrer'],
            })

        return journey

    def get_heatmap_data(self, page_url: str) -> Dict:
        """
        获取页面热力图数据
        
        Args:
            page_url: 页面URL
            
        Returns:
            热力图数据（点击分布、滚动深度）
        """
        # 获取该页面的所有点击事件
        clicks = []
        for event_type, events in self._click_events.items():
            for event in events:
                if event['page_url'] == page_url:
                    clicks.append(event)

        # 获取滚动深度
        max_scroll = self._scroll_depth.get(page_url, 0)

        return {
            'page_url': page_url,
            'total_clicks': len(clicks),
            'click_distribution': clicks[:50],  # 最近50个点击
            'max_scroll_depth': max_scroll,
        }

    def cleanup_old_sessions(self, days: int = 30):
        """
        清理旧会话数据
        
        Args:
            days: 保留天数
        """
        cutoff = datetime.now() - timedelta(days=days)

        sessions_to_remove = []
        for session_id, session in self._sessions.items():
            if session['start_time'] < cutoff:
                sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            del self._sessions[session_id]
            if session_id in self._page_views:
                del self._page_views[session_id]

        logger.info(f"Cleaned up {len(sessions_to_remove)} old sessions")


# 全局实例
behavior_tracker = UserBehaviorTracker()
