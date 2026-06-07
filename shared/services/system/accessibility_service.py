"""
无障碍支持服务
提供 WCAG 2.1 标准的无障碍功能支持
"""
import json
import logging
from typing import Dict, Any, List

from src.extensions import get_db

logger = logging.getLogger(__name__)

# 配置在 system_settings 表中的 key 前缀
_CONFIG_KEY_PREFIX = 'accessibility_config_'


class AccessibilityService:
    """
    无障碍支持服务

    功能:
    1. 键盘导航支持
    2. 屏幕阅读器优化
    3. 高对比度模式
    4. 字体大小调整
    5. 动画减少选项
    6. ARIA 标签生成

    持久化: 使用 system_settings 表存储 per-user 配置
    - key: accessibility_config_{user_id}
    - value: JSON 字符串
    """

    # 默认无障碍配置
    DEFAULT_CONFIG: Dict[str, Any] = {
        'keyboard_navigation': True,
        'screen_reader_support': True,
        'high_contrast_mode': False,
        'font_size': 'medium',  # small, medium, large, x-large
        'reduce_motion': False,
        'focus_visible': True,
        'skip_links': True,
    }

    # 有效配置键
    VALID_KEYS = set(DEFAULT_CONFIG.keys())

    # 有效字体大小
    VALID_FONT_SIZES = ['small', 'medium', 'large', 'x-large']

    def get_accessibility_config(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户的无障碍配置

        Args:
            user_id: 用户 ID

        Returns:
            用户的无障碍配置字典
        """
        setting_key = f'{_CONFIG_KEY_PREFIX}{user_id}'
        try:
            with get_db() as db:
                from shared.models.system_settings import SystemSettings
                record = db.query(SystemSettings).filter(
                    SystemSettings.setting_key == setting_key
                ).first()

                if record and record.setting_value:
                    try:
                        user_config = json.loads(record.setting_value)
                        # 合并默认值，确保返回所有字段
                        merged = {**self.DEFAULT_CONFIG, **user_config}
                        return merged
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse accessibility config for user {user_id}")

        except Exception as e:
            logger.error(f"DB error getting accessibility config for user {user_id}: {e}")

        return self.DEFAULT_CONFIG.copy()

    def update_accessibility_config(self, user_id: int, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新用户无障碍配置（持久化到 system_settings 表）

        Args:
            user_id: 用户ID
            config: 新的配置

        Returns:
            更新后的完整配置
        """
        # 验证配置项
        for key in config:
            if key not in self.VALID_KEYS:
                raise ValueError(f"Invalid config key: {key}")

        # 验证值的有效性
        if 'font_size' in config:
            if config['font_size'] not in self.VALID_FONT_SIZES:
                raise ValueError(f"Invalid font_size: {config['font_size']}")

        # 验证布尔字段
        bool_keys = [k for k in self.VALID_KEYS if k != 'font_size']
        for key in bool_keys:
            if key in config and not isinstance(config[key], bool):
                raise ValueError(f"Config key '{key}' must be a boolean")

        setting_key = f'{_CONFIG_KEY_PREFIX}{user_id}'

        try:
            with get_db() as db:
                from shared.models.system_settings import SystemSettings
                from datetime import datetime, timezone

                record = db.query(SystemSettings).filter(
                    SystemSettings.setting_key == setting_key
                ).first()

                # 获取当前配置
                if record and record.setting_value:
                    try:
                        current = json.loads(record.setting_value)
                    except json.JSONDecodeError:
                        current = {}
                else:
                    current = {}

                # 合并更新
                current.update(config)

                if record:
                    record.setting_value = json.dumps(current, ensure_ascii=False)
                    record.updated_at = datetime.now(timezone.utc)
                else:
                    record = SystemSettings(
                        setting_key=setting_key,
                        setting_value=json.dumps(current, ensure_ascii=False),
                        setting_type='json',
                        description=f'用户 {user_id} 的无障碍配置',
                        is_public=False,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    )
                    db.add(record)

                db.commit()

                # 返回合并默认值的完整配置
                return {**self.DEFAULT_CONFIG, **current}

        except Exception as e:
            logger.error(f"DB error updating accessibility config for user {user_id}: {e}")
            raise

    def generate_skip_links(self) -> List[Dict[str, str]]:
        """
        生成跳过链接

        跳过链接允许键盘用户快速跳转到页面的主要部分

        Returns:
            跳过链接列表
        """
        return [
            {
                'id': 'skip-to-main',
                'text': '跳到主要内容',
                'target': '#main-content',
                'aria_label': 'Skip to main content'
            },
            {
                'id': 'skip-to-nav',
                'text': '跳到导航',
                'target': '#main-navigation',
                'aria_label': 'Skip to navigation'
            },
            {
                'id': 'skip-to-search',
                'text': '跳到搜索',
                'target': '#search-form',
                'aria_label': 'Skip to search'
            },
            {
                'id': 'skip-to-footer',
                'text': '跳到底部',
                'target': '#footer',
                'aria_label': 'Skip to footer'
            }
        ]

    def generate_keyboard_shortcuts(self) -> List[Dict[str, str]]:
        """
        生成键盘快捷键

        Returns:
            快捷键列表
        """
        return [
            {
                'key': 'Alt+1',
                'action': '跳到主页',
                'description': 'Navigate to home page'
            },
            {
                'key': 'Alt+2',
                'action': '跳到文章列表',
                'description': 'Navigate to articles list'
            },
            {
                'key': 'Alt+S',
                'action': '聚焦搜索框',
                'description': 'Focus search input'
            },
            {
                'key': 'Alt+H',
                'action': '显示帮助',
                'description': 'Show keyboard shortcuts help'
            },
            {
                'key': 'Escape',
                'action': '关闭弹窗/菜单',
                'description': 'Close modal/menu'
            },
            {
                'key': 'Tab',
                'action': '下一个焦点元素',
                'description': 'Move to next focusable element'
            },
            {
                'key': 'Shift+Tab',
                'action': '上一个焦点元素',
                'description': 'Move to previous focusable element'
            }
        ]

    def generate_aria_labels(self, element_type: str, context: Dict[str, Any] = None) -> Dict[str, str]:
        """
        生成 ARIA 标签

        Args:
            element_type: 元素类型 (button, link, form, navigation, etc.)
            context: 上下文信息

        Returns:
            ARIA 属性字典
        """
        aria_labels = {
            'button': {
                'role': 'button',
                'aria_pressed': 'false',
            },
            'link': {
                'role': 'link',
            },
            'navigation': {
                'role': 'navigation',
                'aria_label': 'Main navigation',
            },
            'search': {
                'role': 'search',
                'aria_label': 'Search',
            },
            'form': {
                'role': 'form',
                'aria_labelledby': 'form-title',
            },
            'dialog': {
                'role': 'dialog',
                'aria_modal': 'true',
                'aria_labelledby': 'dialog-title',
            },
            'alert': {
                'role': 'alert',
                'aria_live': 'polite',
            },
            'menu': {
                'role': 'menu',
                'aria_label': 'Menu',
            },
            'tablist': {
                'role': 'tablist',
                'aria_label': 'Tabs',
            },
        }

        return aria_labels.get(element_type, {})

    def get_high_contrast_css(self) -> str:
        """
        生成高对比度模式的 CSS

        Returns:
            CSS 样式字符串
        """
        return """
/* High Contrast Mode Styles */
.high-contrast {
    --bg-color: #000000;
    --text-color: #ffffff;
    --link-color: #ffff00;
    --border-color: #ffffff;
    --focus-color: #00ff00;
}

.high-contrast body {
    background-color: var(--bg-color) !important;
    color: var(--text-color) !important;
}

.high-contrast a {
    color: var(--link-color) !important;
    text-decoration: underline !important;
}

.high-contrast a:focus,
.high-contrast button:focus,
.high-contrast input:focus {
    outline: 3px solid var(--focus-color) !important;
    outline-offset: 2px !important;
}

.high-contrast img {
    border: 2px solid var(--border-color) !important;
}

.high-contrast .btn {
    border: 2px solid var(--border-color) !important;
}
"""

    def get_font_size_css(self, size: str) -> str:
        """
        生成字体大小调整的 CSS

        Args:
            size: 字体大小级别 (small, medium, large, x-large)

        Returns:
            CSS 样式字符串
        """
        size_map = {
            'small': '0.875rem',
            'medium': '1rem',
            'large': '1.125rem',
            'x-large': '1.25rem',
        }

        base_size = size_map.get(size, '1rem')

        return f"""
/* Font Size: {size} */
.font-size-{size} {{
    --base-font-size: {base_size};
}}

.font-size-{size} body {{
    font-size: var(--base-font-size);
}}

.font-size-{size} h1 {{
    font-size: calc(var(--base-font-size) * 2.5);
}}

.font-size-{size} h2 {{
    font-size: calc(var(--base-font-size) * 2);
}}

.font-size-{size} h3 {{
    font-size: calc(var(--base-font-size) * 1.75);
}}

.font-size-{size} p {{
    font-size: var(--base-font-size);
    line-height: 1.8;
}}
"""

    def get_reduce_motion_css(self) -> str:
        """
        生成减少动画的 CSS

        Returns:
            CSS 样式字符串
        """
        return """
/* Reduce Motion */
@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
    }
}

.reduce-motion * {
    animation: none !important;
    transition: none !important;
}
"""

    def validate_accessibility(self, html_content: str) -> Dict[str, Any]:
        """
        验证 HTML 内容的无障碍性

        Args:
            html_content: HTML 内容

        Returns:
            验证结果，包括问题和警告
        """
        issues = []
        warnings = []

        # 检查 alt 属性
        if '<img' in html_content and 'alt=' not in html_content:
            issues.append({
                'type': 'error',
                'rule': 'img-alt',
                'message': '图片缺少 alt 属性',
                'severity': 'critical'
            })

        # 检查表单标签
        if '<input' in html_content and '<label' not in html_content:
            warnings.append({
                'type': 'warning',
                'rule': 'form-label',
                'message': '表单元素可能缺少关联的 label',
                'severity': 'moderate'
            })

        # 检查标题层级
        if '<h1>' not in html_content:
            warnings.append({
                'type': 'warning',
                'rule': 'heading-hierarchy',
                'message': '页面缺少 h1 标题',
                'severity': 'moderate'
            })

        # 检查语言属性
        if '<html' in html_content and 'lang=' not in html_content:
            issues.append({
                'type': 'error',
                'rule': 'html-lang',
                'message': 'HTML 元素缺少 lang 属性',
                'severity': 'serious'
            })

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'score': max(0, 100 - len(issues) * 20 - len(warnings) * 10),
        }

    def get_accessibility_guide(self) -> Dict[str, Any]:
        """
        获取无障碍使用指南

        Returns:
            指南内容
        """
        return {
            'title': '无障碍功能使用指南',
            'sections': [
                {
                    'title': '键盘导航',
                    'content': '使用 Tab 键在页面元素间移动，Shift+Tab 反向移动，Enter 或 Space 激活按钮和链接。',
                    'shortcuts': self.generate_keyboard_shortcuts()
                },
                {
                    'title': '屏幕阅读器',
                    'content': '系统为所有交互元素提供了适当的 ARIA 标签，确保屏幕阅读器能够正确识别和朗读。',
                    'tips': [
                        '所有按钮都有明确的标签',
                        '表单字段有关联的说明文本',
                        '错误消息会自动朗读',
                        '动态内容更新会通知屏幕阅读器'
                    ]
                },
                {
                    'title': '视觉辅助',
                    'content': '您可以自定义字体大小、启用高对比度模式、减少动画效果，以获得更好的阅读体验。',
                    'options': [
                        '字体大小：小、中、大、特大',
                        '高对比度模式：增强颜色对比度',
                        '减少动画：禁用不必要的动画效果'
                    ]
                },
                {
                    'title': '跳过链接',
                    'content': '按 Tab 键时，第一个焦点是"跳到主要内容"链接，可以快速跳过导航到达主要内容区域。',
                    'links': self.generate_skip_links()
                }
            ],
            'wcag_compliance': 'WCAG 2.1 Level AA',
            'contact': '如有无障碍相关问题，请联系 support@fastblog.com'
        }
