"""
块编辑器扩展服务
提供高级块类型和块操作功能
"""

from typing import Dict, Any, List, Optional

from .block_editor_service import BlockType, BlockEditorService


class BlockEditorExtensions:
    """
    块编辑器扩展服务
    
    功能：
    1. 高级块类型注册（Embed、Interactive等）
    2. 块转换工具
    3. 块验证增强
    4. 块导入/导出
    """

    def __init__(self, base_service: BlockEditorService):
        self.base_service = base_service
        self._register_extended_blocks()

    def _register_extended_blocks(self):
        """注册扩展块类型"""

        # Embed 块 - YouTube
        self.base_service.register_block(BlockType(
            name="youtube",
            display_name="YouTube 视频",
            category="embed",
            icon="▶️",
            description="嵌入 YouTube 视频",
            attributes={
                "videoId": {"type": "string", "required": True},
                "startAt": {"type": "integer", "default": 0},
                "autoplay": {"type": "boolean", "default": False},
                "width": {"type": "string", "default": "100%"},
                "height": {"type": "string", "default": "400px"}
            }
        ))

        # Embed 块 - Bilibili
        self.base_service.register_block(BlockType(
            name="bilibili",
            display_name="Bilibili 视频",
            category="embed",
            icon="📺",
            description="嵌入 Bilibili 视频",
            attributes={
                "bvid": {"type": "string", "required": True},
                "page": {"type": "integer", "default": 1},
                "autoplay": {"type": "boolean", "default": False}
            }
        ))

        # Embed 块 - Twitter/X
        self.base_service.register_block(BlockType(
            name="twitter",
            display_name="Twitter 推文",
            category="embed",
            icon="🐦",
            description="嵌入 Twitter 推文",
            attributes={
                "tweetUrl": {"type": "string", "required": True},
                "theme": {"type": "string", "enum": ["light", "dark"], "default": "light"}
            }
        ))

        # Interactive 块 - Button
        self.base_service.register_block(BlockType(
            name="button",
            display_name="按钮",
            category="widget",
            icon="🔘",
            description="可点击的按钮",
            attributes={
                "text": {"type": "string", "required": True},
                "url": {"type": "string", "required": True},
                "style": {"type": "string", "enum": ["primary", "secondary", "outline"], "default": "primary"},
                "size": {"type": "string", "enum": ["small", "medium", "large"], "default": "medium"},
                "openInNewTab": {"type": "boolean", "default": False}
            }
        ))

        # Interactive 块 - Callout
        self.base_service.register_block(BlockType(
            name="callout",
            display_name="提示框",
            category="widget",
            icon="💡",
            description="重要信息提示",
            attributes={
                "type": {"type": "string", "enum": ["info", "warning", "error", "success"], "default": "info"},
                "title": {"type": "string", "default": ""},
                "content": {"type": "string", "required": True},
                "icon": {"type": "string", "default": ""}
            }
        ))

        # Layout 块 - Accordion
        self.base_service.register_block(BlockType(
            name="accordion",
            display_name="折叠面板",
            category="layout",
            icon="📂",
            description="可折叠的内容区域",
            attributes={
                "items": {"type": "array", "required": True},
                "allowMultiple": {"type": "boolean", "default": False}
            },
            allowed_children=["accordion-item"]
        ))

        self.base_service.register_block(BlockType(
            name="accordion-item",
            display_name="折叠项",
            category="layout",
            icon="📄",
            description="折叠面板中的单项",
            attributes={
                "title": {"type": "string", "required": True},
                "defaultOpen": {"type": "boolean", "default": False}
            },
            is_inline=True
        ))

        # Media 块 - Audio
        self.base_service.register_block(BlockType(
            name="audio",
            display_name="音频",
            category="media",
            icon="🎵",
            description="嵌入音频播放器",
            attributes={
                "url": {"type": "string", "required": True},
                "title": {"type": "string", "default": ""},
                "artist": {"type": "string", "default": ""},
                "autoplay": {"type": "boolean", "default": False},
                "loop": {"type": "boolean", "default": False}
            }
        ))

        # Widget 块 - Divider with Text
        self.base_service.register_block(BlockType(
            name="divider-text",
            display_name="带文字分隔线",
            category="layout",
            icon="—",
            description="中间带文字的分隔线",
            attributes={
                "text": {"type": "string", "default": ""},
                "alignment": {"type": "string", "enum": ["left", "center", "right"], "default": "center"},
                "lineStyle": {"type": "string", "enum": ["solid", "dashed", "dotted"], "default": "solid"}
            }
        ))

        # Advanced 块 - Tabs
        self.base_service.register_block(BlockType(
            name="tabs",
            display_name="标签页",
            category="layout",
            icon="📑",
            description="多标签内容切换",
            attributes={
                "tabs": {"type": "array", "required": True},
                "defaultTab": {"type": "integer", "default": 0},
                "style": {"type": "string", "enum": ["default", "pills", "underline"], "default": "default"}
            },
            allowed_children=["tab-pane"]
        ))

        self.base_service.register_block(BlockType(
            name="tab-pane",
            display_name="标签面板",
            category="layout",
            icon="📃",
            description="标签页中的内容面板",
            attributes={
                "label": {"type": "string", "required": True},
                "icon": {"type": "string", "default": ""}
            },
            is_inline=True
        ))

    def convert_block_type(self, block_data: Dict[str, Any], new_type: str) -> Optional[Dict[str, Any]]:
        """
        转换块类型
        
        Args:
            block_data: 原始块数据
            new_type: 目标块类型
            
        Returns:
            转换后的块数据，失败返回 None
        """
        old_type = block_data.get("type")
        if not old_type or not new_type:
            return None

        # 检查目标类型是否存在
        target_block_type = self.base_service.get_block_type(new_type)
        if not target_block_type:
            return None

        # 创建新块数据
        new_block = {
            "type": new_type,
            "attributes": {},
            "children": block_data.get("children", [])
        }

        # 尝试映射常见属性
        old_attrs = block_data.get("attributes", {})

        # content 属性通用映射
        if "content" in old_attrs and "content" in target_block_type.attributes:
            new_block["attributes"]["content"] = old_attrs["content"]

        # alignment 属性通用映射
        if "alignment" in old_attrs and "alignment" in target_block_type.attributes:
            new_block["attributes"]["alignment"] = old_attrs["alignment"]

        # url 属性通用映射
        if "url" in old_attrs and "url" in target_block_type.attributes:
            new_block["attributes"]["url"] = old_attrs["url"]

        # 标题级别映射 (heading -> paragraph)
        if old_type == "heading" and new_type == "paragraph":
            if "content" in old_attrs:
                new_block["attributes"]["content"] = old_attrs["content"]

        # 段落转标题 (paragraph -> heading)
        if old_type == "paragraph" and new_type == "heading":
            if "content" in old_attrs:
                new_block["attributes"]["content"] = old_attrs["content"]
                new_block["attributes"]["level"] = 2  # 默认 H2

        return new_block

    def duplicate_block(self, block_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        复制块
        
        Args:
            block_data: 原始块数据
            
        Returns:
            复制的块数据（深拷贝）
        """
        import copy
        return copy.deepcopy(block_data)

    def merge_blocks(self, block1: Dict[str, Any], block2: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        合并两个相邻的文本块
        
        Args:
            block1: 第一个块
            block2: 第二个块
            
        Returns:
            合并后的块，如果无法合并返回 None
        """
        # 只能合并相同类型的文本块
        if block1.get("type") != block2.get("type"):
            return None

        block_type = block1["type"]

        # 只支持段落和标题的合并
        if block_type not in ["paragraph", "heading"]:
            return None

        attrs1 = block1.get("attributes", {})
        attrs2 = block2.get("attributes", {})

        # 合并 content
        content1 = attrs1.get("content", "")
        content2 = attrs2.get("content", "")

        merged_block = {
            "type": block_type,
            "attributes": {
                **attrs1,
                "content": f"{content1} {content2}"
            }
        }

        return merged_block

    def split_block(self, block_data: Dict[str, Any], position: int) -> List[Dict[str, Any]]:
        """
        在指定位置分割块
        
        Args:
            block_data: 要分割的块
            position: 分割位置（字符索引）
            
        Returns:
            分割后的块列表
        """
        block_type = block_data.get("type")
        attrs = block_data.get("attributes", {})
        content = attrs.get("content", "")

        # 只支持文本块的分割
        if block_type not in ["paragraph", "heading"]:
            return [block_data]

        # 确保分割位置有效
        if position < 0 or position > len(content):
            return [block_data]

        # 分割内容
        content1 = content[:position]
        content2 = content[position:]

        # 创建两个新块
        block1 = {
            "type": block_type,
            "attributes": {**attrs, "content": content1}
        }

        block2 = {
            "type": block_type,
            "attributes": {**attrs, "content": content2}
        }

        return [block1, block2]

    def export_blocks_json(self, blocks: List[Dict[str, Any]]) -> str:
        """
        导出块数据为 JSON 字符串
        
        Args:
            blocks: 块数据列表
            
        Returns:
            JSON 字符串
        """
        import json
        return json.dumps(blocks, ensure_ascii=False, indent=2)

    def import_blocks_json(self, json_str: str) -> List[Dict[str, Any]]:
        """
        从 JSON 字符串导入块数据
        
        Args:
            json_str: JSON 字符串
            
        Returns:
            块数据列表
        """
        import json
        try:
            blocks = json.loads(json_str)
            if isinstance(blocks, list):
                return blocks
            return []
        except json.JSONDecodeError:
            return []

    def get_block_statistics(self, blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取块统计信息
        
        Args:
            blocks: 块数据列表
            
        Returns:
            统计信息
        """
        stats = {
            "total_blocks": len(blocks),
            "by_type": {},
            "by_category": {},
            "has_media": False,
            "has_embeds": False
        }

        for block in blocks:
            block_type = block.get("type", "unknown")
            block_info = self.base_service.get_block_type(block_type)

            # 按类型统计
            stats["by_type"][block_type] = stats["by_type"].get(block_type, 0) + 1

            # 按分类统计
            if block_info:
                category = block_info.category
                stats["by_category"][category] = stats["by_category"].get(category, 0) + 1

                # 检查是否有媒体或嵌入内容
                if category == "media":
                    stats["has_media"] = True
                elif category == "embed":
                    stats["has_embeds"] = True

        return stats


# 全局扩展实例（需要先初始化基础服务）
def create_extensions(base_service: BlockEditorService) -> BlockEditorExtensions:
    """创建扩展服务实例"""
    return BlockEditorExtensions(base_service)
