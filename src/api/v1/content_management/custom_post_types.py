"""
自定义内容类型API
提供CPT的CRUD操作
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.custom_post_type import CustomPostType
from src.api.v1.core.responses import ApiResponse
from src.utils.database.unified_manager import get_db_session

router = APIRouter(tags=["custom-post-types"])


class CustomPostTypeCreate(BaseModel):
    """创建CPT请求"""
    name: str
    slug: str
    description: Optional[str] = None
    supports: Optional[str] = None
    has_archive: bool = False
    menu_icon: Optional[str] = None
    menu_position: int = 5


class CustomPostTypeUpdate(BaseModel):
    """更新CPT请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    supports: Optional[str] = None
    has_archive: Optional[bool] = None
    menu_icon: Optional[str] = None
    menu_position: Optional[int] = None
    is_active: Optional[bool] = None


@router.get("")
async def list_custom_post_types(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
        db: AsyncSession = Depends(get_db_session)
):
    """获取自定义内容类型列表"""
    try:
        from sqlalchemy import func

        # 获取总数
        count_result = await db.execute(select(func.count()).select_from(CustomPostType))
        total = count_result.scalar()

        # 获取列表
        result = await db.execute(
            select(CustomPostType).offset(skip).limit(limit)
        )
        items = result.scalars().all()
        
        return ApiResponse(
            success=True,
            data={
                'items': [item.to_dict() for item in items],
                'total': total,
                'skip': skip,
                'limit': limit
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取列表失败: {str(e)}")


@router.post("")
async def create_custom_post_type(
    data: CustomPostTypeCreate,
        db: AsyncSession = Depends(get_db_session)
):
    """创建自定义内容类型"""
    try:
        cpt = CustomPostType(
            name=data.name,
            slug=data.slug,
            description=data.description,
            supports=data.supports,
            has_archive=data.has_archive,
            menu_icon=data.menu_icon,
            menu_position=data.menu_position,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(cpt)
        await db.commit()
        await db.refresh(cpt)
        
        return ApiResponse(
            success=True,
            message="创建成功",
            data=cpt.to_dict()
        )
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=f"创建失败: {str(e)}")


@router.get("/{cpt_id}")
async def get_custom_post_type(cpt_id: int, db: AsyncSession = Depends(get_db_session)):
    """获取自定义内容类型详情"""
    try:
        result = await db.execute(
            select(CustomPostType).where(CustomPostType.id == cpt_id)
        )
        cpt = result.scalar_one_or_none()
        
        if not cpt:
            return ApiResponse(success=False, error="内容类型不存在")
        
        return ApiResponse(success=True, data=cpt.to_dict())
    except Exception as e:
        return ApiResponse(success=False, error=f"获取详情失败: {str(e)}")


@router.put("/{cpt_id}")
async def update_custom_post_type(
    cpt_id: int,
    data: CustomPostTypeUpdate,
        db: AsyncSession = Depends(get_db_session)
):
    """更新自定义内容类型"""
    try:
        result = await db.execute(
            select(CustomPostType).where(CustomPostType.id == cpt_id)
        )
        cpt = result.scalar_one_or_none()
        
        if not cpt:
            return ApiResponse(success=False, error="内容类型不存在")
        
        if data.name is not None:
            cpt.name = data.name
        if data.description is not None:
            cpt.description = data.description
        if data.supports is not None:
            cpt.supports = data.supports
        if data.has_archive is not None:
            cpt.has_archive = data.has_archive
        if data.menu_icon is not None:
            cpt.menu_icon = data.menu_icon
        if data.menu_position is not None:
            cpt.menu_position = data.menu_position
        if data.is_active is not None:
            cpt.is_active = data.is_active

        cpt.updated_at = datetime.now()

        await db.commit()
        await db.refresh(cpt)
        
        return ApiResponse(
            success=True,
            message="更新成功",
            data=cpt.to_dict()
        )
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=f"更新失败: {str(e)}")


@router.delete("/{cpt_id}")
async def delete_custom_post_type(cpt_id: int, db: AsyncSession = Depends(get_db_session)):
    """删除自定义内容类型"""
    try:
        result = await db.execute(
            select(CustomPostType).where(CustomPostType.id == cpt_id)
        )
        cpt = result.scalar_one_or_none()
        
        if not cpt:
            return ApiResponse(success=False, error="内容类型不存在")

        await db.delete(cpt)
        await db.commit()
        
        return ApiResponse(success=True, message="删除成功")
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=f"删除失败: {str(e)}")
