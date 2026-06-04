"""
Block 编辑器系统 - 数据结构定义
类似 WordPress Gutenberg 的块系统
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional


class BlockType(str, Enum):
    """块类型枚举"""
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    IMAGE = "image"
    QUOTE = "quote"
    BUTTON = "button"
    LIST = "list"
    CODE = "code"
    SEPARATOR = "separator"
    SPACER = "spacer"
    COLUMNS = "columns"
    COLUMN = "column"
    GROUP = "group"


class Block:
    """
    Block 数据模型
    
    属性:
        block_type: 块类型
        attributes: 块的属性配置
        inner_blocks: 嵌套的子块
        inner_html: 块的 HTML 内容
    """
    
    def __init__(
        self,
        block_type: str,
        attributes: Optional[Dict[str, Any]] = None,
        inner_blocks: Optional[List['Block']] = None,
        inner_html: str = ""
    ):
        self.block_type = block_type
        self.attributes = attributes or {}
        self.inner_blocks = inner_blocks or []
        self.inner_html = inner_html
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'block_type': self.block_type,
            'attributes': self.attributes,
            'inner_blocks': [block.to_dict() for block in self.inner_blocks],
            'inner_html': self.inner_html,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Block':
        """从字典创建 Block"""
        inner_blocks = [
            cls.from_dict(block_data) 
            for block_data in data.get('inner_blocks', [])
        ]
        
        return cls(
            block_type=data['block_type'],
            attributes=data.get('attributes', {}),
            inner_blocks=inner_blocks,
            inner_html=data.get('inner_html', '')
        )


class BlockRegistry:
    """
    Block 注册表
    
    管理所有注册的块类型及其配置
    """
    
    def __init__(self):
        # 注册的块类型 {block_type: config}
        self.registered_blocks: Dict[str, Dict[str, Any]] = {}
    
    def register_block(
        self,
        block_type: str,
        name: str,
        description: str,
        icon: str = "",
        category: str = "common",
        attributes_schema: Optional[Dict[str, Any]] = None,
        render_callback: Optional[Any] = None
    ):
        """
        注册一个块类型
        
        Args:
            block_type: 块类型标识
            name: 块名称
            description: 块描述
            icon: 图标
            category: 分类 (common, formatting, layout, widgets)
            attributes_schema: 属性 schema
            render_callback: 渲染回调函数
        """
        self.registered_blocks[block_type] = {
            'name': name,
            'description': description,
            'icon': icon,
            'category': category,
            'attributes_schema': attributes_schema or {},
            'render_callback': render_callback,
        }
    
    def get_block_config(self, block_type: str) -> Optional[Dict[str, Any]]:
        """获取块配置"""
        return self.registered_blocks.get(block_type)
    
    def get_all_blocks(self) -> Dict[str, Dict[str, Any]]:
        """获取所有注册的块"""
        return self.registered_blocks.copy()
    
    def unregister_block(self, block_type: str):
        """注销块类型"""
        if block_type in self.registered_blocks:
            del self.registered_blocks[block_type]


# 全局实例
block_registry = BlockRegistry()


def register_default_blocks():
    """注册默认的块类型"""
    
    # 段落块
    block_registry.register_block(
        block_type="paragraph",
        name="段落",
        description="普通文本段落",
        icon="📝",
        category="common",
        attributes_schema={
            'content': {'type': 'string', 'default': ''},
            'align': {'type': 'string', 'enum': ['left', 'center', 'right']},
        }
    )
    
    # 标题块
    block_registry.register_block(
        block_type="heading",
        name="标题",
        description="标题文本",
        icon="📌",
        category="common",
        attributes_schema={
            'level': {'type': 'integer', 'default': 2, 'min': 1, 'max': 6},
            'content': {'type': 'string', 'default': ''},
            'align': {'type': 'string', 'enum': ['left', 'center', 'right']},
        }
    )
    
    # 图片块
    block_registry.register_block(
        block_type="image",
        name="图片",
        description="插入图片",
        icon="🖼️",
        category="common",
        attributes_schema={
            'url': {'type': 'string', 'default': ''},
            'alt': {'type': 'string', 'default': ''},
            'caption': {'type': 'string', 'default': ''},
            'width': {'type': 'integer'},
            'height': {'type': 'integer'},
            'align': {'type': 'string', 'enum': ['left', 'center', 'right', 'full']},
        }
    )
    
    # 引用块
    block_registry.register_block(
        block_type="quote",
        name="引用",
        description="引用文本",
        icon="💬",
        category="formatting",
        attributes_schema={
            'content': {'type': 'string', 'default': ''},
            'citation': {'type': 'string', 'default': ''},
            'style': {'type': 'string', 'enum': ['default', 'large']},
        }
    )
    
    # 按钮块
    block_registry.register_block(
        block_type="button",
        name="按钮",
        description="可点击的按钮",
        icon="🔘",
        category="widgets",
        attributes_schema={
            'text': {'type': 'string', 'default': '点击我'},
            'url': {'type': 'string', 'default': ''},
            'style': {'type': 'string', 'enum': ['primary', 'secondary', 'outline']},
            'size': {'type': 'string', 'enum': ['small', 'medium', 'large']},
            'open_in_new_tab': {'type': 'boolean', 'default': False},
        }
    )
    
    # 列表块
    block_registry.register_block(
        block_type="list",
        name="列表",
        description="有序或无序列表",
        icon="📋",
        category="formatting",
        attributes_schema={
            'items': {'type': 'array', 'default': []},
            'ordered': {'type': 'boolean', 'default': False},
        }
    )
    
    # 代码块
    block_registry.register_block(
        block_type="code",
        name="代码",
        description="代码片段",
        icon="💻",
        category="formatting",
        attributes_schema={
            'language': {'type': 'string', 'default': 'javascript'},
            'content': {'type': 'string', 'default': ''},
            'show_line_numbers': {'type': 'boolean', 'default': True},
        }
    )
    
    # 分隔线块
    block_registry.register_block(
        block_type="separator",
        name="分隔线",
        description="水平分隔线",
        icon="➖",
        category="layout",
        attributes_schema={
            'style': {'type': 'string', 'enum': ['solid', 'dashed', 'dotted']},
        }
    )
    
    # 间距块
    block_registry.register_block(
        block_type="spacer",
        name="间距",
        description="自定义间距",
        icon="↕️",
        category="layout",
        attributes_schema={
            'height': {'type': 'integer', 'default': 50, 'min': 10, 'max': 500},
        }
    )
    
    # 列布局块
    block_registry.register_block(
        block_type="columns",
        name="列布局",
        description="多列布局容器",
        icon="📊",
        category="layout",
        attributes_schema={
            'column_count': {'type': 'integer', 'default': 2, 'min': 1, 'max': 6},
            'gap': {'type': 'string', 'default': 'medium'},
        }
    )


# 初始化默认块
register_default_blocks()
