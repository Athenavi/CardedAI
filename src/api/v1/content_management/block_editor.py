"""
块编辑器 API 路由
提供块类型查询、验证和渲染的 REST API
"""

from typing import Dict, Any, List, Optional
import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from shared.services.content_management.block_editor_extensions import create_extensions
from shared.services.content_management.block_editor_service import block_editor_service

# 创建扩展服务实例
block_extensions = create_extensions(block_editor_service)

router = APIRouter(tags=["Block Editor"])


class BlockData(BaseModel):
    """块数据模型"""
    type: str
    attributes: Dict[str, Any] = {}
    children: List[Dict[str, Any]] = []


class BlockValidationRequest(BaseModel):
    """块验证请求"""
    block: BlockData


class BlockValidationResponse(BaseModel):
    """块验证响应"""
    is_valid: bool
    error_message: str = ""


class BlockRenderRequest(BaseModel):
    """块渲染请求"""
    blocks: List[BlockData]


class BlockRenderResponse(BaseModel):
    """块渲染响应"""
    html: str


class BlockTypeInfo(BaseModel):
    """块类型信息"""
    name: str
    display_name: str
    category: str
    icon: str
    description: str
    attributes: Dict[str, Any]
    is_inline: bool


@router.get("/block-types", response_model=List[BlockTypeInfo])
async def get_block_types(category: Optional[str] = None):
    """
    获取所有块类型
    
    Args:
        category: 可选，按分类过滤
        
    Returns:
        块类型列表
    """
    if category:
        block_types = block_editor_service.get_block_types_by_category(category)
    else:
        block_types = block_editor_service.get_all_block_types()

    return [
        BlockTypeInfo(
            name=bt.name,
            display_name=bt.display_name,
            category=bt.category,
            icon=bt.icon,
            description=bt.description,
            attributes=bt.attributes,
            is_inline=bt.is_inline
        )
        for bt in block_types
    ]


@router.get("/block-categories", response_model=List[str])
async def get_block_categories():
    """
    获取所有块分类
    
    Returns:
        分类名称列表
    """
    categories = set(bt.category for bt in block_editor_service.get_all_block_types())
    return list(categories)


@router.post("/validate", response_model=BlockValidationResponse)
async def validate_block(request: BlockValidationRequest):
    """
    验证块数据
    
    Args:
        request: 块验证请求
        
    Returns:
        验证结果
    """
    block_data = request.block.dict()
    is_valid, error_msg = block_editor_service.validate_block(block_data)

    return BlockValidationResponse(
        is_valid=is_valid,
        error_message=error_msg
    )


@router.post("/render", response_model=BlockRenderResponse)
async def render_blocks(request: BlockRenderRequest):
    """
    将块数据渲染为 HTML
    
    Args:
        request: 块渲染请求
        
    Returns:
        HTML 字符串
    """
    blocks_data = [block.dict() for block in request.blocks]
    html = block_editor_service.blocks_to_html(blocks_data)

    return BlockRenderResponse(html=html)


@router.post("/convert/html-to-blocks")
async def convert_html_to_blocks(html: str):
    """
    将 HTML 转换为块数据
    
    Args:
        html: HTML 字符串
        
    Returns:
        块数据列表
    """
    blocks = []

    # 解析 H1-H6 标题
    heading_pattern = r'<h([1-6])([^>]*)>(.*?)</h\1>'
    for match in re.finditer(heading_pattern, html, re.DOTALL):
        level = int(match.group(1))
        content = re.sub(r'<[^>]+>', '', match.group(3)).strip()
        blocks.append({
            'type': 'heading',
            'attributes': {
                'level': level,
                'content': content
            }
        })

    # 解析段落
    p_pattern = r'<p[^>]*>(.*?)</p>'
    for match in re.finditer(p_pattern, html, re.DOTALL):
        content = re.sub(r'<[^>]+>', '', match.group(1)).strip()
        if content:
            blocks.append({
                'type': 'paragraph',
                'attributes': {
                    'content': content
                }
            })

    # 解析图片
    img_pattern = r'<img[^>]*src=["\']([^"\']+)["\'][^>]*(?:alt=["\']([^"\']*)["\'])?[^>]*/?>'
    for match in re.finditer(img_pattern, html):
        url = match.group(1)
        alt = match.group(2) or ''
        blocks.append({
            'type': 'image',
            'attributes': {
                'url': url,
                'alt': alt
            }
        })

    # 解析代码块
    code_pattern = r'<pre[^>]*><code(?: class="language-(\w+)")?>(.*?)</code></pre>'
    for match in re.finditer(code_pattern, html, re.DOTALL):
        language = match.group(1) or 'text'
        content = match.group(2).strip()
        blocks.append({
            'type': 'code',
            'attributes': {
                'language': language,
                'content': content
            }
        })

    # 解析引用
    quote_pattern = r'<blockquote[^>]*>(.*?)</blockquote>'
    for match in re.finditer(quote_pattern, html, re.DOTALL):
        content = re.sub(r'<[^>]+>', '', match.group(1)).strip()
        blocks.append({
            'type': 'quote',
            'attributes': {
                'content': content
            }
        })

    # 解析无序列表
    ul_pattern = r'<ul[^>]*>(.*?)</ul>'
    for match in re.finditer(ul_pattern, html, re.DOTALL):
        items = re.findall(r'<li[^>]*>(.*?)</li>', match.group(1), re.DOTALL)
        item_contents = [re.sub(r'<[^>]+>', '', item).strip() for item in items]
        blocks.append({
            'type': 'list',
            'attributes': {
                'items': [{'content': item} for item in item_contents if item],
                'ordered': False
            }
        })

    # 如果没有解析到任何块，返回原始 HTML 作为段落
    if not blocks and html.strip():
        text_content = re.sub(r'<[^>]+>', '', html).strip()
        if text_content:
            blocks.append({
                'type': 'paragraph',
                'attributes': {
                    'content': text_content
                }
            })
    
    return {
        "blocks": blocks,
        "count": len(blocks)
    }


@router.get("/example")
async def get_example_blocks():
    """
    获取示例块数据
    
    Returns:
        示例块数据列表
    """
    examples = [
        {
            "type": "heading",
            "attributes": {
                "level": 1,
                "content": "欢迎使用块编辑器",
                "alignment": "center"
            }
        },
        {
            "type": "paragraph",
            "attributes": {
                "content": "这是一个段落示例。块编辑器让你可以轻松地创建丰富的内容。",
                "alignment": "left"
            }
        },
        {
            "type": "image",
            "attributes": {
                "url": "https://example.com/image.jpg",
                "alt": "示例图片",
                "caption": "这是一张图片说明",
                "alignment": "center"
            }
        },
        {
            "type": "code",
            "attributes": {
                "language": "python",
                "content": "print('Hello, World!')",
                "showLineNumbers": True
            }
        },
        {
            "type": "quote",
            "attributes": {
                "content": "编程是一种艺术，而块编辑器是你的画布。",
                "citation": "Anonymous",
                "style": "elegant"
            }
        },
        {
            "type": "youtube",
            "attributes": {
                "videoId": "dQw4w9WgXcQ",
                "autoplay": False
            }
        },
        {
            "type": "callout",
            "attributes": {
                "type": "info",
                "title": "提示",
                "content": "这是一个信息提示框",
                "icon": "💡"
            }
        },
        {
            "type": "button",
            "attributes": {
                "text": "点击我",
                "url": "https://example.com",
                "style": "primary",
                "size": "medium"
            }
        }
    ]

    return {"examples": examples}


@router.post("/convert-type")
async def convert_block_type(
        block: BlockData,
        new_type: str
):
    """
    转换块类型
    
    Args:
        block: 原始块数据
        new_type: 目标块类型
        
    Returns:
        转换后的块数据
    """
    block_data = block.dict()
    result = block_extensions.convert_block_type(block_data, new_type)

    if result is None:
        raise HTTPException(status_code=400, detail="无法转换块类型")

    return {"block": result}


@router.post("/duplicate")
async def duplicate_block(block: BlockData):
    """
    复制块
    
    Args:
        block: 要复制的块数据
        
    Returns:
        复制的块数据
    """
    block_data = block.dict()
    duplicated = block_extensions.duplicate_block(block_data)

    return {"block": duplicated}


@router.post("/merge")
async def merge_blocks(
        block1: BlockData,
        block2: BlockData
):
    """
    合并两个相邻的文本块
    
    Args:
        block1: 第一个块
        block2: 第二个块
        
    Returns:
        合并后的块
    """
    result = block_extensions.merge_blocks(block1.dict(), block2.dict())

    if result is None:
        raise HTTPException(status_code=400, detail="无法合并这两个块")

    return {"block": result}


@router.post("/split")
async def split_block(
        block: BlockData,
        position: int
):
    """
    在指定位置分割块
    
    Args:
        block: 要分割的块
        position: 分割位置（字符索引）
        
    Returns:
        分割后的块列表
    """
    blocks = block_extensions.split_block(block.dict(), position)

    return {"blocks": blocks}


@router.post("/export")
async def export_blocks(blocks: List[BlockData]):
    """
    导出块数据为 JSON
    
    Args:
        blocks: 块数据列表
        
    Returns:
        JSON 字符串
    """
    blocks_data = [b.dict() for b in blocks]
    json_str = block_extensions.export_blocks_json(blocks_data)

    return {"json": json_str}


@router.post("/import")
async def import_blocks(json_str: str):
    """
    从 JSON 导入块数据
    
    Args:
        json_str: JSON 字符串
        
    Returns:
        块数据列表
    """
    blocks = block_extensions.import_blocks_json(json_str)

    return {"blocks": blocks}


@router.post("/statistics")
async def get_statistics(blocks: List[BlockData]):
    """
    获取块统计信息
    
    Args:
        blocks: 块数据列表
        
    Returns:
        统计信息
    """
    blocks_data = [b.dict() for b in blocks]
    stats = block_extensions.get_block_statistics(blocks_data)

    return stats
