"""
图片懒加载服务

提供图片懒加载的HTML生成和JavaScript支持
支持IntersectionObserver API和渐进式加载
"""

from typing import Optional


class ImageLazyLoadService:
    """
    图片懒加载服务
    
    生成懒加载图片HTML和所需的JavaScript代码
    """

    def __init__(self, placeholder_color: str = "#f0f0f0",
                 fade_in_duration: int = 300,
                 root_margin: str = "200px"):
        """
        初始化懒加载服务
        
        Args:
            placeholder_color: 占位符背景色
            fade_in_duration: 淡入动画时长(毫秒)
            root_margin: IntersectionObserver的rootMargin
        """
        self.placeholder_color = placeholder_color
        self.fade_in_duration = fade_in_duration
        self.root_margin = root_margin

    def generate_lazy_image(self, src: str, alt: str = "",
                            width: Optional[int] = None,
                            height: Optional[int] = None,
                            class_name: str = "",
                            loading_strategy: str = "lazy") -> str:
        """
        生成懒加载图片HTML
        
        Args:
            src: 图片URL
            alt: 替代文本
            width: 图片宽度
            height: 图片高度
            class_name: CSS类名
            loading_strategy: 加载策略 (lazy, eager, auto)
        
        Returns:
            懒加载图片HTML
        """
        # 构建样式
        styles = [
            f"background-color: {self.placeholder_color}",
            "transition: opacity 0.3s ease-in-out",
        ]

        if width:
            styles.append(f"width: {width}px")
        if height:
            styles.append(f"height: {height}px")

        style_attr = f'style="{"; ".join(styles)}"' if styles else ""
        class_attr = f'class="lazy-image {class_name}"' if class_name else 'class="lazy-image"'

        # 生成HTML
        html = f'''<img 
            {class_attr}
            data-src="{src}"
            alt="{alt}"
            {style_attr}
            loading="{loading_strategy}"
        />'''

        return html

    def generate_progressive_image(self, low_quality_src: str,
                                   high_quality_src: str,
                                   alt: str = "",
                                   width: Optional[int] = None,
                                   height: Optional[int] = None,
                                   class_name: str = "") -> str:
        """
        生成渐进式加载图片HTML
        
        先显示低质量图片，然后加载高质量版本
        
        Args:
            low_quality_src: 低质量图片URL（小尺寸）
            high_quality_src: 高质量图片URL
            alt: 替代文本
            width: 图片宽度
            height: 图片高度
            class_name: CSS类名
        
        Returns:
            渐进式图片HTML
        """
        styles = []
        if width:
            styles.append(f"width: {width}px")
        if height:
            styles.append(f"height: {height}px")

        style_attr = f'style="{"; ".join(styles)}"' if styles else ""
        class_attr = f'class="progressive-image {class_name}"' if class_name else 'class="progressive-image"'

        html = f'''<div {class_attr} {style_attr}>
            <img 
                class="progressive-image__low"
                src="{low_quality_src}"
                alt="{alt}"
            />
            <img 
                class="progressive-image__high"
                data-src="{high_quality_src}"
                alt="{alt}"
                loading="lazy"
            />
        </div>'''

        return html

    def generate_lazy_load_script(self) -> str:
        """
        生成懒加载JavaScript代码
        
        Returns:
            JavaScript代码
        """
        script = f'''
<script>
(function() {{
    'use strict';
    
    // 检查浏览器是否支持IntersectionObserver
    if ('IntersectionObserver' in window) {{
        const imageObserver = new IntersectionObserver((entries, observer) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    const img = entry.target;
                    
                    // 加载真实图片
                    if (img.dataset.src) {{
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                    }}
                    
                    // 添加loaded类用于动画
                    img.classList.add('loaded');
                    
                    // 停止观察
                    observer.unobserve(img);
                }}
            }});
        }}, {{
            rootMargin: '{self.root_margin}',
            threshold: 0.01
        }});
        
        // 观察所有懒加载图片
        document.addEventListener('DOMContentLoaded', () => {{
            const lazyImages = document.querySelectorAll('img[data-src]');
            lazyImages.forEach(img => imageObserver.observe(img));
        }});
        
        // 动态添加的图片也需要观察
        const originalAppendChild = Element.prototype.appendChild;
        Element.prototype.appendChild = function(element) {{
            const appended = originalAppendChild.call(this, element);
            if (element.tagName === 'IMG' && element.dataset.src) {{
                imageObserver.observe(element);
            }}
            return appended;
        }};
    }} else {{
        // 降级方案：直接加载所有图片
        document.addEventListener('DOMContentLoaded', () => {{
            const lazyImages = document.querySelectorAll('img[data-src]');
            lazyImages.forEach(img => {{
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
            }});
        }});
    }}
}})();
</script>
        '''

        return script.strip()

    def generate_progressive_load_script(self) -> str:
        """
        生成渐进式加载JavaScript代码
        
        Returns:
            JavaScript代码
        """
        script = f'''
<script>
(function() {{
    'use strict';
    
    // 渐进式图片加载
    function loadProgressiveImage(container) {{
        const highQualityImg = container.querySelector('.progressive-image__high');
        const lowQualityImg = container.querySelector('.progressive-image__low');
        
        if (!highQualityImg || !highQualityImg.dataset.src) return;
        
        const img = new Image();
        
        img.onload = function() {{
            highQualityImg.src = highQualityImg.dataset.src;
            highQualityImg.classList.add('loaded');
            
            // 淡出低质量图片
            if (lowQualityImg) {{
                lowQualityImg.style.opacity = '0';
                setTimeout(() => {{
                    lowQualityImg.remove();
                }}, {self.fade_in_duration});
            }}
        }};
        
        img.src = highQualityImg.dataset.src;
    }}
    
    // 使用IntersectionObserver
    if ('IntersectionObserver' in window) {{
        const observer = new IntersectionObserver((entries) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    loadProgressiveImage(entry.target);
                    observer.unobserve(entry.target);
                }}
            }});
        }}, {{
            rootMargin: '{self.root_margin}'
        }});
        
        document.addEventListener('DOMContentLoaded', () => {{
            const progressiveImages = document.querySelectorAll('.progressive-image');
            progressiveImages.forEach(img => observer.observe(img));
        }});
    }} else {{
        // 降级方案
        document.addEventListener('DOMContentLoaded', () => {{
            const progressiveImages = document.querySelectorAll('.progressive-image');
            progressiveImages.forEach(loadProgressiveImage);
        }});
    }}
}})();
</script>
        '''

        return script.strip()

    def generate_css_styles(self) -> str:
        """
        生成懒加载CSS样式
        
        Returns:
            CSS样式代码
        """
        css = '''
<style>
/* 懒加载图片基础样式 */
.lazy-image {
    opacity: 0;
    transition: opacity 0.3s ease-in-out;
}

.lazy-image.loaded {
    opacity: 1;
}

/* 渐进式图片容器 */
.progressive-image {
    position: relative;
    overflow: hidden;
}

.progressive-image__low,
.progressive-image__high {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: opacity 0.3s ease-in-out;
}

.progressive-image__high {
    position: absolute;
    top: 0;
    left: 0;
    opacity: 0;
}

.progressive-image__high.loaded {
    opacity: 1;
}

/* 占位符动画 */
@keyframes pulse {
    0%, 100% {
        opacity: 1;
    }
    50% {
        opacity: 0.5;
    }
}

.lazy-image:not([src]) {
    animation: pulse 1.5s ease-in-out infinite;
}
</style>
        '''

        return css.strip()

    def inject_lazy_load(self, html_content: str) -> str:
        """
        在HTML中注入懒加载脚本
        
        Args:
            html_content: HTML内容
        
        Returns:
            注入脚本后的HTML
        """
        # 添加CSS样式
        css_styles = self.generate_css_styles()

        # 添加JavaScript
        js_script = self.generate_lazy_load_script()

        # 在</head>前插入CSS
        if '</head>' in html_content:
            html_content = html_content.replace('</head>', f'{css_styles}\n</head>')
        else:
            html_content = f'{css_styles}\n{html_content}'

        # 在</body>前插入JS
        if '</body>' in html_content:
            html_content = html_content.replace('</body>', f'{js_script}\n</body>')
        else:
            html_content = f'{html_content}\n{js_script}'

        return html_content


# 全局实例
image_lazy_load_service = ImageLazyLoadService()

# 导出
__all__ = ['ImageLazyLoadService', 'image_lazy_load_service']
