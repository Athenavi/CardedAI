"""
AMP (Accelerated Mobile Pages) 服务
生成符合AMP规范的移动页面
类似WordPress AMP插件
"""
import re
from datetime import datetime
from typing import Dict, Any


class AMPService:
    """AMP页面生成服务"""
    
    def __init__(self):
        self.amp_css_limit = 50000  # 50KB限制
    
    def generate_amp_html(self, article_data: Dict[str, Any]) -> str:
        """
        生成AMP HTML页面
        
        Args:
            article_data: 文章数据字典
            
        Returns:
            AMP HTML字符串
        """
        title = article_data.get('title', '')
        content = article_data.get('content', '')
        author = article_data.get('author', {})
        published_time = article_data.get('published_at', datetime.now().isoformat())
        modified_time = article_data.get('updated_at', published_time)
        featured_image = article_data.get('featured_image', '')
        canonical_url = article_data.get('canonical_url', '')
        
        # 转换内容为AMP兼容格式
        amp_content = self._convert_to_amp(content)
        
        # 提取关键CSS(简化版)
        critical_css = self._extract_critical_css()
        
        # 构建AMP HTML
        amp_html = f"""<!doctype html>
<html ⚡ lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,minimum-scale=1,initial-scale=1">
    <link rel="canonical" href="{canonical_url}">
    <title>{title}</title>
    
    <!-- AMP Boilerplate -->
    <style amp-boilerplate>body{{-webkit-animation:-amp-start 8s steps(1,end) 0s 1 normal both;-moz-animation:-amp-start 8s steps(1,end) 0s 1 normal both;-ms-animation:-amp-start 8s steps(1,end) 0s 1 normal both;animation:-amp-start 8s steps(1,end) 0s 1 normal both}}@-webkit-keyframes -amp-start{{from{{visibility:hidden}}to{{visibility:visible}}}}@-moz-keyframes -amp-start{{from{{visibility:hidden}}to{{visibility:visible}}}}@-ms-keyframes -amp-start{{from{{visibility:hidden}}to{{visibility:visible}}}}@-o-keyframes -amp-start{{from{{visibility:hidden}}to{{visibility:visible}}}}@keyframes -amp-start{{from{{visibility:hidden}}to{{visibility:visible}}}}</style><noscript><style amp-boilerplate>body{{-webkit-animation:none;-moz-animation:none;-ms-animation:none;animation:none}}</style></noscript>
    
    <!-- AMP Runtime -->
    <script async src="https://cdn.ampproject.org/v0.js"></script>
    
    <!-- AMP Components -->
    <script async custom-element="amp-img" src="https://cdn.ampproject.org/v0/amp-img-0.1.js"></script>
    <script async custom-element="amp-analytics" src="https://cdn.ampproject.org/v0/amp-analytics-0.1.js"></script>
    
    <!-- Structured Data -->
    <script type="application/ld+json">
    {{
      "@context": "http://schema.org",
      "@type": "NewsArticle",
      "headline": "{title}",
      "datePublished": "{published_time}",
      "dateModified": "{modified_time}",
      "author": {{
        "@type": "Person",
        "name": "{author.get('name', '')}"
      }},
      "publisher": {{
        "@type": "Organization",
        "name": "FastBlog"
      }}
    }}
    </script>
    
    <!-- Custom CSS (max 50KB) -->
    <style amp-custom>
    {critical_css}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      line-height: 1.6;
      color: #333;
      max-width: 800px;
      margin: 0 auto;
      padding: 20px;
    }}
    .amp-header {{
      margin-bottom: 30px;
    }}
    .amp-title {{
      font-size: 2em;
      margin-bottom: 10px;
    }}
    .amp-meta {{
      color: #666;
      font-size: 0.9em;
    }}
    .amp-content {{
      font-size: 1.1em;
    }}
    .amp-content img {{
      max-width: 100%;
      height: auto;
    }}
    </style>
</head>
<body>
    <article>
        <header class="amp-header">
            <h1 class="amp-title">{title}</h1>
            <div class="amp-meta">
                <span>作者: {author.get('name', '')}</span> | 
                <span>发布时间: {published_time[:10]}</span>
            </div>
        </header>
        
        {f'<amp-img src="{featured_image}" width="800" height="450" layout="responsive" alt="{title}"></amp-img>' if featured_image else ''}
        
        <div class="amp-content">
            {amp_content}
        </div>
    </article>
    
    <!-- Analytics (optional) -->
    <amp-analytics type="googleanalytics">
        <script type="application/json">
        {{
          "vars": {{
            "account": "UA-XXXXX-Y"
          }},
          "triggers": {{
            "trackPageview": {{
              "on": "visible",
              "request": "pageview"
            }}
          }}
        }}
        </script>
    </amp-analytics>
</body>
</html>"""
        
        return amp_html
    
    def _convert_to_amp(self, html_content: str) -> str:
        """
        将普通HTML转换为AMP兼容格式
        
        Args:
            html_content: 原始HTML内容
            
        Returns:
            AMP兼容的HTML
        """
        if not html_content:
            return ''
        
        # 转换img为amp-img
        html_content = re.sub(
            r'<img\s+([^>]*)src=["\']([^"\']+)["\']([^>]*)>',
            r'<amp-img \1src="\2"\3 width="800" height="600" layout="responsive"></amp-img>',
            html_content
        )
        
        # 移除不允许的标签
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<iframe[^>]*>.*?</iframe>', '[Embedded content removed for AMP]', html_content, flags=re.DOTALL)
        
        # 移除内联事件处理器
        html_content = re.sub(r'\son\w+\s*=\s*["\'][^"\']*["\']', '', html_content)
        
        return html_content
    
    def _extract_critical_css(self) -> str:
        """
        提取关键CSS(Above-the-fold样式)
        
        Returns:
            关键CSS字符串
        """
        # 简化版:返回基础样式
        # 实际实现应该分析页面结构,提取首屏CSS
        return """
        /* Critical CSS - Above the fold */
        * {
          box-sizing: border-box;
        }
        body {
          margin: 0;
          padding: 0;
        }
        h1, h2, h3 {
          margin-top: 0;
        }
        p {
          margin-bottom: 1em;
        }
        """
    
    def validate_amp(self, amp_html: str) -> Dict[str, Any]:
        """
        验证AMP HTML是否符合规范
        
        Args:
            amp_html: AMP HTML字符串
            
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        
        # 检查必需的AMP属性
        if '<html ⚡' not in amp_html and '<html amp' not in amp_html:
            errors.append('Missing AMP attribute on <html> tag')
        
        # 检查boilerplate
        if 'amp-boilerplate' not in amp_html:
            errors.append('Missing AMP boilerplate')
        
        # 检查CSS大小
        css_match = re.search(r'<style amp-custom>(.*?)</style>', amp_html, re.DOTALL)
        if css_match:
            css_size = len(css_match.group(1).encode('utf-8'))
            if css_size > self.amp_css_limit:
                errors.append(f'Custom CSS exceeds 50KB limit: {css_size / 1024:.1f}KB')
        
        # 检查不允许的标签
        forbidden_tags = ['script', 'iframe', 'form', 'input', 'button']
        for tag in forbidden_tags:
            if re.search(rf'<{tag}[^>]*>', amp_html, re.IGNORECASE):
                if tag != 'script':  # script允许用于JSON-LD和AMP组件
                    warnings.append(f'Found forbidden tag: <{tag}>')
        
        # 检查必需的meta标签
        if '<meta charset="utf-8">' not in amp_html:
            errors.append('Missing charset meta tag')
        
        if '<meta name="viewport"' not in amp_html:
            errors.append('Missing viewport meta tag')
        
        # 检查canonical链接
        if '<link rel="canonical"' not in amp_html:
            warnings.append('Missing canonical link')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'error_count': len(errors),
            'warning_count': len(warnings),
        }
    
    def add_amp_link_to_canonical(self, canonical_url: str) -> str:
        """
        在规范URL页面添加AMP链接标记
        
        Args:
            canonical_url: 规范URL
            
        Returns:
            AMP URL
        """
        # 通常AMP URL是规范URL + /amp/
        if canonical_url.endswith('/'):
            return canonical_url + 'amp/'
        else:
            return canonical_url + '/amp/'


# 单例实例
amp_service = AMPService()
