"""
智能相关内容推荐插件
整合基于标签、分类、内容相似度的文章推荐功能

功能模块:
1. 相关文章推荐 - 基于标签和分类
2. 智能推荐算法 - 内容相似度分析
3. 手动推荐设置 - 自定义推荐关系
4. 推荐小部件 - 可配置的展示组件
"""

from typing import Dict, List, Any

from shared.services.plugins.plugin_manager.core import BasePlugin, plugin_hooks


class RelatedPlugin(BasePlugin):
    """
    智能相关内容推荐插件
    
    整合了以下原有插件的功能:
    - related-posts: 相关文章
    - related-content: 相关内容增强
    """

    def __init__(self):
        super().__init__(
            plugin_id=0,
            name="相关内容推荐",
            slug="related",
            version="2.0.0"
        )

        # ==================== 推荐设置 ====================
        self.settings = {
            'enable_related': True,
            'limit': 5,
            'method': 'mixed',  # tags, categories, similarity, mixed, popular
            'min_similarity': 0.3,
            'show_in_sidebar': True,
            'show_in_article_footer': True,
        }

        # 手动推荐映射
        self.manual_recommendations: Dict[str, List[str]] = {}

        # 推荐统计
        self.recommendation_stats = {
            'total_shown': 0,
            'total_clicked': 0,
            'by_method': {},
        }

    def register_hooks(self):
        """注册钩子"""
        if self.settings.get('enable_related'):
            # 文章页面注入相关内容
            plugin_hooks.add_action(
                "article_page_footer",
                self.render_related_content,
                priority=10
            )

    def activate(self):
        """激活插件"""
        super().activate()
        print("[Related] Plugin activated - Recommendation engine initialized")

    def deactivate(self):
        """停用插件"""
        super().deactivate()
        print("[Related] Plugin deactivated")

    # ==================== 相关推荐 ====================

    def render_related_content(self, context: Dict[str, Any]):
        """渲染相关内容"""
        if not self.settings.get('enable_related'):
            return

        article = context.get('article', {})
        if not article:
            return

        method = self.settings.get('method', 'mixed')
        limit = self.settings.get('limit', 5)

        # 获取相关文章
        related_articles = self.get_related_articles(article, method, limit)

        if related_articles:
            html = self._generate_related_html(related_articles)

            if 'related_content' not in context:
                context['related_content'] = ''

            context['related_content'] += html

            # 更新统计
            self.recommendation_stats['total_shown'] += len(related_articles)

    def get_related_articles(self, article: Dict[str, Any], method: str = None, limit: int = None) -> List[
        Dict[str, Any]]:
        """
        获取相关文章
        
        Args:
            article: 当前文章
            method: 推荐方法
            limit: 返回数量
            
        Returns:
            相关文章列表
        """
        if not self.settings.get('enable_related'):
            return []

        method = method or self.settings.get('method', 'mixed')
        limit = limit or self.settings.get('limit', 5)

        # 检查手动推荐
        article_id = str(article.get('id', ''))
        if article_id in self.manual_recommendations:
            manual_ids = self.manual_recommendations[article_id]
            # 这里应该从数据库获取文章详情
            # 简化实现：返回空列表
            pass

        # 根据方法获取相关文章
        if method == 'tags':
            related = self._get_by_tags(article, limit)
        elif method == 'categories':
            related = self._get_by_categories(article, limit)
        elif method == 'similarity':
            related = self._get_by_similarity(article, limit)
        elif method == 'popular':
            related = self._get_popular(limit)
        else:  # mixed
            related = self._get_mixed(article, limit)

        # 排除当前文章
        related = [r for r in related if r.get('id') != article.get('id')]

        # 限制数量
        return related[:limit]

    def _get_by_tags(self, article: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """基于标签推荐"""
        article_tags = set(article.get('tags', []))
        if not article_tags:
            return []

        # 这里应该从数据库查询有相同标签的文章
        # 简化实现：返回空列表
        print(f"[Related] Finding articles with tags: {article_tags}")
        return []

    def _get_by_categories(self, article: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """基于分类推荐"""
        article_categories = article.get('categories', [])
        if not article_categories:
            return []

        # 这里应该从数据库查询同分类的文章
        # 简化实现：返回空列表
        print(f"[Related] Finding articles in categories: {article_categories}")
        return []

    def _get_by_similarity(self, article: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """基于内容相似度推荐"""
        content = article.get('content', '')
        if not content:
            return []

        # 这里应该使用NLP算法计算相似度
        # 简化实现：返回空列表
        print(f"[Related] Finding similar articles (min_similarity: {self.settings.get('min_similarity', 0.3)})")
        return []

    def _get_popular(self, limit: int) -> List[Dict[str, Any]]:
        """获取热门文章"""
        # 这里应该从数据库查询热门文章
        # 简化实现：返回空列表
        print(f"[Related] Getting popular articles (limit: {limit})")
        return []

    def _get_mixed(self, article: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """混合推荐（标签+分类+热门）"""
        all_related = []

        # 基于标签
        tag_based = self._get_by_tags(article, limit // 2)
        all_related.extend(tag_based)

        # 基于分类（去重）
        existing_ids = {r.get('id') for r in all_related}
        cat_based = self._get_by_categories(article, limit // 2)
        for r in cat_based:
            if r.get('id') not in existing_ids:
                all_related.append(r)
                existing_ids.add(r.get('id'))

        # 如果还不够，补充热门文章
        if len(all_related) < limit:
            remaining = limit - len(all_related)
            popular = self._get_popular(remaining)
            for r in popular:
                if r.get('id') not in existing_ids:
                    all_related.append(r)

        return all_related

    def _generate_related_html(self, articles: List[Dict[str, Any]]) -> str:
        """生成相关文章HTML"""
        if not articles:
            return ''

        items_html = ''
        for article in articles:
            title = article.get('title', '')
            url = article.get('url', '#')
            excerpt = article.get('excerpt', '')[:100]
            featured_image = article.get('featured_image', '')

            image_html = f'<img src="{featured_image}" alt="{title}">' if featured_image else ''

            items_html += f'''
            <div class="related-article-item">
                {image_html}
                <h4><a href="{url}">{title}</a></h4>
                <p>{excerpt}</p>
            </div>
            '''

        return f'''
        <div class="related-content-section">
            <h3>相关文章</h3>
            <div class="related-articles-grid">
                {items_html}
            </div>
        </div>
        '''

    # ==================== 手动推荐 ====================

    def add_manual_recommendation(self, article_id: str, related_ids: List[str]):
        """添加手动推荐"""
        self.manual_recommendations[str(article_id)] = related_ids
        print(f"[Related] Manual recommendations added for article {article_id}")

    def remove_manual_recommendation(self, article_id: str):
        """删除手动推荐"""
        if str(article_id) in self.manual_recommendations:
            del self.manual_recommendations[str(article_id)]
            print(f"[Related] Manual recommendations removed for article {article_id}")

    # ==================== 统计分析 ====================

    def track_recommendation_click(self, article_id: str, recommended_id: str):
        """追踪推荐点击"""
        self.recommendation_stats['total_clicked'] += 1

    def get_recommendation_stats(self) -> Dict[str, Any]:
        """获取推荐统计"""
        total_shown = self.recommendation_stats['total_shown']
        total_clicked = self.recommendation_stats['total_clicked']

        click_rate = round((total_clicked / total_shown * 100) if total_shown > 0 else 0, 2)

        return {
            'total_shown': total_shown,
            'total_clicked': total_clicked,
            'click_rate': click_rate,
            'by_method': self.recommendation_stats['by_method'],
        }

    # ==================== 管理API ====================

    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表板数据"""
        return {
            'stats': self.get_recommendation_stats(),
            'manual_recommendations_count': len(self.manual_recommendations),
        }

    def get_admin_ui_config(self) -> Dict[str, Any]:
        """获取管理界面配置"""
        return {
            'title': '相关内容推荐',
            'icon': '🔗',
            'sections': [
                {
                    'title': '推荐概览',
                    'widgets': [
                        {'type': 'stat', 'label': '总展示数', 'value': self.recommendation_stats['total_shown']},
                        {'type': 'stat', 'label': '总点击数', 'value': self.recommendation_stats['total_clicked']},
                        {'type': 'stat', 'label': '点击率',
                         'value': f"{self.get_recommendation_stats()['click_rate']}%"},
                    ],
                },
                {
                    'title': '推荐设置',
                    'fields': [
                        {
                            'key': 'enable_related',
                            'label': '启用相关推荐',
                            'type': 'boolean',
                        },
                        {
                            'key': 'limit',
                            'label': '推荐数量',
                            'type': 'number',
                            'min': 1,
                            'max': 20,
                            'default': 5,
                        },
                        {
                            'key': 'method',
                            'label': '推荐方法',
                            'type': 'select',
                            'options': ['tags', 'categories', 'similarity', 'mixed', 'popular'],
                        },
                        {
                            'key': 'min_similarity',
                            'label': '最小相似度',
                            'type': 'number',
                            'min': 0,
                            'max': 1,
                            'step': 0.1,
                            'default': 0.3,
                        },
                    ],
                },
                {
                    'title': '显示设置',
                    'fields': [
                        {
                            'key': 'show_in_article_footer',
                            'label': '在文章底部显示',
                            'type': 'boolean',
                        },
                        {
                            'key': 'show_in_sidebar',
                            'label': '在侧边栏显示',
                            'type': 'boolean',
                        },
                    ],
                },
            ],
        }


# 导出插件实例
plugin = RelatedPlugin()
