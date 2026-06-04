"""
综合SEO优化插件
整合元标签管理、Sitemap生成、Robots.txt、重定向管理、404监控、Schema结构化数据等功能

功能模块:
1. 元标签管理 - 自动生成title、description、keywords、OG标签、Twitter Card
2. Sitemap生成 - XML Sitemap、支持图片、多语言
3. Robots.txt管理 - 可视化编辑
4. 重定向管理 - 301/302重定向规则
5. 404监控 - 追踪和修复404错误
6. Schema标记 - Article、Organization、Breadcrumb等结构化数据
"""

import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from shared.services.plugins.plugin_manager.core import BasePlugin, plugin_hooks


class SEOPlugin(BasePlugin):
    """
    综合SEO优化插件
    
    整合了以下原有插件的功能:
    - seo-optimizer: 基础SEO优化
    - advanced-seo: 高级SEO工具
    - schema-markup: Schema结构化数据
    """

    def __init__(self):
        super().__init__(
            plugin_id=0,
            name="SEO优化中心",
            slug="seo",
            version="2.0.0"
        )

        # ==================== 全局设置 ====================
        self.settings = {
            # 元标签设置
            'auto_generate_meta': True,
            'site_name': 'FastBlog',
            'twitter_handle': '',
            'canonical_url_base': '',

            # Sitemap设置
            'include_images_in_sitemap': True,
            'sitemap_update_frequency': 'daily',

            # Robots.txt设置
            'robots_txt_enabled': True,

            # 重定向设置
            'enable_redirects': True,

            # 404监控设置
            'monitor_404': True,

            # Schema设置
            'enable_schema': True,
            'enable_article_schema': True,
            'enable_breadcrumb_schema': True,
            'enable_organization_schema': True,
            'organization_name': '',
            'organization_logo': '',
            'organization_url': '',
            'default_article_type': 'Article',
        }

        # ==================== 重定向规则 ====================
        self.redirects: List[Dict[str, Any]] = []

        # ==================== 404错误记录 ====================
        self.not_found_errors: List[Dict[str, Any]] = []

        # ==================== Schema统计 ====================
        self.schema_stats = {
            'total_generated': 0,
            'by_type': {},
        }

    def register_hooks(self):
        """注册钩子"""
        # 元标签钩子
        if self.settings.get('auto_generate_meta'):
            plugin_hooks.add_filter(
                "page_meta_tags",
                self.generate_article_meta_tags,
                priority=10
            )
            plugin_hooks.add_filter(
                "homepage_meta_tags",
                self.generate_homepage_meta_tags,
                priority=10
            )

        # Sitemap生成
        plugin_hooks.add_action(
            "sitemap_generation",
            self.generate_sitemap,
            priority=10
        )

        # 文章发布时更新Sitemap
        plugin_hooks.add_action(
            "article_published",
            self.on_article_published,
            priority=10
        )
        plugin_hooks.add_action(
            "article_updated",
            self.on_article_published,
            priority=10
        )

        # 重定向检查
        if self.settings.get('enable_redirects'):
            plugin_hooks.add_filter(
                "request_url",
                self.check_redirect,
                priority=5
            )

        # 404追踪
        if self.settings.get('monitor_404'):
            plugin_hooks.add_action(
                "page_not_found",
                self.track_404_error,
                priority=10
            )

        # Schema注入
        if self.settings.get('enable_schema'):
            plugin_hooks.add_action(
                "article_page_head",
                self.inject_article_schema,
                priority=10
            )
            plugin_hooks.add_action(
                "page_head",
                self.inject_general_schema,
                priority=10
            )
            plugin_hooks.add_filter(
                "breadcrumb_data",
                self.generate_breadcrumb_schema,
                priority=10
            )

    def activate(self):
        """激活插件"""
        super().activate()
        # 生成初始sitemap
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.generate_sitemap())
            else:
                loop.run_until_complete(self.generate_sitemap())
        except Exception as e:
            print(f"[SEO] Failed to generate initial sitemap: {e}")

        print("[SEO] Plugin activated - All SEO modules initialized")

    def deactivate(self):
        """停用插件"""
        super().deactivate()
        print("[SEO] Plugin deactivated")

    # ==================== 元标签管理 ====================

    def generate_article_meta_tags(self, meta_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成文章页面的元标签"""
        if not self.settings.get('auto_generate_meta'):
            return meta_data

        article = meta_data.get('article', {})
        if not article:
            return meta_data

        tags = meta_data.get('tags', [])

        # Title
        title = article.get('title', '')
        tags.append(f'<title>{title} | {self.settings["site_name"]}</title>')

        # Description
        description = article.get('excerpt', '')[:160]
        if description:
            tags.append(f'<meta name="description" content="{description}" />')

        # Keywords
        article_tags = article.get('tags', [])
        if article_tags:
            keywords = ', '.join(article_tags[:10])
            tags.append(f'<meta name="keywords" content="{keywords}" />')

        # Canonical URL
        canonical_url = self._get_canonical_url(article.get('slug', ''))
        if canonical_url:
            tags.append(f'<link rel="canonical" href="{canonical_url}" />')

        # Open Graph标签
        og_tags = self._generate_og_tags(article, 'article')
        tags.extend(og_tags)

        # Twitter Card标签
        twitter_tags = self._generate_twitter_tags(article)
        tags.extend(twitter_tags)

        meta_data['tags'] = tags
        return meta_data

    def generate_homepage_meta_tags(self, meta_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成首页元标签"""
        if not self.settings.get('auto_generate_meta'):
            return meta_data

        tags = meta_data.get('tags', [])

        tags.append(f'<title>{self.settings["site_name"]} - 博客首页</title>')
        tags.append('<meta name="description" content="欢迎访问我们的博客，分享技术文章和见解" />')

        if self.settings.get('canonical_url_base'):
            tags.append(f'<link rel="canonical" href="{self.settings["canonical_url_base"]}/" />')

        tags.append('<meta property="og:type" content="website" />')
        tags.append(f'<meta property="og:title" content="{self.settings["site_name"]}" />')
        tags.append('<meta property="og:description" content="欢迎访问我们的博客" />')

        meta_data['tags'] = tags
        return meta_data

    def _generate_og_tags(self, article: Dict[str, Any], content_type: str = 'article') -> List[str]:
        """生成Open Graph标签"""
        tags = []

        tags.append(f'<meta property="og:type" content="{content_type}" />')
        tags.append(f'<meta property="og:title" content="{article.get("title", "")}" />')

        excerpt = article.get('excerpt', '')[:200]
        if excerpt:
            tags.append(f'<meta property="og:description" content="{excerpt}" />')

        # 封面图片
        featured_image = article.get('featured_image', '')
        if featured_image:
            tags.append(f'<meta property="og:image" content="{featured_image}" />')

        tags.append(f'<meta property="og:url" content="{self._get_canonical_url(article.get("slug", ""))}" />')
        tags.append(f'<meta property="og:site_name" content="{self.settings["site_name"]}" />')

        return tags

    def _generate_twitter_tags(self, article: Dict[str, Any]) -> List[str]:
        """生成Twitter Card标签"""
        tags = []

        tags.append('<meta name="twitter:card" content="summary_large_image" />')

        if self.settings.get('twitter_handle'):
            tags.append(f'<meta name="twitter:site" content="@{self.settings["twitter_handle"]}" />')

        tags.append(f'<meta name="twitter:title" content="{article.get("title", "")}" />')

        excerpt = article.get('excerpt', '')[:200]
        if excerpt:
            tags.append(f'<meta name="twitter:description" content="{excerpt}" />')

        featured_image = article.get('featured_image', '')
        if featured_image:
            tags.append(f'<meta name="twitter:image" content="{featured_image}" />')

        return tags

    def _get_canonical_url(self, slug: str) -> str:
        """获取规范URL"""
        base = self.settings.get('canonical_url_base', '')
        if base and slug:
            return f"{base}/article/{slug}"
        return base

    # ==================== Sitemap生成 ====================

    async def generate_sitemap(self):
        """生成sitemap.xml文件"""
        try:
            # 从数据库获取所有文章和页面（简化实现）
            articles = await self._get_all_articles()

            # 创建XML
            urlset = ET.Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')

            # 添加首页
            homepage = ET.SubElement(urlset, 'url')
            ET.SubElement(homepage, 'loc').text = self.settings.get('canonical_url_base', 'https://example.com') + '/'
            ET.SubElement(homepage, 'lastmod').text = datetime.now().strftime('%Y-%m-%d')
            ET.SubElement(homepage, 'changefreq').text = 'daily'
            ET.SubElement(homepage, 'priority').text = '1.0'

            # 添加文章
            for article in articles:
                url = ET.SubElement(urlset, 'url')

                loc = self._get_canonical_url(article.get('slug', ''))
                ET.SubElement(url, 'loc').text = loc

                updated_at = article.get('updated_at') or article.get('created_at')
                if updated_at:
                    ET.SubElement(url, 'lastmod').text = updated_at.strftime('%Y-%m-%d')

                ET.SubElement(url, 'changefreq').text = 'weekly'
                ET.SubElement(url, 'priority').text = '0.8'

                # 如果有图片，添加图片信息
                if self.settings.get('include_images_in_sitemap'):
                    images = article.get('images', [])
                    for image in images:
                        image_elem = ET.SubElement(url, 'image:image',
                                                   xmlns='http://www.google.com/schemas/sitemap-image/1.1')
                        ET.SubElement(image_elem, 'image:loc').text = image.get('url', '')
                        if image.get('caption'):
                            ET.SubElement(image_elem, 'image:caption').text = image['caption']

            # 格式化并保存
            xml_str = ET.tostring(urlset, encoding='unicode', method='xml')
            from xml.dom import minidom
            pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")

            # 保存到文件
            sitemap_path = Path('public/sitemap.xml')
            sitemap_path.parent.mkdir(parents=True, exist_ok=True)
            with open(sitemap_path, 'w', encoding='utf-8') as f:
                f.write(pretty_xml)

            print(f"[SEO] Sitemap generated with {len(articles)} articles")

        except Exception as e:
            print(f"[SEO] Failed to generate sitemap: {e}")
            import traceback
            traceback.print_exc()

    async def _get_all_articles(self) -> List[Dict[str, Any]]:
        """获取所有文章（简化实现，实际应从数据库查询）"""
        # Query articles from database
        # Example implementation:
        # from sqlalchemy import select
        # from shared.models.article import Article
        # 
        # stmt = select(Article).where(Article.status == 'published')
        # result = await db.execute(stmt)
        # articles = result.scalars().all()
        # 
        # return [{
        #     'id': article.id,
        #     'title': article.title,
        #     'slug': article.slug,
        #     'created_at': article.created_at.isoformat(),
        #     'updated_at': article.updated_at.isoformat(),
        # } for article in articles]

        # For now, return empty list
        return []

    def on_article_published(self, article_data: Dict[str, Any]):
        """文章发布时更新Sitemap"""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.generate_sitemap())
            else:
                loop.run_until_complete(self.generate_sitemap())
            print(f"[SEO] Sitemap updated for article: {article_data.get('title')}")
        except Exception as e:
            print(f"[SEO] Failed to update sitemap: {e}")

    # ==================== Robots.txt管理 ====================

    def generate_robots_txt(self) -> str:
        """生成robots.txt内容"""
        lines = [
            "# FastBlog robots.txt",
            f"# Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "User-agent: *",
            "Disallow: /admin/",
            "Disallow: /api/",
            "Disallow: /private/",
            "",
            "# Allow search engines to crawl content",
            "Allow: /articles/",
            "Allow: /categories/",
            "",
            "# Sitemap",
            f"Sitemap: {self.settings.get('canonical_url_base', 'https://example.com')}/sitemap.xml",
        ]

        return '\n'.join(lines)

    def save_robots_txt(self, custom_content: str = None):
        """保存robots.txt文件"""
        content = custom_content if custom_content else self.generate_robots_txt()

        robots_path = Path('public/robots.txt')
        robots_path.parent.mkdir(parents=True, exist_ok=True)
        with open(robots_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("[SEO] robots.txt saved")

    # ==================== 重定向管理 ====================

    def check_redirect(self, url: str) -> str:
        """检查URL是否需要重定向"""
        if not self.settings.get('enable_redirects'):
            return url

        for redirect in self.redirects:
            if redirect['from_url'] == url and redirect.get('active', True):
                print(f"[SEO] Redirecting: {url} -> {redirect['to_url']}")
                return redirect['to_url']

        return url

    def add_redirect(self, from_url: str, to_url: str, status_code: int = 301):
        """添加重定向规则"""
        redirect = {
            'from_url': from_url,
            'to_url': to_url,
            'status_code': status_code,
            'active': True,
            'created_at': datetime.now().isoformat(),
        }

        self.redirects.append(redirect)
        print(f"[SEO] Redirect added: {from_url} -> {to_url}")

    def remove_redirect(self, from_url: str):
        """删除重定向规则"""
        self.redirects = [r for r in self.redirects if r['from_url'] != from_url]
        print(f"[SEO] Redirect removed: {from_url}")

    # ==================== 404监控 ====================

    def track_404_error(self, error_data: Dict[str, Any]):
        """追踪404错误"""
        if not self.settings.get('monitor_404'):
            return

        error_record = {
            'url': error_data.get('url', ''),
            'referrer': error_data.get('referrer', ''),
            'user_agent': error_data.get('user_agent', ''),
            'timestamp': error_data.get('timestamp', datetime.now().isoformat()),
            'count': 1,
        }

        # 检查是否已存在相同URL的错误
        existing = next(
            (e for e in self.not_found_errors if e['url'] == error_record['url']),
            None
        )

        if existing:
            existing['count'] += 1
            existing['timestamp'] = error_record['timestamp']
        else:
            self.not_found_errors.append(error_record)

        print(f"[SEO] 404 error tracked: {error_record['url']}")

    def get_top_404_errors(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取最多的404错误"""
        sorted_errors = sorted(self.not_found_errors, key=lambda x: x['count'], reverse=True)
        return sorted_errors[:limit]

    # ==================== Schema结构化数据 ====================

    def inject_article_schema(self, context: Dict[str, Any]):
        """注入文章Schema"""
        if not self.settings.get('enable_schema') or not self.settings.get('enable_article_schema'):
            return

        article = context.get('article')
        if not article:
            return

        schema = self.generate_article_schema(article)

        if schema:
            script_tag = f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>'

            if 'schema_scripts' not in context:
                context['schema_scripts'] = []

            context['schema_scripts'].append(script_tag)
            self._update_schema_stats('Article')

    def inject_general_schema(self, context: Dict[str, Any]):
        """注入通用Schema"""
        if not self.settings.get('enable_schema'):
            return

        scripts = []

        # 组织信息Schema
        if self.settings.get('enable_organization_schema'):
            org_schema = self.generate_organization_schema()
            if org_schema:
                scripts.append(
                    f'<script type="application/ld+json">{json.dumps(org_schema, ensure_ascii=False)}</script>')
                self._update_schema_stats('Organization')

        # 网站搜索Schema
        website_schema = self.generate_website_schema()
        if website_schema:
            scripts.append(
                f'<script type="application/ld+json">{json.dumps(website_schema, ensure_ascii=False)}</script>')
            self._update_schema_stats('WebSite')

        if scripts:
            if 'schema_scripts' not in context:
                context['schema_scripts'] = []
            context['schema_scripts'].extend(scripts)

    def generate_breadcrumb_schema(self, breadcrumb_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成面包屑Schema"""
        if not self.settings.get('enable_schema') or not self.settings.get('enable_breadcrumb_schema'):
            return breadcrumb_data

        items = breadcrumb_data.get('items', [])
        if not items:
            return breadcrumb_data

        schema = {
            '@context': 'https://schema.org',
            '@type': 'BreadcrumbList',
            'itemListElement': []
        }

        for index, item in enumerate(items, 1):
            schema['itemListElement'].append({
                '@type': 'ListItem',
                'position': index,
                'name': item.get('name', ''),
                'item': item.get('url', '')
            })

        breadcrumb_data['schema'] = schema
        self._update_schema_stats('BreadcrumbList')

        return breadcrumb_data

    def generate_article_schema(self, article: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """生成文章Schema"""
        try:
            article_type = self.settings.get('default_article_type', 'Article')

            schema = {
                '@context': 'https://schema.org',
                '@type': article_type,
                'headline': article.get('title', ''),
                'description': article.get('excerpt', '')[:200],
                'url': self._get_canonical_url(article.get('slug', '')),
            }

            # 作者信息
            if self.settings.get('include_author_info') and article.get('author'):
                schema['author'] = {
                    '@type': 'Person',
                    'name': article['author'].get('name', ''),
                }

            # 发布日期
            if self.settings.get('include_publish_date') and article.get('created_at'):
                schema['datePublished'] = article['created_at'].isoformat()

            # 修改日期
            if self.settings.get('include_modify_date') and article.get('updated_at'):
                schema['dateModified'] = article['updated_at'].isoformat()

            # 封面图片
            if article.get('featured_image'):
                schema['image'] = article['featured_image']

            return schema

        except Exception as e:
            print(f"[SEO] Failed to generate article schema: {e}")
            return None

    def generate_organization_schema(self) -> Optional[Dict[str, Any]]:
        """生成组织Schema"""
        if not self.settings.get('organization_name'):
            return None

        schema = {
            '@context': 'https://schema.org',
            '@type': 'Organization',
            'name': self.settings['organization_name'],
            'url': self.settings.get('organization_url', ''),
        }

        if self.settings.get('organization_logo'):
            schema['logo'] = self.settings['organization_logo']

        # 社交资料
        social_profiles = self.settings.get('social_profiles', [])
        if social_profiles:
            schema['sameAs'] = social_profiles

        return schema

    def generate_website_schema(self) -> Dict[str, Any]:
        """生成网站Schema"""
        schema = {
            '@context': 'https://schema.org',
            '@type': 'WebSite',
            'name': self.settings.get('site_name', 'FastBlog'),
            'url': self.settings.get('canonical_url_base', ''),
        }

        # 搜索动作
        schema['potentialAction'] = {
            '@type': 'SearchAction',
            'target': f"{self.settings.get('canonical_url_base', '')}/search?q={search_term_string}",
            'query-input': 'required name=search_term_string',
        }

        return schema

    def _update_schema_stats(self, schema_type: str):
        """更新Schema统计"""
        self.schema_stats['total_generated'] += 1

        if schema_type not in self.schema_stats['by_type']:
            self.schema_stats['by_type'][schema_type] = 0

        self.schema_stats['by_type'][schema_type] += 1

    # ==================== 管理API ====================

    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表板数据"""
        return {
            'redirects_count': len(self.redirects),
            '404_errors_count': len(self.not_found_errors),
            'top_404_errors': self.get_top_404_errors(limit=10),
            'schema_stats': self.schema_stats,
            'sitemap_last_generated': datetime.now().isoformat(),
        }

    def get_seo_report(self) -> Dict[str, Any]:
        """生成SEO报告"""
        return {
            'meta_tags': {
                'auto_generate': self.settings.get('auto_generate_meta', False),
                'canonical_base': self.settings.get('canonical_url_base', ''),
            },
            'sitemap': {
                'enabled': True,
                'includes_images': self.settings.get('include_images_in_sitemap', False),
                'update_frequency': self.settings.get('sitemap_update_frequency', 'daily'),
            },
            'redirects': {
                'enabled': self.settings.get('enable_redirects', False),
                'total_rules': len(self.redirects),
            },
            '404_monitoring': {
                'enabled': self.settings.get('monitor_404', False),
                'total_errors': len(self.not_found_errors),
            },
            'schema_markup': {
                'enabled': self.settings.get('enable_schema', False),
                'total_generated': self.schema_stats['total_generated'],
                'by_type': self.schema_stats['by_type'],
            },
        }

    def get_admin_ui_config(self) -> Dict[str, Any]:
        """获取管理界面配置"""
        return {
            'title': 'SEO优化中心',
            'icon': '🔍',
            'sections': [
                {
                    'title': 'SEO概览',
                    'widgets': [
                        {'type': 'stat', 'label': '重定向规则', 'value': len(self.redirects)},
                        {'type': 'stat', 'label': '404错误', 'value': len(self.not_found_errors)},
                        {'type': 'stat', 'label': 'Schema生成数', 'value': self.schema_stats['total_generated']},
                    ],
                },
                {
                    'title': '元标签设置',
                    'fields': [
                        {
                            'key': 'auto_generate_meta',
                            'label': '自动生成元标签',
                            'type': 'boolean',
                        },
                        {
                            'key': 'site_name',
                            'label': '网站名称',
                            'type': 'text',
                        },
                        {
                            'key': 'canonical_url_base',
                            'label': '规范URL基础',
                            'type': 'text',
                            'placeholder': 'https://example.com',
                        },
                    ],
                },
                {
                    'title': 'Sitemap设置',
                    'fields': [
                        {
                            'key': 'include_images_in_sitemap',
                            'label': 'Sitemap包含图片',
                            'type': 'boolean',
                        },
                        {
                            'key': 'sitemap_update_frequency',
                            'label': '更新频率',
                            'type': 'select',
                            'options': ['daily', 'weekly', 'monthly'],
                        },
                    ],
                },
                {
                    'title': 'Schema设置',
                    'fields': [
                        {
                            'key': 'enable_schema',
                            'label': '启用Schema',
                            'type': 'boolean',
                        },
                        {
                            'key': 'organization_name',
                            'label': '组织名称',
                            'type': 'text',
                        },
                    ],
                },
                {
                    'title': '操作',
                    'actions': [
                        {
                            'type': 'button',
                            'label': '重新生成Sitemap',
                            'action': 'regenerate_sitemap',
                            'variant': 'primary',
                        },
                        {
                            'type': 'button',
                            'label': '生成robots.txt',
                            'action': 'generate_robots',
                            'variant': 'outline',
                        },
                        {
                            'type': 'button',
                            'label': '查看SEO报告',
                            'action': 'view_report',
                            'variant': 'outline',
                        },
                    ],
                },
            ],
        }


# 导出插件实例
plugin = SEOPlugin()
