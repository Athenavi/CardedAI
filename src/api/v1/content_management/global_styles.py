"""
全局样式（Global Styles）API 端点
提供全局样式配置的查询和管理功能
"""
import json
from typing import Optional

from fastapi import APIRouter, Depends, Body
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.global_style import GlobalStyle
from shared.models.global_style_config import GlobalStyleConfig
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required
from src.utils.database.main import get_async_session

router = APIRouter(tags=["global-styles"])


@router.get("")
@router.get("/list")
async def list_global_styles(
    current_user=Depends(jwt_required),
    db: AsyncSession = Depends(get_async_session),
):
    """
    获取全局样式列表

    Returns:
        全局样式配置列表
    """
    try:
        # 查询 GlobalStyleConfig 表
        query = select(GlobalStyleConfig).order_by(desc(GlobalStyleConfig.is_active), GlobalStyleConfig.id)
        result = await db.execute(query)
        configs = result.scalars().all()

        styles = []
        for config in configs:
            style_data = {
                "id": config.id,
                "name": config.name,
                "slug": config.slug,
                "is_active": config.is_active,
                "theme_type": config.theme_type,
                "color_scheme": _safe_json_parse(config.color_scheme, {}),
                "typography": _safe_json_parse(config.typography, {}),
                "spacing": _safe_json_parse(config.spacing, {}),
                "border_radius": _safe_json_parse(config.border_radius, {}),
                "shadows": _safe_json_parse(config.shadows, {}),
                "breakpoints": _safe_json_parse(config.breakpoints, {}),
                "css_variables": _safe_json_parse(config.css_variables, {}),
                "preview_image": config.preview_image,
                "created_at": config.created_at.isoformat() if config.created_at else None,
                "updated_at": config.updated_at.isoformat() if config.updated_at else None,
            }
            styles.append(style_data)

        # 如果 GlobalStyleConfig 为空，尝试从 GlobalStyle 表获取
        if not styles:
            gs_query = select(GlobalStyle).order_by(desc(GlobalStyle.is_active), GlobalStyle.id)
            gs_result = await db.execute(gs_query)
            gs_configs = gs_result.scalars().all()

            for gs in gs_configs:
                style_data = {
                    "id": gs.id,
                    "name": gs.theme_name or f"Style #{gs.id}",
                    "slug": gs.theme_name or f"style-{gs.id}",
                    "is_active": gs.is_active,
                    "theme_type": "legacy",
                    "variables": _safe_json_parse(gs.variables_json, {}),
                    "created_at": gs.created_at.isoformat() if gs.created_at else None,
                }
                styles.append(style_data)

        return ApiResponse(
            success=True,
            data=styles
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=str(e))


@router.get("/{style_id}")
async def get_global_style(
    style_id: int,
    current_user=Depends(jwt_required),
    db: AsyncSession = Depends(get_async_session),
):
    """获取单个全局样式详情"""
    try:
        result = await db.execute(
            select(GlobalStyleConfig).where(GlobalStyleConfig.id == style_id)
        )
        config = result.scalar_one_or_none()

        if not config:
            return ApiResponse(success=False, error="全局样式不存在")

        return ApiResponse(
            success=True,
            data=config.to_dict()
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("")
async def create_global_style(
    current_user=Depends(jwt_required),
    db: AsyncSession = Depends(get_async_session),
    name: str = Body(...),
    slug: Optional[str] = Body(None),
    theme_type: str = Body("custom"),
    color_scheme: str = Body("{}"),
    typography: str = Body("{}"),
    spacing: str = Body("{}"),
    border_radius: str = Body("{}"),
    shadows: Optional[str] = Body(None),
    breakpoints: Optional[str] = Body(None),
    css_variables: Optional[str] = Body(None),
):
    """创建全局样式配置"""
    try:
        if not slug:
            slug = name.lower().replace(" ", "-")

        new_config = GlobalStyleConfig(
            name=name,
            slug=slug,
            theme_type=theme_type,
            color_scheme=color_scheme,
            typography=typography,
            spacing=spacing,
            border_radius=border_radius,
            shadows=shadows,
            breakpoints=breakpoints,
            css_variables=css_variables,
            created_by=current_user.id,
        )

        db.add(new_config)
        await db.commit()
        await db.refresh(new_config)

        return ApiResponse(
            success=True,
            message="全局样式创建成功",
            data=new_config.to_dict()
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=str(e))


@router.post("/{style_id}/activate")
async def activate_global_style(
    style_id: int,
    current_user=Depends(jwt_required),
    db: AsyncSession = Depends(get_async_session),
):
    """激活指定全局样式"""
    try:
        result = await db.execute(
            select(GlobalStyleConfig).where(GlobalStyleConfig.id == style_id)
        )
        config = result.scalar_one_or_none()

        if not config:
            return ApiResponse(success=False, error="全局样式不存在")

        # 取消所有已激活的样式
        from sqlalchemy import update
        await db.execute(
            update(GlobalStyleConfig).values(is_active=False)
        )

        # 激活目标样式
        config.is_active = True
        await db.commit()

        return ApiResponse(
            success=True,
            message=f"已激活样式: {config.name}"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(success=False, error=str(e))


@router.delete("/{style_id}")
async def delete_global_style(
    style_id: int,
    current_user=Depends(jwt_required),
    db: AsyncSession = Depends(get_async_session),
):
    """删除全局样式"""
    try:
        result = await db.execute(
            select(GlobalStyleConfig).where(GlobalStyleConfig.id == style_id)
        )
        config = result.scalar_one_or_none()

        if not config:
            return ApiResponse(success=False, error="全局样式不存在")

        if config.is_active:
            return ApiResponse(success=False, error="不能删除当前激活的样式")

        await db.delete(config)
        await db.commit()

        return ApiResponse(
            success=True,
            message="全局样式已删除"
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


def _safe_json_parse(json_str: Optional[str], default=None):
    """安全解析 JSON 字符串"""
    if not json_str:
        return default if default is not None else {}
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else {}
