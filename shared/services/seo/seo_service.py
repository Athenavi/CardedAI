"""
SEO优化服务
包含站点地图、结构化数据、面包屑、Canonical URL
"""

from datetime import datetime
from typing import Dict, Any, List
from xml.dom.minidom import parseString
from xml.etree.ElementTree import Element, SubElement, tostring


class SEOService:
    """
    SEO服务
    
    功能:
    1. XML站点地图生成
    2. Schema.org结构化数据
    3. 面包屑导航
    4. Canonical URL处理
    """

    def __init__(self, base_url: str = "https://example.com"):
        self.base_url = base_url

    # ==================== XML站点地图 ====================

    def generate_sitemap(
            self,
            articles: List[Dict[str, Any]],
            categories: List[Dict[str, Any]] = None,
            pages: List[Dict[str, Any]] = None
    ) -> str:
        """
        生成XML站点地图
        
        Args:
            articles: 文章列表
            categories: 分类列表
            pages: 页面列表
            
        Returns:
            XML字符串
        """
        urlset = Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')

        # 添加首页
        self._add_url(urlset, self.base_url, '1.0', 'daily')

        # 添加文章
        for article in articles:
            loc = f"{self.base_url}/articles/{article.get('slug', article.get('id'))}"
            priority = '0.8' if article.get('is_featured') else '0.6'
            changefreq = 'weekly'

            self._add_url(
                urlset,
                loc,
                priority,
                changefreq,
                article.get('updated_at') or article.get('created_at')
            )

        # 添加分类
        if categories:
            for category in categories:
                loc = f"{self.base_url}/categories/{category.get('slug', category.get('id'))}"
                self._add_url(urlset, loc, '0.7', 'weekly')

        # 添加页面
        if pages:
            for page in pages:
                loc = f"{self.base_url}/pages/{page.get('slug', page.get('id'))}"
                self._add_url(urlset, loc, '0.5', 'monthly')

        # 格式化XML
        rough_string = tostring(urlset, encoding='unicode')
        dom = parseString(rough_string)
        return dom.toprettyxml(indent="  ")

    def _add_url(
            self,
            urlset: Element,
            loc: str,
            priority: str = '0.5',
            changefreq: str = 'monthly',
            lastmod: str = None
    ):
        """添加URL到站点地图"""
        url_elem = SubElement(urlset, 'url')

        loc_elem = SubElement(url_elem, 'loc')
        loc_elem.text = loc

        if lastmod:
            try:
                # 格式化日期
                if isinstance(lastmod, str):
                    dt = datetime.fromisoformat(lastmod.replace('Z', '+00:00'))
                else:
                    dt = lastmod
                lastmod_elem = SubElement(url_elem, 'lastmod')
                lastmod_elem.text = dt.strftime('%Y-%m-%dT%H:%M:%S+00:00')
            except:
                pass

        changefreq_elem = SubElement(url_elem, 'changefreq')
        changefreq_elem.text = changefreq

        priority_elem = SubElement(url_elem, 'priority')
        priority_elem.text = priority

    # ==================== Schema.org结构化数据 ====================

    def generate_article_schema(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成文章结构化数据
        
        Args:
            article: 文章数据
            
        Returns:
            Schema.org JSON-LD数据
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": article.get('title', ''),
            "description": article.get('excerpt', ''),
            "image": article.get('cover_image', ''),
            "datePublished": article.get('created_at', ''),
            "dateModified": article.get('updated_at', ''),
            "author": {
                "@type": "Person",
                "name": article.get('author_name', '')
            },
            "publisher": {
                "@type": "Organization",
                "name": "FastBlog",
                "logo": {
                    "@type": "ImageObject",
                    "url": f"{self.base_url}/logo.png"
                }
            },
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": f"{self.base_url}/articles/{article.get('slug', article.get('id'))}"
            }
        }

        return schema

    def generate_breadcrumb_schema(self, breadcrumbs: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        生成面包屑结构化数据
        
        Args:
            breadcrumbs: 面包屑列表 [{'name': '...', 'url': '...'}]
            
        Returns:
            Schema.org JSON-LD数据
        """
        item_list_elements = []

        for i, crumb in enumerate(breadcrumbs, 1):
            item_list_elements.append({
                "@type": "ListItem",
                "position": i,
                "name": crumb['name'],
                "item": crumb['url']
            })

        schema = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": item_list_elements
        }

        return schema

    def generate_person_schema(self, person: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成人员结构化数据
        
        Args:
            person: 人员数据 {name, job_title, description, image, url, ...}
            
        Returns:
            Schema.org JSON-LD数据
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "Person",
            "name": person.get('name', ''),
        }

        if person.get('job_title'):
            schema['jobTitle'] = person['job_title']

        if person.get('description') or person.get('bio'):
            schema['description'] = person.get('description') or person.get('bio')

        if person.get('image') or person.get('profile_picture'):
            schema['image'] = person.get('image') or person.get('profile_picture')

        if person.get('url') or person.get('website'):
            schema['url'] = person.get('url') or person.get('website')

        if person.get('email'):
            schema['email'] = person['email']

        if person.get('same_as'):
            schema['sameAs'] = person['same_as']

        return schema

    def generate_organization_schema(self, org: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成组织结构化数据
        
        Args:
            org: 组织数据 {name, url, logo, description, contact_point, ...}
            
        Returns:
            Schema.org JSON-LD数据
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": org.get('name', ''),
            "url": org.get('url', self.base_url),
        }

        if org.get('logo'):
            schema['logo'] = org['logo']

        if org.get('description'):
            schema['description'] = org['description']

        if org.get('contact_point'):
            schema['contactPoint'] = org['contact_point']

        if org.get('same_as'):
            schema['sameAs'] = org['same_as']

        return schema

    def generate_faq_schema(self, faqs: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        生成FAQ结构化数据
        
        Args:
            faqs: FAQ列表 [{'question': '...', 'answer': '...'}]
            
        Returns:
            Schema.org JSON-LD数据
        """
        main_entity = []

        for faq in faqs:
            main_entity.append({
                "@type": "Question",
                "name": faq.get('question', ''),
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": faq.get('answer', '')
                }
            })

        schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": main_entity
        }

        return schema

    def generate_howto_schema(self, howto: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成HowTo结构化数据
        
        Args:
            howto: HowTo数据 {
                'name': '教程名称',
                'description': '教程描述',
                'step': [{'name': '步骤名', 'text': '步骤说明', 'image': '图片URL'}],
                'totalTime': 'PT30M',
                'estimatedCost': {'currency': 'USD', 'value': '10'},
                ...
            }
            
        Returns:
            Schema.org JSON-LD数据
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "HowTo",
            "name": howto.get('name', ''),
            "description": howto.get('description', ''),
        }

        # 添加步骤
        if howto.get('step'):
            steps = []
            for i, step in enumerate(howto['step'], 1):
                step_data = {
                    "@type": "HowToStep",
                    "position": i,
                    "name": step.get('name', f'步骤 {i}'),
                    "text": step.get('text', ''),
                }
                if step.get('image'):
                    step_data['image'] = step['image']
                if step.get('url'):
                    step_data['url'] = step['url']
                steps.append(step_data)
            schema['step'] = steps

        # 添加总时间
        if howto.get('total_time') or howto.get('totalTime'):
            schema['totalTime'] = howto.get('total_time') or howto.get('totalTime')

        # 添加预估成本
        if howto.get('estimated_cost') or howto.get('estimatedCost'):
            schema['estimatedCost'] = howto.get('estimated_cost') or howto.get('estimatedCost')

        # 添加工具
        if howto.get('tool'):
            schema['tool'] = howto['tool']

        # 添加供应
        if howto.get('supply'):
            schema['supply'] = howto['supply']

        return schema

    # ==================== 面包屑导航 ====================

    def generate_breadcrumbs(
            self,
            article: Dict[str, Any] = None,
            category: Dict[str, Any] = None
    ) -> List[Dict[str, str]]:
        """
        生成面包屑导航
        
        Args:
            article: 文章数据
            category: 分类数据
            
        Returns:
            面包屑列表
        """
        breadcrumbs = [
            {'name': '首页', 'url': self.base_url}
        ]

        if category:
            breadcrumbs.append({
                'name': category.get('name', ''),
                'url': f"{self.base_url}/categories/{category.get('slug', '')}"
            })

        if article:
            if article.get('category_name'):
                breadcrumbs.append({
                    'name': article.get('category_name', ''),
                    'url': f"{self.base_url}/categories/{article.get('category_slug', '')}"
                })

            breadcrumbs.append({
                'name': article.get('title', ''),
                'url': f"{self.base_url}/articles/{article.get('slug', '')}"
            })

        return breadcrumbs

    # ==================== Canonical URL ====================

    def normalize_url(self, url: str) -> str:
        """
        URL规范化 - 统一URL格式
        
        规则:
        1. 移除尾部斜杠（除非是根路径）
        2. 转换为小写
        3. 移除末尾的index.html
        4. 标准化查询参数排序
        
        Args:
            url: 原始URL
            
        Returns:
            规范化后的URL
        """
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

        parsed = urlparse(url)

        # 转换为小写
        path = parsed.path.lower()

        # 移除尾部斜杠（除非是根路径）
        if path != '/' and path.endswith('/'):
            path = path.rstrip('/')

        # 移除末尾的index.html
        if path.endswith('/index.html'):
            path = path[:-len('/index.html')] or '/'

        # 标准化查询参数排序
        query_params = parse_qs(parsed.query, keep_blank_values=True)
        if query_params:
            sorted_query = urlencode(sorted(query_params.items()), doseq=True)
        else:
            sorted_query = ''

        # 重建URL
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc.lower(),
            path,
            parsed.params,
            sorted_query,
            parsed.fragment
        ))

        return normalized

    def detect_duplicate_content(
            self,
            urls: List[str],
            content_hash: str = None
    ) -> Dict[str, Any]:
        """
        检测重复内容
        
        Args:
            urls: URL列表
            content_hash: 内容哈希值（可选）
            
        Returns:
            检测结果 {is_duplicate: bool, canonical_url: str, duplicates: []}
        """
        if not urls:
            return {
                'is_duplicate': False,
                'canonical_url': None,
                'duplicates': []
            }

        # 规范化所有URL
        normalized_urls = [self.normalize_url(url) for url in urls]

        # 找出唯一的规范化URL
        unique_urls = list(set(normalized_urls))

        # 如果只有一个唯一URL，则没有重复
        if len(unique_urls) <= 1:
            return {
                'is_duplicate': False,
                'canonical_url': unique_urls[0] if unique_urls else None,
                'duplicates': []
            }

        # 选择主URL策略：最短的URL作为canonical
        canonical_url = min(unique_urls, key=len)

        # 找出重复的URL
        duplicates = [url for url in unique_urls if url != canonical_url]

        return {
            'is_duplicate': True,
            'canonical_url': canonical_url,
            'duplicates': duplicates,
            'total_urls': len(urls),
            'unique_urls': len(unique_urls)
        }

    def get_canonical_url(
            self,
            path: str,
            params: Dict[str, Any] = None,
            page: int = None
    ) -> str:
        """
        获取规范URL
        
        Args:
            path: 路径
            params: 查询参数(会被移除)
            page: 页码（用于分页处理）
            
        Returns:
            规范URL
        """
        # 规范化路径
        normalized_path = path.lower().rstrip('/')
        if normalized_path == '':
            normalized_path = '/'

        # Canonical URL不包含查询参数（除了page参数）
        if page and page > 1:
            return f"{self.base_url}{normalized_path}?page={page}"

        return f"{self.base_url}{normalized_path}"

    def generate_canonical_tag(
            self,
            path: str,
            params: Dict[str, Any] = None,
            page: int = None
    ) -> str:
        """
        生成Canonical标签
        
        Args:
            path: 路径
            params: 查询参数
            page: 页码
            
        Returns:
            HTML link标签
        """
        canonical_url = self.get_canonical_url(path, params, page)
        return f'<link rel="canonical" href="{canonical_url}" />'

    def generate_pagination_tags(
            self,
            path: str,
            current_page: int,
            total_pages: int,
            params: Dict[str, Any] = None
    ) -> List[str]:
        """
        生成分页相关标签 (rel=prev/next)
        
        Args:
            path: 基础路径
            current_page: 当前页码
            total_pages: 总页数
            params: 其他查询参数
            
        Returns:
            HTML link标签列表
        """
        tags = []

        # 上一页
        if current_page > 1:
            prev_page = current_page - 1
            prev_url = f"{self.base_url}{path}?page={prev_page}"
            tags.append(f'<link rel="prev" href="{prev_url}" />')

        # 下一页
        if current_page < total_pages:
            next_page = current_page + 1
            next_url = f"{self.base_url}{path}?page={next_page}"
            tags.append(f'<link rel="next" href="{next_url}" />')

        return tags

    def select_primary_url(
            self,
            urls: List[str],
            strategy: str = 'shortest'
    ) -> str:
        """
        主URL选择策略
        
        Args:
            urls: URL列表
            strategy: 选择策略 ('shortest', 'first', 'https_preferred')
            
        Returns:
            选定的主URL
        """
        if not urls:
            return None

        # 规范化所有URL
        normalized = [self.normalize_url(url) for url in urls]

        if strategy == 'shortest':
            # 选择最短的URL
            return min(normalized, key=len)
        elif strategy == 'first':
            # 选择第一个URL
            return normalized[0]
        elif strategy == 'https_preferred':
            # 优先选择HTTPS
            https_urls = [url for url in normalized if url.startswith('https://')]
            if https_urls:
                return https_urls[0]
            return normalized[0]
        else:
            return normalized[0]

    # ==================== SEO分析和评分 ====================

    def analyze_article_seo(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析文章SEO并给出评分和建议
        
        Args:
            article: 文章数据 {title, excerpt, content, cover_image, tags, ...}
            
        Returns:
            SEO分析报告 {score, checks, suggestions}
        """
        checks = []
        suggestions = []
        score = 100

        # 1. 标题长度检查
        title = article.get('title', '')
        title_length = len(title)
        if title_length < 30:
            checks.append(
                {'item': '标题长度', 'status': 'warning', 'message': f'标题过短 ({title_length}字符)，建议30-60字符'})
            suggestions.append('增加标题长度，包含更多关键词')
            score -= 10
        elif title_length > 60:
            checks.append(
                {'item': '标题长度', 'status': 'warning', 'message': f'标题过长 ({title_length}字符)，建议30-60字符'})
            suggestions.append('缩短标题，确保在搜索结果中完整显示')
            score -= 10
        else:
            checks.append({'item': '标题长度', 'status': 'pass', 'message': f'标题长度合适 ({title_length}字符)'})

        # 2. 描述长度检查
        excerpt = article.get('excerpt', '')
        excerpt_length = len(excerpt)
        if not excerpt:
            checks.append({'item': '文章摘要', 'status': 'fail', 'message': '缺少文章摘要'})
            suggestions.append('添加文章摘要（150-160字符），用于搜索引擎展示')
            score -= 20
        elif excerpt_length < 120:
            checks.append({'item': '文章摘要', 'status': 'warning', 'message': f'摘要过短 ({excerpt_length}字符)'})
            suggestions.append('扩展摘要到150-160字符')
            score -= 10
        elif excerpt_length > 160:
            checks.append({'item': '文章摘要', 'status': 'warning', 'message': f'摘要过长 ({excerpt_length}字符)'})
            suggestions.append('精简摘要到150-160字符')
            score -= 5
        else:
            checks.append({'item': '文章摘要', 'status': 'pass', 'message': f'摘要长度合适 ({excerpt_length}字符)'})

        # 3. 封面图片检查
        cover_image = article.get('cover_image', '')
        if not cover_image:
            checks.append({'item': '封面图片', 'status': 'warning', 'message': '缺少封面图片'})
            suggestions.append('添加封面图片，提升点击率')
            score -= 10
        else:
            checks.append({'item': '封面图片', 'status': 'pass', 'message': '已设置封面图片'})

        # 4. 内容长度检查
        content = article.get('content', '')
        content_length = len(content)
        word_count = len(content.split()) if content else 0
        if word_count < 300:
            checks.append({'item': '内容长度', 'status': 'warning', 'message': f'内容过短 ({word_count}字)'})
            suggestions.append('增加内容长度，建议至少600字以上')
            score -= 15
        elif word_count < 600:
            checks.append({'item': '内容长度', 'status': 'warning', 'message': f'内容较短 ({word_count}字)'})
            suggestions.append('继续丰富内容，建议达到1000字以上')
            score -= 5
        else:
            checks.append({'item': '内容长度', 'status': 'pass', 'message': f'内容长度充足 ({word_count}字)'})

        # 5. 标签检查
        tags = article.get('tags', [])
        tag_count = len(tags) if isinstance(tags, list) else 0
        if tag_count == 0:
            checks.append({'item': '标签', 'status': 'warning', 'message': '未设置标签'})
            suggestions.append('添加3-5个相关标签，提升分类和搜索')
            score -= 10
        elif tag_count > 10:
            checks.append({'item': '标签', 'status': 'warning', 'message': f'标签过多 ({tag_count}个)'})
            suggestions.append('减少标签数量，建议3-5个精准标签')
            score -= 5
        else:
            checks.append({'item': '标签', 'status': 'pass', 'message': f'标签数量合适 ({tag_count}个)'})

        # 6. URL Slug检查
        slug = article.get('slug', '')
        if not slug:
            checks.append({'item': 'URL Slug', 'status': 'fail', 'message': '缺少URL Slug'})
            suggestions.append('设置友好的URL Slug（使用英文或拼音）')
            score -= 15
        elif len(slug) > 100:
            checks.append({'item': 'URL Slug', 'status': 'warning', 'message': 'URL Slug过长'})
            suggestions.append('缩短URL Slug，保持简洁')
            score -= 5
        else:
            checks.append({'item': 'URL Slug', 'status': 'pass', 'message': 'URL Slug设置合理'})

        # 7. 内部链接检查（简单检测）
        internal_links = content.count(f'{self.base_url}/') if content else 0
        if internal_links == 0 and word_count > 500:
            checks.append({'item': '内部链接', 'status': 'warning', 'message': '缺少内部链接'})
            suggestions.append('添加2-3个相关文章的内部链接')
            score -= 5
        else:
            checks.append({'item': '内部链接', 'status': 'pass', 'message': f'包含{internal_links}个内部链接'})

        # 确保分数不低于0
        score = max(0, score)

        # 评级
        if score >= 90:
            grade = 'A'
        elif score >= 80:
            grade = 'B'
        elif score >= 70:
            grade = 'C'
        elif score >= 60:
            grade = 'D'
        else:
            grade = 'F'

        return {
            'score': score,
            'grade': grade,
            'checks': checks,
            'suggestions': suggestions,
            'total_checks': len(checks),
            'passed_checks': len([c for c in checks if c['status'] == 'pass']),
            'warnings': len([c for c in checks if c['status'] == 'warning']),
            'failures': len([c for c in checks if c['status'] == 'fail'])
        }


# 全局实例
seo_service = SEOService()
