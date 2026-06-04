"""
综合社交媒体插件
整合社交分享、自动发布、社交登录、社交证明、Instagram Feed等功能

功能模块:
1. 社交分享按钮 - 多平台支持、自定义样式
2. 自动分享 - 文章发布时自动分享到社交平台
3. 社交登录 - 微信、微博、QQ、Twitter等
4. 社交证明 - 显示粉丝数、分享数
5. Instagram Feed - 展示Instagram内容
"""

from typing import Dict, List, Any

from shared.services.plugins.plugin_manager.core import BasePlugin, plugin_hooks


class SocialPlugin(BasePlugin):
    """
    综合社交媒体插件
    
    整合了以下原有插件的功能:
    - social-share: 社交分享
    - social-media-kit: 社交媒体套件
    """

    def __init__(self):
        super().__init__(
            plugin_id=0,
            name="社交媒体中心",
            slug="social",
            version="2.0.0"
        )

        # ==================== 全局设置 ====================
        self.settings = {
            # 分享设置
            'enable_share_buttons': True,
            'share_platforms': ['wechat', 'weibo', 'twitter', 'facebook'],
            'button_style': 'default',
            'button_position': 'bottom',

            # 自动分享设置
            'enable_auto_share': True,
            'auto_share_platforms': ['twitter'],

            # 社交登录设置
            'enable_social_login': True,

            # 社交证明设置
            'show_social_proof': True,

            # Instagram设置
            'instagram_username': '',
        }

        # 分享统计
        self.share_stats = {
            'total_shares': 0,
            'by_platform': {},
        }

    def register_hooks(self):
        """注册钩子"""
        # 文章页面添加分享按钮
        if self.settings.get('enable_share_buttons'):
            plugin_hooks.add_action(
                "article_page_footer",
                self.render_share_buttons,
                priority=10
            )

        # 文章发布时自动分享
        if self.settings.get('enable_auto_share'):
            plugin_hooks.add_action(
                "article_published",
                self.auto_share_article,
                priority=10
            )

    def activate(self):
        """激活插件"""
        super().activate()
        print("[Social] Plugin activated - All social modules initialized")

    def deactivate(self):
        """停用插件"""
        super().deactivate()
        print("[Social] Plugin deactivated")

    # ==================== 社交分享 ====================

    def render_share_buttons(self, context: Dict[str, Any]):
        """渲染分享按钮"""
        if not self.settings.get('enable_share_buttons'):
            return

        article = context.get('article', {})
        if not article:
            return

        platforms = self.settings.get('share_platforms', [])
        style = self.settings.get('button_style', 'default')

        buttons_html = self._generate_share_buttons(article, platforms, style)

        if 'social_buttons' not in context:
            context['social_buttons'] = ''

        context['social_buttons'] += buttons_html

    def _generate_share_buttons(self, article: Dict[str, Any], platforms: List[str], style: str) -> str:
        """生成分享按钮HTML"""
        url = article.get('url', '')
        title = article.get('title', '')

        buttons = []

        platform_configs = {
            'wechat': {'name': '微信', 'icon': '💬', 'color': '#07C160'},
            'weibo': {'name': '微博', 'icon': '🔴', 'color': '#E6162D'},
            'qq': {'name': 'QQ', 'icon': '🐧', 'color': '#12B7F5'},
            'twitter': {'name': 'Twitter', 'icon': '🐦', 'color': '#1DA1F2'},
            'facebook': {'name': 'Facebook', 'icon': '📘', 'color': '#1877F2'},
            'linkedin': {'name': 'LinkedIn', 'icon': '💼', 'color': '#0A66C2'},
            'zhihu': {'name': '知乎', 'icon': '📖', 'color': '#0084FF'},
            'juejin': {'name': '掘金', 'icon': '⚡', 'color': '#1E80FF'},
            'segmentfault': {'name': 'SegmentFault', 'icon': '🔗', 'color': '#009A61'},
            'telegram': {'name': 'Telegram', 'icon': '✈️', 'color': '#0088CC'},
        }

        for platform in platforms:
            config = platform_configs.get(platform, {})
            share_url = self._get_share_url(platform, url, title)

            button_class = f'share-button share-{platform}'
            if style == 'rounded':
                button_class += ' rounded'
            elif style == 'icon-only':
                button_class += ' icon-only'

            buttons.append(f'''
                <a href="{share_url}" 
                   target="_blank" 
                   class="{button_class}"
                   style="background-color: {config.get('color', '#ccc')}"
                   onclick="trackShare('{platform}')">
                    <span class="icon">{config.get('icon', '🔗')}</span>
                    {config.get('name', platform) if style != 'icon-only' else ''}
                </a>
            ''')

        position = self.settings.get('button_position', 'bottom')
        container_class = f'share-buttons-container position-{position}'

        return f'<div class="{container_class}">{"".join(buttons)}</div>'

    def _get_share_url(self, platform: str, url: str, title: str) -> str:
        """获取分享URL"""
        import urllib.parse

        encoded_url = urllib.parse.quote(url, safe='')
        encoded_title = urllib.parse.quote(title, safe='')

        share_urls = {
            'wechat': f'https://api.weixin.qq.com/share?url={encoded_url}',
            'weibo': f'http://service.weibo.com/share/share.php?url={encoded_url}&title={encoded_title}',
            'qq': f'http://connect.qq.com/widget/shareqq/index.html?url={encoded_url}&title={encoded_title}',
            'twitter': f'https://twitter.com/intent/tweet?url={encoded_url}&text={encoded_title}',
            'facebook': f'https://www.facebook.com/sharer/sharer.php?u={encoded_url}',
            'linkedin': f'https://www.linkedin.com/shareArticle?mini=true&url={encoded_url}&title={encoded_title}',
            'zhihu': f'https://zhuanlan.zhihu.com/share?url={encoded_url}&title={encoded_title}',
            'juejin': f'https://juejin.cn/share?url={encoded_url}&title={encoded_title}',
            'segmentfault': f'https://segmentfault.com/share?url={encoded_url}&title={encoded_title}',
            'telegram': f'https://t.me/share/url?url={encoded_url}&text={encoded_title}',
        }

        return share_urls.get(platform, url)

    def auto_share_article(self, article_data: Dict[str, Any]):
        """文章发布时自动分享"""
        if not self.settings.get('enable_auto_share'):
            return

        platforms = self.settings.get('auto_share_platforms', [])
        url = article_data.get('url', '')
        title = article_data.get('title', '')

        for platform in platforms:
            try:
                # 这里应该调用各平台的API进行自动分享
                # 简化实现：仅记录
                print(f"[Social] Auto-shared to {platform}: {title}")
                self._update_share_stats(platform)
            except Exception as e:
                print(f"[Social] Failed to auto-share to {platform}: {e}")

    def _update_share_stats(self, platform: str):
        """更新分享统计"""
        self.share_stats['total_shares'] += 1

        if platform not in self.share_stats['by_platform']:
            self.share_stats['by_platform'][platform] = 0

        self.share_stats['by_platform'][platform] += 1

    # ==================== 社交登录 ====================

    def get_social_login_providers(self) -> List[Dict[str, Any]]:
        """获取可用的社交登录提供商"""
        if not self.settings.get('enable_social_login'):
            return []

        providers = [
            {'id': 'wechat', 'name': '微信', 'icon': '💬', 'enabled': True},
            {'id': 'weibo', 'name': '微博', 'icon': '🔴', 'enabled': True},
            {'id': 'qq', 'name': 'QQ', 'icon': '🐧', 'enabled': True},
            {'id': 'twitter', 'name': 'Twitter', 'icon': '🐦', 'enabled': False},
            {'id': 'facebook', 'name': 'Facebook', 'icon': '📘', 'enabled': False},
        ]

        return providers

    # ==================== 社交证明 ====================

    def get_social_proof_data(self) -> Dict[str, Any]:
        """获取社交证明数据"""
        if not self.settings.get('show_social_proof'):
            return {}

        return {
            'total_shares': self.share_stats['total_shares'],
            'shares_by_platform': self.share_stats['by_platform'],
            'instagram_followers': 0,  # 需要从API获取
            'twitter_followers': 0,
        }

    # ==================== Instagram Feed ====================

    def get_instagram_feed(self, count: int = 6) -> List[Dict[str, Any]]:
        """获取Instagram Feed"""
        username = self.settings.get('instagram_username', '')
        if not username:
            return []

        # 这里应该调用Instagram API
        # 简化实现：返回空列表
        print(f"[Social] Instagram feed requested for @{username}")
        return []

    # ==================== 管理API ====================

    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表板数据"""
        return {
            'share_stats': self.share_stats,
            'social_login_enabled': self.settings.get('enable_social_login', False),
            'auto_share_enabled': self.settings.get('enable_auto_share', False),
            'instagram_username': self.settings.get('instagram_username', ''),
        }

    def get_admin_ui_config(self) -> Dict[str, Any]:
        """获取管理界面配置"""
        return {
            'title': '社交媒体中心',
            'icon': '🌐',
            'sections': [
                {
                    'title': '社交概览',
                    'widgets': [
                        {'type': 'stat', 'label': '总分享数', 'value': self.share_stats['total_shares']},
                        {'type': 'stat', 'label': '分享平台数', 'value': len(self.settings.get('share_platforms', []))},
                    ],
                },
                {
                    'title': '分享设置',
                    'fields': [
                        {
                            'key': 'enable_share_buttons',
                            'label': '启用分享按钮',
                            'type': 'boolean',
                        },
                        {
                            'key': 'share_platforms',
                            'label': '分享平台',
                            'type': 'multiselect',
                            'options': ['wechat', 'weibo', 'qq', 'twitter', 'facebook', 'linkedin', 'zhihu', 'juejin',
                                        'segmentfault', 'telegram'],
                        },
                        {
                            'key': 'button_position',
                            'label': '按钮位置',
                            'type': 'select',
                            'options': ['top', 'bottom', 'floating', 'sidebar'],
                        },
                    ],
                },
                {
                    'title': '自动分享',
                    'fields': [
                        {
                            'key': 'enable_auto_share',
                            'label': '启用自动分享',
                            'type': 'boolean',
                        },
                        {
                            'key': 'auto_share_platforms',
                            'label': '自动分享平台',
                            'type': 'multiselect',
                            'options': ['twitter', 'facebook', 'linkedin'],
                        },
                    ],
                },
                {
                    'title': '其他设置',
                    'fields': [
                        {
                            'key': 'enable_social_login',
                            'label': '启用社交登录',
                            'type': 'boolean',
                        },
                        {
                            'key': 'instagram_username',
                            'label': 'Instagram用户名',
                            'type': 'text',
                        },
                    ],
                },
            ],
        }


# 导出插件实例
plugin = SocialPlugin()
