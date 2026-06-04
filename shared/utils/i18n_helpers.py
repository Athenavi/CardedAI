"""
国际化(i18n)辅助函数 - WordPress风格
提供便捷的翻译函数,类似WordPress的 __(), _e(), _x() 等
"""
from shared.services.translation.translation_manager.i18n_service import i18n_service


def __(text: str, domain: str = 'default', language: str = None) -> str:
    """
    翻译并返回文本 (WordPress: __())
    
    Args:
        text: 要翻译的文本
        domain: 文本域(用于区分不同插件/主题的翻译)
        language: 目标语言(默认使用当前语言)
        
    Returns:
        翻译后的文本
        
    Example:
        >>> title = __('Hello World')
        >>> print(title)
        '你好世界'
    """
    return i18n_service.translate(text, language=language)


def _e(text: str, domain: str = 'default', language: str = None) -> None:
    """
    翻译并直接输出 (WordPress: _e())
    
    Args:
        text: 要翻译的文本
        domain: 文本域
        language: 目标语言
        
    Example:
        >>> _e('Hello World')
        # 直接输出: 你好世界
    """
    print(__(text, domain, language), end='')


def _x(text: str, context: str, domain: str = 'default', language: str = None) -> str:
    """
    带上下文的翻译 (WordPress: _x())
    用于同一文本在不同上下文中有不同翻译的情况
    
    Args:
        text: 要翻译的文本
        context: 上下文说明
        domain: 文本域
        language: 目标语言
        
    Returns:
        翻译后的文本
        
    Example:
        >>> # "post" 作为名词 vs 动词
        >>> _x('Post', 'noun')  # 文章
        >>> _x('Post', 'verb')  # 发布
    """
    # 使用 context|text 作为key来区分不同上下文
    key = f"{context}|{text}"
    translation = i18n_service.translate(key, language=language)
    
    # 如果没有找到带上下文的翻译,回退到普通翻译
    if translation == key:
        translation = __(text, domain, language)
    
    return translation


def _ex(text: str, context: str, domain: str = 'default', language: str = None) -> None:
    """
    带上下文翻译并输出 (WordPress: _ex())
    
    Args:
        text: 要翻译的文本
        context: 上下文说明
        domain: 文本域
        language: 目标语言
    """
    print(_x(text, context, domain, language), end='')


def _n(singular: str, plural: str, count: int, domain: str = 'default', language: str = None) -> str:
    """
    复数形式翻译 (WordPress: _n())
    
    Args:
        singular: 单数形式
        plural: 复数形式
        count: 数量
        domain: 文本域
        language: 目标语言
        
    Returns:
        翻译后的文本
        
    Example:
        >>> _n('%d comment', '%d comments', 1)
        '%d 条评论'
        >>> _n('%d comment', '%d comments', 5)
        '%d 条评论'
    """
    # 中文不区分单复数,直接返回复数形式
    # 其他语言可以根据需要扩展逻辑
    key = f"plural:{singular}|{plural}"
    translation = i18n_service.translate(key, language=language)
    
    # 如果没有找到复数翻译,根据数量选择
    if translation == key:
        if count == 1:
            translation = __(singular, domain, language)
        else:
            translation = __(plural, domain, language)
    
    # 替换 %d 占位符
    if '%d' in translation:
        translation = translation.replace('%d', str(count))
    
    return translation


def _nx(singular: str, plural: str, count: int, context: str, domain: str = 'default', language: str = None) -> str:
    """
    带上下文的复数翻译 (WordPress: _nx())
    
    Args:
        singular: 单数形式
        plural: 复数形式
        count: 数量
        context: 上下文说明
        domain: 文本域
        language: 目标语言
        
    Returns:
        翻译后的文本
    """
    key = f"context:{context}|plural:{singular}|{plural}"
    translation = i18n_service.translate(key, language=language)
    
    # 回退到不带上下文的复数翻译
    if translation == key:
        translation = _n(singular, plural, count, domain, language)
    
    return translation


def esc_html__(text: str, domain: str = 'default', language: str = None) -> str:
    """
    翻译并转义HTML (WordPress: esc_html__())
    
    Args:
        text: 要翻译的文本
        domain: 文本域
        language: 目标语言
        
    Returns:
        转义后的翻译文本
    """
    from html import escape
    translated = __(text, domain, language)
    return escape(translated)


def esc_attr__(text: str, domain: str = 'default', language: str = None) -> str:
    """
    翻译并转义属性值 (WordPress: esc_attr__())
    
    Args:
        text: 要翻译的文本
        domain: 文本域
        language: 目标语言
        
    Returns:
        转义后的翻译文本
    """
    from html import escape
    translated = __(text, domain, language)
    return escape(translated, quote=True)


# 导出所有函数
__all__ = [
    '__', '_e', '_x', '_ex', '_n', '_nx',
    'esc_html__', 'esc_attr__'
]
