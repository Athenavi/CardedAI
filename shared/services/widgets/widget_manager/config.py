"""
Widget配置常量
定义所有Widget类型和区域配置
"""

# Widget类型定义
WIDGET_TYPES = {
    'recent_posts': {
        'name': '最新文章',
        'description': '显示最近发布的文章列表',
        'icon': '📝',
        'category': 'content',
        'default_config': {
            'title': '最新文章',
            'count': 5,
            'show_thumbnail': True,
            'show_date': True,
            'show_excerpt': False,
            'excerpt_length': 100
        }
    },
    'categories': {
        'name': '分类目录',
        'description': '显示文章分类列表',
        'icon': '📂',
        'category': 'navigation',
        'default_config': {
            'title': '分类目录',
            'show_count': True,
            'hierarchical': True
        }
    },
    'tags': {
        'name': '标签云',
        'description': '显示热门标签云',
        'icon': '🏷️',
        'category': 'navigation',
        'default_config': {
            'title': '标签云',
            'count': 20,
            'display_type': 'cloud'
        }
    },
    'menu': {
        'name': '菜单',
        'description': '显示网站菜单',
        'icon': '📋',
        'category': 'navigation',
        'default_config': {
            'title': '菜单',
            'menu_slug': 'main-menu',
            'show_submenus': True
        }
    },
    'search': {
        'name': '搜索框',
        'description': '站内搜索功能',
        'icon': '🔍',
        'category': 'utility',
        'default_config': {
            'title': '搜索',
            'placeholder': '搜索文章...'
        }
    },
    'archives': {
        'name': '文章归档',
        'description': '按月份显示文章归档',
        'icon': '📅',
        'category': 'navigation',
        'default_config': {
            'title': '文章归档',
            'type': 'monthly',
            'show_count': True
        }
    },
    'social_links': {
        'name': '社交链接',
        'description': '显示社交媒体链接',
        'icon': '🌐',
        'category': 'social',
        'default_config': {
            'title': '关注我们',
            'platforms': ['weibo', 'wechat', 'twitter', 'facebook']
        }
    },
    'newsletter': {
        'name': '邮件订阅',
        'description': '邮件订阅表单',
        'icon': '📧',
        'category': 'marketing',
        'default_config': {
            'title': '订阅更新',
            'description': '获取最新文章通知',
            'button_text': '订阅'
        }
    },
    'advertisement': {
        'name': '广告位',
        'description': '自定义广告内容',
        'icon': '📢',
        'category': 'monetization',
        'default_config': {
            'title': '',
            'content': '',
            'link': '',
            'image': ''
        }
    },
    'html': {
        'name': '自定义HTML',
        'description': '插入自定义HTML代码',
        'icon': '💻',
        'category': 'custom',
        'default_config': {
            'title': '',
            'html_content': ''
        }
    },
    'recent_comments': {
        'name': '最新评论',
        'description': '显示最近的评论',
        'icon': '💬',
        'category': 'content',
        'default_config': {
            'title': '最新评论',
            'count': 5,
            'show_avatar': True
        }
    },
    'popular_posts': {
        'name': '热门文章',
        'description': '显示浏览量最高的文章',
        'icon': '🔥',
        'category': 'content',
        'default_config': {
            'title': '热门文章',
            'count': 5,
            'period': 'week'
        }
    }
}

# Widget区域定义
WIDGET_AREAS = {
    'sidebar_primary': {
        'name': '主边栏',
        'description': '网站右侧边栏',
        'max_widgets': None
    },
    'sidebar_secondary': {
        'name': '次边栏',
        'description': '网站左侧边栏',
        'max_widgets': None
    },
    'footer_1': {
        'name': '页脚区域1',
        'description': '页脚第一列',
        'max_widgets': 5
    },
    'footer_2': {
        'name': '页脚区域2',
        'description': '页脚第二列',
        'max_widgets': 5
    },
    'footer_3': {
        'name': '页脚区域3',
        'description': '页脚第三列',
        'max_widgets': 5
    },
    'header_top': {
        'name': '顶部区域',
        'description': '网站顶部横幅',
        'max_widgets': 3
    },
    'before_content': {
        'name': '内容前',
        'description': '文章内容之前',
        'max_widgets': 2
    },
    'after_content': {
        'name': '内容后',
        'description': '文章内容之后',
        'max_widgets': 2
    }
}
