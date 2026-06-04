import json
from datetime import datetime, timedelta, UTC
from functools import lru_cache
from typing import Any

from markdown_it import MarkdownIt
from mdit_py_emoji import emoji_plugin
from mdit_py_plugins import (
    footnote,
    tasklists,
    front_matter,
    admon,  # 注意：提示框插件名是 admon
)
# 目录和表情来自独立的第三方包，需手动安装
# pip install mdit-py-toc mdit-py-emoji
from mdit_py_toc import toc_plugin
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name


# ────────────── 工具函数（保留原样） ──────────────

def json_filter(value):
    """将 JSON 字符串解析为 Python 对象"""
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return None
    try:
        return json.loads(value)
    except (ValueError, TypeError) as e:
        print(f"Error parsing JSON: {e}, Value: {value}")
        return None

def string_split(value, delimiter=','):
    """在模板中对字符串进行分割"""
    if not isinstance(value, str):
        print(f"Unexpected type for value: {type(value)}. Expected a string.")
        return []
    try:
        return value.split(delimiter)
    except Exception as e:
        print(f"Error splitting string: {e}, Value: {value}")
        return []

def relative_time_filter(dt):
    """改进的相对时间过滤器，处理各种时间输入"""
    if dt is None:
        return "未知时间"
    if dt.tzinfo is None:
        dt_utc = dt.replace(tzinfo=UTC)
    else:
        dt_utc = dt.astimezone(UTC)
    now_utc = datetime.now(UTC)
    if dt_utc > now_utc:
        diff = dt_utc - now_utc
        if diff < timedelta(minutes=1):
            return "即将"
        elif diff < timedelta(hours=1):
            return f"{int(diff.seconds / 60)}分钟后"
        elif diff < timedelta(days=1):
            return f"{int(diff.seconds / 3600)}小时后"
        else:
            return dt_utc.strftime('%Y-%m-%d')
    else:
        diff = now_utc - dt_utc
        if diff < timedelta(minutes=1):
            return "刚刚"
        elif diff < timedelta(hours=1):
            return f"{int(diff.seconds / 60)}分钟前"
        elif diff < timedelta(days=1):
            return f"{int(diff.seconds / 3600)}小时前"
        elif diff < timedelta(days=30):
            return f"{diff.days}天前"
        else:
            return dt_utc.strftime('%Y-%m-%d')

@lru_cache(maxsize=128)
async def category_filter(category_id):
    """异步获取分类名称（带缓存）"""
    from sqlalchemy import select
    from shared.models import Category
    from src.utils.database.unified_manager import db_manager

    async with db_manager.get_session() as db:
        result = await db.execute(
            select(Category).where(Category.id == category_id)
        )
        category = result.scalar_one_or_none()
        return category.name if category else None

def f2list(input_value, delimiter=';'):
    """将分隔符分隔的字符串转换为列表"""
    try:
        if input_value is None:
            return []
        if isinstance(input_value, list):
            if input_value and isinstance(input_value[0], str) and delimiter in input_value[0]:
                result = []
                for item in input_value:
                    if isinstance(item, str):
                        result.extend([tag.strip() for tag in item.split(delimiter) if tag.strip()])
                    else:
                        result.append(str(item).strip())
                return result
            return input_value
        if isinstance(input_value, str):
            return [tag.strip() for tag in input_value.split(delimiter) if tag.strip()]
        return [str(input_value).strip()]
    except (ValueError, TypeError, AttributeError) as e:
        print(f"Error converting to list: {e}, Input: {input_value}")
        return [str(input_value)] if input_value else []


# ────────────── Markdown 转 HTML 核心 ──────────────

def _create_highlighter(pygments_style: str):
    """返回一个符合 markdown-it-py highlight 签名的函数"""

    def highlighter(code: str, lang: str, attrs: str = None) -> str:
        if not lang:
            return f'<pre><code>{code}</code></pre>'

        # Mermaid 图表特殊处理
        if lang.lower() == 'mermaid':
            return f'<div class="mermaid"><pre><code>{code}</code></pre></div>'

        # 普通代码高亮
        try:
            lexer = get_lexer_by_name(lang, stripall=True)
            formatter = HtmlFormatter(style=pygments_style, cssclass='highlight')
            return highlight(code, lexer, formatter)
        except Exception:
            return f'<pre><code class="language-{lang}">{code}</code></pre>'
    return highlighter


def md2html(markdown_text: str, **options: Any) -> str:
    """
    Markdown 转 HTML（基于 markdown-it-py，已修复所有导入问题）
    参数与原函数完全兼容。
    """
    # 默认配置（与原函数完全一致）
    default_opts = {
        'style_theme': 'github',
        'pygments_style': 'default',
        'tab_length': 4,
        'enable_tables': True,
        'enable_fenced_code': True,           # 始终启用，markdown-it-py 原生支持
        'enable_sane_lists': True,            # 默认行为已足够
        'enable_footnotes': False,
        'enable_attr_list': False,            # 暂无对应插件，忽略
        'enable_meta': True,                  # 始终启用 front_matter
        'enable_nl2br': False,
        'enable_admonition': False,
        'enable_code_highlight': True,
        'enable_toc': False,
        'enable_superfences': True,           # 高亮逻辑统一由 highlight 处理，无需额外操作
        'enable_tasklist': True,
        'enable_magiclink': False,
        'enable_emoji': False,
        'toc_title': '目录',
        'toc_anchorlink': True,
        'toc_permalink': True,
        'toc_depth': 6,
    }
    opts = {**default_opts, **options}

    # 构建 MarkdownIt 实例，使用通用的 commonmark 预设并启用表格
    md = MarkdownIt("commonmark", {
        "html": True,
        "breaks": opts['enable_nl2br'],
        "linkify": opts['enable_magiclink'],
        "typographer": False,
    })

    # 表格是内置插件，直接启用
    if opts['enable_tables']:
        md.enable('table')

    # 代码高亮通过官方 highlight 选项注入，对所有围栏代码块生效
    if opts['enable_code_highlight']:
        md.options['highlight'] = _create_highlighter(opts['pygments_style'])

    # 第三方插件注册
    if opts['enable_footnotes']:
        md.use(footnote.footnote_plugin)
    if opts['enable_admonition']:
        md.use(admon.admon_plugin)               # 注意：admon 而非 admonition
    if opts['enable_tasklist']:
        md.use(tasklists.tasklists_plugin, enabled=True, label=True)
    if opts['enable_emoji']:
        md.use(emoji_plugin)                     # 来自 mdit_py_emoji
    if opts['enable_toc']:
        # mdit_py_toc 插件不支持配置参数，使用默认配置
        md.use(toc_plugin)
    # front_matter 始终启用，代价极小
    md.use(front_matter.front_matter_plugin)

    # 注：superfences 无需额外插件，原生 fenced code 即可，高亮已在上面处理
    # 注：sane_lists 使用默认行为，无需干预
    # 注：attr_list 无对应插件，暂不处理

    # 渲染 HTML
    html_content = md.render(markdown_text)

    # 拼装 CSS
    css_style = _get_css_style(opts['style_theme'])
    pygments_css = _get_pygments_css(opts['pygments_style'])

    result = f"""
<style>
{css_style}
{pygments_css}
</style>
<div class="markdown-content">
{html_content}
</div>
"""
    return result.strip()


def markdown_to_html(markdown_text, theme='github', enable_toc=True, **kwargs):
    """简化的 Markdown 转 HTML 便捷函数"""
    return md2html(
        markdown_text,
        style_theme=theme,
        enable_toc=enable_toc,
        **kwargs
    )


# ────────────── CSS 主题（保留全部原始样式） ──────────────

_THEME_STYLES = {
    'github': '''
        .markdown-content { 
            font-family: -apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans",Helvetica,Arial,sans-serif; 
            line-height: 1.6; color: #24292f; background-color: #ffffff; 
            max-width: 980px; margin: 0 auto; padding: 45px; 
        }
        .markdown-content h1,.markdown-content h2,.markdown-content h3,.markdown-content h4,.markdown-content h5,.markdown-content h6 { 
            margin-top: 24px; margin-bottom: 16px; font-weight: 600; line-height: 1.25; 
        }
        .markdown-content h1 { font-size: 2em; border-bottom: 1px solid #d0d7de; padding-bottom: .3em; }
        .markdown-content h2 { font-size: 1.5em; border-bottom: 1px solid #d0d7de; padding-bottom: .3em; }
        .markdown-content p { margin-bottom: 16px; }
        .markdown-content code { background-color: rgba(175,184,193,0.2); border-radius: 6px; font-size: 85%; margin: 0; padding: .2em .4em; }
        .markdown-content pre { background-color: #f6f8fa; border-radius: 6px; font-size: 85%; line-height: 1.45; overflow: auto; padding: 16px; }
        .markdown-content blockquote { border-left: .25em solid #d0d7de; color: #656d76; margin: 0; padding: 0 1em; }
        .markdown-content table { border-collapse: collapse; border-spacing: 0; width: 100%; margin-bottom: 16px; }
        .markdown-content td,.markdown-content th { border: 1px solid #d0d7de; padding: 6px 13px; }
        .markdown-content th { background-color: #f6f8fa; font-weight: 600; }
        .markdown-content ul,.markdown-content ol { padding-left: 2em; margin-bottom: 16px; }
        .markdown-content .toc { background-color: #f6f8fa; border: 1px solid #d0d7de; border-radius: 6px; padding: 16px; margin: 16px 0; }
        .markdown-content .toc ul { margin: 0; padding-left: 1.5em; list-style-type: none; }
        .markdown-content .toc > ul { padding-left: 0; }
        .markdown-content .toc li { margin: 4px 0; }
        .markdown-content .toc a, .markdown-content .toc a:link, .markdown-content .toc a:visited, .markdown-content .toc a:hover, .markdown-content .toc a:active { 
            text-decoration: none !important; color: #0969da; font-weight: 500; 
            border: none !important; outline: none !important;
        }
        .markdown-content .toc a:hover { 
            color: #0550ae !important; background-color: rgba(9, 105, 218, 0.1) !important;
            padding: 2px 4px; border-radius: 3px;
        }
        .markdown-content .toclink, .markdown-content .toclink:link, .markdown-content .toclink:visited, .markdown-content .toclink:hover, .markdown-content .toclink:active {
            text-decoration: none !important; border-bottom: none !important;
            border: none !important; outline: none !important;
        }
        .markdown-content .headerlink { display: none !important; }
        .markdown-content .admonition { margin: 1em 0; padding: 12px; border-left: 4px solid #0969da; background-color: #ddf4ff; }
        .markdown-content .task-list-item { list-style-type: none; }
        .markdown-content .task-list-item input { margin-right: 8px; }
        .markdown-content .mermaid { background-color: #f6f8fa; border: 1px solid #d0d7de; border-radius: 6px; padding: 16px; margin: 16px 0; }
        .markdown-content .mermaid pre { background: transparent; border: none; padding: 0; margin: 0; }
        .markdown-content .mermaid code { background: transparent; padding: 0; font-size: 14px; }
    ''',
    'dark': '''
        .markdown-content { 
            font-family: -apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans",Helvetica,Arial,sans-serif; 
            line-height: 1.6; color: #e6edf3; background-color: #0d1117; 
            max-width: 980px; margin: 0 auto; padding: 45px; 
        }
        .markdown-content h1,.markdown-content h2,.markdown-content h3,.markdown-content h4,.markdown-content h5,.markdown-content h6 { 
            margin-top: 24px; margin-bottom: 16px; font-weight: 600; line-height: 1.25; color: #f0f6fc; 
        }
        .markdown-content h1 { font-size: 2em; border-bottom: 1px solid #21262d; padding-bottom: .3em; }
        .markdown-content h2 { font-size: 1.5em; border-bottom: 1px solid #21262d; padding-bottom: .3em; }
        .markdown-content p { margin-bottom: 16px; }
        .markdown-content code { background-color: rgba(110,118,129,0.4); border-radius: 6px; font-size: 85%; margin: 0; padding: .2em .4em; }
        .markdown-content pre { background-color: #161b22; border-radius: 6px; font-size: 85%; line-height: 1.45; overflow: auto; padding: 16px; }
        .markdown-content blockquote { border-left: .25em solid #30363d; color: #8b949e; margin: 0; padding: 0 1em; }
        .markdown-content table { border-collapse: collapse; border-spacing: 0; width: 100%; margin-bottom: 16px; }
        .markdown-content td,.markdown-content th { border: 1px solid #30363d; padding: 6px 13px; }
        .markdown-content th { background-color: #161b22; font-weight: 600; }
        .markdown-content ul,.markdown-content ol { padding-left: 2em; margin-bottom: 16px; }
        .markdown-content .toc { background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 16px; margin: 16px 0; }
        .markdown-content .toc ul { margin: 0; padding-left: 1.5em; list-style-type: none; }
        .markdown-content .toc > ul { padding-left: 0; }
        .markdown-content .toc li { margin: 4px 0; }
        .markdown-content .toc a, .markdown-content .toc a:link, .markdown-content .toc a:visited, .markdown-content .toc a:hover, .markdown-content .toc a:active { 
            text-decoration: none !important; color: #58a6ff; font-weight: 500; 
            border: none !important; outline: none !important;
        }
        .markdown-content .toc a:hover { 
            color: #79c0ff !important; background-color: rgba(88, 166, 255, 0.1) !important;
            padding: 2px 4px; border-radius: 3px;
        }
        .markdown-content .toclink, .markdown-content .toclink:link, .markdown-content .toclink:visited, .markdown-content .toclink:hover, .markdown-content .toclink:active {
            text-decoration: none !important; border-bottom: none !important;
            border: none !important; outline: none !important;
        }
        .markdown-content .headerlink { display: none !important; }
        .markdown-content .admonition { margin: 1em 0; padding: 12px; border-left: 4px solid #1f6feb; background-color: #0c2d6b; }
        .markdown-content .task-list-item { list-style-type: none; }
        .markdown-content .task-list-item input { margin-right: 8px; }
        .markdown-content .mermaid { background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 16px; margin: 16px 0; }
        .markdown-content .mermaid pre { background: transparent; border: none; padding: 0; margin: 0; }
        .markdown-content .mermaid code { background: transparent; padding: 0; font-size: 14px; color: #e6edf3; }
    ''',
    'minimal': '''
        .markdown-content { 
            font-family: Georgia, 'Times New Roman', serif; line-height: 1.8; color: #333; 
            max-width: 800px; margin: 0 auto; padding: 40px 20px; 
        }
        .markdown-content h1,.markdown-content h2,.markdown-content h3,.markdown-content h4,.markdown-content h5,.markdown-content h6 { 
            color: #000; margin-top: 2em; margin-bottom: 0.5em; 
        }
        .markdown-content h1 { font-size: 2.2em; }
        .markdown-content h2 { font-size: 1.8em; }
        .markdown-content p { margin-bottom: 1.2em; }
        .markdown-content code { background-color: #f5f5f5; padding: 2px 4px; border-radius: 3px; font-family: 'Courier New', monospace; }
        .markdown-content pre { background-color: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; font-family: 'Courier New', monospace; }
        .markdown-content blockquote { border-left: 4px solid #ddd; margin: 1.5em 0; padding-left: 20px; font-style: italic; color: #666; }
        .markdown-content table { width: 100%; border-collapse: collapse; margin: 1.5em 0; }
        .markdown-content td,.markdown-content th { border: 1px solid #ddd; padding: 8px 12px; }
        .markdown-content th { background-color: #f9f9f9; font-weight: bold; }
        .markdown-content ul,.markdown-content ol { margin-bottom: 1.2em; }
        .markdown-content .toc { background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin: 1.5em 0; }
        .markdown-content .toc ul { margin: 0; padding-left: 1.5em; list-style-type: none; }
        .markdown-content .toc > ul { padding-left: 0; }
        .markdown-content .toc li { margin: 4px 0; }
        .markdown-content .toc a, .markdown-content .toc a:link, .markdown-content .toc a:visited, .markdown-content .toc a:hover, .markdown-content .toc a:active { 
            text-decoration: none !important; color: #0066cc; font-weight: 500; 
            border: none !important; outline: none !important;
        }
        .markdown-content .toc a:hover { 
            color: #004499 !important; background-color: rgba(0, 102, 204, 0.1) !important;
            padding: 2px 4px; border-radius: 3px;
        }
        .markdown-content .toclink, .markdown-content .toclink:link, .markdown-content .toclink:visited, .markdown-content .toclink:hover, .markdown-content .toclink:active {
            text-decoration: none !important; border-bottom: none !important;
            border: none !important; outline: none !important;
        }
        .markdown-content .headerlink { display: none !important; }
        .markdown-content .admonition { margin: 1.5em 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; background-color: #f9f9f9; }
        .markdown-content .mermaid { background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin: 1.5em 0; }
        .markdown-content .mermaid pre { background: transparent; border: none; padding: 0; margin: 0; }
        .markdown-content .mermaid code { background: transparent; padding: 0; font-size: 14px; }
    ''',
    'academic': '''
        .markdown-content { 
            font-family: "Times New Roman", Times, serif; line-height: 1.8; color: #2c3e50; background-color: #ffffff; 
            max-width: 900px; margin: 0 auto; padding: 60px 40px; 
        }
        .markdown-content h1,.markdown-content h2,.markdown-content h3,.markdown-content h4,.markdown-content h5,.markdown-content h6 { 
            font-family: "Georgia", serif; font-weight: bold; color: #1a252f; 
            margin-top: 2.5em; margin-bottom: 1em; 
        }
        .markdown-content h1 { font-size: 2.4em; text-align: center; border-bottom: 3px double #34495e; padding-bottom: 0.5em; }
        .markdown-content h2 { font-size: 1.8em; border-bottom: 1px solid #bdc3c7; padding-bottom: 0.3em; }
        .markdown-content h3 { font-size: 1.4em; }
        .markdown-content p { margin-bottom: 1.5em; text-align: justify; text-indent: 2em; }
        .markdown-content blockquote { 
            border-left: 4px solid #95a5a6; margin: 2em 0; padding: 1em 2em; 
            background-color: #f8f9fa; font-style: italic; color: #5d6d7e; 
        }
        .markdown-content code { 
            background-color: #ecf0f1; padding: 3px 6px; border-radius: 4px; 
            font-family: "Consolas", "Monaco", monospace; font-size: 0.9em; 
        }
        .markdown-content pre { 
            background-color: #f4f6f7; border: 1px solid #d5dbdb; border-radius: 6px; 
            padding: 20px; overflow-x: auto; margin: 2em 0; 
            font-family: "Consolas", "Monaco", monospace; line-height: 1.5; 
        }
        .markdown-content table { width: 100%; border-collapse: collapse; margin: 2em 0; font-size: 0.95em; }
        .markdown-content td,.markdown-content th { border: 1px solid #bdc3c7; padding: 12px 15px; text-align: left; }
        .markdown-content th { background-color: #34495e; color: white; font-weight: bold; }
        .markdown-content tr:nth-child(even) { background-color: #f8f9fa; }
        .markdown-content .toc { background-color: #f8f9fa; border: 2px solid #bdc3c7; border-radius: 6px; padding: 20px; margin: 2em 0; }
        .markdown-content .toc ul { margin: 0; padding-left: 1.5em; list-style-type: none; }
        .markdown-content .toc > ul { padding-left: 0; }
        .markdown-content .toc li { margin: 6px 0; }
        .markdown-content .toc a, .markdown-content .toc a:link, .markdown-content .toc a:visited, .markdown-content .toc a:hover, .markdown-content .toc a:active { 
            text-decoration: none !important; color: #2c3e50; font-weight: 600; 
            border: none !important; outline: none !important;
        }
        .markdown-content .toc a:hover { 
            color: #34495e !important; background-color: rgba(44, 62, 80, 0.1) !important;
            padding: 2px 4px; border-radius: 3px;
        }
        .markdown-content .toclink, .markdown-content .toclink:link, .markdown-content .toclink:visited, .markdown-content .toclink:hover, .markdown-content .toclink:active {
            text-decoration: none !important; border-bottom: none !important;
            border: none !important; outline: none !important;
        }
        .markdown-content .headerlink { display: none !important; }
        .markdown-content .task-list-item { list-style-type: none; margin-left: -1.5em; }
        .markdown-content .task-list-item input { margin-right: 8px; transform: scale(1.2); }
        .markdown-content .mermaid { background-color: #f8f9fa; border: 2px solid #bdc3c7; border-radius: 6px; padding: 20px; margin: 2em 0; }
        .markdown-content .mermaid pre { background: transparent; border: none; padding: 0; margin: 0; }
        .markdown-content .mermaid code { background: transparent; padding: 0; font-size: 14px; }
    ''',
    'elegant': '''
        .markdown-content { 
            font-family: "Crimson Text", "Georgia", serif; line-height: 1.8; color: #2c3e50; background-color: #fdfcf8; 
            max-width: 850px; margin: 0 auto; padding: 60px 50px; 
        }
        .markdown-content h1,.markdown-content h2,.markdown-content h3,.markdown-content h4,.markdown-content h5,.markdown-content h6 { 
            font-family: "Playfair Display", "Georgia", serif; font-weight: 700; color: #1a252f; 
            margin-top: 3em; margin-bottom: 1em; 
        }
        .markdown-content h1 { 
            font-size: 3.2em; text-align: center; margin-bottom: 0.5em; 
            border-bottom: 2px solid #d4af37; padding-bottom: 0.3em; 
        }
        .markdown-content h2 { font-size: 2.4em; color: #8b4513; }
        .markdown-content h3 { font-size: 1.8em; color: #a0522d; }
        .markdown-content p { margin-bottom: 1.6em; text-align: justify; font-size: 1.1em; }
        .markdown-content blockquote { 
            border-left: 4px solid #d4af37; background-color: #f9f7f1; margin: 2.5em 0; 
            padding: 1.5em 2.5em; font-style: italic; font-size: 1.05em; color: #5d4e37; 
            border-radius: 0 8px 8px 0; 
        }
        .markdown-content code { 
            background-color: #f4f1eb; border: 1px solid #e8dcc6; padding: 3px 6px; 
            border-radius: 4px; font-family: "Source Code Pro", monospace; color: #8b4513; 
        }
        .markdown-content pre { 
            background-color: #f9f7f1; border: 1px solid #e8dcc6; border-radius: 8px; 
            padding: 25px; overflow-x: auto; margin: 2.5em 0; 
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.06); 
        }
        .markdown-content table { width: 100%; border-collapse: collapse; margin: 2.5em 0; font-size: 1em; }
        .markdown-content th { background-color: #8b4513; color: #fdfcf8; padding: 15px; font-weight: bold; border: 1px solid #a0522d; }
        .markdown-content td { padding: 12px 15px; border: 1px solid #d4af37; background-color: #fdfcf8; }
        .markdown-content tr:nth-child(even) td { background-color: #f9f7f1; }
        .markdown-content .toc { background-color: #f9f7f1; border: 2px solid #d4af37; border-radius: 8px; padding: 25px; margin: 2.5em 0; }
        .markdown-content .toc ul { margin: 0; padding-left: 1.5em; list-style-type: none; }
        .markdown-content .toc > ul { padding-left: 0; }
        .markdown-content .toc li { margin: 6px 0; }
        .markdown-content .toc a, .markdown-content .toc a:link, .markdown-content .toc a:visited, .markdown-content .toc a:hover, .markdown-content .toc a:active { 
            text-decoration: none !important; color: #8b4513; font-weight: 600; 
            font-family: "Playfair Display", "Georgia", serif;
            border: none !important; outline: none !important;
        }
        .markdown-content .toc a:hover { 
            color: #a0522d !important; background-color: rgba(139, 69, 19, 0.1) !important;
            padding: 2px 4px; border-radius: 3px;
        }
        .markdown-content .toclink, .markdown-content .toclink:link, .markdown-content .toclink:visited, .markdown-content .toclink:hover, .markdown-content .toclink:active {
            text-decoration: none !important; border-bottom: none !important;
            border: none !important; outline: none !important;
        }
        .markdown-content .headerlink { display: none !important; }
        .markdown-content .mermaid { background-color: #f9f7f1; border: 2px solid #d4af37; border-radius: 8px; padding: 25px; margin: 2.5em 0; }
        .markdown-content .mermaid pre { background: transparent; border: none; padding: 0; margin: 0; }
        .markdown-content .mermaid code { background: transparent; padding: 0; font-size: 14px; color: #8b4513; }
    ''',
}

def _get_css_style(theme: str) -> str:
    return _THEME_STYLES.get(theme, _THEME_STYLES['github'])

def _get_pygments_css(style: str) -> str:
    try:
        formatter = HtmlFormatter(style=style, cssclass='highlight')
        return formatter.get_style_defs()
    except Exception:
        return ''


# ────────────── 过滤器注册接口 ──────────────

def register_filters():
    """返回过滤器字典，供外部使用（前后端分离后不再直接注册到 Jinja2）"""
    return {
        'json': json_filter,
        'string_split': string_split,
        'md2html': md2html,
        'relative_time': relative_time_filter,
        'CategoryName': category_filter,
        'F2list': f2list,
    }