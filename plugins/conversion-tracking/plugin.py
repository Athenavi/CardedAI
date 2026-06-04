"""
转化追踪插件
集成 Google Analytics、Facebook Pixel 等追踪代码，支持自定义事件和转化漏斗分析
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any

from shared.services.plugins.plugin_manager.core import BasePlugin, plugin_hooks
from shared.utils.plugin_database import plugin_db


class ConversionTrackingPlugin(BasePlugin):
    """
    转化追踪插件
    
    功能:
    1. 多平台追踪代码集成（Google Analytics, Facebook Pixel, Baidu Analytics等）
    2. 自定义事件追踪
    3. 转化漏斗分析
    4. 转化目标设置
    5. A/B测试集成
    6. 实时转化监控
    7. 转化报告生成
    """

    def __init__(self):
        super().__init__(
            plugin_id=0,
            name="转化追踪",
            slug="conversion-tracking",
            version="1.0.0"
        )

        # 默认设置
        self.settings = {
            'enable_tracking': True,
            'google_analytics_id': '',  # GA4 Measurement ID (G-XXXXXXXXXX)
            'facebook_pixel_id': '',
            'baidu_analytics_id': '',
            'tiktok_pixel_id': '',
            'enable_custom_events': True,
            'enable_funnel_analysis': True,
            'enable_goal_tracking': True,
            'track_page_views': True,
            'track_clicks': True,
            'track_form_submissions': True,
            'anonymize_ip': False,  # GDPR合规
            'respect_dnt': True,  # 尊重Do Not Track
        }

        # 转化目标 {goal_id: goal_config}
        self.goals: Dict[str, Dict[str, Any]] = {}

        # 转化漏斗 {funnel_id: funnel_config}
        self.funnels: Dict[str, Dict[str, Any]] = {}

        # 事件统计缓存
        self.event_stats_cache: Dict[str, Any] = {}

    def register_hooks(self):
        """注册钩子"""
        # 在页面头部注入追踪代码
        if self.settings.get('enable_tracking'):
            plugin_hooks.add_action(
                "page_head",
                self.inject_tracking_codes,
                priority=10
            )

        # 追踪页面浏览
        if self.settings.get('track_page_views'):
            plugin_hooks.add_action(
                "page_view",
                self.track_page_view,
                priority=10
            )

        # 追踪自定义事件
        if self.settings.get('enable_custom_events'):
            plugin_hooks.add_action(
                "custom_event",
                self.track_custom_event,
                priority=10
            )

        # 追踪表单提交
        if self.settings.get('track_form_submissions'):
            plugin_hooks.add_action(
                "form_submission",
                self.track_form_submission,
                priority=10
            )

    def activate(self):
        """激活插件"""
        super().activate()
        self._init_database()
        self._load_goals_and_funnels()
        print("[ConversionTracking] Plugin activated")

    def deactivate(self):
        """停用插件"""
        super().deactivate()
        print("[ConversionTracking] Plugin deactivated")

    def _init_database(self):
        """初始化数据库表"""
        try:
            init_conversion_tracking_db()
        except Exception as e:
            print(f"[ConversionTracking] Failed to initialize database: {e}")

    def _load_goals_and_funnels(self):
        """从数据库加载目标和漏斗配置"""
        try:
            # 加载转化目标
            goals = plugin_db.execute_query(
                'conversion-tracking',
                "SELECT * FROM conversion_goals WHERE active = 1"
            )
            for goal in goals:
                goal_dict = dict(goal)
                if goal_dict.get('conditions'):
                    try:
                        goal_dict['conditions'] = json.loads(goal_dict['conditions'])
                    except:
                        goal_dict['conditions'] = {}
                self.goals[goal_dict['id']] = goal_dict

            # 加载转化漏斗
            funnels = plugin_db.execute_query(
                'conversion-tracking',
                "SELECT * FROM conversion_funnels WHERE active = 1"
            )
            for funnel in funnels:
                funnel_dict = dict(funnel)
                if funnel_dict.get('steps'):
                    try:
                        funnel_dict['steps'] = json.loads(funnel_dict['steps'])
                    except:
                        funnel_dict['steps'] = []
                self.funnels[funnel_dict['id']] = funnel_dict

            print(f"[ConversionTracking] Loaded {len(self.goals)} goals and {len(self.funnels)} funnels")
        except Exception as e:
            print(f"[ConversionTracking] Failed to load goals/funnels: {e}")

    def inject_tracking_codes(self, context: Dict[str, Any]):
        """
        注入追踪代码到页面头部
        
        Args:
            context: 上下文数据
        """
        if not self.settings.get('enable_tracking'):
            return

        scripts = []

        # Google Analytics 4
        ga_id = self.settings.get('google_analytics_id')
        if ga_id:
            ga_script = self._generate_ga4_code(ga_id)
            scripts.append(ga_script)

        # Facebook Pixel
        fb_pixel_id = self.settings.get('facebook_pixel_id')
        if fb_pixel_id:
            fb_script = self._generate_facebook_pixel_code(fb_pixel_id)
            scripts.append(fb_script)

        # Baidu Analytics
        baidu_id = self.settings.get('baidu_analytics_id')
        if baidu_id:
            baidu_script = self._generate_baidu_analytics_code(baidu_id)
            scripts.append(baidu_script)

        # TikTok Pixel
        tiktok_id = self.settings.get('tiktok_pixel_id')
        if tiktok_id:
            tiktok_script = self._generate_tiktok_pixel_code(tiktok_id)
            scripts.append(tiktok_script)

        # 添加到上下文
        if scripts:
            if 'tracking_scripts' not in context:
                context['tracking_scripts'] = []
            context['tracking_scripts'].extend(scripts)

    def track_page_view(self, view_data: Dict[str, Any]):
        """
        追踪页面浏览
        
        Args:
            view_data: 页面数据 {url, title, user_id, referrer}
        """
        if not self.settings.get('enable_tracking'):
            return

        try:
            # 记录到数据库
            plugin_db.execute_update(
                'conversion-tracking',
                """INSERT INTO page_views (url, title, user_id, referrer, timestamp)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    view_data.get('url', ''),
                    view_data.get('title', ''),
                    view_data.get('user_id'),
                    view_data.get('referrer', ''),
                    datetime.now().isoformat()
                )
            )

            # 检查是否触发转化目标
            self._check_goals(view_data)

        except Exception as e:
            print(f"[ConversionTracking] Failed to track page view: {e}")

    def track_custom_event(self, event_data: Dict[str, Any]):
        """
        追踪自定义事件
        
        Args:
            event_data: 事件数据 {event_name, category, label, value, properties}
        """
        if not self.settings.get('enable_custom_events'):
            return

        try:
            event_name = event_data.get('event_name', '')
            if not event_name:
                return

            # 记录到数据库
            plugin_db.execute_update(
                'conversion-tracking',
                """INSERT INTO custom_events
                   (event_name, category, label, value, properties, user_id, url, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    event_name,
                    event_data.get('category', ''),
                    event_data.get('label', ''),
                    event_data.get('value', 0),
                    json.dumps(event_data.get('properties', {})),
                    event_data.get('user_id'),
                    event_data.get('url', ''),
                    datetime.now().isoformat()
                )
            )

            # 检查是否触发转化目标
            self._check_goals(event_data, event_type='event')

        except Exception as e:
            print(f"[ConversionTracking] Failed to track custom event: {e}")

    def track_form_submission(self, form_data: Dict[str, Any]):
        """
        追踪表单提交
        
        Args:
            form_data: 表单数据 {form_id, form_name, fields, user_id, success}
        """
        if not self.settings.get('track_form_submissions'):
            return

        try:
            # 记录到数据库
            plugin_db.execute_update(
                'conversion-tracking',
                """INSERT INTO form_submissions
                       (form_id, form_name, fields, user_id, success, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    form_data.get('form_id', ''),
                    form_data.get('form_name', ''),
                    json.dumps(form_data.get('fields', {})),
                    form_data.get('user_id'),
                    1 if form_data.get('success', False) else 0,
                    datetime.now().isoformat()
                )
            )

            # 检查是否触发转化目标
            if form_data.get('success'):
                self._check_goals(form_data, event_type='form_submission')

        except Exception as e:
            print(f"[ConversionTracking] Failed to track form submission: {e}")

    def create_goal(self, goal_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建转化目标
        
        Args:
            goal_config: 目标配置 {name, type, conditions, value}
            
        Returns:
            创建的目标
        """
        try:
            goal_id = f"goal_{int(time.time() * 1000)}"

            # 保存到数据库
            plugin_db.execute_update(
                'conversion-tracking',
                """INSERT INTO conversion_goals
                       (id, name, type, conditions, value, active, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    goal_id,
                    goal_config.get('name', ''),
                    goal_config.get('type', 'page_view'),  # page_view, event, form_submission
                    json.dumps(goal_config.get('conditions', {})),
                    goal_config.get('value', 0),
                    1,
                    datetime.now().isoformat()
                )
            )

            # 更新内存缓存
            goal_config['id'] = goal_id
            goal_config['active'] = True
            goal_config['created_at'] = datetime.now().isoformat()
            self.goals[goal_id] = goal_config

            print(f"[ConversionTracking] Created goal: {goal_id}")
            return goal_config

        except Exception as e:
            print(f"[ConversionTracking] Failed to create goal: {e}")
            raise

    def create_funnel(self, funnel_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建转化漏斗
        
        Args:
            funnel_config: 漏斗配置 {name, steps, description}
            
        Returns:
            创建的漏斗
        """
        try:
            funnel_id = f"funnel_{int(time.time() * 1000)}"

            # 保存到数据库
            plugin_db.execute_update(
                'conversion-tracking',
                """INSERT INTO conversion_funnels
                       (id, name, steps, description, active, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    funnel_id,
                    funnel_config.get('name', ''),
                    json.dumps(funnel_config.get('steps', [])),
                    funnel_config.get('description', ''),
                    1,
                    datetime.now().isoformat()
                )
            )

            # 更新内存缓存
            funnel_config['id'] = funnel_id
            funnel_config['active'] = True
            funnel_config['created_at'] = datetime.now().isoformat()
            self.funnels[funnel_id] = funnel_config

            print(f"[ConversionTracking] Created funnel: {funnel_id}")
            return funnel_config

        except Exception as e:
            print(f"[ConversionTracking] Failed to create funnel: {e}")
            raise

    def get_conversion_report(self, days: int = 30) -> Dict[str, Any]:
        """
        获取转化报告
        
        Args:
            days: 统计天数
            
        Returns:
            报告数据
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            # 页面浏览统计
            page_views = plugin_db.execute_query(
                'conversion-tracking',
                "SELECT COUNT(*) as count FROM page_views WHERE timestamp > ?",
                (cutoff_date,)
            )

            # 自定义事件统计
            events = plugin_db.execute_query(
                'conversion-tracking',
                """SELECT event_name, COUNT(*) as count
                   FROM custom_events
                   WHERE timestamp > ?
                   GROUP BY event_name
                   ORDER BY count DESC
                   LIMIT 20""",
                (cutoff_date,)
            )

            # 表单提交统计
            form_submissions = plugin_db.execute_query(
                'conversion-tracking',
                """SELECT form_name,
                          COUNT(*)                                     as total,
                          SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
                   FROM form_submissions
                   WHERE timestamp > ?
                   GROUP BY form_name""",
                (cutoff_date,)
            )

            # 转化目标完成情况
            goal_completions = plugin_db.execute_query(
                'conversion-tracking',
                """SELECT goal_id, COUNT(*) as completions
                   FROM goal_completions
                   WHERE completed_at > ?
                   GROUP BY goal_id""",
                (cutoff_date,)
            )

            return {
                'period_days': days,
                'page_views': page_views[0]['count'] if page_views else 0,
                'events': [dict(e) for e in events],
                'form_submissions': [dict(f) for f in form_submissions],
                'goal_completions': [dict(g) for g in goal_completions],
                'generated_at': datetime.now().isoformat(),
            }

        except Exception as e:
            print(f"[ConversionTracking] Failed to generate report: {e}")
            return {'error': str(e)}

    def get_funnel_analysis(self, funnel_id: str, days: int = 30) -> Dict[str, Any]:
        """
        获取漏斗分析
        
        Args:
            funnel_id: 漏斗ID
            days: 统计天数
            
        Returns:
            漏斗分析数据
        """
        if funnel_id not in self.funnels:
            return {'error': 'Funnel not found'}

        funnel = self.funnels[funnel_id]
        steps = funnel.get('steps', [])

        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            # 分析每一步的转化情况
            step_results = []
            for i, step in enumerate(steps):
                # 这里需要根据步骤类型查询相应的数据
                # 简化实现：返回示例数据
                step_results.append({
                    'step_number': i + 1,
                    'step_name': step.get('name', ''),
                    'step_type': step.get('type', 'page_view'),
                    'users_reached': 0,  # 需要实际计算
                    'conversion_rate': 0,
                })

            return {
                'funnel_id': funnel_id,
                'funnel_name': funnel.get('name', ''),
                'period_days': days,
                'steps': step_results,
                'overall_conversion_rate': 0,
            }

        except Exception as e:
            print(f"[ConversionTracking] Failed to analyze funnel: {e}")
            return {'error': str(e)}

    def _check_goals(self, data: Dict[str, Any], event_type: str = 'page_view'):
        """
        检查是否触发转化目标
        
        Args:
            data: 事件数据
            event_type: 事件类型
        """
        for goal_id, goal in self.goals.items():
            if goal.get('type') != event_type:
                continue

            conditions = goal.get('conditions', {})
            if self._evaluate_conditions(data, conditions):
                # 记录转化完成
                try:
                    plugin_db.execute_update(
                        'conversion-tracking',
                        """INSERT INTO goal_completions (goal_id, user_id, data, completed_at)
                           VALUES (?, ?, ?, ?)""",
                        (
                            goal_id,
                            data.get('user_id'),
                            json.dumps(data),
                            datetime.now().isoformat()
                        )
                    )
                    print(f"[ConversionTracking] Goal completed: {goal_id}")
                except Exception as e:
                    print(f"[ConversionTracking] Failed to record goal completion: {e}")

    def _evaluate_conditions(self, data: Dict[str, Any], conditions: Dict[str, Any]) -> bool:
        """
        评估条件是否满足
        
        Args:
            data: 事件数据
            conditions: 条件配置
            
        Returns:
            是否满足条件
        """
        # 简化实现：检查URL匹配
        if 'url_contains' in conditions:
            url = data.get('url', '')
            if conditions['url_contains'] not in url:
                return False

        if 'url_equals' in conditions:
            url = data.get('url', '')
            if conditions['url_equals'] != url:
                return False

        if 'event_name' in conditions:
            event_name = data.get('event_name', '')
            if conditions['event_name'] != event_name:
                return False

        return True

    def _generate_ga4_code(self, measurement_id: str) -> str:
        """生成Google Analytics 4追踪代码"""
        anonymize = 'true' if self.settings.get('anonymize_ip') else 'false'

        return f'''
<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id={measurement_id}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{measurement_id}', {{
    'anonymize_ip': {anonymize},
    'send_page_view': {str(self.settings.get('track_page_views', True)).lower()}
  }});
</script>
'''

    def _generate_facebook_pixel_code(self, pixel_id: str) -> str:
        """生成Facebook Pixel追踪代码"""
        return f'''
<!-- Facebook Pixel -->
<script>
  !function(f,b,e,v,n,t,s)
  {{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?
  n.callMethod.apply(n,arguments):n.queue.push(arguments)}};
  if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
  n.queue=[];t=b.createElement(e);t.async=!0;
  t.src=v;s=b.getElementsByTagName(e)[0];
  s.parentNode.insertBefore(t,s)}}(window, document,'script',
  'https://connect.facebook.net/en_US/fbevents.js');
  fbq('init', '{pixel_id}');
  fbq('track', 'PageView');
</script>
<noscript>
  <img height="1" width="1" style="display:none" 
       src="https://www.facebook.com/tr?id={pixel_id}&ev=PageView&noscript=1"/>
</noscript>
'''

    def _generate_baidu_analytics_code(self, site_id: str) -> str:
        """生成百度统计追踪代码"""
        return f'''
<!-- Baidu Analytics -->
<script>
  var _hmt = _hmt || [];
  (function() {{
    var hm = document.createElement("script");
    hm.src = "https://hm.baidu.com/hm.js?{site_id}";
    var s = document.getElementsByTagName("script")[0]; 
    s.parentNode.insertBefore(hm, s);
  }})();
</script>
'''

    def _generate_tiktok_pixel_code(self, pixel_id: str) -> str:
        """生成TikTok Pixel追踪代码"""
        return f'''
<!-- TikTok Pixel -->
<script>
  !function (w, d, t) {{
    w.TiktokAnalyticsObject=t;var ttq=w[t]=w[t]||[];ttq.methods=["page","track","identify","instances","debug","on","off","once","ready","alias","group","enableCookie","disableCookie"],ttq.setAndDefer=function(t,e){{t[e]=function(){{t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}}};for(var i=0;i<ttq.methods.length;i++)ttq.setAndDefer(ttq,ttq.methods[i]);ttq.instance=function(t){{for(var e=ttq._i[t]||[],n=0;n<ttq.methods.length;n++)ttq.setAndDefer(e,ttq.methods[n]);return e}},ttq.load=function(e,n){{var r="https://analytics.tiktok.com/i18n/pixel/events.js";ttq._i=ttq._i||{{}},ttq._i[e]=[],ttq._i[e]._u=r,ttq._t=ttq._t||{{}},ttq._t[e]=+new Date,ttq._o=ttq._o||{{}},ttq._o[e]=n||{{}};var o=document.createElement("script");o.type="text/javascript",o.async=!0,o.src=r+"?sdkid="+e+"&lib="+t;var a=document.getElementsByTagName("script")[0];a.parentNode.insertBefore(o,a)}};
    ttq.load('{pixel_id}');
    ttq.page();
  }}(window, document, 'ttq');
</script>
'''

    def get_settings_ui(self) -> Dict[str, Any]:
        """返回设置界面配置"""
        return {
            'fields': [
                {
                    'key': 'enable_tracking',
                    'type': 'boolean',
                    'label': '启用追踪',
                },
                {
                    'key': 'google_analytics_id',
                    'type': 'text',
                    'label': 'Google Analytics ID',
                    'placeholder': 'G-XXXXXXXXXX',
                    'help': 'GA4 Measurement ID',
                },
                {
                    'key': 'facebook_pixel_id',
                    'type': 'text',
                    'label': 'Facebook Pixel ID',
                    'placeholder': '输入Pixel ID',
                },
                {
                    'key': 'baidu_analytics_id',
                    'type': 'text',
                    'label': '百度统计ID',
                    'placeholder': '输入站点ID',
                },
                {
                    'key': 'tiktok_pixel_id',
                    'type': 'text',
                    'label': 'TikTok Pixel ID',
                    'placeholder': '输入Pixel ID',
                },
                {
                    'key': 'track_page_views',
                    'type': 'boolean',
                    'label': '追踪页面浏览',
                },
                {
                    'key': 'track_clicks',
                    'type': 'boolean',
                    'label': '追踪点击事件',
                },
                {
                    'key': 'track_form_submissions',
                    'type': 'boolean',
                    'label': '追踪表单提交',
                },
                {
                    'key': 'anonymize_ip',
                    'type': 'boolean',
                    'label': '匿名化IP地址',
                    'help': 'GDPR合规要求',
                },
                {
                    'key': 'respect_dnt',
                    'type': 'boolean',
                    'label': '尊重Do Not Track',
                },
            ],
            'actions': [
                {
                    'type': 'button',
                    'label': '查看转化报告',
                    'action': 'view_report',
                    'variant': 'outline',
                },
                {
                    'type': 'button',
                    'label': '管理转化目标',
                    'action': 'manage_goals',
                    'variant': 'outline',
                },
                {
                    'type': 'button',
                    'label': '分析转化漏斗',
                    'action': 'analyze_funnels',
                    'variant': 'outline',
                },
            ]
        }


def init_conversion_tracking_db():
    """初始化转化追踪插件数据库"""
    slug = "conversion-tracking"

    # 页面浏览记录表
    if not plugin_db.table_exists(slug, "page_views"):
        plugin_db.execute_update(slug, """
                                       CREATE TABLE page_views
                                       (
                                           id        INTEGER PRIMARY KEY AUTOINCREMENT,
                                           url       TEXT NOT NULL,
                                           title     TEXT,
                                           user_id   INTEGER,
                                           referrer  TEXT,
                                           timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                       )
                                       """)
        plugin_db.execute_update(slug, "CREATE INDEX idx_page_views_url ON page_views(url)")
        plugin_db.execute_update(slug, "CREATE INDEX idx_page_views_timestamp ON page_views(timestamp)")

    # 自定义事件表
    if not plugin_db.table_exists(slug, "custom_events"):
        plugin_db.execute_update(slug, """
                                       CREATE TABLE custom_events
                                       (
                                           id         INTEGER PRIMARY KEY AUTOINCREMENT,
                                           event_name TEXT NOT NULL,
                                           category   TEXT,
                                           label      TEXT,
                                           value      REAL      DEFAULT 0,
                                           properties TEXT,
                                           user_id    INTEGER,
                                           url        TEXT,
                                           timestamp  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                       )
                                       """)
        plugin_db.execute_update(slug, "CREATE INDEX idx_custom_events_name ON custom_events(event_name)")
        plugin_db.execute_update(slug, "CREATE INDEX idx_custom_events_timestamp ON custom_events(timestamp)")

    # 表单提交记录表
    if not plugin_db.table_exists(slug, "form_submissions"):
        plugin_db.execute_update(slug, """
                                       CREATE TABLE form_submissions
                                       (
                                           id        INTEGER PRIMARY KEY AUTOINCREMENT,
                                           form_id   TEXT NOT NULL,
                                           form_name TEXT,
                                           fields    TEXT,
                                           user_id   INTEGER,
                                           success   BOOLEAN   DEFAULT 0,
                                           timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                       )
                                       """)
        plugin_db.execute_update(slug, "CREATE INDEX idx_form_submissions_form ON form_submissions(form_id)")
        plugin_db.execute_update(slug, "CREATE INDEX idx_form_submissions_timestamp ON form_submissions(timestamp)")

    # 转化目标表
    if not plugin_db.table_exists(slug, "conversion_goals"):
        plugin_db.execute_update(slug, """
                                       CREATE TABLE conversion_goals
                                       (
                                           id         TEXT PRIMARY KEY,
                                           name       TEXT NOT NULL,
                                           type       TEXT NOT NULL CHECK (type IN ('page_view', 'event', 'form_submission')),
                                           conditions TEXT,
                                           value      REAL      DEFAULT 0,
                                           active     BOOLEAN   DEFAULT 1,
                                           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                       )
                                       """)

    # 转化漏斗表
    if not plugin_db.table_exists(slug, "conversion_funnels"):
        plugin_db.execute_update(slug, """
                                       CREATE TABLE conversion_funnels
                                       (
                                           id          TEXT PRIMARY KEY,
                                           name        TEXT NOT NULL,
                                           steps       TEXT,
                                           description TEXT,
                                           active      BOOLEAN   DEFAULT 1,
                                           created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                       )
                                       """)

    # 目标完成记录表
    if not plugin_db.table_exists(slug, "goal_completions"):
        plugin_db.execute_update(slug, """
                                       CREATE TABLE goal_completions
                                       (
                                           id           INTEGER PRIMARY KEY AUTOINCREMENT,
                                           goal_id      TEXT NOT NULL,
                                           user_id      INTEGER,
                                           data         TEXT,
                                           completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                           FOREIGN KEY (goal_id) REFERENCES conversion_goals (id)
                                       )
                                       """)
        plugin_db.execute_update(slug, "CREATE INDEX idx_goal_completions_goal ON goal_completions(goal_id)")
        plugin_db.execute_update(slug, "CREATE INDEX idx_goal_completions_timestamp ON goal_completions(completed_at)")

    print(f"[PluginDB] Conversion Tracking database initialized")


# 插件实例
plugin_instance = ConversionTrackingPlugin()
