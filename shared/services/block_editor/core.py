"""
Block Editor 核心架构

提供类似 WordPress Gutenberg 的块编辑器系统

功能:
1. Block 数据结构 (JSON Schema)
2. Block 注册机制
3. Block 渲染引擎
4. Block 验证和转换
5. Portable Text 格式支持
6. 版本控制集成
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Callable


class BlockType(Enum):
    """Block 类型枚举"""
    TEXT = "text"
    HEADING = "heading"
    IMAGE = "image"
    VIDEO = "video"
    QUOTE = "quote"
    CODE = "code"
    LIST = "list"
    GALLERY = "gallery"
    TABLE = "table"
    EMBED = "embed"
    BUTTON = "button"
    DIVIDER = "divider"
    SPACER = "spacer"
    CUSTOM = "custom"


class BlockCategory(Enum):
    """Block 分类"""
    BASIC = "basic"
    MEDIA = "media"
    DESIGN = "design"
    WIDGETS = "widgets"
    EMBEDS = "embeds"
    CUSTOM = "custom"


class BlockSchema:
    """
    Block 数据模式定义
    
    定义每个 Block 类型的结构和验证规则
    """

    def __init__(
            self,
            block_type: BlockType,
            name: str,
            description: str,
            category: BlockCategory,
            attributes: Dict[str, Any],
            icon: str = "",
    ):
        self.block_type = block_type
        self.name = name
        self.description = description
        self.category = category
        self.attributes = attributes
        self.icon = icon

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.block_type.value,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "attributes": self.attributes,
            "icon": self.icon,
        }

    def validate(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        验证 Block 数据
        
        Returns:
            (是否有效, 错误列表)
        """
        errors = []

        # 检查必需属性
        for attr_name, attr_schema in self.attributes.items():
            if attr_schema.get("required") and attr_name not in data:
                errors.append(f"Missing required attribute: {attr_name}")

            # 类型检查
            if attr_name in data:
                expected_type = attr_schema.get("type")
                if expected_type and not isinstance(data[attr_name], eval(expected_type)):
                    errors.append(f"Invalid type for {attr_name}: expected {expected_type}")

        return len(errors) == 0, errors


class Block:
    """
    Block 实例
    
    表示编辑器中的一个内容块
    """

    def __init__(
            self,
            block_id: str,
            block_type: BlockType,
            attributes: Dict[str, Any],
            parent_id: Optional[str] = None,
            order: int = 0,
    ):
        self.block_id = block_id
        self.block_type = block_type
        self.attributes = attributes
        self.parent_id = parent_id
        self.order = order
        self.children: List['Block'] = []
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "block_id": self.block_id,
            "type": self.block_type.value,
            "attributes": self.attributes,
            "parent_id": self.parent_id,
            "order": self.order,
            "children": [child.to_dict() for child in self.children],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Block':
        block = cls(
            block_id=data["block_id"],
            block_type=BlockType(data["type"]),
            attributes=data.get("attributes", {}),
            parent_id=data.get("parent_id"),
            order=data.get("order", 0),
        )

        # 恢复子块
        for child_data in data.get("children", []):
            child = cls.from_dict(child_data)
            block.children.append(child)

        return block

    def add_child(self, child: 'Block'):
        """添加子块"""
        child.parent_id = self.block_id
        child.order = len(self.children)
        self.children.append(child)

    def remove_child(self, child_id: str) -> bool:
        """移除子块"""
        for i, child in enumerate(self.children):
            if child.block_id == child_id:
                self.children.pop(i)
                # 重新排序
                for j, c in enumerate(self.children):
                    c.order = j
                return True
        return False


class BlockRegistry:
    """
    Block 注册表
    
    管理所有注册的 Block 类型
    """

    def __init__(self):
        self.schemas: Dict[str, BlockSchema] = {}
        self.renderers: Dict[str, Callable] = {}
        self.validators: Dict[str, Callable] = {}

    def register_block_type(
            self,
            schema: BlockSchema,
            renderer: Callable = None,
            validator: Callable = None,
    ):
        """
        注册 Block 类型
        
        Args:
            schema: Block 模式定义
            renderer: 渲染函数
            validator: 验证函数
        """
        block_type = schema.block_type.value

        if block_type in self.schemas:
            raise ValueError(f"Block type already registered: {block_type}")

        self.schemas[block_type] = schema

        if renderer:
            self.renderers[block_type] = renderer

        if validator:
            self.validators[block_type] = validator

    def get_schema(self, block_type: str) -> Optional[BlockSchema]:
        """获取 Block 模式"""
        return self.schemas.get(block_type)

    def get_renderer(self, block_type: str) -> Optional[Callable]:
        """获取渲染器"""
        return self.renderers.get(block_type)

    def list_block_types(self, category: BlockCategory = None) -> List[Dict[str, Any]]:
        """列出 Block 类型"""
        types = []

        for schema in self.schemas.values():
            if category and schema.category != category:
                continue
            types.append(schema.to_dict())

        return types

    def validate_block(self, block: Block) -> tuple[bool, List[str]]:
        """验证 Block 数据"""
        schema = self.get_schema(block.block_type.value)

        if not schema:
            return False, [f"Unknown block type: {block.block_type.value}"]

        # 使用自定义验证器或默认验证
        if block.block_type.value in self.validators:
            return self.validators[block.block_type.value](block)
        else:
            return schema.validate(block.attributes)


class BlockRenderer:
    """
    Block 渲染引擎
    
    将 Block 数据渲染为 HTML 或其他格式
    """

    def __init__(self, registry: BlockRegistry):
        self.registry = registry

    def render_block(self, block: Block) -> str:
        """
        渲染单个 Block
        
        Args:
            block: Block 实例
            
        Returns:
            渲染后的 HTML
        """
        block_type = block.block_type.value

        # 尝试使用自定义渲染器
        renderer = self.registry.get_renderer(block_type)
        if renderer:
            return renderer(block)

        # 使用默认渲染
        return self._default_render(block)

    def render_document(self, blocks: List[Block]) -> str:
        """
        渲染整个文档
        
        Args:
            blocks: Block 列表
            
        Returns:
            完整的 HTML
        """
        html_parts = []

        for block in blocks:
            html_parts.append(self.render_block(block))

        return "\n".join(html_parts)

    def _default_render(self, block: Block) -> str:
        """默认渲染逻辑"""
        block_type = block.block_type.value
        attrs = block.attributes

        if block_type == "heading":
            level = attrs.get("level", 2)
            content = attrs.get("content", "")
            return f"<h{level}>{content}</h{level}>"

        elif block_type == "text":
            content = attrs.get("content", "")
            return f"<p>{content}</p>"

        elif block_type == "image":
            src = attrs.get("src", "")
            alt = attrs.get("alt", "")
            caption = attrs.get("caption", "")
            html = f'<img src="{src}" alt="{alt}" />'
            if caption:
                html += f"<figcaption>{caption}</figcaption>"
            return f"<figure>{html}</figure>"

        elif block_type == "quote":
            content = attrs.get("content", "")
            cite = attrs.get("cite", "")
            html = f"<blockquote>{content}</blockquote>"
            if cite:
                html += f"<cite>{cite}</cite>"
            return html

        elif block_type == "code":
            code = attrs.get("code", "")
            language = attrs.get("language", "")
            return f'<pre><code class="language-{language}">{code}</code></pre>'

        elif block_type == "list":
            items = attrs.get("items", [])
            ordered = attrs.get("ordered", False)
            tag = "ol" if ordered else "ul"
            items_html = "".join(f"<li>{item}</li>" for item in items)
            return f"<{tag}>{items_html}</{tag}>"

        elif block_type == "divider":
            return "<hr />"

        elif block_type == "spacer":
            height = attrs.get("height", 20)
            return f'<div style="height: {height}px;"></div>'

        else:
            # 未知类型，返回空
            return f"<!-- Unknown block type: {block_type} -->"


class PortableTextConverter:
    """
    Portable Text 格式转换器
    
    支持与其他编辑器的格式互操作
    """

    @staticmethod
    def blocks_to_portable_text(blocks: List[Block]) -> Dict[str, Any]:
        """
        将 Blocks 转换为 Portable Text 格式
        
        Args:
            blocks: Block 列表
            
        Returns:
            Portable Text 文档
        """
        return {
            "_type": "document",
            "children": [block.to_dict() for block in blocks],
        }

    @staticmethod
    def portable_text_to_blocks(portable_text: Dict[str, Any]) -> List[Block]:
        """
        将 Portable Text 转换为 Blocks
        
        Args:
            portable_text: Portable Text 文档
            
        Returns:
            Block 列表
        """
        blocks = []

        for child in portable_text.get("children", []):
            block = Block.from_dict(child)
            blocks.append(block)

        return blocks


class BlockHistory:
    """
    Block 历史记录
    
    支持撤销/重做功能
    """

    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.undo_stack: List[List[Dict[str, Any]]] = []
        self.redo_stack: List[List[Dict[str, Any]]] = []

    def save_state(self, blocks: List[Block]):
        """保存当前状态"""
        state = [block.to_dict() for block in blocks]
        self.undo_stack.append(state)

        # 限制历史记录大小
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)

        # 清空重做栈
        self.redo_stack.clear()

    def undo(self) -> Optional[List[Block]]:
        """撤销操作"""
        if not self.undo_stack:
            return None

        # 保存当前状态到重做栈
        current_state = self.undo_stack[-1]
        self.redo_stack.append(current_state)

        # 弹出上一个状态
        self.undo_stack.pop()

        if not self.undo_stack:
            return None

        prev_state = self.undo_stack[-1]
        return [Block.from_dict(data) for data in prev_state]

    def redo(self) -> Optional[List[Block]]:
        """重做操作"""
        if not self.redo_stack:
            return None

        # 弹出重做状态
        next_state = self.redo_stack.pop()
        self.undo_stack.append(next_state)

        return [Block.from_dict(data) for data in next_state]

    def can_undo(self) -> bool:
        """是否可以撤销"""
        return len(self.undo_stack) > 1

    def can_redo(self) -> bool:
        """是否可以重做"""
        return len(self.redo_stack) > 0


# 全局实例
block_registry = BlockRegistry()
block_renderer = BlockRenderer(block_registry)
portable_text_converter = PortableTextConverter()
block_history = BlockHistory()


def register_builtin_blocks():
    """注册内置 Block 类型"""

    # 标题
    heading_schema = BlockSchema(
        block_type=BlockType.HEADING,
        name="Heading",
        description="标题块",
        category=BlockCategory.BASIC,
        attributes={
            "content": {"type": "str", "required": True},
            "level": {"type": "int", "required": False, "default": 2},
        },
        icon="heading",
    )
    block_registry.register_block_type(heading_schema)

    # 段落
    text_schema = BlockSchema(
        block_type=BlockType.TEXT,
        name="Paragraph",
        description="文本段落",
        category=BlockCategory.BASIC,
        attributes={
            "content": {"type": "str", "required": True},
        },
        icon="paragraph",
    )
    block_registry.register_block_type(text_schema)

    # 图片
    image_schema = BlockSchema(
        block_type=BlockType.IMAGE,
        name="Image",
        description="图片块",
        category=BlockCategory.MEDIA,
        attributes={
            "src": {"type": "str", "required": True},
            "alt": {"type": "str", "required": False},
            "caption": {"type": "str", "required": False},
        },
        icon="image",
    )
    block_registry.register_block_type(image_schema)

    # 引用
    quote_schema = BlockSchema(
        block_type=BlockType.QUOTE,
        name="Quote",
        description="引用块",
        category=BlockCategory.BASIC,
        attributes={
            "content": {"type": "str", "required": True},
            "cite": {"type": "str", "required": False},
        },
        icon="quote",
    )
    block_registry.register_block_type(quote_schema)

    # 代码
    code_schema = BlockSchema(
        block_type=BlockType.CODE,
        name="Code",
        description="代码块",
        category=BlockCategory.BASIC,
        attributes={
            "code": {"type": "str", "required": True},
            "language": {"type": "str", "required": False},
        },
        icon="code",
    )
    block_registry.register_block_type(code_schema)

    # 列表
    list_schema = BlockSchema(
        block_type=BlockType.LIST,
        name="List",
        description="列表块",
        category=BlockCategory.BASIC,
        attributes={
            "items": {"type": "list", "required": True},
            "ordered": {"type": "bool", "required": False, "default": False},
        },
        icon="list",
    )
    block_registry.register_block_type(list_schema)

    # 分隔线
    divider_schema = BlockSchema(
        block_type=BlockType.DIVIDER,
        name="Divider",
        description="分隔线",
        category=BlockCategory.DESIGN,
        attributes={},
        icon="divider",
    )
    block_registry.register_block_type(divider_schema)

    # 间距
    spacer_schema = BlockSchema(
        block_type=BlockType.SPACER,
        name="Spacer",
        description="间距块",
        category=BlockCategory.DESIGN,
        attributes={
            "height": {"type": "int", "required": False, "default": 20},
        },
        icon="spacer",
    )
    block_registry.register_block_type(spacer_schema)


# 自动注册内置 Blocks
register_builtin_blocks()
