"""
团队协作 API
提供工作区管理、成员管理、任务分配等功能
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import WorkspaceMember, Workspace
from shared.services.chat.collaboration import collaboration_service
from shared.services.chat.collaboration_service import TeamRole
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import get_current_user
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["collaboration"])


# ==================== 工作区管理 ====================

@router.post("/workspaces", summary="创建工作区")
async def create_workspace(
        name: str = Body(..., description="工作区名称"),
        slug: str = Body(..., description="工作区标识"),
        description: Optional[str] = Body(None, description="描述"),
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db)
):
    """
    创建新的团队工作区
    
    Args:
        name: 工作区名称
        slug: 工作区标识（唯一）
        description: 描述
        
    Returns:
        创建的工作区
    """
    try:
        workspace = await collaboration_service.create_workspace(
            db=db,
            name=name,
            slug=slug,
            owner_id=current_user.id,
            description=description
        )

        return ApiResponse(
            success=True,
            data={
                'id': workspace.id,
                'name': workspace.name,
                'slug': workspace.slug,
                'description': workspace.description,
                'owner_id': workspace.owner_id,
                'created_at': workspace.created_at.isoformat() if workspace.created_at else None,
            },
            message="Workspace created successfully"
        )

    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/workspaces", summary="获取我的工作区列表")
async def get_my_workspaces(
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取当前用户的所有工作区
    
    Returns:
        工作区列表
    """
    try:
        from sqlalchemy import select

        stmt = (
            select(Workspace)
            .join(WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id)
            .where(
                WorkspaceMember.user_id == current_user.id,
                WorkspaceMember.is_active == True,
                Workspace.is_active == True
            )
        )

        result = await db.execute(stmt)
        workspaces = result.scalars().all()

        workspace_list = []
        for ws in workspaces:
            # 获取用户在该工作区的角色
            member_stmt = select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == ws.id,
                WorkspaceMember.user_id == current_user.id
            )
            member_result = await db.execute(member_stmt)
            member = member_result.scalar_one_or_none()

            workspace_list.append({
                'id': ws.id,
                'name': ws.name,
                'slug': ws.slug,
                'description': ws.description,
                'role': member.role if member else None,
                'created_at': ws.created_at.isoformat() if ws.created_at else None,
            })

        return ApiResponse(
            success=True,
            data={
                'workspaces': workspace_list,
                'total': len(workspace_list)
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/workspaces/{workspace_slug}", summary="获取工作区详情")
async def get_workspace(
        workspace_slug: str,
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取工作区详情
    
    Args:
        workspace_slug: 工作区标识
        
    Returns:
        工作区详情
    """
    try:
        from sqlalchemy import select
        stmt = select(Workspace).where(Workspace.slug == workspace_slug)
        result = await db.execute(stmt)
        workspace = result.scalar_one_or_none()

        if not workspace:
            return ApiResponse(success=False, error="Workspace not found")

        # 检查权限
        has_permission = await collaboration_service.check_permission(
            db, workspace.id, current_user.id, TeamRole.VIEWER
        )

        if not has_permission:
            return ApiResponse(success=False, error="Access denied")

        # 获取成员数量
        member_count_stmt = select(func.count()).select_from(
            WorkspaceMember
        ).where(
            WorkspaceMember.workspace_id == workspace.id,
            WorkspaceMember.is_active == True
        )
        member_count_result = await db.execute(member_count_stmt)
        member_count = member_count_result.scalar()

        return ApiResponse(
            success=True,
            data={
                'id': workspace.id,
                'name': workspace.name,
                'slug': workspace.slug,
                'description': workspace.description,
                'owner_id': workspace.owner_id,
                'member_count': member_count,
                'created_at': workspace.created_at.isoformat() if workspace.created_at else None,
                'updated_at': workspace.updated_at.isoformat() if workspace.updated_at else None,
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# ==================== 成员管理 ====================

@router.post("/workspaces/{workspace_id}/members", summary="添加成员")
async def add_member(
        workspace_id: int,
        user_id: int = Body(..., description="用户ID"),
        role: str = Body(TeamRole.VIEWER.value, description="角色"),
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db)
):
    """
    添加成员到工作区
    
    Args:
        workspace_id: 工作区ID
        user_id: 用户ID
        role: 角色 (owner/admin/editor/viewer)
        
    Returns:
        添加结果
    """
    try:
        # 检查权限（需要admin或以上）
        has_permission = await collaboration_service.check_permission(
            db, workspace_id, current_user.id, TeamRole.ADMIN
        )

        if not has_permission:
            return ApiResponse(success=False, error="Insufficient permissions")

        member = await collaboration_service.add_member(
            db=db,
            workspace_id=workspace_id,
            user_id=user_id,
            role=role
        )

        return ApiResponse(
            success=True,
            data={
                'id': member.id,
                'user_id': member.user_id,
                'role': member.role,
                'joined_at': member.joined_at.isoformat() if member.joined_at else None,
            },
            message="Member added successfully"
        )

    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.delete("/workspaces/{workspace_id}/members/{user_id}", summary="移除成员")
async def remove_member(
        workspace_id: int,
        user_id: int,
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db)
):
    """
    从工作区移除成员
    
    Args:
        workspace_id: 工作区ID
        user_id: 用户ID
        
    Returns:
        移除结果
    """
    try:
        # 检查权限（需要admin或以上）
        has_permission = await collaboration_service.check_permission(
            db, workspace_id, current_user.id, TeamRole.ADMIN
        )

        if not has_permission:
            return ApiResponse(success=False, error="Insufficient permissions")

        await collaboration_service.remove_member(
            db=db,
            workspace_id=workspace_id,
            user_id=user_id
        )

        return ApiResponse(
            success=True,
            message="Member removed successfully"
        )

    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.put("/workspaces/{workspace_id}/members/{user_id}/role", summary="更新成员角色")
async def update_member_role(
        workspace_id: int,
        user_id: int,
        role: str = Body(..., description="新角色"),
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db)
):
    """
    更新成员角色
    
    Args:
        workspace_id: 工作区ID
        user_id: 用户ID
        role: 新角色
        
    Returns:
        更新结果
    """
    try:
        # 检查权限（需要owner）
        has_permission = await collaboration_service.check_permission(
            db, workspace_id, current_user.id, TeamRole.OWNER
        )

        if not has_permission:
            return ApiResponse(success=False, error="Insufficient permissions")

        await collaboration_service.update_member_role(
            db=db,
            workspace_id=workspace_id,
            user_id=user_id,
            new_role=role
        )

        return ApiResponse(
            success=True,
            message="Member role updated successfully"
        )

    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/workspaces/{workspace_id}/members", summary="获取成员列表")
async def get_members(
        workspace_id: int,
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取工作区成员列表
    
    Args:
        workspace_id: 工作区ID
        
    Returns:
        成员列表
    """
    try:
        # 检查权限
        has_permission = await collaboration_service.check_permission(
            db, workspace_id, current_user.id, TeamRole.VIEWER
        )

        if not has_permission:
            return ApiResponse(success=False, error="Access denied")

        members = await collaboration_service.get_workspace_members(db, workspace_id)

        return ApiResponse(
            success=True,
            data={
                'members': members,
                'total': len(members)
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# ==================== 任务管理 ====================

@router.post("/workspaces/{workspace_id}/tasks", summary="创建任务")
async def create_task(
        workspace_id: int,
        title: str = Body(..., description="任务标题"),
        description: Optional[str] = Body(None, description="任务描述"),
        assigned_to: Optional[int] = Body(None, description="分配给的用户ID"),
        priority: str = Body("medium", description="优先级 (low/medium/high/urgent)"),
        due_date: Optional[str] = Body(None, description="截止日期 (ISO格式)"),
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db)
):
    """
    创建任务
    
    Args:
        workspace_id: 工作区ID
        title: 任务标题
        description: 任务描述
        assigned_to: 分配给的用户ID
        priority: 优先级
        due_date: 截止日期
        
    Returns:
        创建的任务
    """
    try:
        # 检查权限（需要editor或以上）
        has_permission = await collaboration_service.check_permission(
            db, workspace_id, current_user.id, TeamRole.EDITOR
        )

        if not has_permission:
            return ApiResponse(success=False, error="Insufficient permissions")

        # 解析日期
        due_dt = None
        if due_date:
            due_dt = datetime.fromisoformat(due_date.replace('Z', '+00:00'))

        task = await collaboration_service.create_task(
            db=db,
            workspace_id=workspace_id,
            title=title,
            description=description,
            created_by=current_user.id,
            assigned_to=assigned_to,
            priority=priority,
            due_date=due_dt
        )

        return ApiResponse(
            success=True,
            data={
                'id': task.id,
                'title': task.title,
                'status': task.status,
                'priority': task.priority,
                'assigned_to': task.assigned_to,
                'created_at': task.created_at.isoformat() if task.created_at else None,
            },
            message="Task created successfully"
        )

    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.put("/tasks/{task_id}/status", summary="更新任务状态")
async def update_task_status(
        task_id: int,
        status: str = Body(..., description="新状态 (pending/in_progress/completed/cancelled)"),
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db)
):
    """
    更新任务状态
    
    Args:
        task_id: 任务ID
        status: 新状态
        
    Returns:
        更新后的任务
    """
    try:
        task = await collaboration_service.update_task_status(
            db=db,
            task_id=task_id,
            status=status,
            completed_by=current_user.id if status == 'completed' else None
        )

        return ApiResponse(
            success=True,
            data={
                'id': task.id,
                'status': task.status,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            },
            message="Task status updated successfully"
        )

    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/workspaces/{workspace_id}/tasks", summary="获取任务列表")
async def get_tasks(
        workspace_id: int,
        status: Optional[str] = Query(None, description="状态过滤"),
        assigned_to: Optional[int] = Query(None, description="分配给用户过滤"),
        page: int = Query(1, ge=1, description="页码"),
        per_page: int = Query(20, ge=1, le=100, description="每页数量"),
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取工作区任务列表
    
    Args:
        workspace_id: 工作区ID
        status: 状态过滤
        assigned_to: 分配给用户过滤
        page: 页码
        per_page: 每页数量
        
    Returns:
        任务列表和分页信息
    """
    try:
        # 检查权限
        has_permission = await collaboration_service.check_permission(
            db, workspace_id, current_user.id, TeamRole.VIEWER
        )

        if not has_permission:
            return ApiResponse(success=False, error="Access denied")

        result = await collaboration_service.get_workspace_tasks(
            db=db,
            workspace_id=workspace_id,
            status=status,
            assigned_to=assigned_to,
            page=page,
            per_page=per_page
        )

        return ApiResponse(
            success=True,
            data=result
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# 导入func
from sqlalchemy import func
