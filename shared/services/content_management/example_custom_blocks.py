"""
自定义块示例插件
演示如何创建和注册自定义块类型
"""

from shared.services.content_management.block_editor_service import BlockType
from shared.services.content_management.custom_block_framework import CustomBlockPlugin


class ExampleBlocksPlugin(CustomBlockPlugin):
    """示例块插件 - 展示如何创建自定义块"""

    name = "example-blocks"
    version = "1.0.0"
    description = "示例自定义块集合，展示框架使用方法"
    author = "FastBlog Team"

    def register_blocks(self):
        """注册示例块类型"""

        # 1. 警告框块
        self.register_block(BlockType(
            name="alert",
            display_name="警告框",
            category="widget",
            icon="⚠️",
            description="显示重要提示信息",
            attributes={
                "message": {"type": "string", "required": True, "description": "警告消息"},
                "level": {
                    "type": "string",
                    "enum": ["info", "warning", "error", "success"],
                    "default": "info",
                    "description": "警告级别"
                },
                "dismissible": {
                    "type": "boolean",
                    "default": False,
                    "description": "是否可关闭"
                }
            }
        ))

        # 2. 进度条块
        self.register_block(BlockType(
            name="progress",
            display_name="进度条",
            category="widget",
            icon="📊",
            description="显示进度百分比",
            attributes={
                "percentage": {
                    "type": "integer",
                    "default": 0,
                    "description": "进度百分比 (0-100)"
                },
                "label": {
                    "type": "string",
                    "default": "",
                    "description": "进度标签"
                },
                "color": {
                    "type": "string",
                    "default": "#3b82f6",
                    "description": "进度条颜色"
                },
                "showPercentage": {
                    "type": "boolean",
                    "default": True,
                    "description": "是否显示百分比"
                }
            }
        ))

        # 3. 卡片块
        self.register_block(BlockType(
            name="card",
            display_name="卡片",
            category="layout",
            icon="🃏",
            description="内容卡片容器",
            attributes={
                "title": {
                    "type": "string",
                    "default": "",
                    "description": "卡片标题"
                },
                "subtitle": {
                    "type": "string",
                    "default": "",
                    "description": "副标题"
                },
                "shadow": {
                    "type": "boolean",
                    "default": True,
                    "description": "是否显示阴影"
                },
                "bordered": {
                    "type": "boolean",
                    "default": False,
                    "description": "是否显示边框"
                },
                "padding": {
                    "type": "string",
                    "enum": ["none", "small", "medium", "large"],
                    "default": "medium",
                    "description": "内边距大小"
                }
            },
            allowed_children=["paragraph", "heading", "image", "button"]
        ))

        # 4. 倒计时块
        self.register_block(BlockType(
            name="countdown",
            display_name="倒计时",
            category="widget",
            icon="⏱️",
            description="倒计时计时器",
            attributes={
                "targetDate": {
                    "type": "string",
                    "required": True,
                    "description": "目标日期时间 (ISO格式)"
                },
                "label": {
                    "type": "string",
                    "default": "倒计时",
                    "description": "倒计时标签"
                },
                "showDays": {
                    "type": "boolean",
                    "default": True,
                    "description": "是否显示天数"
                },
                "expiredMessage": {
                    "type": "string",
                    "default": "已结束",
                    "description": "过期后显示的消息"
                }
            }
        ))

        # 5. 引用块（带样式）
        self.register_block(BlockType(
            name="testimonial",
            display_name="客户评价",
            category="widget",
            icon="💬",
            description="展示客户评价或推荐语",
            attributes={
                "quote": {
                    "type": "string",
                    "required": True,
                    "description": "评价内容"
                },
                "author": {
                    "type": "string",
                    "required": True,
                    "description": "评价者姓名"
                },
                "role": {
                    "type": "string",
                    "default": "",
                    "description": "评价者职位/角色"
                },
                "avatar": {
                    "type": "string",
                    "default": "",
                    "description": "头像URL"
                },
                "rating": {
                    "type": "integer",
                    "default": 5,
                    "description": "评分 (1-5)"
                }
            }
        ))

    # 自定义渲染方法

    def render_alert(self, attributes, children):
        """渲染警告框"""
        level = attributes.get("level", "info")
        message = attributes.get("message", "")
        dismissible = attributes.get("dismissible", False)

        level_classes = {
            "info": "bg-blue-50 border-blue-200 text-blue-800",
            "warning": "bg-yellow-50 border-yellow-200 text-yellow-800",
            "error": "bg-red-50 border-red-200 text-red-800",
            "success": "bg-green-50 border-green-200 text-green-800"
        }

        css_class = level_classes.get(level, level_classes["info"])
        dismiss_button = '<button class="ml-2 text-current opacity-50 hover:opacity-100">&times;</button>' if dismissible else ''

        return f'''
        <div class="p-4 border-l-4 rounded {css_class}" role="alert">
            <div class="flex items-center justify-between">
                <span>{message}</span>
                {dismiss_button}
            </div>
        </div>
        '''

    def render_progress(self, attributes, children):
        """渲染进度条"""
        percentage = min(max(attributes.get("percentage", 0), 0), 100)
        label = attributes.get("label", "")
        color = attributes.get("color", "#3b82f6")
        show_percentage = attributes.get("showPercentage", True)

        label_html = f'<div class="mb-2 text-sm font-medium">{label}</div>' if label else ''
        percentage_html = f'<span class="text-sm">{percentage}%</span>' if show_percentage else ''

        return f'''
        <div class="w-full">
            {label_html}
            <div class="w-full bg-gray-200 rounded-full h-2.5">
                <div class="h-2.5 rounded-full transition-all" 
                     style="width: {percentage}%; background-color: {color};"></div>
            </div>
            <div class="mt-1 flex justify-between">
                {percentage_html}
            </div>
        </div>
        '''

    def render_card(self, attributes, children):
        """渲染卡片"""
        title = attributes.get("title", "")
        subtitle = attributes.get("subtitle", "")
        shadow = attributes.get("shadow", True)
        bordered = attributes.get("bordered", False)
        padding = attributes.get("padding", "medium")

        padding_classes = {
            "none": "p-0",
            "small": "p-3",
            "medium": "p-6",
            "large": "p-8"
        }

        shadow_class = "shadow-lg" if shadow else ""
        border_class = "border border-gray-200" if bordered else ""
        padding_class = padding_classes.get(padding, "p-6")

        title_html = f'<h3 class="text-lg font-semibold mb-1">{title}</h3>' if title else ''
        subtitle_html = f'<p class="text-sm text-gray-600 mb-4">{subtitle}</p>' if subtitle else ''

        children_html = "".join([self.base_service.render_block(child) for child in children]) if children else ""

        return f'''
        <div class="bg-white rounded-lg {shadow_class} {border_class} {padding_class}">
            {title_html}
            {subtitle_html}
            {children_html}
        </div>
        '''

    def render_countdown(self, attributes, children):
        """渲染倒计时（需要JavaScript支持）"""
        target_date = attributes.get("targetDate", "")
        label = attributes.get("label", "倒计时")
        show_days = attributes.get("showDays", True)
        expired_message = attributes.get("expiredMessage", "已结束")

        return f'''
        <div class="countdown-timer p-4 bg-gray-50 rounded-lg text-center" 
             data-target="{target_date}" 
             data-show-days="{str(show_days).lower()}"
             data-expired-message="{expired_message}">
            <div class="text-sm text-gray-600 mb-2">{label}</div>
            <div class="countdown-display text-2xl font-mono font-bold">
                加载中...
            </div>
            <script>
            (function() {{
                const timer = document.currentScript.parentElement;
                const target = new Date(timer.dataset.target).getTime();
                const showDays = timer.dataset.showDays === 'true';
                
                function update() {{
                    const now = new Date().getTime();
                    const distance = target - now;
                    
                    if (distance < 0) {{
                        timer.querySelector('.countdown-display').textContent = timer.dataset.expiredMessage;
                        return;
                    }}
                    
                    const days = Math.floor(distance / (1000 * 60 * 60 * 24));
                    const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                    const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                    const seconds = Math.floor((distance % (1000 * 60)) / 1000);
                    
                    let display = '';
                    if (showDays) display += days + '天 ';
                    display += hours.toString().padStart(2, '0') + ':';
                    display += minutes.toString().padStart(2, '0') + ':';
                    display += seconds.toString().padStart(2, '0');
                    
                    timer.querySelector('.countdown-display').textContent = display;
                }}
                
                update();
                setInterval(update, 1000);
            }})();
            </script>
        </div>
        '''

    def render_testimonial(self, attributes, children):
        """渲染客户评价"""
        quote = attributes.get("quote", "")
        author = attributes.get("author", "")
        role = attributes.get("role", "")
        avatar = attributes.get("avatar", "")
        rating = attributes.get("rating", 5)

        stars = "⭐" * rating
        avatar_html = f'<img src="{avatar}" alt="{author}" class="w-12 h-12 rounded-full mr-4"/>' if avatar else ''
        role_html = f'<div class="text-sm text-gray-600">{role}</div>' if role else ''

        return f'''
        <blockquote class="p-6 bg-white border-l-4 border-blue-500 rounded-lg shadow-sm">
            <div class="flex items-start">
                {avatar_html}
                <div class="flex-1">
                    <div class="text-lg italic text-gray-700 mb-3">"{quote}"</div>
                    <div class="flex items-center">
                        <div>
                            <div class="font-semibold">{author}</div>
                            {role_html}
                        </div>
                    </div>
                    <div class="mt-2 text-sm">{stars}</div>
                </div>
            </div>
        </blockquote>
        '''
