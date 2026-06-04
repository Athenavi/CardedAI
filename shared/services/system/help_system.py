"""
帮助系统服务
提供上下文帮助、帮助标签和文档链接功能
"""
from typing import List, Dict, Any, Optional


class HelpSystem:
    """帮助系统服务"""

    # 默认帮助内容
    DEFAULT_HELP_CONTENT = {
        'admin_dashboard': {
            'title': '管理仪表板',
            'content': '''
                <h3>仪表板概览</h3>
                <p>仪表板显示网站的关键统计信息和快速操作。</p>
                <ul>
                    <li><strong>文章统计</strong> - 查看已发布、草稿和待审文章数量</li>
                    <li><strong>访问统计</strong> - 今日/本周/本月访问量</li>
                    <li><strong>快速操作</strong> - 快速创建新文章或页面</li>
                </ul>
                <h4>常见问题</h4>
                <p><strong>Q: 如何查看详细的访问统计？</strong><br>
                A: 点击"访问统计"卡片可进入详细分析页面。</p>
            ''',
            'related_links': [
                {'title': '文章管理指南', 'url': '/docs/articles'},
                {'title': 'SEO 优化技巧', 'url': '/docs/seo'},
            ]
        },
        'article_editor': {
            'title': '文章编辑器',
            'content': '''
                <h3>使用文章编辑器</h3>
                <p>文章编辑器支持 Markdown 和富文本两种模式。</p>
                <h4>主要功能</h4>
                <ul>
                    <li><strong>标题设置</strong> - 设置文章标题和副标题</li>
                    <li><strong>分类和标签</strong> - 为文章添加分类和标签</li>
                    <li><strong>特色图片</strong> - 上传封面图片</li>
                    <li><strong>SEO 设置</strong> - 自定义 meta 标题和描述</li>
                    <li><strong>定时发布</strong> - 设置未来发布时间</li>
                </ul>
                <h4>快捷键</h4>
                <ul>
                    <li><code>Ctrl/Cmd + S</code> - 保存草稿</li>
                    <li><code>Ctrl/Cmd + P</code> - 预览</li>
                    <li><code>Ctrl/Cmd + Enter</code> - 发布文章</li>
                </ul>
            ''',
            'related_links': [
                {'title': 'Markdown 语法指南', 'url': '/docs/markdown'},
                {'title': 'SEO 最佳实践', 'url': '/docs/seo-tips'},
            ]
        },
        'media_library': {
            'title': '媒体库',
            'content': '''
                <h3>管理媒体文件</h3>
                <p>媒体库支持图片、视频、音频和文档等多种文件类型。</p>
                <h4>支持的文件类型</h4>
                <ul>
                    <li><strong>图片</strong> - JPG, PNG, GIF, WebP, SVG</li>
                    <li><strong>视频</strong> - MP4, WebM, AVI</li>
                    <li><strong>音频</strong> - MP3, WAV, OGG</li>
                    <li><strong>文档</strong> - PDF, DOC, DOCX</li>
                </ul>
                <h4>拖拽上传</h4>
                <p>直接将文件拖拽到媒体库区域即可上传。支持批量上传。</p>
                <h4>文件夹管理</h4>
                <p>可以创建文件夹来组织媒体文件，支持嵌套文件夹结构。</p>
            ''',
            'related_links': [
                {'title': '图片优化指南', 'url': '/docs/image-optimization'},
                {'title': 'SVG 安全上传', 'url': '/docs/svg-security'},
            ]
        },
        'theme_settings': {
            'title': '主题设置',
            'content': '''
                <h3>自定义主题</h3>
                <p>主题设置允许您自定义网站的外观和行为。</p>
                <h4>主要设置项</h4>
                <ul>
                    <li><strong>颜色和字体</strong> - 设置主色调和字体</li>
                    <li><strong>布局</strong> - 选择页面布局和侧边栏位置</li>
                    <li><strong>首页设置</strong> - 配置首页显示内容</li>
                    <li><strong>页脚</strong> - 自定义页脚内容和版权信息</li>
                </ul>
                <h4>预览更改</h4>
                <p>所有更改都会实时预览，满意后点击"保存"应用。</p>
            ''',
            'related_links': [
                {'title': '主题开发指南', 'url': '/docs/theme-development'},
                {'title': '自定义 CSS', 'url': '/docs/custom-css'},
            ]
        },
        'plugin_manager': {
            'title': '插件管理',
            'content': '''
                <h3>管理插件</h3>
                <p>插件可以扩展网站的功能。</p>
                <h4>插件操作</h4>
                <ul>
                    <li><strong>安装</strong> - 从市场搜索并安装插件</li>
                    <li><strong>激活/停用</strong> - 控制插件是否生效</li>
                    <li><strong>配置</strong> - 调整插件设置</li>
                    <li><strong>更新</strong> - 检查并安装最新版本</li>
                    <li><strong>卸载</strong> - 完全移除插件</li>
                </ul>
                <h4>注意事项</h4>
                <ul>
                    <li>定期更新插件以获得最新功能和安全补丁</li>
                    <li>避免安装过多插件影响性能</li>
                    <li>卸载前备份相关数据</li>
                </ul>
            ''',
            'related_links': [
                {'title': '插件开发指南', 'url': '/docs/plugin-development'},
                {'title': '推荐插件列表', 'url': '/docs/recommended-plugins'},
            ]
        },
        'user_management': {
            'title': '用户管理',
            'content': '''
                <h3>管理用户账户</h3>
                <p>创建和管理网站用户及其权限。</p>
                <h4>用户角色</h4>
                <ul>
                    <li><strong>管理员</strong> - 完全访问权限</li>
                    <li><strong>编辑</strong> - 可以管理和发布所有文章</li>
                    <li><strong>作者</strong> - 只能管理自己的文章</li>
                    <li><strong>贡献者</strong> - 可以撰写但不能发布文章</li>
                    <li><strong>订阅者</strong> - 只能阅读内容</li>
                </ul>
                <h4>批量操作</h4>
                <p>可以选择多个用户进行批量操作，如更改角色或删除。</p>
            ''',
            'related_links': [
                {'title': '用户角色详解', 'url': '/docs/user-roles'},
                {'title': '权限管理', 'url': '/docs/permissions'},
            ]
        },
    }

    @classmethod
    def get_help_content(cls, page_key: str, language: str = 'zh_CN') -> Optional[Dict[str, Any]]:
        """
        获取指定页面的帮助内容

        Args:
            page_key: 页面标识符
            language: 语言代码

        Returns:
            帮助内容字典，如果不存在返回 None
        """
        help_data = cls.DEFAULT_HELP_CONTENT.get(page_key)
        if not help_data:
            return None

        return {
            'page_key': page_key,
            'title': help_data['title'],
            'content': help_data['content'],
            'related_links': help_data.get('related_links', []),
            'language': language
        }

    @classmethod
    def get_all_help_topics(cls) -> List[Dict[str, str]]:
        """
        获取所有帮助主题列表

        Returns:
            主题列表
        """
        topics = []
        for key, data in cls.DEFAULT_HELP_CONTENT.items():
            topics.append({
                'key': key,
                'title': data['title']
            })
        return topics

    @classmethod
    def search_help(cls, query: str) -> List[Dict[str, Any]]:
        """
        搜索帮助内容

        Args:
            query: 搜索关键词

        Returns:
            匹配的帮助内容列表
        """
        results = []
        query_lower = query.lower()

        for key, data in cls.DEFAULT_HELP_CONTENT.items():
            # 在标题和内容中搜索
            if (query_lower in data['title'].lower() or
                query_lower in data['content'].lower()):
                results.append({
                    'page_key': key,
                    'title': data['title'],
                    'excerpt': cls._extract_excerpt(data['content'], query),
                    'relevance': cls._calculate_relevance(data, query)
                })

        # 按相关性排序
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results

    @classmethod
    def _extract_excerpt(cls, content: str, query: str, max_length: int = 150) -> str:
        """
        提取包含关键词的摘要

        Args:
            content: 完整内容
            query: 搜索词
            max_length: 最大长度

        Returns:
            摘要文本
        """
        # 简单实现：返回前 max_length 个字符
        import re
        # 移除 HTML 标签
        text = re.sub(r'<[^>]+>', '', content)
        text = ' '.join(text.split())

        if len(text) <= max_length:
            return text

        # 查找关键词位置
        query_lower = query.lower()
        text_lower = text.lower()
        pos = text_lower.find(query_lower)

        if pos == -1:
            return text[:max_length] + '...'

        # 从关键词前后截取
        start = max(0, pos - 50)
        end = min(len(text), pos + len(query) + 100)

        excerpt = text[start:end]
        if start > 0:
            excerpt = '...' + excerpt
        if end < len(text):
            excerpt += '...'

        return excerpt

    @classmethod
    def _calculate_relevance(cls, help_data: Dict, query: str) -> float:
        """
        计算相关性分数

        Args:
            help_data: 帮助数据
            query: 搜索词

        Returns:
            相关性分数 (0-1)
        """
        score = 0.0
        query_lower = query.lower()

        # 标题匹配权重更高
        if query_lower in help_data['title'].lower():
            score += 0.5

        # 内容匹配
        if query_lower in help_data['content'].lower():
            score += 0.3

        # 相关链接标题匹配
        for link in help_data.get('related_links', []):
            if query_lower in link['title'].lower():
                score += 0.2

        return min(score, 1.0)

    @classmethod
    def add_custom_help(cls, page_key: str, title: str, content: str,
                       related_links: List[Dict[str, str]] = None):
        """
        添加自定义帮助内容（供插件使用）

        Args:
            page_key: 页面标识符
            title: 帮助标题
            content: 帮助内容（HTML）
            related_links: 相关链接
        """
        cls.DEFAULT_HELP_CONTENT[page_key] = {
            'title': title,
            'content': content,
            'related_links': related_links or []
        }

    @classmethod
    def get_field_tooltip(cls, field_name: str, context: str = 'general') -> Optional[str]:
        """
        获取字段的 tooltip 提示

        Args:
            field_name: 字段名称
            context: 上下文（页面或模块）

        Returns:
            提示文本
        """
        tooltips = {
            'slug': 'URL 友好的标识符，只允许小写字母、数字和连字符',
            'excerpt': '文章摘要，用于列表页显示和 SEO 描述',
            'featured_image': '文章封面图，建议在列表页和社交媒体分享时显示',
            'tags': '用逗号分隔的标签，帮助读者发现相关内容',
            'status': '草稿不会公开显示，已发布文章对所有访客可见',
            'publish_date': '留空则立即发布，设置未来时间可定时发布',
            'meta_title': '搜索引擎显示的标题，建议 50-60 个字符',
            'meta_description': '搜索引擎显示的描述，建议 150-160 个字符',
        }

        return tooltips.get(field_name)

    @classmethod
    def get_video_tutorials(cls, topic: str = None) -> List[Dict[str, str]]:
        """
        获取视频教程列表

        Args:
            topic: 主题过滤（可选）

        Returns:
            教程列表
        """
        tutorials = [
            {
                'id': 'getting-started',
                'title': '快速入门指南',
                'description': '学习如何使用 FastBlog 的基本功能',
                'duration': '5:30',
                'url': '/tutorials/getting-started',
                'thumbnail': '/api/v2/static/tutorials/getting-started.jpg'
            },
            {
                'id': 'writing-articles',
                'title': '撰写优秀文章',
                'description': '掌握文章编辑器的所有功能',
                'duration': '8:15',
                'url': '/tutorials/writing-articles',
                'thumbnail': '/api/v2/static/tutorials/writing.jpg'
            },
            {
                'id': 'seo-optimization',
                'title': 'SEO 优化技巧',
                'description': '提高文章在搜索引擎中的排名',
                'duration': '12:00',
                'url': '/tutorials/seo',
                'thumbnail': '/api/v2/static/tutorials/seo.jpg'
            },
        ]

        if topic:
            tutorials = [t for t in tutorials if topic.lower() in t['title'].lower()]

        return tutorials
