"""
块模式（Block Patterns）API 端点
"""

from fastapi import APIRouter, Depends, Query

from shared.services.content_management.block_pattern_library import block_pattern_library
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required

router = APIRouter(tags=["block-patterns"])


@router.get("")
@router.get("/list")
async def list_block_patterns(
    category: str = Query(None, description="分类过滤"),
    current_user=Depends(jwt_required)
):
    """
    获取所有块模式列表

    Args:
        category: 可选的分类过滤

    Returns:
        块模式列表
    """
    try:
        patterns = block_pattern_library.get_all_patterns(category=category)

        return ApiResponse(
            success=True,
            data={
                "patterns": patterns,
                "total": len(patterns),
                "categories": block_pattern_library.get_categories()
            }
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=str(e))


@router.get("/categories")
async def get_pattern_categories(
    current_user=Depends(jwt_required)
):
    """
    获取所有块模式分类

    Returns:
        分类列表
    """
    try:
        categories = block_pattern_library.get_categories()

        return ApiResponse(
            success=True,
            data={"categories": categories}
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/search")
async def search_block_patterns(
    q: str = Query(..., description="搜索关键词"),
    current_user=Depends(jwt_required)
):
    """
    搜索块模式

    Args:
        q: 搜索关键词

    Returns:
        匹配的块模式列表
    """
    try:
        if not q or len(q.strip()) == 0:
            return ApiResponse(
                success=False,
                error="请提供搜索关键词"
            )

        patterns = block_pattern_library.search_patterns(q)

        return ApiResponse(
            success=True,
            data={
                "patterns": patterns,
                "total": len(patterns),
                "query": q
            }
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=str(e))


@router.get("/{pattern_slug}")
async def get_block_pattern(
    pattern_slug: str,
    current_user=Depends(jwt_required)
):
    """
    获取单个块模式详情

    Args:
        pattern_slug: 模式标识

    Returns:
        块模式详情
    """
    try:
        pattern = block_pattern_library.get_pattern_by_slug(pattern_slug)

        if not pattern:
            return ApiResponse(
                success=False,
                error=f"块模式不存在: {pattern_slug}"
            )

        return ApiResponse(
            success=True,
            data={"pattern": pattern}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=str(e))
