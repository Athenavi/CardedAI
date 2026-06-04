"""
团队协作服务
提供团队工作区、成员管理、协作编辑和任务分配功能
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.functions import func

from shared.models.workspace import Workspace
from shared.models.workspace_member import WorkspaceMember
from shared.models.task import Task

from src.unified_logger import default_logger as logger


class TeamRole(Enum):
    """团队角色"""
    OWNER = "owner"  # 所有者
    ADMIN = "admin"  # 管理员
    EDITOR = "editor"  # 编辑者
    VIEWER = "viewer"  # 查看者


class CollaborationService:
    """
    团队协作服务
    
    功能:
    1. 团队工作区管理
    2. 成员权限管理
    3. 任务分配和追踪
    4. 协作编辑支持
    """

    def __init__(self):
        pass

    async def create_workspace(self, db, name: str, slug: str, owner_id: int,
                               description: str = None, settings: Dict = None) -> Workspace:
        """
        创建工作区
        
        Args:
            db: 数据库会话
            name: 工作区名称
            slug: 工作区标识
            owner_id: 所有者ID
            description: 描述
            settings: 设置
            
        Returns:
            创建的工作区
        """
        from sqlalchemy import select

        # 检查slug是否已存在
        stmt = select(Workspace).where(Workspace.slug == slug)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise ValueError(f"Workspace with slug '{slug}' already exists")

        # 创建工作区
        workspace = Workspace(
            name=name,
            slug=slug,
            description=description,
            owner_id=owner_id,
            settings=str(settings) if settings else None
        )

        db.add(workspace)
        await db.flush()

        # 添加所有者为管理员
        member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=owner_id,
            role=TeamRole.OWNER.value
        )
        db.add(member)

        await db.commit()
        await db.refresh(workspace)

        logger.info(f"Workspace created: {slug} by user {owner_id}")
        return workspace

    async def add_member(self, db, workspace_id: int, user_id: int,
                         role: str = TeamRole.VIEWER.value) -> WorkspaceMember:
        """
        添加成员到工作区
        
        Args:
            db: 数据库会话
            workspace_id: 工作区ID
            user_id: 用户ID
            role: 角色
            
        Returns:
            创建的成员记录
        """
        from sqlalchemy import select

        # 检查工作区是否存在
        stmt = select(Workspace).where(Workspace.id == workspace_id)
        result = await db.execute(stmt)
        workspace = result.scalar_one_or_none()

        if not workspace:
            raise ValueError("Workspace not found")

        # 检查成员是否已存在
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            if existing.is_active:
                raise ValueError("User is already a member of this workspace")
            # 重新激活
            existing.is_active = True
            existing.role = role
            await db.commit()
            await db.refresh(existing)
            return existing

        # 添加新成员
        member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=user_id,
            role=role
        )

        db.add(member)
        await db.commit()
        await db.refresh(member)

        logger.info(f"User {user_id} added to workspace {workspace_id} as {role}")
        return member

    async def remove_member(self, db, workspace_id: int, user_id: int):
        """
        从工作区移除成员
        
        Args:
            db: 数据库会话
            workspace_id: 工作区ID
            user_id: 用户ID
        """
        from sqlalchemy import select

        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id
        )
        result = await db.execute(stmt)
        member = result.scalar_one_or_none()

        if not member:
            raise ValueError("Member not found")

        # 不能移除所有者
        if member.role == TeamRole.OWNER.value:
            raise ValueError("Cannot remove the owner")

        member.is_active = False
        await db.commit()

        logger.info(f"User {user_id} removed from workspace {workspace_id}")

    async def update_member_role(self, db, workspace_id: int, user_id: int, new_role: str):
        """
        更新成员角色
        
        Args:
            db: 数据库会话
            workspace_id: 工作区ID
            user_id: 用户ID
            new_role: 新角色
        """
        from sqlalchemy import select

        if new_role not in [r.value for r in TeamRole]:
            raise ValueError(f"Invalid role: {new_role}")

        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id
        )
        result = await db.execute(stmt)
        member = result.scalar_one_or_none()

        if not member:
            raise ValueError("Member not found")

        old_role = member.role
        member.role = new_role
        await db.commit()

        logger.info(f"User {user_id} role changed from {old_role} to {new_role} in workspace {workspace_id}")

    async def create_task(self, db, workspace_id: int, title: str, created_by: int,
                          description: str = None, assigned_to: int = None,
                          priority: str = 'medium', due_date: datetime = None) -> Task:
        """
        创建任务
        
        Args:
            db: 数据库会话
            workspace_id: 工作区ID
            title: 任务标题
            created_by: 创建者ID
            description: 任务描述
            assigned_to: 分配给的用户ID
            priority: 优先级
            due_date: 截止日期
            
        Returns:
            创建的任务
        """
        task = Task(
            workspace_id=workspace_id,
            title=title,
            description=description,
            created_by=created_by,
            assigned_to=assigned_to,
            priority=priority,
            due_date=due_date
        )

        db.add(task)
        await db.commit()
        await db.refresh(task)

        logger.info(f"Task created: {title} in workspace {workspace_id}")
        return task

    async def update_task_status(self, db, task_id: int, status: str,
                                 completed_by: int = None) -> Task:
        """
        更新任务状态
        
        Args:
            db: 数据库会话
            task_id: 任务ID
            status: 新状态
            completed_by: 完成者ID（当状态为completed时）
            
        Returns:
            更新后的任务
        """
        from sqlalchemy import select

        valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}")

        stmt = select(Task).where(Task.id == task_id)
        result = await db.execute(stmt)
        task = result.scalar_one_or_none()

        if not task:
            raise ValueError("Task not found")

        task.status = status

        if status == 'completed':
            task.completed_at = datetime.now()

        await db.commit()
        await db.refresh(task)

        logger.info(f"Task {task_id} status updated to {status}")
        return task

    async def get_workspace_members(self, db, workspace_id: int) -> List[Dict[str, Any]]:
        """
        获取工作区成员列表
        
        Args:
            db: 数据库会话
            workspace_id: 工作区ID
            
        Returns:
            成员列表
        """
        from sqlalchemy import select
        from shared.models.user import User

        stmt = (
            select(WorkspaceMember, User)
            .join(User, WorkspaceMember.user_id == User.id)
            .where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.is_active == True
            )
        )

        result = await db.execute(stmt)
        rows = result.all()

        members = []
        for member, user in rows:
            members.append({
                'id': member.id,
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'role': member.role,
                'joined_at': member.joined_at.isoformat() if member.joined_at else None,
            })

        return members

    async def get_workspace_tasks(self, db, workspace_id: int,
                                  status: str = None,
                                  assigned_to: int = None,
                                  page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        获取工作区任务列表
        
        Args:
            db: 数据库会话
            workspace_id: 工作区ID
            status: 状态过滤
            assigned_to: 分配给用户过滤
            page: 页码
            per_page: 每页数量
            
        Returns:
            任务列表和分页信息
        """
        from sqlalchemy import select, func
        from shared.models.user import User

        query = select(Task).where(Task.workspace_id == workspace_id)

        if status:
            query = query.where(Task.status == status)

        if assigned_to:
            query = query.where(Task.assigned_to == assigned_to)

        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # 分页
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page).order_by(Task.created_at.desc())

        result = await db.execute(query)
        tasks = result.scalars().all()

        task_list = []
        for task in tasks:
            task_list.append({
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'assigned_to': task.assigned_to,
                'created_by': task.created_by,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                'created_at': task.created_at.isoformat() if task.created_at else None,
            })

        return {
            'tasks': task_list,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }
        }

    async def check_permission(self, db, workspace_id: int, user_id: int,
                               required_role: TeamRole = TeamRole.VIEWER) -> bool:
        """
        检查用户权限
        
        Args:
            db: 数据库会话
            workspace_id: 工作区ID
            user_id: 用户ID
            required_role: 所需角色
            
        Returns:
            是否有权限
        """
        from sqlalchemy import select

        role_hierarchy = {
            TeamRole.VIEWER.value: 1,
            TeamRole.EDITOR.value: 2,
            TeamRole.ADMIN.value: 3,
            TeamRole.OWNER.value: 4,
        }

        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.is_active == True
        )
        result = await db.execute(stmt)
        member = result.scalar_one_or_none()

        if not member:
            return False

        user_level = role_hierarchy.get(member.role, 0)
        required_level = role_hierarchy.get(required_role.value, 0)

        return user_level >= required_level


# 全局实例
collaboration_service = CollaborationService()
