"""
资源提示服务
提供 preload、prefetch、preconnect 等资源优化功能
"""
from typing import List, Dict, Any


class ResourceHints:
    """资源提示生成服务"""

    @classmethod
    def generate_preload(cls, href: str, as_type: str = 'script',
                        crossorigin: bool = False,
                        type_attr: str = None) -> str:
        """
        生成 preload link 标签

        Args:
            href: 资源 URL
            as_type: 资源类型 (script, style, image, font, fetch)
            crossorigin: 是否需要跨域
            type_attr: MIME 类型

        Returns:
            HTML link 标签字符串
        """
        attrs = [
            'rel="preload"',
            f'href="{href}"',
            f'as="{as_type}"'
        ]

        if crossorigin:
            attrs.append('crossorigin')

        if type_attr:
            attrs.append(f'type="{type_attr}"')

        return f'<link {" ".join(attrs)}>'

    @classmethod
    def generate_prefetch(cls, href: str, as_type: str = None) -> str:
        """
        生成 prefetch link 标签

        Args:
            href: 资源 URL
            as_type: 资源类型（可选）

        Returns:
            HTML link 标签字符串
        """
        attrs = [
            'rel="prefetch"',
            f'href="{href}"'
        ]

        if as_type:
            attrs.append(f'as="{as_type}"')

        return f'<link {" ".join(attrs)}>'

    @classmethod
    def generate_preconnect(cls, href: str, crossorigin: bool = False) -> str:
        """
        生成 preconnect link 标签

        Args:
            href: 目标域名 URL
            crossorigin: 是否需要跨域凭证

        Returns:
            HTML link 标签字符串
        """
        attrs = [
            'rel="preconnect"',
            f'href="{href}"'
        ]

        if crossorigin:
            attrs.append('crossorigin')

        return f'<link {" ".join(attrs)}>'

    @classmethod
    def generate_dns_prefetch(cls, href: str) -> str:
        """
        生成 dns-prefetch link 标签

        Args:
            href: 目标域名 URL

        Returns:
            HTML link 标签字符串
        """
        return f'<link rel="dns-prefetch" href="{href}">'

    @classmethod
    def generate_modulepreload(cls, href: str) -> str:
        """
        生成 modulepreload link 标签（用于 ES 模块）

        Args:
            href: 模块 URL

        Returns:
            HTML link 标签字符串
        """
        return f'<link rel="modulepreload" href="{href}">'

    @classmethod
    def get_common_third_party_domains(cls) -> List[str]:
        """
        获取常见的第三方域名（用于 preconnect）

        Returns:
            域名列表
        """
        return [
            'https://fonts.googleapis.com',
            'https://fonts.gstatic.com',
            'https://cdn.jsdelivr.net',
            'https://unpkg.com',
            'https://www.googletagmanager.com',
            'https://www.google-analytics.com',
            'https://connect.facebook.net',
            'https://platform.twitter.com',
        ]

    @classmethod
    def generate_font_preloads(cls, font_urls: List[str]) -> List[str]:
        """
        生成字体预加载标签

        Args:
            font_urls: 字体文件 URL 列表

        Returns:
            link 标签列表
        """
        hints = []
        for url in font_urls:
            # 检测字体格式
            if url.endswith('.woff2'):
                hints.append(cls.generate_preload(
                    url,
                    as_type='font',
                    crossorigin=True,
                    type_attr='font/woff2'
                ))
            elif url.endswith('.woff'):
                hints.append(cls.generate_preload(
                    url,
                    as_type='font',
                    crossorigin=True,
                    type_attr='font/woff'
                ))
        return hints

    @classmethod
    def generate_image_preloads(cls, images: List[Dict[str, Any]]) -> List[str]:
        """
        生成图片预加载标签（用于 LCP 优化）

        Args:
            images: 图片配置列表 [{src, media, fetchpriority}]

        Returns:
            link 标签列表
        """
        hints = []
        for img in images:
            attrs = [
                'rel="preload"',
                f'href="{img["src"]}"',
                'as="image"'
            ]

            if img.get('media'):
                attrs.append(f'media="{img["media"]}"')

            if img.get('fetchpriority') == 'high':
                attrs.append('fetchpriority="high"')

            hints.append(f'<link {" ".join(attrs)}>')

        return hints

    @classmethod
    def generate_smart_prefetch(cls, next_pages: List[str]) -> List[str]:
        """
        智能生成下一页资源的 prefetch

        Args:
            next_pages: 可能访问的下一页 URL 列表

        Returns:
            link 标签列表
        """
        hints = []
        for page_url in next_pages:
            hints.append(cls.generate_prefetch(page_url))

        return hints

    @classmethod
    def get_page_specific_hints(cls, page_type: str) -> Dict[str, List[str]]:
        """
        根据页面类型获取特定的资源提示

        Args:
            page_type: 页面类型 (home, article, category, search)

        Returns:
            按类别分组的资源提示
        """
        hints = {
            'preconnect': [],
            'preload': [],
            'prefetch': [],
            'dns_prefetch': []
        }

        if page_type == 'home':
            # 首页：预连接 CDN，预加载关键 CSS/JS
            hints['preconnect'] = [
                cls.generate_preconnect('https://fonts.googleapis.com'),
                cls.generate_preconnect('https://fonts.gstatic.com', crossorigin=True),
            ]
            hints['preload'] = [
                cls.generate_preload('/api/v2/static/css/critical.css', as_type='style'),
            ]
            hints['prefetch'] = [
                cls.generate_prefetch('/api/v1/articles?page=2'),
            ]

        elif page_type == 'article':
            # 文章页：预加载字体和相关资源
            hints['preconnect'] = [
                cls.generate_preconnect('https://fonts.googleapis.com'),
            ]
            hints['preload'] = [
                cls.generate_preload('/api/v2/static/fonts/main.woff2', as_type='font', crossorigin=True),
            ]
            hints['prefetch'] = [
                cls.generate_prefetch('/api/v1/articles/related'),
            ]

        elif page_type == 'category':
            # 分类页：预加载下一页
            hints['prefetch'] = [
                cls.generate_prefetch('/api/v1/articles?category=1&page=2'),
            ]

        elif page_type == 'search':
            # 搜索页：预连接搜索 API
            hints['preconnect'] = [
                cls.generate_preconnect('/api'),
            ]

        return hints

    @classmethod
    def generate_all_hints(cls, page_type: str = 'home',
                          custom_hints: Dict[str, List[str]] = None) -> str:
        """
        生成完整的资源提示 HTML

        Args:
            page_type: 页面类型
            custom_hints: 自定义提示

        Returns:
            完整的 HTML 字符串
        """
        # 获取页面特定提示
        hints = cls.get_page_specific_hints(page_type)

        # 合并自定义提示
        if custom_hints:
            for key, values in custom_hints.items():
                if key in hints:
                    hints[key].extend(values)

        # 生成 HTML
        html_parts = []

        # DNS Prefetch
        for hint in hints.get('dns_prefetch', []):
            html_parts.append(f'  {hint}')

        # Preconnect
        for hint in hints.get('preconnect', []):
            html_parts.append(f'  {hint}')

        # Preload
        for hint in hints.get('preload', []):
            html_parts.append(f'  {hint}')

        # Prefetch
        for hint in hints.get('prefetch', []):
            html_parts.append(f'  {hint}')

        return '\n'.join(html_parts)
