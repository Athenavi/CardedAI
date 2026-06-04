"""
内容管理扩展 API

提供文章修订注释(ArticleRevisionNote)、菜单位置(MenuLocation)、菜单-位置关联(MenuLocationAssignment) 的 CRUD 管理接口
"""
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import ArticleRevisionNote, MenuLocation, MenuLocationAssignment, Menus
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["content-management-ext"])


# ==================== 文章修订注释管理 ====================


@router.get("/revision-notes")
async def list_revision_notes(
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
    revision_id: Optional[int] = Query(None, description="修订版本ID"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """获取文章修订注释列表"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(ArticleRevisionNote)

        if revision_id:
            query = query.where(ArticleRevisionNote.revision_id == revision_id)

        if user_id:
            query = query.where(ArticleRevisionNote.user_id == user_id)

        query = query.order_by(ArticleRevisionNote.created_at.desc())

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        result = await db.execute(query)
        notes = result.scalars().all()

        return ApiResponse(
            success=True,
            data={
                "revision_notes": [n.to_dict() for n in notes],
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "total_pages": (total + per_page - 1) // per_page if total > 0 else 0,
                },
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/revision-notes/{note_id}")
async def get_revision_note(
    note_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """获取修订注释详情"""
    try:
        query = select(ArticleRevisionNote).where(ArticleRevisionNote.id == note_id)
        result = await db.execute(query)
        note = result.scalar_one_or_none()

        if not note:
            return ApiResponse(success=False, error="修订注释不存在")

        return ApiResponse(success=True, data=note.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/revision-notes")
async def create_revision_note(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """创建修订注释"""
    try:
        data = await request.json()

        revision_id = data.get("revision_id")
        note_content = data.get("note_content")
        if not revision_id or not note_content:
            return ApiResponse(success=False, error="revision_id 和 note_content 为必填字段")

        now = datetime.utcnow()
        note = ArticleRevisionNote(
            revision_id=revision_id,
            user_id=current_user.id,
            note_content=note_content,
            created_at=now,
        )

        db.add(note)
        await db.commit()
        await db.refresh(note)

        return ApiResponse(success=True, data=note.to_dict(), message="修订注释创建成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


@router.put("/revision-notes/{note_id}")
async def update_revision_note(
    note_id: int,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """更新修订注释"""
    try:
        query = select(ArticleRevisionNote).where(ArticleRevisionNote.id == note_id)
        result = await db.execute(query)
        note = result.scalar_one_or_none()

        if not note:
            return ApiResponse(success=False, error="修订注释不存在")

        # 仅允许作者或管理员修改
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if note.user_id != current_user.id and not is_admin:
            raise HTTPException(status_code=403, detail="无权修改此注释")

        data = await request.json()
        if "note_content" in data:
            note.note_content = data["note_content"]

        await db.commit()
        await db.refresh(note)

        return ApiResponse(success=True, data=note.to_dict(), message="修订注释更新成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


@router.delete("/revision-notes/{note_id}")
async def delete_revision_note(
    note_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """删除修订注释"""
    try:
        query = select(ArticleRevisionNote).where(ArticleRevisionNote.id == note_id)
        result = await db.execute(query)
        note = result.scalar_one_or_none()

        if not note:
            return ApiResponse(success=False, error="修订注释不存在")

        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if note.user_id != current_user.id and not is_admin:
            raise HTTPException(status_code=403, detail="无权删除此注释")

        await db.delete(note)
        await db.commit()

        return ApiResponse(success=True, message="修订注释删除成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


# ==================== 菜单位置管理 ====================


@router.get("/menu-locations")
async def list_menu_locations(
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """获取所有菜单位置"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(MenuLocation).order_by(MenuLocation.name)
        result = await db.execute(query)
        locations = result.scalars().all()

        return ApiResponse(
            success=True,
            data={"menu_locations": [loc.to_dict() for loc in locations]}
        )
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/menu-locations/{location_id}")
async def get_menu_location(
    location_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """获取菜单位置详情（包含已分配的菜单列表）"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(MenuLocation).where(MenuLocation.id == location_id)
        result = await db.execute(query)
        location = result.scalar_one_or_none()

        if not location:
            return ApiResponse(success=False, error="菜单位置不存在")

        # 获取该位置下分配的菜单
        assignment_query = (
            select(MenuLocationAssignment, Menus)
            .join(Menus, MenuLocationAssignment.menu_id == Menus.id)
            .where(MenuLocationAssignment.location_id == location_id)
        )
        assignment_result = await db.execute(assignment_query)
        assignments = assignment_result.all()

        data = location.to_dict()
        data["assigned_menus"] = [
            {
                "assignment_id": a[0].id,
                "menu_id": a[1].id,
                "menu_name": a[1].name if hasattr(a[1], 'name') else None,
                "assigned_at": a[0].created_at.isoformat() if a[0].created_at else None,
            }
            for a in assignments
        ]

        return ApiResponse(success=True, data=data)
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/menu-locations")
async def create_menu_location(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """创建菜单位置"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        data = await request.json()

        name = data.get("name")
        slug = data.get("slug")
        if not name or not slug:
            return ApiResponse(success=False, error="name 和 slug 为必填字段")

        # 检查 slug 唯一性
        existing = await db.execute(
            select(MenuLocation).where(MenuLocation.slug == slug)
        )
        if existing.scalar_one_or_none():
            return ApiResponse(success=False, error=f"菜单位置标识 '{slug}' 已存在")

        theme_supports = data.get("theme_supports")
        if isinstance(theme_supports, list):
            theme_supports = json.dumps(theme_supports, ensure_ascii=False)

        now = datetime.utcnow()
        location = MenuLocation(
            name=name,
            slug=slug,
            description=data.get("description"),
            theme_supports=theme_supports,
            created_at=now,
            updated_at=now,
        )

        db.add(location)
        await db.commit()
        await db.refresh(location)

        return ApiResponse(success=True, data=location.to_dict(), message="菜单位置创建成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


@router.put("/menu-locations/{location_id}")
async def update_menu_location(
    location_id: int,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """更新菜单位置"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(MenuLocation).where(MenuLocation.id == location_id)
        result = await db.execute(query)
        location = result.scalar_one_or_none()

        if not location:
            return ApiResponse(success=False, error="菜单位置不存在")

        data = await request.json()

        if "name" in data:
            location.name = data["name"]

        if "slug" in data and data["slug"] != location.slug:
            existing = await db.execute(
                select(MenuLocation).where(MenuLocation.slug == data["slug"])
            )
            if existing.scalar_one_or_none():
                return ApiResponse(success=False, error=f"标识 '{data['slug']}' 已被其他位置使用")
            location.slug = data["slug"]

        if "description" in data:
            location.description = data["description"]

        if "theme_supports" in data:
            ts = data["theme_supports"]
            location.theme_supports = json.dumps(ts, ensure_ascii=False) if isinstance(ts, list) else ts

        location.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(location)

        return ApiResponse(success=True, data=location.to_dict(), message="菜单位置更新成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


@router.delete("/menu-locations/{location_id}")
async def delete_menu_location(
    location_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """删除菜单位置"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(MenuLocation).where(MenuLocation.id == location_id)
        result = await db.execute(query)
        location = result.scalar_one_or_none()

        if not location:
            return ApiResponse(success=False, error="菜单位置不存在")

        # 级联删除关联分配
        await db.execute(
            MenuLocationAssignment.__table__.delete().where(
                MenuLocationAssignment.location_id == location_id
            )
        )

        await db.delete(location)
        await db.commit()

        return ApiResponse(success=True, message="菜单位置及其关联删除成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


# ==================== 菜单-位置关联管理 ====================


@router.get("/menu-location-assignments")
async def list_assignments(
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(50, ge=1, le=200, description="每页数量"),
    menu_id: Optional[int] = Query(None, description="按菜单ID筛选"),
    location_id: Optional[int] = Query(None, description="按位置ID筛选"),
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """获取菜单-位置关联列表"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(MenuLocationAssignment)

        if menu_id:
            query = query.where(MenuLocationAssignment.menu_id == menu_id)
        if location_id:
            query = query.where(MenuLocationAssignment.location_id == location_id)

        query = query.order_by(MenuLocationAssignment.created_at.desc())

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        result = await db.execute(query)
        assignments = result.scalars().all()

        return ApiResponse(
            success=True,
            data={
                "assignments": [a.to_dict() for a in assignments],
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "total_pages": (total + per_page - 1) // per_page if total > 0 else 0,
                },
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/menu-location-assignments")
async def create_assignment(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """创建菜单-位置关联"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        data = await request.json()

        menu_id = data.get("menu_id")
        location_id = data.get("location_id")
        if not menu_id or not location_id:
            return ApiResponse(success=False, error="menu_id 和 location_id 为必填字段")

        # 验证菜单存在性
        menu_query = select(Menus).where(Menus.id == menu_id)
        menu_result = await db.execute(menu_query)
        if not menu_result.scalar_one_or_none():
            return ApiResponse(success=False, error=f"菜单 ID={menu_id} 不存在")

        # 验证位置存在性
        loc_query = select(MenuLocation).where(MenuLocation.id == location_id)
        loc_result = await db.execute(loc_query)
        if not loc_result.scalar_one_or_none():
            return ApiResponse(success=False, error=f"菜单位置 ID={location_id} 不存在")

        # 检查唯一性
        existing = await db.execute(
            select(MenuLocationAssignment).where(
                MenuLocationAssignment.menu_id == menu_id,
                MenuLocationAssignment.location_id == location_id,
            )
        )
        if existing.scalar_one_or_none():
            return ApiResponse(success=False, error="该菜单已分配到此位置")

        now = datetime.utcnow()
        assignment = MenuLocationAssignment(
            menu_id=menu_id,
            location_id=location_id,
            created_at=now,
        )

        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)

        return ApiResponse(success=True, data=assignment.to_dict(), message="菜单-位置关联创建成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


@router.delete("/menu-location-assignments/{assignment_id}")
async def delete_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """删除菜单-位置关联"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(MenuLocationAssignment).where(MenuLocationAssignment.id == assignment_id)
        result = await db.execute(query)
        assignment = result.scalar_one_or_none()

        if not assignment:
            return ApiResponse(success=False, error="菜单-位置关联不存在")

        await db.delete(assignment)
        await db.commit()

        return ApiResponse(success=True, message="菜单-位置关联删除成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))
