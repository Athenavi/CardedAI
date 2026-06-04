"""
代码片段收藏插件
允许用户收藏和分享代码片段，支持多种编程语言高亮
"""

import time
from datetime import datetime
from typing import Dict, List, Any, Optional

from shared.services.plugins.plugin_manager.core import BasePlugin, plugin_hooks


class CodeSnippetsPlugin(BasePlugin):
    """
    代码片段收藏插件
    
    功能:
    1. 代码片段管理（增删改查）
    2. 多语言语法高亮
    3. 代码片段分类标签
    4. 公开/私有设置
    5. 搜索和过滤
    6. 嵌入代码功能
    """

    def __init__(self):
        super().__init__(
            plugin_id=0,
            name="代码片段收藏",
            slug="code-snippets",
            version="1.0.0"
        )

        # 默认设置
        self.settings = {
            'enable_snippets': True,
            'allow_public_sharing': True,
            'allow_embedding': True,
            'max_snippet_length': 10000,  # 最大代码长度
            'supported_languages': [
                'python', 'javascript', 'typescript', 'java', 'cpp', 'c',
                'html', 'css', 'sql', 'bash', 'json', 'yaml', 'markdown'
            ],
            'default_language': 'python',
            'enable_syntax_highlighting': True,
            'theme': 'default',  # 代码高亮主题
        }

        # 代码片段存储 {snippet_id: snippet_data}
        self.snippets: Dict[str, Dict[str, Any]] = {}

        # 用户片段索引 {user_id: [snippet_id, ...]}
        self.user_snippets: Dict[str, List[str]] = {}

        # 标签索引 {tag: [snippet_id, ...]}
        self.tag_index: Dict[str, List[str]] = {}

    def register_hooks(self):
        """注册钩子"""
        # 在文章中嵌入代码片段
        plugin_hooks.add_filter(
            "article_content",
            self.embed_snippets_in_content,
            priority=10
        )

    def activate(self):
        """激活插件"""
        super().activate()
        print("[CodeSnippets] Plugin activated")

    def deactivate(self):
        """停用插件"""
        super().deactivate()
        print("[CodeSnippets] Plugin deactivated")

    def create_snippet(self, snippet_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建代码片段
        
        Args:
            snippet_data: 片段数据 {title, code, language, user_id, tags, visibility}
            
        Returns:
            创建的片段
        """
        if not self.settings.get('enable_snippets'):
            raise Exception("代码片段功能已禁用")

        # 生成ID
        snippet_id = f"snippet_{int(time.time() * 1000)}"

        # 验证数据
        validation = self._validate_snippet(snippet_data)
        if not validation['valid']:
            raise ValueError(validation['error'])

        snippet = {
            'id': snippet_id,
            'title': snippet_data.get('title', 'Untitled'),
            'code': snippet_data.get('code', ''),
            'language': snippet_data.get('language', self.settings.get('default_language', 'python')),
            'description': snippet_data.get('description', ''),
            'tags': snippet_data.get('tags', []),
            'visibility': snippet_data.get('visibility', 'private'),  # public, private, unlisted
            'user_id': snippet_data.get('user_id'),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'view_count': 0,
            'embed_count': 0,
        }

        self.snippets[snippet_id] = snippet

        # 更新用户索引
        user_id = snippet_data.get('user_id')
        if user_id:
            if user_id not in self.user_snippets:
                self.user_snippets[user_id] = []
            self.user_snippets[user_id].append(snippet_id)

        # 更新标签索引
        for tag in snippet['tags']:
            if tag not in self.tag_index:
                self.tag_index[tag] = []
            self.tag_index[tag].append(snippet_id)

        print(f"[CodeSnippets] Created snippet: {snippet_id}")
        return snippet

    def update_snippet(self, snippet_id: str, updates: Dict[str, Any], user_id: str) -> bool:
        """
        更新代码片段
        
        Args:
            snippet_id: 片段ID
            updates: 更新的字段
            user_id: 用户ID
            
        Returns:
            是否成功更新
        """
        if snippet_id not in self.snippets:
            return False

        snippet = self.snippets[snippet_id]

        # 检查权限
        if snippet['user_id'] != user_id:
            raise PermissionError("无权修改此代码片段")

        # 应用更新
        if 'title' in updates:
            snippet['title'] = updates['title']
        if 'code' in updates:
            snippet['code'] = updates['code']
        if 'language' in updates:
            snippet['language'] = updates['language']
        if 'description' in updates:
            snippet['description'] = updates['description']
        if 'tags' in updates:
            # 更新标签索引
            old_tags = set(snippet['tags'])
            new_tags = set(updates['tags'])
            
            # 移除旧标签
            for tag in old_tags - new_tags:
                if tag in self.tag_index and snippet_id in self.tag_index[tag]:
                    self.tag_index[tag].remove(snippet_id)
            
            # 添加新标签
            for tag in new_tags - old_tags:
                if tag not in self.tag_index:
                    self.tag_index[tag] = []
                self.tag_index[tag].append(snippet_id)
            
            snippet['tags'] = updates['tags']
        
        if 'visibility' in updates:
            snippet['visibility'] = updates['visibility']

        snippet['updated_at'] = datetime.now().isoformat()

        return True

    def delete_snippet(self, snippet_id: str, user_id: str) -> bool:
        """
        删除代码片段
        
        Args:
            snippet_id: 片段ID
            user_id: 用户ID
            
        Returns:
            是否成功删除
        """
        if snippet_id not in self.snippets:
            return False

        snippet = self.snippets[snippet_id]

        # 检查权限
        if snippet['user_id'] != user_id:
            raise PermissionError("无权删除此代码片段")

        # 从标签索引中移除
        for tag in snippet['tags']:
            if tag in self.tag_index and snippet_id in self.tag_index[tag]:
                self.tag_index[tag].remove(snippet_id)

        # 从用户索引中移除
        user_id = snippet['user_id']
        if user_id in self.user_snippets and snippet_id in self.user_snippets[user_id]:
            self.user_snippets[user_id].remove(snippet_id)

        # 删除片段
        del self.snippets[snippet_id]

        print(f"[CodeSnippets] Deleted snippet: {snippet_id}")
        return True

    def get_snippet(self, snippet_id: str, user_id: str = None) -> Optional[Dict[str, Any]]:
        """
        获取代码片段
        
        Args:
            snippet_id: 片段ID
            user_id: 用户ID（用于权限检查）
            
        Returns:
            片段数据
        """
        if snippet_id not in self.snippets:
            return None

        snippet = self.snippets[snippet_id]

        # 权限检查
        if snippet['visibility'] == 'private' and snippet['user_id'] != user_id:
            return None

        # 增加浏览次数
        snippet['view_count'] += 1

        return snippet.copy()

    def get_user_snippets(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取用户的代码片段
        
        Args:
            user_id: 用户ID
            limit: 返回数量
            offset: 偏移量
            
        Returns:
            片段列表
        """
        snippet_ids = self.user_snippets.get(user_id, [])
        
        snippets = []
        for snippet_id in snippet_ids[offset:offset + limit]:
            if snippet_id in self.snippets:
                snippets.append(self.snippets[snippet_id].copy())

        return snippets

    def search_snippets(self, query: str, language: str = None, tags: List[str] = None, 
                       limit: int = 20) -> List[Dict[str, Any]]:
        """
        搜索代码片段
        
        Args:
            query: 搜索关键词
            language: 编程语言
            tags: 标签列表
            limit: 返回数量
            
        Returns:
            片段列表
        """
        results = []

        for snippet_id, snippet in self.snippets.items():
            # 只显示公开的或未列出的
            if snippet['visibility'] not in ['public', 'unlisted']:
                continue

            # 关键词匹配
            if query:
                query_lower = query.lower()
                if (query_lower not in snippet['title'].lower() and
                    query_lower not in snippet.get('description', '').lower()):
                    continue

            # 语言过滤
            if language and snippet['language'] != language:
                continue

            # 标签过滤
            if tags:
                if not any(tag in snippet['tags'] for tag in tags):
                    continue

            results.append(snippet.copy())

        # 按浏览量排序
        results.sort(key=lambda x: x.get('view_count', 0), reverse=True)

        return results[:limit]

    def get_snippets_by_tag(self, tag: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        根据标签获取片段
        
        Args:
            tag: 标签
            limit: 返回数量
            
        Returns:
            片段列表
        """
        snippet_ids = self.tag_index.get(tag, [])
        
        snippets = []
        for snippet_id in snippet_ids[:limit]:
            if snippet_id in self.snippets:
                snippet = self.snippets[snippet_id]
                if snippet['visibility'] in ['public', 'unlisted']:
                    snippets.append(snippet.copy())

        return snippets

    def get_popular_snippets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取热门片段
        
        Args:
            limit: 返回数量
            
        Returns:
            片段列表
        """
        public_snippets = [
            s for s in self.snippets.values()
            if s['visibility'] in ['public', 'unlisted']
        ]

        # 按浏览量排序
        public_snippets.sort(key=lambda x: x.get('view_count', 0), reverse=True)

        return [s.copy() for s in public_snippets[:limit]]

    def generate_embed_code(self, snippet_id: str) -> str:
        """
        生成嵌入代码
        
        Args:
            snippet_id: 片段ID
            
        Returns:
            嵌入HTML代码
        """
        if not self.settings.get('allow_embedding'):
            return '<!-- Embedding is disabled -->'

        if snippet_id not in self.snippets:
            return '<!-- Snippet not found -->'

        snippet = self.snippets[snippet_id]
        
        # 增加嵌入计数
        snippet['embed_count'] += 1

        embed_html = f'''
<div class="code-snippet-embed" data-snippet-id="{snippet_id}">
    <div class="snippet-header">
        <span class="snippet-title">{snippet['title']}</span>
        <span class="snippet-language">{snippet['language']}</span>
    </div>
    <pre class="snippet-code"><code class="language-{snippet['language']}">{self._escape_html(snippet['code'])}</code></pre>
    <div class="snippet-footer">
        <a href="/snippets/{snippet_id}" target="_blank">View on FastBlog</a>
    </div>
</div>
        '''

        return embed_html

    def embed_snippets_in_content(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        在文章内容中嵌入代码片段
        
        Args:
            content_data: 内容数据 {html}
            
        Returns:
            处理后的内容
        """
        html = content_data.get('html', '')
        
        # 查找 [snippet:id] 标记
        import re
        pattern = r'\[snippet:(\w+)\]'
        
        def replace_snippet(match):
            snippet_id = match.group(1)
            return self.generate_embed_code(snippet_id)
        
        html = re.sub(pattern, replace_snippet, html)
        content_data['html'] = html
        
        return content_data

    def get_all_tags(self) -> List[str]:
        """获取所有标签"""
        return list(self.tag_index.keys())

    def _validate_snippet(self, snippet_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证片段数据"""
        if not snippet_data.get('code'):
            return {'valid': False, 'error': '代码不能为空'}

        max_length = self.settings.get('max_snippet_length', 10000)
        if len(snippet_data['code']) > max_length:
            return {'valid': False, 'error': f'代码长度不能超过{max_length}字符'}

        language = snippet_data.get('language', self.settings.get('default_language'))
        supported = self.settings.get('supported_languages', [])
        if language not in supported:
            return {'valid': False, 'error': f'不支持的编程语言: {language}'}

        return {'valid': True, 'error': ''}

    def _escape_html(self, text: str) -> str:
        """转义HTML"""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))

    def get_settings_ui(self) -> Dict[str, Any]:
        """返回设置界面配置"""
        return {
            'fields': [
                {
                    'key': 'enable_snippets',
                    'type': 'boolean',
                    'label': '启用代码片段',
                },
                {
                    'key': 'allow_public_sharing',
                    'type': 'boolean',
                    'label': '允许公开分享',
                },
                {
                    'key': 'allow_embedding',
                    'type': 'boolean',
                    'label': '允许嵌入',
                },
                {
                    'key': 'max_snippet_length',
                    'type': 'number',
                    'label': '最大代码长度',
                    'min': 1000,
                    'max': 50000,
                },
                {
                    'key': 'enable_syntax_highlighting',
                    'type': 'boolean',
                    'label': '启用语法高亮',
                },
                {
                    'key': 'theme',
                    'type': 'select',
                    'label': '高亮主题',
                    'options': [
                        {'value': 'default', 'label': 'Default'},
                        {'value': 'dark', 'label': 'Dark'},
                        {'value': 'monokai', 'label': 'Monokai'},
                    ],
                },
            ],
            'actions': [
                {
                    'type': 'button',
                    'label': '查看热门片段',
                    'action': 'view_popular',
                    'variant': 'outline',
                },
            ]
        }


# 插件实例
plugin_instance = CodeSnippetsPlugin()
