"""
Shortcode短代码系统
提供类似WordPress的短代码解析功能
"""

import re
from typing import Dict, Callable


class ShortcodeService:
    """
    Shortcode短代码服务
    
    功能:
    1. Shortcode解析器
    2. 内置Shortcode(gallery/embed/button/columns)
    3. 插件扩展支持
    4. Shortcode钩子
    """

    def __init__(self):
        # 注册的shortcodes
        self.shortcodes: Dict[str, Callable] = {}
        
        # 注册内置shortcodes
        self._register_builtin_shortcodes()

    def _register_builtin_shortcodes(self):
        """注册内置短代码"""
        self.register('gallery', self._gallery_shortcode)
        self.register('embed', self._embed_shortcode)
        self.register('button', self._button_shortcode)
        self.register('columns', self._columns_shortcode)
        self.register('column', self._column_shortcode)
        self.register('caption', self._caption_shortcode)

    def register(self, name: str, handler: Callable):
        """
        注册shortcode
        
        Args:
            name: shortcode名称
            handler: 处理函数,接收 (attrs, content) 参数
        """
        self.shortcodes[name.lower()] = handler

    def unregister(self, name: str):
        """
        注销shortcode
        
        Args:
            name: shortcode名称
        """
        if name.lower() in self.shortcodes:
            del self.shortcodes[name.lower()]

    def parse(self, content: str) -> str:
        """
        解析内容中的shortcodes
        
        Args:
            content: 包含shortcodes的内容
            
        Returns:
            解析后的内容
        """
        if not content:
            return content
        
        # 匹配shortcode模式: [name attr="value"]content[/name]
        pattern = r'\[(\w+)([^\]]*)\](.*?)\[\/\1\]'
        
        def replace_shortcode(match):
            name = match.group(1).lower()
            attrs_str = match.group(2)
            content = match.group(3)
            
            # 解析属性
            attrs = self._parse_attrs(attrs_str)
            
            # 查找处理器
            if name in self.shortcodes:
                try:
                    return self.shortcodes[name](attrs, content)
                except Exception as e:
                    return f'<!-- Shortcode error: {str(e)} -->'
            else:
                # 未注册的shortcode,保留原文
                return match.group(0)
        
        # 替换所有shortcodes
        result = re.sub(pattern, replace_shortcode, content, flags=re.DOTALL)
        
        return result

    def _parse_attrs(self, attrs_str: str) -> Dict[str, str]:
        """
        解析shortcode属性字符串
        
        Args:
            attrs_str: 属性字符串,如 'id="123" class="test"'
            
        Returns:
            属性字典
        """
        attrs = {}
        
        if not attrs_str or not attrs_str.strip():
            return attrs
        
        # 匹配 key="value" 或 key='value'
        pattern = r'(\w+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\')'
        matches = re.findall(pattern, attrs_str)
        
        for match in matches:
            key = match[0]
            value = match[1] or match[2]  # 取双引号或单引号的值
            attrs[key] = value
        
        return attrs

    # ========== 内置Shortcode处理器 ==========

    def _gallery_shortcode(self, attrs: Dict[str, str], content: str) -> str:
        """画廊短代码: [gallery ids="1,2,3" columns="3"]"""
        ids = attrs.get('ids', '')
        columns = int(attrs.get('columns', '3'))
        
        if not ids:
            return '<!-- Gallery: No images specified -->'
        
        image_ids = [id.strip() for id in ids.split(',') if id.strip()]
        
        html = f'<div class="gallery grid grid-cols-{columns} gap-4">'
        for img_id in image_ids:
            html += f'''
            <div class="gallery-item">
                <img src="/api/v1/media/{img_id}" alt="Gallery Image" loading="lazy" />
            </div>
            '''
        html += '</div>'
        
        return html

    def _embed_shortcode(self, attrs: Dict[str, str], content: str) -> str:
        """嵌入短代码: [embed url="https://youtube.com/..."]"""
        url = attrs.get('url', content.strip())
        
        if not url:
            return '<!-- Embed: No URL specified -->'
        
        # YouTube
        youtube_match = re.match(r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/(?:watch\?v=)?(.+)', url)
        if youtube_match:
            video_id = youtube_match.group(1).split('&')[0]
            return f'''
            <div class="embed-container aspect-video">
                <iframe 
                    src="https://www.youtube.com/embed/{video_id}" 
                    frameborder="0" 
                    allowfullscreen
                    class="w-full h-full"
                ></iframe>
            </div>
            '''
        
        # Bilibili
        bilibili_match = re.match(r'(?:https?:\/\/)?(?:www\.)?bilibili\.com\/video\/(.+)', url)
        if bilibili_match:
            video_id = bilibili_match.group(1)
            return f'''
            <div class="embed-container aspect-video">
                <iframe 
                    src="//player.bilibili.com/player.html?bvid={video_id}" 
                    frameborder="0" 
                    allowfullscreen
                    class="w-full h-full"
                ></iframe>
            </div>
            '''
        
        # 通用iframe
        return f'''
        <div class="embed-container">
            <iframe src="{url}" frameborder="0" class="w-full"></iframe>
        </div>
        '''

    def _button_shortcode(self, attrs: Dict[str, str], content: str) -> str:
        """按钮短代码: [button url="#" style="primary"]Click Me[/button]"""
        url = attrs.get('url', '#')
        style = attrs.get('style', 'primary')
        target = attrs.get('target', '_self')
        
        style_classes = {
            'primary': 'bg-blue-600 hover:bg-blue-700 text-white',
            'secondary': 'bg-gray-600 hover:bg-gray-700 text-white',
            'success': 'bg-green-600 hover:bg-green-700 text-white',
            'danger': 'bg-red-600 hover:bg-red-700 text-white',
            'outline': 'border-2 border-blue-600 text-blue-600 hover:bg-blue-50'
        }
        
        css_class = style_classes.get(style, style_classes['primary'])
        
        return f'''
        <a href="{url}" target="{target}" class="inline-block px-6 py-3 rounded-lg font-semibold transition-colors {css_class}">
            {content}
        </a>
        '''

    def _columns_shortcode(self, attrs: Dict[str, str], content: str) -> str:
        """分栏短代码: [columns count="2"][/columns]"""
        count = int(attrs.get('count', '2'))
        
        return f'''
        <div class="grid grid-cols-{count} gap-6 my-6">
            {content}
        </div>
        '''

    def _column_shortcode(self, attrs: Dict[str, str], content: str) -> str:
        """列短代码: [column span="1"][/column]"""
        span = attrs.get('span', '1')
        
        return f'''
        <div class="col-span-{span}">
            {content}
        </div>
        '''

    def _caption_shortcode(self, attrs: Dict[str, str], content: str) -> str:
        """标题短代码: [caption align="center"]Image Caption[/caption]"""
        align = attrs.get('align', 'center')
        
        align_classes = {
            'left': 'text-left',
            'center': 'text-center',
            'right': 'text-right'
        }
        
        css_class = align_classes.get(align, 'text-center')
        
        return f'''
        <p class="text-sm text-gray-600 dark:text-gray-400 italic mt-2 {css_class}">
            {content}
        </p>
        '''


# 全局实例
shortcode_service = ShortcodeService()
