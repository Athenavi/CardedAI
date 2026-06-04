"""
自定义块模式 API 端点
"""

from fastapi import APIRouter, Depends, Query, Body

from shared.services.content_management.custom_block_pattern import custom_block_pattern_service
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required

router = APIRouter(tags=["custom-patterns"])


@router.post("")
async def create_custom_pattern(
    title: str = Body(..., description="模式标题"),
    description: str = Body(..., description="描述"),
    blocks: list = Body(..., description="区块数据"),
    category: str = Body("custom", description="分类"),
    tags: list = Body(None, description="标签"),
    current_user=Depends(jwt_required)
):
    """创建自定义块模式"""
    try:
        # 从 JWT token 获取 user_id
        user_id = current_user.id if hasattr(current_user, 'id') else None

        if not user_id:
            return ApiResponse(success=False, error="未授权，请先登录")

        result = await custom_block_pattern_service.save_pattern(
            user_id=user_id,
            title=title,
            description=description,
            blocks=blocks,
            category=category,
            tags=tags
        )

        if result["success"]:
            return ApiResponse(
                success=True,
                message=result["message"],
                data={"pattern": result["pattern"]}
            )
        else:
            return ApiResponse(
                success=False,
                error=result["error"]
            )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=str(e))


@router.get("")
async def list_user_patterns(
    category: str = Query(None, description="分类过滤"),
    current_user=Depends(jwt_required)
):
    """获取用户的自定义块模式列表"""
    try:
        user_id = getattr(current_user, 'id', 1)

        patterns = await custom_block_pattern_service.get_user_patterns(user_id, category)

        return ApiResponse(
            success=True,
            data={
                "patterns": patterns,
                "total": len(patterns),
                "categories": await custom_block_pattern_service.get_categories(user_id)
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/{pattern_id}")
async def get_pattern_detail(
    pattern_id: int,
    current_user=Depends(jwt_required)
):
    """获取块模式详情"""
    try:
        user_id = getattr(current_user, 'id', 1)

        pattern = await custom_block_pattern_service.get_pattern_by_id(user_id, pattern_id)

        if not pattern:
            return ApiResponse(
                success=False,
                error="块模式不存在"
            )

        return ApiResponse(
            success=True,
            data={"pattern": pattern}
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.put("/{pattern_id}")
async def update_pattern(
    pattern_id: int,
    title: str = Body(None, description="模式标题"),
    description: str = Body(None, description="描述"),
    blocks: list = Body(None, description="区块数据"),
    category: str = Body(None, description="分类"),
    tags: list = Body(None, description="标签"),
    current_user=Depends(jwt_required)
):
    """更新块模式"""
    try:
        user_id = getattr(current_user, 'id', 1)

        result = await custom_block_pattern_service.update_pattern(
            user_id=user_id,
            pattern_id=pattern_id,
            title=title,
            description=description,
            blocks=blocks,
            category=category,
            tags=tags
        )

        if result["success"]:
            return ApiResponse(
                success=True,
                message=result["message"],
                data={"pattern": result["pattern"]}
            )
        else:
            return ApiResponse(
                success=False,
                error=result["error"]
            )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.delete("/{pattern_id}")
async def delete_pattern(
    pattern_id: int,
    current_user=Depends(jwt_required)
):
    """删除块模式"""
    try:
        user_id = getattr(current_user, 'id', 1)

        result = await custom_block_pattern_service.delete_pattern(user_id, pattern_id)

        if result["success"]:
            return ApiResponse(
                success=True,
                message=result["message"]
            )
        else:
            return ApiResponse(
                success=False,
                error=result["error"]
            )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))
