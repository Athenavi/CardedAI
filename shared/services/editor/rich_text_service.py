"""
富文本编辑器服务
提供HTML与Markdown转换、内容清理等功能
"""

import re
from html import unescape


class RichTextService:
    """
    富文本编辑器服务
    
    功能:
    1. HTML到Markdown转换
    2. Markdown到HTML转换
    3. 内容清理和 sanitization
    4. 图片/视频处理
    """

    def __init__(self):
        # 允许的HTML标签白名单
        self.allowed_tags = {
            'p', 'br', 'strong', 'b', 'em', 'i', 'u', 's',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li',
            'blockquote', 'code', 'pre',
            'a', 'img', 'video', 'audio',
            'table', 'thead', 'tbody', 'tr', 'th', 'td',
            'hr', 'div', 'span'
        }

        # 允许的属性白名单
        self.allowed_attributes = {
            'a': {'href', 'title', 'target'},
            'img': {'src', 'alt', 'width', 'height'},
            'video': {'src', 'controls', 'width', 'height'},
            'audio': {'src', 'controls'},
            '*': {'class', 'style'}  # 所有元素允许class和style
        }

    def html_to_markdown(self, html: str) -> str:
        """
        将HTML转换为Markdown
        
        Args:
            html: HTML字符串
            
        Returns:
            Markdown字符串
        """
        if not html:
            return ""

        markdown = html

        # 标题转换
        for i in range(6, 0, -1):
            pattern = f'<h{i}[^>]*>(.*?)</h{i}>'
            replacement = '#' * i + r' \1\n\n'
            markdown = re.sub(pattern, replacement, markdown, flags=re.DOTALL | re.IGNORECASE)

        # 粗体
        markdown = re.sub(r'<(strong|b)[^>]*>(.*?)</\1>', r'**\2**', markdown, flags=re.IGNORECASE)

        # 斜体
        markdown = re.sub(r'<(em|i)[^>]*>(.*?)</\1>', r'*\2*', markdown, flags=re.IGNORECASE)

        # 删除线
        markdown = re.sub(r'<(s|del|strike)[^>]*>(.*?)</\1>', r'~~\2~~', markdown, flags=re.IGNORECASE)

        # 下划线 (Markdown原生不支持,保留为HTML)

        # 链接
        markdown = re.sub(
            r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>',
            r'[\2](\1)',
            markdown,
            flags=re.IGNORECASE
        )

        # 图片
        markdown = re.sub(
            r'<img[^>]*src=["\']([^"\']*)["\'][^>]*alt=["\']([^"\']*)["\'][^>]*/?>',
            r'![\2](\1)',
            markdown,
            flags=re.IGNORECASE
        )
        markdown = re.sub(
            r'<img[^>]*src=["\']([^"\']*)["\'][^>]*/?>',
            r'![](\1)',
            markdown,
            flags=re.IGNORECASE
        )

        # 代码块
        markdown = re.sub(r'<pre[^>]*><code[^>]*>(.*?)</code></pre>', r'```\n\1\n```', markdown,
                          flags=re.DOTALL | re.IGNORECASE)
        markdown = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', markdown, flags=re.IGNORECASE)

        # 引用
        markdown = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>', r'> \1\n', markdown, flags=re.DOTALL | re.IGNORECASE)

        # 无序列表
        markdown = re.sub(r'<ul[^>]*>(.*?)</ul>', r'\1', markdown, flags=re.DOTALL | re.IGNORECASE)
        markdown = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', markdown, flags=re.DOTALL | re.IGNORECASE)

        # 有序列表
        markdown = re.sub(r'<ol[^>]*>(.*?)</ol>', r'\1', markdown, flags=re.DOTALL | re.IGNORECASE)
        # 简单的有序列表项(实际需要更复杂的逻辑来编号)
        markdown = re.sub(r'<li[^>]*>(.*?)</li>', r'1. \1\n', markdown, flags=re.DOTALL | re.IGNORECASE)

        # 段落
        markdown = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', markdown, flags=re.DOTALL | re.IGNORECASE)

        # 换行
        markdown = re.sub(r'<br\s*/?>', '\n', markdown, flags=re.IGNORECASE)

        # 水平线
        markdown = re.sub(r'<hr\s*/?>', '\n---\n', markdown, flags=re.IGNORECASE)

        # 视频 (保留为HTML)
        # 音频 (保留为HTML)

        # 清理多余的空白
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        markdown = markdown.strip()

        return markdown

    def sanitize_html(self, html: str) -> str:
        """
        清理HTML,移除不安全的标签和属性
        
        Args:
            html: HTML字符串
            
        Returns:
            清理后的HTML
        """
        if not html:
            return ""

        # 移除script标签
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)

        # 移除危险的事件处理器属性
        html = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', html, flags=re.IGNORECASE)
        html = re.sub(r'\s+on\w+\s*=\s*[^\s>]+', '', html, flags=re.IGNORECASE)

        # 移除javascript:协议
        html = re.sub(r'href\s*=\s*["\']javascript:[^"\']*["\']', 'href="#"', html, flags=re.IGNORECASE)

        return html

    def extract_text_from_html(self, html: str, max_length: int = 200) -> str:
        """
        从HTML中提取纯文本
        
        Args:
            html: HTML字符串
            max_length: 最大长度
            
        Returns:
            纯文本
        """
        if not html:
            return ""

        # 移除所有HTML标签
        text = re.sub(r'<[^>]+>', '', html)

        # 解码HTML实体
        text = unescape(text)

        # 清理空白
        text = re.sub(r'\s+', ' ', text).strip()

        # 截断
        if len(text) > max_length:
            text = text[:max_length] + '...'

        return text

    def extract_images_from_html(self, html: str) -> list:
        """
        从HTML中提取所有图片URL
        
        Args:
            html: HTML字符串
            
        Returns:
            图片URL列表
        """
        if not html:
            return []

        # 匹配img标签的src属性
        pattern = r'<img[^>]*src=["\']([^"\']+)["\'][^>]*/?>'
        matches = re.findall(pattern, html, flags=re.IGNORECASE)

        return matches


# 全局实例
rich_text_service = RichTextService()
