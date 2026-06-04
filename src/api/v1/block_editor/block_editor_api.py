"""
Block Editor API

提供块编辑器的后端接口
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Body

from shared.services.block_editor.core import (
    block_registry,
    block_renderer,
    portable_text_converter,
    block_history,
    Block,
    BlockType,
    BlockCategory,
)
from src.api.v1.core.responses import ApiResponse
from src.api.v1.users.user_management import jwt_required

router = APIRouter(prefix="/block-editor", tags=["Block Editor"])


@router.get("/block-types")
async def list_block_types(
        category: Optional[str] = None,
        current_user=Depends(jwt_required)
):
    """
    列出所有可用的 Block 类型
    
    可按分类过滤
    """
    cat_enum = BlockCategory(category) if category else None
    types = block_registry.list_block_types(category=cat_enum)

    return ApiResponse(
        success=True,
        data={
            "block_types": types,
            "total": len(types),
        }
    )


@router.post("/validate-block")
async def validate_block(
        block_data: dict = Body(..., description="Block 数据"),
        current_user=Depends(jwt_required)
):
    """
    验证 Block 数据
    
    检查 Block 是否符合模式定义
    """
    try:
        block = Block.from_dict(block_data)
        is_valid, errors = block_registry.validate_block(block)

        return ApiResponse(
            success=is_valid,
            data={
                "is_valid": is_valid,
                "errors": errors,
            }
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e)
        )


@router.post("/render-block")
async def render_single_block(
        block_data: dict = Body(..., description="Block 数据"),
        current_user=Depends(jwt_required)
):
    """
    渲染单个 Block
    
    将 Block 数据转换为 HTML
    """
    try:
        block = Block.from_dict(block_data)
        html = block_renderer.render_block(block)

        return ApiResponse(
            success=True,
            data={
                "html": html,
            }
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e)
        )


@router.post("/render-document")
async def render_document(
        blocks_data: List[dict] = Body(..., description="Blocks 数据列表"),
        current_user=Depends(jwt_required)
):
    """
    渲染整个文档
    
    将所有 Blocks 转换为完整的 HTML
    """
    try:
        blocks = [Block.from_dict(data) for data in blocks_data]
        html = block_renderer.render_document(blocks)

        return ApiResponse(
            success=True,
            data={
                "html": html,
                "block_count": len(blocks),
            }
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e)
        )


@router.post("/convert/to-portable-text")
async def convert_to_portable_text(
        blocks_data: List[dict] = Body(..., description="Blocks 数据"),
        current_user=Depends(jwt_required)
):
    """
    转换为 Portable Text 格式
    
    用于与其他编辑器互操作
    """
    try:
        blocks = [Block.from_dict(data) for data in blocks_data]
        portable_text = portable_text_converter.blocks_to_portable_text(blocks)

        return ApiResponse(
            success=True,
            data=portable_text
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e)
        )


@router.post("/convert/from-portable-text")
async def convert_from_portable_text(
        portable_text: dict = Body(..., description="Portable Text 文档"),
        current_user=Depends(jwt_required)
):
    """
    从 Portable Text 转换
    
    将 Portable Text 格式转换为 Blocks
    """
    try:
        blocks = portable_text_converter.portable_text_to_blocks(portable_text)

        return ApiResponse(
            success=True,
            data={
                "blocks": [block.to_dict() for block in blocks],
                "count": len(blocks),
            }
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e)
        )


@router.post("/history/save")
async def save_history_state(
        blocks_data: List[dict] = Body(..., description="Blocks 数据"),
        current_user=Depends(jwt_required)
):
    """
    保存历史记录状态
    
    用于撤销/重做功能
    """
    try:
        blocks = [Block.from_dict(data) for data in blocks_data]
        block_history.save_state(blocks)

        return ApiResponse(
            success=True,
            message="State saved"
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e)
        )


@router.post("/history/undo")
async def undo(current_user=Depends(jwt_required)):
    """
    撤销操作
    
    恢复到上一个状态
    """
    blocks = block_history.undo()

    if blocks is None:
        return ApiResponse(
            success=False,
            error="Nothing to undo"
        )

    return ApiResponse(
        success=True,
        data={
            "blocks": [block.to_dict() for block in blocks],
            "can_undo": block_history.can_undo(),
            "can_redo": block_history.can_redo(),
        }
    )


@router.post("/history/redo")
async def redo(current_user=Depends(jwt_required)):
    """
    重做操作
    
    恢复到下一个状态
    """
    blocks = block_history.redo()

    if blocks is None:
        return ApiResponse(
            success=False,
            error="Nothing to redo"
        )

    return ApiResponse(
        success=True,
        data={
            "blocks": [block.to_dict() for block in blocks],
            "can_undo": block_history.can_undo(),
            "can_redo": block_history.can_redo(),
        }
    )


@router.get("/history/status")
async def get_history_status(current_user=Depends(jwt_required)):
    """
    获取历史记录状态
    
    查看是否可以撤销/重做
    """
    return ApiResponse(
        success=True,
        data={
            "can_undo": block_history.can_undo(),
            "can_redo": block_history.can_redo(),
        }
    )


@router.post("/create-block")
async def create_block(
        block_type: str = Body(..., description="Block 类型"),
        attributes: dict = Body({}, description="Block 属性"),
        current_user=Depends(jwt_required)
):
    """
    创建新的 Block
    
    生成一个新的 Block 实例
    """
    try:
        # 验证 Block 类型
        schema = block_registry.get_schema(block_type)
        if not schema:
            return ApiResponse(
                success=False,
                error=f"Unknown block type: {block_type}"
            )

        # 创建 Block
        block = Block(
            block_id=str(uuid.uuid4()),
            block_type=BlockType(block_type),
            attributes=attributes,
        )

        # 验证
        is_valid, errors = block_registry.validate_block(block)

        if not is_valid:
            return ApiResponse(
                success=False,
                error="Validation failed",
                data={"errors": errors}
            )

        return ApiResponse(
            success=True,
            data=block.to_dict()
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e)
        )


@router.get("/guide")
async def get_block_editor_guide(current_user=Depends(jwt_required)):
    """
    获取 Block Editor 使用指南
    """
    guide = {
        "overview": {
            "title": "Block Editor 块编辑器",
            "description": "现代化的内容编辑器，支持模块化内容创作。",
            "version": "1.0.0"
        },
        "features": [
            "模块化设计 - 每个内容块独立管理",
            "拖拽排序 - 轻松调整内容顺序",
            "实时预览 - 即时看到编辑效果",
            "撤销/重做 - 完整的操作历史",
            "格式转换 - 支持 Portable Text 格式",
            "可扩展 - 轻松添加自定义 Block 类型"
        ],
        "available_blocks": [
            {
                "type": "heading",
                "name": "标题",
                "description": "不同级别的标题",
                "category": "basic"
            },
            {
                "type": "text",
                "name": "段落",
                "description": "文本段落",
                "category": "basic"
            },
            {
                "type": "image",
                "name": "图片",
                "description": "图片块，支持标题",
                "category": "media"
            },
            {
                "type": "quote",
                "name": "引用",
                "description": "引用块",
                "category": "basic"
            },
            {
                "type": "code",
                "name": "代码",
                "description": "代码块，支持语法高亮",
                "category": "basic"
            },
            {
                "type": "list",
                "name": "列表",
                "description": "有序或无序列表",
                "category": "basic"
            },
            {
                "type": "divider",
                "name": "分隔线",
                "description": "水平分隔线",
                "category": "design"
            },
            {
                "type": "spacer",
                "name": "间距",
                "description": "空白间距",
                "category": "design"
            }
        ],
        "api_usage": {
            "create_block": "POST /block-editor/create-block - 创建新块",
            "validate_block": "POST /block-editor/validate-block - 验证块数据",
            "render_block": "POST /block-editor/render-block - 渲染单个块",
            "render_document": "POST /block-editor/render-document - 渲染整个文档",
            "undo": "POST /block-editor/history/undo - 撤销",
            "redo": "POST /block-editor/history/redo - 重做"
        },
        "best_practices": [
            "使用语义化的 Block 类型",
            "保持 Block 属性简洁",
            "定期保存历史记录",
            "验证用户输入",
            "提供清晰的错误提示"
        ]
    }

    return ApiResponse(
        success=True,
        data=guide
    )
