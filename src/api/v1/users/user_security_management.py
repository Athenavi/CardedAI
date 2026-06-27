"""
用户安全扩展管理 API

提供字段级权限(FieldPermission)、用户会话(UserSession)、邮件订阅(EmailSubscription) 的 CRUD 管理接口
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import UserSession
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["user-security-management"])


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
