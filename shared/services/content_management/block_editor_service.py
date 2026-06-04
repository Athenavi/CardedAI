"""
块编辑器服务
提供块类型的注册、验证和渲染功能

使用示例:
    from shared.services.block_editor_service import block_editor_service, BlockType
    
    # 1. 获取所有块类型
    all_blocks = block_editor_service.get_all_block_types()
    
    # 2. 按分类获取块类型
    text_blocks = block_editor_service.get_block_types_by_category("text")
    
    # 3. 验证块数据
    block_data = {
        "type": "paragraph",
        "attributes": {
            "content": "Hello World",
            "alignment": "center"
        }
    }
    is_valid, error_msg = block_editor_service.validate_block(block_data)
    
    # 4. 渲染块为 HTML
    html = block_editor_service.render_block(block_data)
    # 输出: <p style="text-align: center;">Hello World</p>
    
    # 5. 批量渲染块列表
    blocks = [
        {"type": "heading", "attributes": {"level": 1, "content": "Title"}},
        {"type": "paragraph", "attributes": {"content": "Content"}}
    ]
    html = block_editor_service.blocks_to_html(blocks)
    
    # 6. 注册自定义块类型
    custom_block = BlockType(
        name="my-custom-block",
        display_name="我的自定义块",
        category="widget",
        attributes={
            "text": {"type": "string", "required": True}
        }
    )
    block_editor_service.register_block(custom_block)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class BlockType:
    """块类型定义"""
    name: str  # 块名称（唯一标识）
    display_name: str  # 显示名称
    category: str  # 分类：text, media, layout, widget, embed
    icon: str = ""  # 图标
    description: str = ""  # 描述
    attributes: Dict[str, Any] = field(default_factory=dict)  # 属性定义
    is_inline: bool = False  # 是否为行内块
    allowed_parents: List[str] = field(default_factory=list)  # 允许的父块
    allowed_children: List[str] = field(default_factory=list)  # 允许的子块


class BlockEditorService:
    """
    块编辑器服务
    
    功能：
    1. 块类型注册和管理
    2. 块数据验证
    3. 块渲染为 HTML
    4. 块转换（HTML ↔ JSON）
    """

    def __init__(self):
        self.block_types: Dict[str, BlockType] = {}
        self._register_default_blocks()

    def _register_default_blocks(self):
        """注册默认块类型"""

        # 文本块
        self.register_block(BlockType(
            name="paragraph",
            display_name="段落",
            category="text",
            icon="¶",
            description="普通文本段落",
            attributes={
                "content": {"type": "string", "required": True},
                "alignment": {"type": "string", "enum": ["left", "center", "right", "justify"], "default": "left"},
                "fontSize": {"type": "string", "default": "normal"}
            }
        ))

        self.register_block(BlockType(
            name="heading",
            display_name="标题",
            category="text",
            icon="H",
            description="标题文本",
            attributes={
                "level": {"type": "integer", "enum": [1, 2, 3, 4, 5, 6], "default": 2},
                "content": {"type": "string", "required": True},
                "alignment": {"type": "string", "enum": ["left", "center", "right"], "default": "left"}
            }
        ))

        self.register_block(BlockType(
            name="quote",
            display_name="引用",
            category="text",
            icon='"',
            description="引用文本块",
            attributes={
                "content": {"type": "string", "required": True},
                "citation": {"type": "string", "default": ""},
                "style": {"type": "string", "enum": ["default", "large", "elegant"], "default": "default"}
            }
        ))

        # 媒体块
        self.register_block(BlockType(
            name="image",
            display_name="图片",
            category="media",
            icon="🖼️",
            description="插入图片",
            attributes={
                "url": {"type": "string", "required": True},
                "alt": {"type": "string", "default": ""},
                "caption": {"type": "string", "default": ""},
                "width": {"type": "string", "default": "full"},
                "height": {"type": "string", "default": "auto"},
                "alignment": {"type": "string", "enum": ["left", "center", "right"], "default": "center"}
            }
        ))

        self.register_block(BlockType(
            name="video",
            display_name="视频",
            category="media",
            icon="🎥",
            description="嵌入视频",
            attributes={
                "url": {"type": "string", "required": True},
                "poster": {"type": "string", "default": ""},
                "autoplay": {"type": "boolean", "default": False},
                "loop": {"type": "boolean", "default": False},
                "controls": {"type": "boolean", "default": True}
            }
        ))

        self.register_block(BlockType(
            name="gallery",
            display_name="图库",
            category="media",
            icon="🖼️🖼️",
            description="多图片展示",
            attributes={
                "images": {"type": "array", "required": True},
                "columns": {"type": "integer", "default": 3},
                "linkTo": {"type": "string", "enum": ["none", "media", "attachment"], "default": "none"}
            }
        ))

        # 布局块
        self.register_block(BlockType(
            name="columns",
            display_name="分栏",
            category="layout",
            icon="⊞",
            description="多栏布局",
            attributes={
                "columns": {"type": "integer", "default": 2},
                "gap": {"type": "string", "default": "medium"}
            },
            allowed_children=["column"]
        ))

        self.register_block(BlockType(
            name="column",
            display_name="栏",
            category="layout",
            icon="|",
            description="分栏中的单栏",
            attributes={
                "width": {"type": "string", "default": "50%"}
            },
            is_inline=True
        ))

        self.register_block(BlockType(
            name="separator",
            display_name="分隔线",
            category="layout",
            icon="—",
            description="水平分隔线",
            attributes={
                "style": {"type": "string", "enum": ["solid", "dashed", "dotted"], "default": "solid"},
                "color": {"type": "string", "default": "#ddd"},
                "thickness": {"type": "string", "default": "1px"}
            }
        ))

        # Widget 块
        self.register_block(BlockType(
            name="code",
            display_name="代码块",
            category="widget",
            icon="</>",
            description="代码片段展示",
            attributes={
                "language": {"type": "string", "default": "javascript"},
                "content": {"type": "string", "required": True},
                "showLineNumbers": {"type": "boolean", "default": True}
            }
        ))

        self.register_block(BlockType(
            name="details",
            display_name="折叠块",
            category="widget",
            icon="📦",
            description="可展开/收起的内容块",
            attributes={
                "title": {"type": "string", "required": True, "default": "点击展开"},
                "content": {"type": "string", "required": True},
                "defaultOpen": {"type": "boolean", "default": False},
                "style": {"type": "string", "enum": ["default", "info", "warning", "success"], "default": "default"}
            }
        ))

        self.register_block(BlockType(
            name="table",
            display_name="表格",
            category="widget",
            icon="⊞",
            description="数据表格",
            attributes={
                "headers": {"type": "array", "default": []},
                "rows": {"type": "array", "required": True},
                "striped": {"type": "boolean", "default": False},
                "bordered": {"type": "boolean", "default": True}
            }
        ))

        self.register_block(BlockType(
            name="list",
            display_name="列表",
            category="widget",
            icon="☰",
            description="有序或无序列表",
            attributes={
                "items": {"type": "array", "required": True},
                "ordered": {"type": "boolean", "default": False}
            }
        ))

        # Embed 块
        self.register_block(BlockType(
            name="embed",
            display_name="嵌入内容",
            category="embed",
            icon="🔗",
            description="嵌入外部内容（YouTube, Twitter等）",
            attributes={
                "url": {"type": "string", "required": True},
                "provider": {"type": "string", "default": ""},
                "preview": {"type": "object", "default": {}}
            }
        ))

    def register_block(self, block_type: BlockType):
        """
        注册块类型
        
        Args:
            block_type: 块类型定义
        """
        self.block_types[block_type.name] = block_type

    def get_block_type(self, name: str) -> Optional[BlockType]:
        """
        获取块类型定义
        
        Args:
            name: 块名称
            
        Returns:
            块类型定义，不存在则返回 None
        """
        return self.block_types.get(name)

    def get_all_block_types(self) -> List[BlockType]:
        """获取所有注册的块类型"""
        return list(self.block_types.values())

    def get_block_types_by_category(self, category: str) -> List[BlockType]:
        """
        按分类获取块类型
        
        Args:
            category: 分类名称
            
        Returns:
            该分类下的所有块类型
        """
        return [bt for bt in self.block_types.values() if bt.category == category]

    def validate_block(self, block_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        验证块数据
        
        Args:
            block_data: 块数据 {type, attributes, children}
            
        Returns:
            (是否有效, 错误信息)
        """
        block_type_name = block_data.get("type")

        if not block_type_name:
            return False, "缺少块类型"

        block_type = self.get_block_type(block_type_name)
        if not block_type:
            return False, f"未知的块类型: {block_type_name}"

        attributes = block_data.get("attributes", {})

        # 验证必需属性
        for attr_name, attr_def in block_type.attributes.items():
            if attr_def.get("required") and attr_name not in attributes:
                return False, f"块 '{block_type.display_name}' 缺少必需属性: {attr_name}"

        # 验证属性类型和枚举值
        for attr_name, attr_value in attributes.items():
            if attr_name not in block_type.attributes:
                continue  # 忽略未定义的属性

            attr_def = block_type.attributes[attr_name]

            # 类型检查
            expected_type = attr_def.get("type")
            if expected_type == "string" and not isinstance(attr_value, str):
                return False, f"属性 '{attr_name}' 应该是字符串类型"
            elif expected_type == "integer" and not isinstance(attr_value, int):
                return False, f"属性 '{attr_name}' 应该是整数类型"
            elif expected_type == "boolean" and not isinstance(attr_value, bool):
                return False, f"属性 '{attr_name}' 应该是布尔类型"
            elif expected_type == "array" and not isinstance(attr_value, list):
                return False, f"属性 '{attr_name}' 应该是数组类型"

            # 枚举值检查
            enum_values = attr_def.get("enum")
            if enum_values and attr_value not in enum_values:
                return False, f"属性 '{attr_name}' 的值必须是以下之一: {enum_values}"

        return True, ""

    def render_block(self, block_data: Dict[str, Any]) -> str:
        """
        将块数据渲染为 HTML
        
        Args:
            block_data: 块数据 {type, attributes, children}
            
        Returns:
            HTML 字符串
        """
        block_type_name = block_data.get("type")
        block_type = self.get_block_type(block_type_name)

        if not block_type:
            return f"<!-- 未知块类型: {block_type_name} -->"

        attributes = block_data.get("attributes", {})
        children = block_data.get("children", [])

        # 根据块类型渲染
        renderer = getattr(self, f"_render_{block_type_name}", None)
        if renderer:
            return renderer(attributes, children)

        # 默认渲染
        return self._render_default(block_type, attributes, children)

    def _render_paragraph(self, attributes: Dict[str, Any], children: List[Dict]) -> str:
        """渲染段落块"""
        content = attributes.get("content", "")
        alignment = attributes.get("alignment", "left")

        style = f"text-align: {alignment};" if alignment != "left" else ""
        style_attr = f' style="{style}"' if style else ""

        return f'<p{style_attr}>{content}</p>'

    def _render_heading(self, attributes: Dict[str, Any], children: List[Dict]) -> str:
        """渲染标题块"""
        level = attributes.get("level", 2)
        content = attributes.get("content", "")
        alignment = attributes.get("alignment", "left")

        style = f"text-align: {alignment};" if alignment != "left" else ""
        style_attr = f' style="{style}"' if style else ""

        return f'<h{level}{style_attr}>{content}</h{level}>'

    def _render_image(self, attributes: Dict[str, Any], children: List[Dict]) -> str:
        """渲染图片块"""
        url = attributes.get("url", "")
        alt = attributes.get("alt", "")
        caption = attributes.get("caption", "")
        alignment = attributes.get("alignment", "center")

        align_class = f"align-{alignment}"

        html = f'<figure class="wp-block-image {align_class}">'
        html += f'<img src="{url}" alt="{alt}" />'
        if caption:
            html += f'<figcaption>{caption}</figcaption>'
        html += '</figure>'

        return html

    def _render_code(self, attributes: Dict[str, Any], children: List[Dict]) -> str:
        """渲染代码块"""
        language = attributes.get("language", "javascript")
        content = attributes.get("content", "")
        show_line_numbers = attributes.get("showLineNumbers", True)

        line_numbers_class = "line-numbers" if show_line_numbers else ""

        html = f'<pre class="wp-block-code {line_numbers_class}"><code class="language-{language}">'
        html += content.replace("<", "&lt;").replace(">", "&gt;")
        html += '</code></pre>'

        return html

    def _render_separator(self, attributes: Dict[str, Any], children: List[Dict]) -> str:
        """渲染分隔线"""
        style = attributes.get("style", "solid")
        color = attributes.get("color", "#ddd")
        thickness = attributes.get("thickness", "1px")

        border_style = {
            "solid": "solid",
            "dashed": "dashed",
            "dotted": "dotted"
        }.get(style, "solid")

        hr_style = f'border-top: {thickness} {border_style} {color};'

        return f'<hr class="wp-block-separator" style="{hr_style}" />'

    def _render_details(self, attributes: Dict[str, Any], children: List[Dict]) -> str:
        """渲染折叠块（details/summary）"""
        title = attributes.get("title", "点击展开")
        content = attributes.get("content", "")
        default_open = attributes.get("defaultOpen", False)
        style = attributes.get("style", "default")

        # 根据样式添加不同的class
        style_classes = {
            "info": "border-l-4 border-blue-500 bg-blue-50 dark:bg-blue-900/20",
            "warning": "border-l-4 border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20",
            "success": "border-l-4 border-green-500 bg-green-50 dark:bg-green-900/20",
            "default": "border-l-4 border-gray-300 dark:border-gray-600"
        }

        container_class = style_classes.get(style, style_classes["default"])
        open_attr = ' open' if default_open else ''

        html = f'''
<details class="wp-block-details {container_class} p-4 rounded-lg my-4"{open_attr}>
    <summary class="cursor-pointer font-semibold text-gray-900 dark:text-gray-100 hover:text-blue-600 dark:hover:text-blue-400 transition-colors select-none">
        {title}
    </summary>
    <div class="mt-3 text-gray-700 dark:text-gray-300 leading-relaxed">
        {content}
    </div>
</details>
'''.strip()

        return html

    def _render_default(self, block_type: BlockType, attributes: Dict[str, Any], children: List[Dict]) -> str:
        """默认渲染方法"""
        # 如果有子块，递归渲染
        children_html = ""
        if children:
            children_html = "".join([self.render_block(child) for child in children])

        return f'<!-- Block: {block_type.name} -->\n{children_html}'

    def blocks_to_html(self, blocks: List[Dict[str, Any]]) -> str:
        """
        将块列表转换为 HTML
        
        Args:
            blocks: 块数据列表
            
        Returns:
            HTML 字符串
        """
        return "\n".join([self.render_block(block) for block in blocks])

    def html_to_blocks(self, html: str) -> List[Dict[str, Any]]:
        """
        将 HTML 转换为块数据（简化版本）
        
        注意：完整的 HTML 解析需要使用专门的解析器
        
        Args:
            html: HTML string
            
        Returns:
            List of block data
        """
        # Use BeautifulSoup for HTML parsing in production
        # Example implementation:
        # from bs4 import BeautifulSoup
        # soup = BeautifulSoup(html, 'html.parser')
        # blocks = []
        # for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'img', 'ul', 'ol']):
        #     block = self._convert_tag_to_block(tag)
        #     if block:
        #         blocks.append(block)
        # return blocks
        
        # For now, return empty list
        return []


# 全局实例
block_editor_service = BlockEditorService()
