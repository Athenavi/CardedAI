"""
懒加载优化服务
提供图片、组件、路由的懒加载支持
"""

import re
from typing import List, Optional


class LazyLoadOptimizer:
    """
    懒加载优化器
    
    功能：
    1. 图片懒加载HTML生成
    2. 响应式图片支持
    3. 占位符生成
    4. 懒加载脚本注入
    """

    def __init__(self):
        # 默认配置
        self.config = {
            'threshold': 200,  # 提前加载距离（像素）
            'placeholder_color': '#f0f0f0',
            'fade_in_duration': 300,  # 淡入动画时长（毫秒）
        }

    def generate_lazy_image(self,
                            src: str,
                            alt: str = "",
                            width: Optional[int] = None,
                            height: Optional[int] = None,
                            class_name: str = "",
                            sizes: Optional[str] = None,
                            srcset: Optional[str] = None) -> str:
        """
        生成懒加载图片HTML
        
        Args:
            src: 图片URL
            alt: 替代文本
            width: 宽度
            height: 高度
            class_name: CSS类名
            sizes: 响应式sizes属性
            srcset: 响应式srcset属性
            
        Returns:
            懒加载图片HTML
        """
        attrs = [
            f'data-src="{src}"',
            f'alt="{alt}"',
            'class="lazy-image ' + class_name + '"',
            'loading="lazy"',
        ]

        if width:
            attrs.append(f'width="{width}"')
        if height:
            attrs.append(f'height="{height}"')
        if sizes:
            attrs.append(f'sizes="{sizes}"')
        if srcset:
            attrs.append(f'data-srcset="{srcset}"')

        # 添加内联样式作为占位符
        placeholder_style = f"background-color: {self.config['placeholder_color']};"
        if width and height:
            aspect_ratio = (height / width) * 100
            placeholder_style += f"padding-bottom: {aspect_ratio}%;"

        attrs.append(f'style="{placeholder_style} min-height: 100px;"')

        return f'<img {" ".join(attrs)} />'

    def generate_responsive_image(self,
                                  base_url: str,
                                  alt: str = "",
                                  widths: List[int] = None) -> str:
        """
        生成响应式图片（自动生成srcset）
        
        Args:
            base_url: 图片基础URL（不含扩展名）
            alt: 替代文本
            widths: 不同宽度的列表
            
        Returns:
            响应式图片HTML
        """
        if widths is None:
            widths = [320, 640, 768, 1024, 1280, 1920]

        # 生成srcset
        srcset_parts = []
        for width in widths:
            srcset_parts.append(f"{base_url}-{width}.webp {width}w")

        srcset = ", ".join(srcset_parts)

        # 生成sizes
        sizes = "(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"

        return self.generate_lazy_image(
            src=f"{base_url}-1024.webp",
            alt=alt,
            srcset=srcset,
            sizes=sizes
        )

    def generate_placeholder_svg(self, width: int = 800, height: int = 600) -> str:
        """
        生成SVG占位符
        
        Args:
            width: 宽度
            height: 高度
            
        Returns:
            SVG占位符data URI
        """
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
            <rect fill="{self.config['placeholder_color']}" width="100%" height="100%"/>
        </svg>'''

        import base64
        encoded = base64.b64encode(svg.encode()).decode()
        return f"data:image/svg+xml;base64,{encoded}"

    def get_lazy_load_script(self) -> str:
        """
        获取懒加载JavaScript代码
        
        Returns:
            JavaScript代码
        """
        return '''
<script>
(function() {
    'use strict';
    
    // Intersection Observer配置
    const observerOptions = {
        root: null,
        rootMargin: '200px 0px',
        threshold: 0.01
    };
    
    // 创建观察者
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                
                // 加载真实图片
                if (img.dataset.src) {
                    img.src = img.dataset.src;
                    
                    // 如果有srcset，也加载
                    if (img.dataset.srcset) {
                        img.srcset = img.dataset.srcset;
                    }
                    
                    // 移除data属性
                    delete img.dataset.src;
                    delete img.dataset.srcset;
                }
                
                // 添加淡入效果
                img.classList.add('loaded');
                
                // 停止观察
                observer.unobserve(img);
            }
        });
    }, observerOptions);
    
    // 观察所有懒加载图片
    function observeImages() {
        const lazyImages = document.querySelectorAll('.lazy-image[data-src]');
        lazyImages.forEach(img => {
            imageObserver.observe(img);
        });
    }
    
    // DOM加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', observeImages);
    } else {
        observeImages();
    }
    
    // 动态内容更新时重新观察
    window.observeLazyImages = observeImages;
})();
</script>
        '''

    def get_lazy_load_styles(self) -> str:
        """
        获取懒加载CSS样式
        
        Returns:
            CSS样式
        """
        return '''
<style>
.lazy-image {
    opacity: 0;
    transition: opacity ''' + str(self.config['fade_in_duration']) + '''ms ease-in-out;
    object-fit: cover;
}

.lazy-image.loaded {
    opacity: 1;
}

/* 占位符背景 */
.lazy-image:not([src]) {
    background-color: ''' + self.config['placeholder_color'] + ''';
    min-height: 100px;
}
</style>
        '''

    def optimize_content_images(self, content: str) -> str:
        """
        优化文章内容中的图片（转换为懒加载）
        
        Args:
            content: HTML内容
            
        Returns:
            优化后的HTML内容
        """
        # 匹配所有img标签
        img_pattern = r'<img[^>]+>'

        def replace_img(match):
            img_tag = match.group(0)

            # 如果已经有loading="lazy"或class包含lazy，跳过
            if 'loading="lazy"' in img_tag or 'lazy-image' in img_tag:
                return img_tag

            # 提取src
            src_match = re.search(r'src=["\']([^"\']+)["\']', img_tag)
            if not src_match:
                return img_tag

            src = src_match.group(1)

            # 提取其他属性
            alt_match = re.search(r'alt=["\']([^"\']*)["\']', img_tag)
            alt = alt_match.group(1) if alt_match else ""

            width_match = re.search(r'width=["\'](\d+)["\']', img_tag)
            width = width_match.group(1) if width_match else None

            height_match = re.search(r'height=["\'](\d+)["\']', img_tag)
            height = height_match.group(1) if height_match else None

            class_match = re.search(r'class=["\']([^"\']*)["\']', img_tag)
            existing_class = class_match.group(1) if class_match else ""
            new_class = f"lazy-image {existing_class}".strip()

            # 构建新的img标签
            new_attrs = [
                f'data-src="{src}"',
                f'alt="{alt}"',
                f'class="{new_class}"',
                'loading="lazy"',
            ]

            if width:
                new_attrs.append(f'width="{width}"')
            if height:
                new_attrs.append(f'height="{height}"')

            # 保留其他重要属性
            style_match = re.search(r'style=["\']([^"\']*)["\']', img_tag)
            if style_match:
                new_attrs.append(f'style="{style_match.group(1)}"')

            return f'<img {" ".join(new_attrs)} />'

        optimized_content = re.sub(img_pattern, replace_img, content)

        return optimized_content


# 全局实例
lazy_load_optimizer = LazyLoadOptimizer()
