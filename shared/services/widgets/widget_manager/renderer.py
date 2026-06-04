"""
Widget渲染器
负责将Widget实例渲染为HTML
"""

from typing import Dict


class WidgetRenderer:
    """Widget HTML渲染器"""

    def render_search(self, config: Dict, title: str = '') -> str:
        """渲染搜索小部件"""
        title = title or config.get('title', '搜索')
        placeholder = config.get('placeholder', '搜索...')

        return f'''
        <div class="widget widget-search">
            {f'<h3 class="widget-title">{title}</h3>' if title else ''}
            <form class="search-form" action="/search" method="get">
                <input type="text" name="q" placeholder="{placeholder}" class="search-input w-full px-4 py-2 border rounded-lg">
                <button type="submit" class="search-button mt-2 w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700">🔍 搜索</button>
            </form>
        </div>
        '''

    def render_recent_posts(self, config: Dict, title: str = '') -> str:
        """渲染最新文章小部件(占位符)"""
        title = title or config.get('title', '最新文章')

        return f'''
        <div class="widget widget-recent-posts">
            {f'<h3 class="widget-title">{title}</h3>' if title else ''}
            <ul class="recent-posts-list space-y-2">
                <li class="text-sm text-gray-600">加载中...</li>
            </ul>
        </div>
        '''

    def render_categories(self, config: Dict, title: str = '') -> str:
        """渲染分类小部件(占位符)"""
        title = title or config.get('title', '分类目录')

        return f'''
        <div class="widget widget-categories">
            {f'<h3 class="widget-title">{title}</h3>' if title else ''}
            <ul class="categories-list space-y-1">
                <li class="text-sm"><a href="#" class="hover:text-blue-600">加载中...</a></li>
            </ul>
        </div>
        '''

    def render_tags(self, config: Dict, title: str = '') -> str:
        """渲染标签云小部件"""
        title = title or config.get('title', '标签云')
        display_type = config.get('display_type', 'cloud')

        if display_type == 'cloud':
            return f'''
            <div class="widget widget-tags">
                {f'<h3 class="widget-title">{title}</h3>' if title else ''}
                <div class="tags-cloud flex flex-wrap gap-2">
                    <span class="text-xs bg-gray-200 px-2 py-1 rounded">加载中...</span>
                </div>
            </div>
            '''
        else:
            return f'''
            <div class="widget widget-tags">
                {f'<h3 class="widget-title">{title}</h3>' if title else ''}
                <ul class="tags-list space-y-1">
                    <li class="text-sm"><a href="#" class="hover:text-blue-600">加载中...</a></li>
                </ul>
            </div>
            '''

    def render_archives(self, config: Dict, title: str = '') -> str:
        """渲染归档小部件(占位符)"""
        title = title or config.get('title', '文章归档')

        return f'''
        <div class="widget widget-archives">
            {f'<h3 class="widget-title">{title}</h3>' if title else ''}
            <ul class="archives-list space-y-1">
                <li class="text-sm"><a href="#" class="hover:text-blue-600">加载中...</a></li>
            </ul>
        </div>
        '''

    def render_social_links(self, config: Dict, title: str = '') -> str:
        """渲染社交链接小部件"""
        title = title or config.get('title', '关注我们')
        platforms = config.get('platforms', [])

        social_icons = {
            'weibo': '📱 微博',
            'wechat': '💬 微信',
            'twitter': '🐦 Twitter',
            'facebook': '👥 Facebook',
            'github': '🐙 GitHub'
        }

        links_html = ''.join([
            f'<a href="#" class="inline-block mr-2 mb-2 px-3 py-1 bg-gray-200 rounded hover:bg-gray-300 text-sm">{social_icons.get(p, p)}</a>'
            for p in platforms
        ])

        return f'''
        <div class="widget widget-social">
            {f'<h3 class="widget-title">{title}</h3>' if title else ''}
            <div class="social-links">
                {links_html or '<span class="text-sm text-gray-500">未配置社交平台</span>'}
            </div>
        </div>
        '''

    def render_html(self, config: Dict, title: str = '') -> str:
        """渲染自定义HTML小部件"""
        html_content = config.get('html_content', '')

        return f'''
        <div class="widget widget-html">
            {f'<h3 class="widget-title">{title}</h3>' if title else ''}
            <div class="html-content prose prose-sm max-w-none">
                {html_content}
            </div>
        </div>
        '''

    def render_advertisement(self, config: Dict, title: str = '') -> str:
        """渲染广告小部件"""
        content = config.get('content', '')
        link = config.get('link', '')
        image = config.get('image', '')

        if image:
            ad_content = f'<img src="{image}" alt="Advertisement" class="w-full rounded-lg">'
        else:
            ad_content = content

        if link:
            ad_content = f'<a href="{link}" target="_blank" rel="noopener noreferrer">{ad_content}</a>'

        return f'''
        <div class="widget widget-advertisement">
            {f'<h3 class="widget-title">{title}</h3>' if title else ''}
            <div class="ad-content">
                {ad_content or '<div class="p-4 bg-gray-100 rounded text-center text-sm text-gray-500">广告位</div>'}
            </div>
        </div>
        '''

    def render_menu(self, config: Dict, title: str = '') -> str:
        """渲染菜单小部件(占位符)"""
        title = title or config.get('title', '菜单')

        return f'''
        <div class="widget widget-menu">
            {f'<h3 class="widget-title">{title}</h3>' if title else ''}
            <nav class="menu-nav">
                <ul class="space-y-1">
                    <li class="text-sm"><a href="#" class="hover:text-blue-600">加载中...</a></li>
                </ul>
            </nav>
        </div>
        '''

    def render_widget(self, widget_type: str, config: Dict, title: str = '') -> str:
        """
        根据类型渲染Widget
        
        Args:
            widget_type: Widget类型
            config: 配置字典
            title: 标题
            
        Returns:
            HTML字符串
        """
        renderers = {
            'search': self.render_search,
            'recent_posts': self.render_recent_posts,
            'categories': self.render_categories,
            'tags': self.render_tags,
            'archives': self.render_archives,
            'social_links': self.render_social_links,
            'html': self.render_html,
            'advertisement': self.render_advertisement,
            'menu': self.render_menu,
        }

        renderer = renderers.get(widget_type)
        if renderer:
            return renderer(config, title)

        return f'<div class="widget"><h3>{title}</h3><p>Widget type: {widget_type} (未实现)</p></div>'
