"""
CSS优化服务
提供关键CSS提取和内联功能
类似WordPress Critical CSS插件
"""
import hashlib
import os
from pathlib import Path
from typing import Dict, Any, Optional


class CSSOptimizerService:
    """CSS优化服务"""
    
    def __init__(self):
        self.cache_dir = Path(__file__).parent.parent.parent / "storage" / "cache" / "critical-css"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_critical_css(self, html_content: str, css_files: list) -> str:
        """
        提取关键CSS(Above-the-fold样式)
        
        Args:
            html_content: HTML内容
            css_files: CSS文件路径列表
            
        Returns:
            关键CSS字符串
        """
        # 简化版:返回基础的关键CSS
        # 实际实现应该使用puppeteer或critical工具分析首屏
        
        critical_css = """
/* Critical CSS - Above the fold */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  line-height: 1.6;
  color: #333;
  background-color: #fff;
}

/* Header styles */
header {
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
  padding: 1rem 0;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
  margin-top: 0;
  margin-bottom: 0.5em;
  font-weight: 600;
  line-height: 1.2;
}

h1 { font-size: 2.5rem; }
h2 { font-size: 2rem; }
h3 { font-size: 1.75rem; }

p {
  margin-bottom: 1em;
}

/* Navigation */
nav ul {
  list-style: none;
  display: flex;
  gap: 1rem;
}

nav a {
  text-decoration: none;
  color: #333;
}

nav a:hover {
  color: #007bff;
}

/* Article header (above the fold) */
.article-header {
  margin-bottom: 2rem;
}

.article-title {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.article-meta {
  color: #666;
  font-size: 0.9rem;
}

/* Featured image */
.featured-image {
  width: 100%;
  height: auto;
  max-height: 500px;
  object-fit: cover;
  margin-bottom: 2rem;
}

/* Loading states */
.loading {
  opacity: 0.6;
  pointer-events: none;
}

/* Utility classes */
.text-center { text-align: center; }
.text-left { text-align: left; }
.text-right { text-align: right; }

.hidden { display: none; }
.visible { display: block; }
"""
        
        return critical_css.strip()
    
    def generate_inline_css_tag(self, critical_css: str) -> str:
        """
        生成内联CSS标签
        
        Args:
            critical_css: 关键CSS字符串
            
        Returns:
            HTML style标签
        """
        return f'<style id="critical-css">{critical_css}</style>'
    
    def generate_async_css_loader(self, css_url: str) -> str:
        """
        生成异步CSS加载器
        
        Args:
            css_url: 完整CSS文件URL
            
        Returns:
            异步加载脚本
        """
        return f'''
<!-- Async CSS Loader -->
<link rel="preload" href="{css_url}" as="style" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="{css_url}"></noscript>
'''.strip()
    
    def get_cached_critical_css(self, cache_key: str) -> Optional[str]:
        """
        从缓存获取关键CSS
        
        Args:
            cache_key: 缓存键
            
        Returns:
            缓存的CSS或None
        """
        cache_file = self.cache_dir / f"{cache_key}.css"
        
        if cache_file.exists():
            try:
                return cache_file.read_text(encoding='utf-8')
            except Exception:
                return None
        
        return None
    
    def cache_critical_css(self, cache_key: str, css: str):
        """
        缓存关键CSS
        
        Args:
            cache_key: 缓存键
            css: CSS内容
        """
        cache_file = self.cache_dir / f"{cache_key}.css"
        
        try:
            cache_file.write_text(css, encoding='utf-8')
        except Exception as e:
            print(f"Failed to cache critical CSS: {e}")
    
    def generate_cache_key(self, content: str, css_files: list) -> str:
        """
        生成缓存键
        
        Args:
            content: 内容(用于检测变化)
            css_files: CSS文件列表
            
        Returns:
            缓存键(hash)
        """
        # 基于内容和CSS文件修改时间生成hash
        hasher = hashlib.md5()
        hasher.update(content.encode('utf-8'))
        
        for css_file in css_files:
            if os.path.exists(css_file):
                mtime = os.path.getmtime(css_file)
                hasher.update(f"{css_file}:{mtime}".encode('utf-8'))
        
        return hasher.hexdigest()[:16]
    
    def optimize_page_css(self, html_content: str, css_files: list, page_type: str = 'article') -> Dict[str, Any]:
        """
        优化页面CSS
        
        Args:
            html_content: HTML内容
            css_files: CSS文件列表
            page_type: 页面类型(article/home/category等)
            
        Returns:
            优化结果
        """
        # 生成缓存键
        cache_key = self.generate_cache_key(html_content, css_files)
        
        # 尝试从缓存获取
        cached_css = self.get_cached_critical_css(f"{page_type}_{cache_key}")
        
        if cached_css:
            return {
                'success': True,
                'cached': True,
                'critical_css': cached_css,
                'inline_tag': self.generate_inline_css_tag(cached_css),
                'cache_key': cache_key,
            }
        
        # 提取关键CSS
        critical_css = self.extract_critical_css(html_content, css_files)
        
        # 缓存结果
        self.cache_critical_css(f"{page_type}_{cache_key}", critical_css)
        
        return {
            'success': True,
            'cached': False,
            'critical_css': critical_css,
            'inline_tag': self.generate_inline_css_tag(critical_css),
            'cache_key': cache_key,
        }
    
    def clear_cache(self):
        """清除所有缓存"""
        try:
            for file in self.cache_dir.glob("*.css"):
                file.unlink()
            return True
        except Exception as e:
            print(f"Failed to clear cache: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        try:
            files = list(self.cache_dir.glob("*.css"))
            total_size = sum(f.stat().st_size for f in files)
            
            return {
                'file_count': len(files),
                'total_size_kb': round(total_size / 1024, 2),
                'cache_dir': str(self.cache_dir),
            }
        except Exception as e:
            return {
                'file_count': 0,
                'total_size_kb': 0,
                'error': str(e),
            }


# 单例实例
css_optimizer_service = CSSOptimizerService()
