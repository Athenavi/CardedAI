"""
群聊管理 API
提供创建群聊、添加成员、删除成员等功能
"""
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.chat_group import ChatGroup
from shared.models.chat_group_invite import ChatGroupInvite
from shared.models.chat_group_member import ChatGroupMember
from shared.models.user import User
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["chat-groups"])


class CreateGroupRequest(BaseModel):
    """创建群聊请求"""
    name: str
    description: Optional[str] = None
    member_ids: List[int] = []  # 初始成员ID列表


class AddMembersRequest(BaseModel):
    """添加成员请求"""
    member_ids: List[int]


@router.post("/")
async def create_chat_group(
        request: CreateGroupRequest,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    创建群聊
    
    Args:
        name: 群聊名称
        description: 群聊描述（可选）
        member_ids: 初始成员ID列表（不包括创建者，创建者自动加入）
    """
    try:
        # 验证群聊名称
        if not request.name or len(request.name.strip()) == 0:
            return ApiResponse(success=False, error="群聊名称不能为空")

        if len(request.name) > 255:
            return ApiResponse(success=False, error="群聊名称不能超过255个字符")

        # 创建群聊
        new_group = ChatGroup(
            name=request.name.strip(),
            description=request.description,
            creator=current_user.id,  # 直接传入user_id整数
            member_count=1,  # 创建者自己
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        db.add(new_group)
        await db.flush()  # 获取群聊ID

        # 添加创建者为owner
        owner_member = ChatGroupMember(
            group=new_group.id,
            user=current_user.id,
            role='owner',
            joined_at=datetime.now()
        )
        db.add(owner_member)

        # 添加其他成员
        if request.member_ids:
            # 验证成员是否存在
            users_query = select(User).where(User.id.in_(request.member_ids))
            users_result = await db.execute(users_query)
            existing_users = users_result.scalars().all()
            existing_user_ids = {user.id for user in existing_users}

            # 过滤掉不存在的用户和重复的用户
            valid_member_ids = [
                uid for uid in request.member_ids
                if uid != current_user.id and uid in existing_user_ids
            ]

            for user_id in valid_member_ids:
                member = ChatGroupMember(
                    group=new_group.id,
                    user=user_id,
                    role='member',
                    joined_at=datetime.now()
                )
                db.add(member)

            # 更新成员数量
            new_group.member_count = 1 + len(valid_member_ids)

        await db.commit()
        await db.refresh(new_group)

        return ApiResponse(
            success=True,
            data={
                "group_id": new_group.id,
                "name": new_group.name,
                "member_count": new_group.member_count,
                "created_at": new_group.created_at.isoformat()
            },
            message="群聊创建成功"
        )

    except Exception as e:
        import traceback
        print(f"Error in create_chat_group: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/")
async def get_user_groups(
        page: int = Query(1, ge=1, description="页码"),
        per_page: int = Query(20, ge=1, le=100, description="每页数量"),
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取当前用户的群聊列表
    """
    try:
        print(f"[ChatGroup] Getting groups for user {current_user.id}")
        offset = (page - 1) * per_page

        # 查询用户加入的群聊
        query = (
            select(ChatGroup)
            .join(ChatGroupMember, ChatGroup.id == ChatGroupMember.group)
            .where(
                and_(
                    ChatGroupMember.user == current_user.id,
                    ChatGroup.is_active == True
                )
            )
            .order_by(
                ChatGroup.last_message_at.desc().nullslast()
            )
            .offset(offset)
            .limit(per_page)
        )

        result = await db.execute(query)
        groups = result.scalars().all()

        print(f"[ChatGroup] Found {len(groups)} groups for user {current_user.id}")
        for g in groups:
            print(f"  - Group: {g.name} (id={g.id})")

        # 获取总数
        count_query = (
            select(func.count())
            .select_from(ChatGroup)
            .join(ChatGroupMember, ChatGroup.id == ChatGroupMember.group)
            .where(
                and_(
                    ChatGroupMember.user == current_user.id,
                    ChatGroup.is_active == True
                )
            )
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar()

        groups_data = []
        for group in groups:
            groups_data.append({
                "id": group.id,
                "name": group.name,
                "description": group.description,
                "avatar": group.avatar,
                "member_count": group.member_count,
                "last_message_at": group.last_message_at.isoformat() if group.last_message_at else None,
                "created_at": group.created_at.isoformat()
            })

        return ApiResponse(
            success=True,
            data={
                "groups": groups_data,
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page
            }
        )

    except Exception as e:
        import traceback
        print(f"Error in get_user_groups: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/{group_id}/members")
async def add_group_members(
        group_id: int,
        request: AddMembersRequest,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    添加群聊成员
    
    Args:
        group_id: 群聊ID
        member_ids: 要添加的成员ID列表
    """
    try:
        # 检查群聊是否存在
        group_query = select(ChatGroup).where(ChatGroup.id == group_id)
        group_result = await db.execute(group_query)
        group = group_result.scalar_one_or_none()

        if not group:
            return ApiResponse(success=False, error="群聊不存在")

        # 检查当前用户是否是群聊成员
        member_query = select(ChatGroupMember).where(
            and_(
                ChatGroupMember.group == group_id,
                ChatGroupMember.user == current_user.id
            )
        )
        member_result = await db.execute(member_query)
        current_member = member_result.scalar_one_or_none()

        if not current_member:
            return ApiResponse(success=False, error="您不是该群聊的成员")

        # 只有owner和admin可以添加成员
        if current_member.role not in ['owner', 'admin']:
            return ApiResponse(success=False, error="只有群主和管理员可以添加成员")

        # 验证要添加的用户是否存在
        users_query = select(User).where(User.id.in_(request.member_ids))
        users_result = await db.execute(users_query)
        existing_users = users_result.scalars().all()
        existing_user_ids = {user.id for user in existing_users}

        # 获取当前群聊的所有成员ID
        existing_members_query = select(ChatGroupMember.user).where(
            ChatGroupMember.group == group_id
        )
        existing_members_result = await db.execute(existing_members_query)
        existing_member_ids = {row[0] for row in existing_members_result.all()}

        # 过滤出需要添加的成员（排除已存在的和不存在的用户）
        new_member_ids = [
            uid for uid in request.member_ids
            if uid in existing_user_ids and uid not in existing_member_ids
        ]

        if not new_member_ids:
            return ApiResponse(success=False, error="没有可添加的成员")

        # 添加新成员
        added_count = 0
        for user_id in new_member_ids:
            new_member = ChatGroupMember(
                group=group_id,
                user=user_id,
                role='member',
                joined_at=datetime.now()
            )
            db.add(new_member)
            added_count += 1

        # 更新群聊成员数量
        group.member_count += added_count
        group.updated_at = datetime.now()

        await db.commit()

        return ApiResponse(
            success=True,
            data={
                "added_count": added_count,
                "new_member_count": group.member_count
            },
            message=f"成功添加 {added_count} 名成员"
        )

    except Exception as e:
        import traceback
        print(f"Error in add_group_members: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.delete("/{group_id}/members/{user_id}")
async def remove_group_member(
        group_id: int,
        user_id: int,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    移除群聊成员
    """
    try:
        # 检查群聊是否存在
        group_query = select(ChatGroup).where(ChatGroup.id == group_id)
        group_result = await db.execute(group_query)
        group = group_result.scalar_one_or_none()

        if not group:
            return ApiResponse(success=False, error="群聊不存在")

        # 检查当前用户权限
        member_query = select(ChatGroupMember).where(
            and_(
                ChatGroupMember.group == group_id,
                ChatGroupMember.user == current_user.id
            )
        )
        member_result = await db.execute(member_query)
        current_member = member_result.scalar_one_or_none()

        if not current_member:
            return ApiResponse(success=False, error="您不是该群聊的成员")

        # 只能移除自己，或者owner/admin可以移除其他人
        if user_id != current_user.id and current_member.role not in ['owner', 'admin']:
            return ApiResponse(success=False, error="您没有权限移除该成员")

        # 不能移除owner（除非是owner自己离开）
        target_member_query = select(ChatGroupMember).where(
            and_(
                ChatGroupMember.group == group_id,
                ChatGroupMember.user == user_id
            )
        )
        target_member_result = await db.execute(target_member_query)
        target_member = target_member_result.scalar_one_or_none()

        if not target_member:
            return ApiResponse(success=False, error="该用户不是群聊成员")

        if target_member.role == 'owner' and user_id != current_user.id:
            return ApiResponse(success=False, error="不能移除群主")

        # 移除成员
        await db.delete(target_member)

        # 更新成员数量
        group.member_count -= 1
        group.updated_at = datetime.now()

        await db.commit()

        return ApiResponse(
            success=True,
            data={
                "remaining_members": group.member_count
            },
            message="成员移除成功"
        )

    except Exception as e:
        import traceback
        print(f"Error in remove_group_member: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/{group_id}/members")
async def get_group_members(
        group_id: int,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取群聊成员列表
    """
    try:
        # 检查当前用户是否是群聊成员
        member_query = select(ChatGroupMember).where(
            and_(
                ChatGroupMember.group == group_id,
                ChatGroupMember.user == current_user.id
            )
        )
        member_result = await db.execute(member_query)
        current_member = member_result.scalar_one_or_none()

        if not current_member:
            return ApiResponse(success=False, error="您不是该群聊的成员")

        # 获取所有成员
        members_query = (
            select(ChatGroupMember, User)
            .join(User, ChatGroupMember.user == User.id)
            .where(ChatGroupMember.group == group_id)
            .order_by(
                ChatGroupMember.role.desc(),
                ChatGroupMember.joined_at.asc()
            )
        )

        members_result = await db.execute(members_query)
        members = members_result.all()

        members_data = []
        for member, user in members:
            members_data.append({
                "id": member.id,
                "user_id": user.id,
                "username": user.username,
                "nickname": user.nickname,
                "avatar": user.avatar,
                "role": member.role,
                "joined_at": member.joined_at.isoformat(),
                "is_muted": member.is_muted
            })

        return ApiResponse(
            success=True,
            data=members_data
        )

    except Exception as e:
        import traceback
        print(f"Error in get_group_members: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/{group_id}/create-invite")
async def create_invite_link(
        group_id: int,
        expires_hours: Optional[int] = Query(None, description="过期时间（小时），null表示永久有效"),
        max_uses: Optional[int] = Query(None, description="最大使用次数，null表示无限制"),
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    创建群聊邀请链接
    
    Args:
        group_id: 群聊ID
        expires_hours: 过期时间（小时）
        max_uses: 最大使用次数
    """
    try:
        # 检查群聊是否存在
        group_query = select(ChatGroup).where(ChatGroup.id == group_id)
        group_result = await db.execute(group_query)
        group = group_result.scalar_one_or_none()

        if not group:
            return ApiResponse(success=False, error="群聊不存在")

        # 检查当前用户是否是群聊成员且有权限
        member_query = select(ChatGroupMember).where(
            and_(
                ChatGroupMember.group == group_id,
                ChatGroupMember.user == current_user.id
            )
        )
        member_result = await db.execute(member_query)
        current_member = member_result.scalar_one_or_none()

        if not current_member:
            return ApiResponse(success=False, error="您不是该群聊的成员")

        # 只有owner和admin可以创建邀请链接
        if current_member.role not in ['owner', 'admin']:
            return ApiResponse(success=False, error="只有群主和管理员可以创建邀请链接")

        # 生成邀请码
        import uuid
        invite_code = str(uuid.uuid4())

        # 计算过期时间
        from datetime import timedelta
        expires_at = None
        if expires_hours:
            expires_at = datetime.now() + timedelta(hours=expires_hours)

        # 创建邀请记录
        new_invite = ChatGroupInvite(
            group=group_id,
            invite_code=invite_code,
            created_by=current_user.id,
            expires_at=expires_at,
            max_uses=max_uses,
            use_count=0,
            is_active=True,
            created_at=datetime.now()
        )

        db.add(new_invite)
        await db.commit()
        await db.refresh(new_invite)

        # 构建邀请链接
        invite_url = f"/join-group/{invite_code}"

        return ApiResponse(
            success=True,
            data={
                "invite_id": new_invite.id,
                "invite_code": invite_code,
                "invite_url": invite_url,
                "full_url": f"http://localhost:3000{invite_url}",  # 根据实际域名调整
                "expires_at": new_invite.expires_at.isoformat() if new_invite.expires_at else None,
                "max_uses": new_invite.max_uses,
                "created_at": new_invite.created_at.isoformat()
            },
            message="邀请链接创建成功"
        )

    except Exception as e:
        import traceback
        print(f"Error in create_invite_link: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/join/{invite_code}")
async def join_group_by_invite(
        invite_code: str,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    通过邀请链接加入群聊
    
    Args:
        invite_code: 邀请码
    """
    try:
        # 查找邀请记录
        invite_query = select(ChatGroupInvite).where(
            and_(
                ChatGroupInvite.invite_code == invite_code,
                ChatGroupInvite.is_active == True
            )
        )
        invite_result = await db.execute(invite_query)
        invite = invite_result.scalar_one_or_none()

        if not invite:
            return ApiResponse(success=False, error="邀请链接无效或已失效")

        # 检查是否过期
        if invite.expires_at and datetime.now() > invite.expires_at:
            return ApiResponse(success=False, error="邀请链接已过期")

        # 检查使用次数
        if invite.max_uses and invite.use_count >= invite.max_uses:
            return ApiResponse(success=False, error="邀请链接已达到最大使用次数")

        # 检查用户是否已经是群聊成员
        member_query = select(ChatGroupMember).where(
            and_(
                ChatGroupMember.group == invite.group,
                ChatGroupMember.user == current_user.id
            )
        )
        member_result = await db.execute(member_query)
        existing_member = member_result.scalar_one_or_none()

        if existing_member:
            return ApiResponse(success=False, error="您已经是该群聊的成员")

        # 获取群聊信息
        group_query = select(ChatGroup).where(ChatGroup.id == invite.group)
        group_result = await db.execute(group_query)
        group = group_result.scalar_one_or_none()

        if not group or not group.is_active:
            return ApiResponse(success=False, error="群聊不存在或已解散")

        # 添加用户到群聊
        new_member = ChatGroupMember(
            group=invite.group,
            user=current_user.id,
            role='member',
            joined_at=datetime.now()
        )
        db.add(new_member)

        # 更新邀请使用次数
        invite.use_count += 1

        # 更新群聊成员数量
        group.member_count += 1
        group.updated_at = datetime.now()

        await db.commit()

        return ApiResponse(
            success=True,
            data={
                "group_id": group.id,
                "group_name": group.name,
                "member_count": group.member_count
            },
            message=f"成功加入群聊：{group.name}"
        )

    except Exception as e:
        import traceback
        print(f"Error in join_group_by_invite: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/{group_id}/invites")
async def get_group_invites(
        group_id: int,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取群聊的所有邀请链接
    """
    try:
        # 检查当前用户是否是群聊成员
        member_query = select(ChatGroupMember).where(
            and_(
                ChatGroupMember.group == group_id,
                ChatGroupMember.user == current_user.id
            )
        )
        member_result = await db.execute(member_query)
        current_member = member_result.scalar_one_or_none()

        if not current_member:
            return ApiResponse(success=False, error="您不是该群聊的成员")

        # 获取所有邀请链接
        invites_query = (
            select(ChatGroupInvite)
            .where(ChatGroupInvite.group == group_id)
            .order_by(desc(ChatGroupInvite.created_at))
        )

        invites_result = await db.execute(invites_query)
        invites = invites_result.scalars().all()

        invites_data = []
        for invite in invites:
            invites_data.append({
                "id": invite.id,
                "invite_code": invite.invite_code,
                "invite_url": f"/join-group/{invite.invite_code}",
                "created_by": invite.created_by,
                "expires_at": invite.expires_at.isoformat() if invite.expires_at else None,
                "max_uses": invite.max_uses,
                "use_count": invite.use_count,
                "is_active": invite.is_active,
                "created_at": invite.created_at.isoformat()
            })

        return ApiResponse(
            success=True,
            data=invites_data
        )

    except Exception as e:
        import traceback
        print(f"Error in get_group_invites: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/{group_id}/revoke-invite")
async def revoke_invite(
        group_id: int,
        invite_id: int = Query(..., description="邀请ID"),
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    撤销邀请链接
    """
    try:
        # 检查当前用户权限
        member_query = select(ChatGroupMember).where(
            and_(
                ChatGroupMember.group == group_id,
                ChatGroupMember.user == current_user.id
            )
        )
        member_result = await db.execute(member_query)
        current_member = member_result.scalar_one_or_none()

        if not current_member or current_member.role not in ['owner', 'admin']:
            return ApiResponse(success=False, error="您没有权限撤销邀请链接")

        # 查找邀请记录
        invite_query = select(ChatGroupInvite).where(
            and_(
                ChatGroupInvite.id == invite_id,
                ChatGroupInvite.group == group_id
            )
        )
        invite_result = await db.execute(invite_query)
        invite = invite_result.scalar_one_or_none()

        if not invite:
            return ApiResponse(success=False, error="邀请链接不存在")

        # 撤销邀请
        invite.is_active = False
        await db.commit()

        return ApiResponse(
            success=True,
            message="邀请链接已撤销"
        )

    except Exception as e:
        import traceback
        print(f"Error in revoke_invite: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))
