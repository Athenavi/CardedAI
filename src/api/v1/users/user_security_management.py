"""
用户安全扩展管理 API

提供字段级权限(FieldPermission)、用户会话(UserSession)、邮件订阅(EmailSubscription) 的 CRUD 管理接口
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import FieldPermission, UserSession, EmailSubscription
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["user-security-management"])


# ==================== 字段级权限管理 ====================


@router.get("/field-permissions")
async def list_field_permissions(
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(50, ge=1, le=200, description="每页数量"),
    role_id: Optional[int] = Query(None, description="角色ID"),
    model_name: Optional[str] = Query(None, description="模型名称"),
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """获取字段权限列表"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(FieldPermission)

        if role_id:
            query = query.where(FieldPermission.role_id == role_id)

        if model_name:
            query = query.where(FieldPermission.model_name == model_name)

        query = query.order_by(FieldPermission.role_id, FieldPermission.model_name, FieldPermission.field_name)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        result = await db.execute(query)
        permissions = result.scalars().all()

        return ApiResponse(
            success=True,
            data={
                "field_permissions": [p.to_dict() for p in permissions],
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


@router.get("/field-permissions/{perm_id}")
async def get_field_permission(
    perm_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """获取字段权限详情"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(FieldPermission).where(FieldPermission.id == perm_id)
        result = await db.execute(query)
        perm = result.scalar_one_or_none()

        if not perm:
            return ApiResponse(success=False, error="字段权限不存在")

        return ApiResponse(success=True, data=perm.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/field-permissions")
async def create_field_permission(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """创建字段权限"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        data = await request.json()

        role_id = data.get("role_id")
        model_name = data.get("model_name")
        field_name = data.get("field_name")
        if not role_id or not model_name or not field_name:
            return ApiResponse(success=False, error="role_id、model_name、field_name 为必填字段")

        # 检查唯一性
        existing = await db.execute(
            select(FieldPermission).where(
                FieldPermission.role_id == role_id,
                FieldPermission.model_name == model_name,
                FieldPermission.field_name == field_name,
            )
        )
        if existing.scalar_one_or_none():
            return ApiResponse(
                success=False,
                error=f"角色 ID={role_id} 对 {model_name}.{field_name} 的权限配置已存在",
            )

        now = datetime.utcnow()
        perm = FieldPermission(
            role_id=role_id,
            model_name=model_name,
            field_name=field_name,
            can_read=data.get("can_read", True),
            can_write=data.get("can_write", False),
            created_at=now,
        )

        db.add(perm)
        await db.commit()
        await db.refresh(perm)

        return ApiResponse(success=True, data=perm.to_dict(), message="字段权限创建成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


@router.put("/field-permissions/{perm_id}")
async def update_field_permission(
    perm_id: int,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """更新字段权限"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(FieldPermission).where(FieldPermission.id == perm_id)
        result = await db.execute(query)
        perm = result.scalar_one_or_none()

        if not perm:
            return ApiResponse(success=False, error="字段权限不存在")

        data = await request.json()

        if "can_read" in data:
            perm.can_read = data["can_read"]
        if "can_write" in data:
            perm.can_write = data["can_write"]
        if "model_name" in data:
            perm.model_name = data["model_name"]
        if "field_name" in data:
            perm.field_name = data["field_name"]

        await db.commit()
        await db.refresh(perm)

        return ApiResponse(success=True, data=perm.to_dict(), message="字段权限更新成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


@router.delete("/field-permissions/{perm_id}")
async def delete_field_permission(
    perm_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """删除字段权限"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(FieldPermission).where(FieldPermission.id == perm_id)
        result = await db.execute(query)
        perm = result.scalar_one_or_none()

        if not perm:
            return ApiResponse(success=False, error="字段权限不存在")

        await db.delete(perm)
        await db.commit()

        return ApiResponse(success=True, message="字段权限删除成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


# ==================== 用户会话管理 ====================


@router.get("/sessions")
async def list_sessions(
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    is_active: Optional[bool] = Query(None, description="是否活跃"),
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """
    获取用户会话列表

    管理员可查看所有用户会话，普通用户仅能查看自己的会话
    """
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)

        query = select(UserSession)

        if is_admin:
            if user_id:
                query = query.where(UserSession.user_id == user_id)
        else:
            # 普通用户只能查看自己的会话
            query = query.where(UserSession.user_id == current_user.id)

        if is_active is not None:
            query = query.where(UserSession.is_active == is_active)

        query = query.order_by(UserSession.last_activity.desc())

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        result = await db.execute(query)
        sessions = result.scalars().all()

        # 安全：对非管理员隐藏敏感 token
        session_data = []
        for s in sessions:
            d = s.to_dict()
            if not is_admin:
                d.pop("access_token", None)
                d.pop("refresh_token", None)
            session_data.append(d)

        return ApiResponse(
            success=True,
            data={
                "sessions": session_data,
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


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """获取会话详情"""
    try:
        query = select(UserSession).where(UserSession.id == session_id)
        result = await db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            return ApiResponse(success=False, error="会话不存在")

        # 权限检查
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if session.user_id != current_user.id and not is_admin:
            raise HTTPException(status_code=403, detail="无权查看此会话")

        data = session.to_dict(exclude_sensitive=False) if is_admin else session.to_dict()
        if not is_admin:
            data.pop("access_token", None)
            data.pop("refresh_token", None)

        return ApiResponse(success=True, data=data)
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.put("/sessions/{session_id}/deactivate")
async def deactivate_session(
    session_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """
    停用会话（踢出登录）

    管理员可停用任意会话，普通用户仅能停用自己的会话
    """
    try:
        query = select(UserSession).where(UserSession.id == session_id)
        result = await db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            return ApiResponse(success=False, error="会话不存在")

        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if session.user_id != current_user.id and not is_admin:
            raise HTTPException(status_code=403, detail="无权操作此会话")

        session.is_active = False
        await db.commit()
        await db.refresh(session)

        return ApiResponse(success=True, data=session.to_dict(), message="会话已停用")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """删除会话记录"""
    try:
        query = select(UserSession).where(UserSession.id == session_id)
        result = await db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            return ApiResponse(success=False, error="会话不存在")

        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        await db.delete(session)
        await db.commit()

        return ApiResponse(success=True, message="会话记录删除成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


# ==================== 邮件订阅管理 ====================


@router.get("/email-subscriptions")
async def list_email_subscriptions(
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    subscribed: Optional[bool] = Query(None, description="是否订阅"),
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """获取邮件订阅列表"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(EmailSubscription)

        if user_id:
            query = query.where(EmailSubscription.user == user_id)

        if subscribed is not None:
            query = query.where(EmailSubscription.subscribed == subscribed)

        query = query.order_by(EmailSubscription.created_at.desc())

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        result = await db.execute(query)
        subscriptions = result.scalars().all()

        return ApiResponse(
            success=True,
            data={
                "email_subscriptions": [s.to_dict() for s in subscriptions],
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


@router.post("/email-subscriptions")
async def create_email_subscription(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """创建邮件订阅"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        data = await request.json()

        user = data.get("user")
        if not user:
            return ApiResponse(success=False, error="user 为必填字段")

        # 检查该用户是否已有订阅记录
        existing = await db.execute(
            select(EmailSubscription).where(EmailSubscription.user == user)
        )
        if existing.scalar_one_or_none():
            return ApiResponse(success=False, error=f"用户 ID={user} 已有邮件订阅记录")

        now = datetime.utcnow()
        subscription = EmailSubscription(
            user=user,
            subscribed=data.get("subscribed", True),
            created_at=now,
        )

        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)

        return ApiResponse(success=True, data=subscription.to_dict(), message="邮件订阅创建成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


@router.put("/email-subscriptions/{sub_id}")
async def update_email_subscription(
    sub_id: int,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """更新邮件订阅状态"""
    try:
        query = select(EmailSubscription).where(EmailSubscription.id == sub_id)
        result = await db.execute(query)
        subscription = result.scalar_one_or_none()

        if not subscription:
            return ApiResponse(success=False, error="邮件订阅记录不存在")

        # 管理员可修改任意记录，普通用户仅可修改自己的记录
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if subscription.user != current_user.id and not is_admin:
            raise HTTPException(status_code=403, detail="无权修改此订阅记录")

        data = await request.json()

        if "subscribed" in data:
            subscription.subscribed = data["subscribed"]

        await db.commit()
        await db.refresh(subscription)

        return ApiResponse(success=True, data=subscription.to_dict(), message="邮件订阅更新成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


@router.delete("/email-subscriptions/{sub_id}")
async def delete_email_subscription(
    sub_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """删除邮件订阅"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(EmailSubscription).where(EmailSubscription.id == sub_id)
        result = await db.execute(query)
        subscription = result.scalar_one_or_none()

        if not subscription:
            return ApiResponse(success=False, error="邮件订阅记录不存在")

        await db.delete(subscription)
        await db.commit()

        return ApiResponse(success=True, message="邮件订阅删除成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))
