t"""
SEO优化工具模块
包含sitemap生成、meta标签优化等功能
"""
import re
from datetime import datetime

from fastapi import Request


def get_article_meta_tags(article, content=None, author=None, request: Request = None):
    """
    为文章页面生成meta标签
    """
    title = article.title
    description = article.excerpt if article.excerpt else (
        content.content[:150] if content and content.content else f"阅读关于{article.title}的文章")
    author_name = author.username if author else "未知作者"
    cover_image = article.cover_image if article.cover_image else ""

    # 从request获取相关信息，如果request为None则使用默认值
    if request:
        host_url = str(request.url).split(str(request.url.path))[0]  # 获取主机部分
        endpoint_parts = request.url.path.split('/')
        page_name = endpoint_parts[1] if len(endpoint_parts) > 1 else '博客'
    else:
        host_url = "http://localhost:8000"
        page_name = "博客"

    meta_tags = {
        'title': f"{title} - {page_name}",
        'description': description,
        'keywords': article.tags_list.replace(';', ', ') if article.tags_list else title,  # 修复：使用 tags_list
        'author': author_name,
        'og:title': title,
        'og:description': description,
        'og:type': 'article',
        'og:url': f"{host_url}/p/{article.slug}",
        'og:image': cover_image if cover_image else f"{host_url}/api/v2/static/images/default-cover.jpg",
        'article:author': author_name,
        'article:published_time': article.created_at.isoformat() if article.created_at else datetime.now().isoformat(),
        'article:modified_time': article.updated_at.isoformat() if article.updated_at else article.created_at.isoformat(),
        'article:section': article.category.name if article.category else '未分类',
        'twitter:card': 'summary_large_image',
        'twitter:title': title,
        'twitter:description': description,
        'twitter:image': cover_image if cover_image else f"{host_url}/api/v2/static/images/default-cover.jpg",
    }

    # 尝试调用插件钩子增强元标签
    try:
        from shared.services.plugins.plugin_manager.init import apply_plugin_filter

        # 构建插件期望的数据格式
        meta_data = {
            'tags': [],
            'article': {
                'title': article.title,
                'excerpt': article.excerpt or '',
                'slug': article.slug,
                'featured_image': cover_image,
                'tags': [t.strip() for t in re.split(r'[,;]', article.tags_list) if
                         t.strip()] if article.tags_list else [],
                'created_at': article.created_at,
                'updated_at': article.updated_at,
            }
        }

        # 应用插件过滤器
        enhanced_meta = apply_plugin_filter('page_meta_tags', meta_data)

        # 如果有增强的标签，添加到返回结果中
        if enhanced_meta and 'tags' in enhanced_meta:
            # 将插件生成的HTML标签转换为字典格式（可选）
            # 这里我们直接返回原始meta_tags，因为前端可能需要HTML格式的标签
            pass
    except Exception as e:
        # 插件钩子失败不应影响主功能
        print(f"[SEO] Plugin hook failed: {e}")

    return meta_tags


def get_page_meta_tags(title, description="", keywords="", page_type="website", request: Request = None):
    """
    为普通页面生成meta标签
    """
    # 从request获取相关信息，如果request为None则使用默认值
    if request:
        url = str(request.url)
        endpoint_parts = request.url.path.split('/')
        page_name = endpoint_parts[1] if len(endpoint_parts) > 1 else '博客'
    else:
        url = "http://localhost:8000"
        page_name = "博客"

    meta_tags = {
        'title': title,
        'description': description,
        'keywords': keywords,
        'og:title': title,
        'og:description': description,
        'og:type': page_type,
        'og:url': url,
        'og:site_name': page_name,
        'twitter:card': 'summary',
        'twitter:title': title,
        'twitter:description': description,
    }

    # 尝试调用插件钩子增强元标签
    try:
        from shared.services.plugins.plugin_manager.init import apply_plugin_filter

        # 构建插件期望的数据格式
        meta_data = {
            'tags': [],
            'page_type': page_type,
        }

        # 根据页面类型应用不同的过滤器
        if page_type == 'homepage':
            enhanced_meta = apply_plugin_filter('homepage_meta_tags', meta_data)
        else:
            enhanced_meta = apply_plugin_filter('page_meta_tags', meta_data)

        # 如果有增强的标签，可以记录下来（当前实现保持原样）
        pass
    except Exception as e:
        # 插件钩子失败不应影响主功能
        print(f"[SEO] Plugin hook failed: {e}")

    return meta_tags


def slugify(text):
    """
    将文本转换为URL友好的slug格式
    """
    import re
    # 转换为小写
    text = text.lower()
    # 替换空格和特殊字符为连字符
    text = re.sub(r'[^a-z0-9\u4e00-\u9fa5\-\s]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def generate_seo_friendly_url(title, model_type='article', id_value=None):
    """
    生成SEO友好的URL
    """
    slug = slugify(title)
    if model_type == 'article':
        return f"/p/{slug}" if slug else f"/{id_value}.html" if id_value else f"/article.html"
    elif model_type == 'category':
        return f"/category/{slug}" if slug else f"/category/{id_value}" if id_value else "/category"
    elif model_type == 'tag':
        return f"/tag/{slug}" if slug else f"/tag/{id_value}" if id_value else "/tag"
    else:
        return f"/{slug}"


def get_feed_discovery_tags(base_url: str = None) -> dict:
    """
    生成RSS/Atom Feed发现标签（用于HTML head）

    Args:
        base_url: 网站基础URL，如果为None则使用默认值

    Returns:
        包含feed link标签的字典
    """
    if not base_url:
        base_url = "http://localhost:8000"

    return {
        'rss_link': f'{base_url}/api/v1/feed/rss',
        'atom_link': f'{base_url}/api/v1/feed/atom',
        'rss_xml': f'<link rel="alternate" type="application/rss+xml" title="RSS 2.0" href="{base_url}/api/v1/feed/rss" />',
        'atom_xml': f'<link rel="alternate" type="application/atom+xml" title="Atom 1.0" href="{base_url}/api/v1/feed/atom" />'
    }
