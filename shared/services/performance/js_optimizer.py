"""
JavaScript 优化服务
提供脚本延迟加载、异步加载和性能优化功能
"""
from typing import List, Dict, Any


class JSOptimizer:
    """JavaScript 优化服务"""

    @classmethod
    def generate_script_tag(cls, src: str, strategy: str = 'defer',
                            async_load: bool = False,
                           attributes: Dict[str, str] = None) -> str:
        """
        生成优化的 script 标签

        Args:
            src: 脚本 URL
            strategy: 加载策略 ('defer', 'async', 'lazy')
            async_load: 是否异步加载
            attributes: 额外属性

        Returns:
            HTML script 标签字符串
        """
        attrs = [f'src="{src}"']

        if strategy == 'defer':
            attrs.append('defer')
        elif strategy == 'async' or async_load:
            attrs.append('async')
        elif strategy == 'lazy':
            # 懒加载通过 JavaScript 实现
            attrs.append('data-lazy="true"')

        # 添加额外属性
        if attributes:
            for key, value in attributes.items():
                attrs.append(f'{key}="{value}"')

        attrs_str = ' '.join(attrs)
        return f'<script {attrs_str}></script>'

    @classmethod
    def generate_lazy_loader(cls, scripts: List[Dict[str, Any]]) -> str:
        """
        生成懒加载脚本代码

        Args:
            scripts: 脚本配置列表，每个元素包含 {src, trigger, delay}

        Returns:
            JavaScript 代码字符串
        """
        script_configs = []
        for script in scripts:
            config = {
                'src': script['src'],
                'trigger': script.get('trigger', 'scroll'),  # scroll, click, idle, visible
                'delay': script.get('delay', 0),
            }
            script_configs.append(config)

        js_code = f'''
// 懒加载脚本管理器
(function() {{
    const scripts = {str(script_configs)};
    const loadedScripts = new Set();

    // 加载单个脚本
    function loadScript(src) {{
        if (loadedScripts.has(src)) return;

        const script = document.createElement('script');
        script.src = src;
        script.defer = true;
        document.head.appendChild(script);
        loadedScripts.add(src);
    }}

    // 根据触发器加载脚本
    scripts.forEach(config => {{
        switch(config.trigger) {{
            case 'scroll':
                let scrollLoaded = false;
                window.addEventListener('scroll', () => {{
                    if (!scrollLoaded) {{
                        setTimeout(() => {{
                            loadScript(config.src);
                            scrollLoaded = true;
                        }}, config.delay);
                    }}
                }}, {{ once: true }});
                break;

            case 'idle':
                if ('requestIdleCallback' in window) {{
                    requestIdleCallback(() => {{
                        setTimeout(() => loadScript(config.src), config.delay);
                    }});
                }} else {{
                    setTimeout(() => loadScript(config.src), Math.max(config.delay, 2000));
                }}
                break;

            case 'visible':
                const observer = new IntersectionObserver((entries) => {{
                    entries.forEach(entry => {{
                        if (entry.isIntersecting) {{
                            setTimeout(() => loadScript(config.src), config.delay);
                            observer.disconnect();
                        }}
                    }});
                }});
                observer.observe(document.body);
                break;

            default:
                // 立即加载
                setTimeout(() => loadScript(config.src), config.delay);
        }}
    }});
}})();
        '''
        return js_code.strip()

    @classmethod
    def get_recommended_scripts(cls) -> Dict[str, List[Dict]]:
        """
        获取推荐的脚本加载配置

        Returns:
            按类别分组的脚本配置
        """
        return {
            'critical': [
                # 关键脚本 - 立即加载
            ],
            'deferred': [
                # 延迟脚本 - DOM 就绪后加载
                {'src': '/api/v2/static/js/analytics.js', 'strategy': 'defer'},
            ],
            'lazy': [
                # 懒加载脚本
                {
                    'src': 'https://www.googletagmanager.com/gtag/js?id=GA_ID',
                    'trigger': 'idle',
                    'delay': 3000
                },
                {
                    'src': 'https://platform.twitter.com/widgets.js',
                    'trigger': 'visible',
                    'delay': 1000
                },
            ]
        }

    @classmethod
    def generate_inline_critical_js(cls) -> str:
        """
        生成内联的关键 JavaScript（用于首屏优化）

        Returns:
            内联 JavaScript 代码
        """
        return '''
// 关键 JavaScript - 内联以提高首屏加载速度
(function() {
    // 检测连接速度
    const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    if (connection) {
        document.documentElement.setAttribute('data-connection', connection.effectiveType || 'unknown');
    }

    // 记录页面加载开始时间
    window.__PAGE_START__ = performance.now();

    // 检测用户偏好
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        document.documentElement.classList.add('reduce-motion');
    }

    // 预加载关键资源
    const preloadLinks = document.querySelectorAll('link[rel="preload"]');
    preloadLinks.forEach(link => {
        if (link.as === 'image' && 'loading' in HTMLImageElement.prototype) {
            link.parentElement.removeChild(link);
        }
    });
})();
        '''.strip()

    @classmethod
    def optimize_third_party_scripts(cls, scripts: List[Dict]) -> List[Dict]:
        """
        优化第三方脚本配置

        Args:
            scripts: 原始脚本配置列表

        Returns:
            优化后的脚本配置
        """
        optimized = []

        for script in scripts:
            opt_script = script.copy()

            # Google Analytics - 延迟加载
            if 'google-analytics' in script.get('src', '') or 'gtag' in script.get('src', ''):
                opt_script['strategy'] = 'lazy'
                opt_script['trigger'] = 'idle'
                opt_script['delay'] = 3000

            # Facebook Pixel - 延迟加载
            elif 'facebook' in script.get('src', '') or 'fbq' in script.get('src', ''):
                opt_script['strategy'] = 'lazy'
                opt_script['trigger'] = 'scroll'
                opt_script['delay'] = 2000

            # Twitter widgets - 可见时加载
            elif 'twitter' in script.get('src', ''):
                opt_script['strategy'] = 'lazy'
                opt_script['trigger'] = 'visible'
                opt_script['delay'] = 1000

            # Disqus 评论 - 滚动时加载
            elif 'disqus' in script.get('src', ''):
                opt_script['strategy'] = 'lazy'
                opt_script['trigger'] = 'scroll'
                opt_script['delay'] = 1500

            optimized.append(opt_script)

        return optimized
