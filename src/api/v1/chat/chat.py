"""
聊天 API
支持群聊和私聊的消息管理
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy import select, desc, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required
from src.utils.database.main import get_async_session

router = APIRouter(tags=["chat"])


@router.get("/groups", summary="获取用户的群聊列表")
async def get_user_groups(
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取用户加入的所有群聊
    
    Returns:
        群聊列表，包含未读消息数等信息
    """
    try:
        from shared.models.chat_group import ChatGroup
        from shared.models.chat_group_member import ChatGroupMember
        from shared.models.private_message import PrivateMessage

        # 获取用户加入的群聊
        member_query = select(ChatGroupMember).where(
            ChatGroupMember.user == current_user.id
        )
        member_result = await db.execute(member_query)
        memberships = member_result.scalars().all()

        group_ids = [m.group for m in memberships]

        if not group_ids:
            return ApiResponse(success=True, data={'groups': [], 'count': 0})

        # 获取群聊详情
        groups_query = select(ChatGroup).where(ChatGroup.id.in_(group_ids))
        groups_result = await db.execute(groups_query)
        groups = groups_result.scalars().all()

        groups_data = []
        for group in groups:
            # 计算未读消息数
            unread_query = select(func.count(PrivateMessage.id)).where(
                and_(
                    PrivateMessage.group == group.id,
                    PrivateMessage.sender != current_user.id,
                    or_(
                        PrivateMessage.is_read == False,
                        PrivateMessage.is_read == None
                    )
                )
            )
            unread_result = await db.execute(unread_query)
            unread_count = unread_result.scalar() or 0

            # 获取在线成员数
            online_query = select(func.count(ChatGroupMember.id)).where(
                ChatGroupMember.group == group.id
            )
            online_result = await db.execute(online_query)
            member_count = online_result.scalar() or 0

            groups_data.append({
                'id': group.id,
                'name': group.name,
                'description': group.description,
                'avatar_url': group.avatar_url,
                'member_count': member_count,
                'unread_count': unread_count,
                'last_message_at': group.last_message_at.isoformat() if group.last_message_at else None,
                'created_at': group.created_at.isoformat(),
            })

        # 按最后消息时间排序
        groups_data.sort(key=lambda x: x['last_message_at'] or '', reverse=True)

        return ApiResponse(
            success=True,
            data={
                'groups': groups_data,
                'count': len(groups_data),
            }
        )
    except Exception as e:
        import traceback
        print(f"Error getting user groups: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=f"获取群聊列表失败: {str(e)}")


@router.get("/groups/{group_id}/messages", summary="获取群聊消息历史")
async def get_group_messages(
        group_id: int,
        limit: int = Query(50, ge=1, le=100, description="返回数量"),
        offset: int = Query(0, ge=0, description="偏移量"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取群聊的历史消息
    
    Args:
        group_id: 群聊ID
        limit: 返回数量
        offset: 偏移量
        
    Returns:
        消息列表
    """
    try:
        from shared.models.private_message import PrivateMessage
        from shared.models.user import User
        from shared.models.chat_group_member import ChatGroupMember

        # 验证用户是否是群聊成员
        member_query = select(ChatGroupMember).where(
            and_(
                ChatGroupMember.group == group_id,
                ChatGroupMember.user == current_user.id
            )
        )
        member_result = await db.execute(member_query)
        member = member_result.scalar_one_or_none()

        if not member:
            return ApiResponse(success=False, error="您不是该群聊的成员")

        # 获取消息列表
        messages_query = select(PrivateMessage).where(
            PrivateMessage.group == group_id
        ).order_by(
            desc(PrivateMessage.created_at)
        ).limit(limit).offset(offset)

        messages_result = await db.execute(messages_query)
        messages = messages_result.scalars().all()

        # 获取发送者信息
        sender_ids = list(set([msg.sender for msg in messages]))
        users_query = select(User).where(User.id.in_(sender_ids))
        users_result = await db.execute(users_query)
        users = {user.id: user for user in users_result.scalars().all()}

        messages_data = []
        for msg in messages:
            sender = users.get(msg.sender)
            messages_data.append({
                'id': msg.id,
                'sender_id': msg.sender,
                'sender_name': sender.username if sender else 'Unknown',
                'sender_avatar': sender.profile_picture if sender else None,
                'content': msg.content,
                'message_type': msg.message_type,
                'attachment_url': msg.attachment_url,
                'parent_message': msg.parent_message,
                'is_read': msg.is_read,
                'created_at': msg.created_at.isoformat(),
            })

        # 反转顺序（最新的在最后）
        messages_data.reverse()

        return ApiResponse(
            success=True,
            data={
                'messages': messages_data,
                'count': len(messages_data),
                'has_more': len(messages_data) == limit,
            }
        )
    except Exception as e:
        import traceback
        print(f"Error getting group messages: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=f"获取消息历史失败: {str(e)}")


@router.get("/private/{user_id}", summary="获取与某用户的私聊消息")
async def get_private_messages(
        user_id: int,
        limit: int = Query(50, ge=1, le=100, description="返回数量"),
        offset: int = Query(0, ge=0, description="偏移量"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取与指定用户的私聊历史
    
    Args:
        user_id: 对方用户ID
        limit: 返回数量
        offset: 偏移量
        
    Returns:
        私聊消息列表
    """
    try:
        from shared.models.private_message import PrivateMessage
        from shared.models.user import User

        # 获取私聊消息（双方之间的所有消息）
        messages_query = select(PrivateMessage).where(
            or_(
                and_(
                    PrivateMessage.sender == current_user.id,
                    PrivateMessage.recipient == user_id
                ),
                and_(
                    PrivateMessage.sender == user_id,
                    PrivateMessage.recipient == current_user.id
                )
            )
        ).order_by(
            desc(PrivateMessage.created_at)
        ).limit(limit).offset(offset)

        messages_result = await db.execute(messages_query)
        messages = messages_result.scalars().all()

        # 获取对方用户信息
        user_query = select(User).where(User.id == user_id)
        user_result = await db.execute(user_query)
        other_user = user_result.scalar_one_or_none()

        messages_data = []
        for msg in messages:
            is_me = msg.sender == current_user.id
            messages_data.append({
                'id': msg.id,
                'sender_id': msg.sender,
                'is_me': is_me,
                'content': msg.content,
                'message_type': msg.message_type,
                'attachment_url': msg.attachment_url,
                'parent_message': msg.parent_message,
                'is_read': msg.is_read,
                'created_at': msg.created_at.isoformat(),
            })

        # 反转顺序
        messages_data.reverse()

        return ApiResponse(
            success=True,
            data={
                'messages': messages_data,
                'other_user': {
                    'id': other_user.id,
                    'username': other_user.username,
                    'avatar': other_user.profile_picture,
                } if other_user else None,
                'count': len(messages_data),
                'has_more': len(messages_data) == limit,
            }
        )
    except Exception as e:
        import traceback
        print(f"Error getting private messages: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=f"获取私聊消息失败: {str(e)}")


@router.post("/private/{user_id}/send", summary="发送私聊消息")
async def send_private_message(
        user_id: int,
        content: str = Body(..., description="消息内容"),
        message_type: str = Body('text', description="消息类型"),
        attachment_url: Optional[str] = Body(None, description="附件URL"),
        parent_message: Optional[int] = Body(None, description="回复的消息ID"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    """
    发送私聊消息
    
    Args:
        user_id: 接收者用户ID
        content: 消息内容
        message_type: 消息类型 (text/image/file)
        attachment_url: 附件URL
        parent_message: 回复的消息ID
        
    Returns:
        发送结果
    """
    try:
        from shared.models.private_message import PrivateMessage
        from shared.models.user import User
        from datetime import datetime

        # 验证接收者存在
        user_query = select(User).where(User.id == user_id)
        user_result = await db.execute(user_query)
        recipient = user_result.scalar_one_or_none()

        if not recipient:
            return ApiResponse(success=False, error="用户不存在")

        # 不能给自己发消息
        if user_id == current_user.id:
            return ApiResponse(success=False, error="不能给自己发送消息")

        # 创建消息
        message = PrivateMessage(
            sender=current_user.id,
            recipient=user_id,
            group=None,
            content=content,
            message_type=message_type,
            attachment_url=attachment_url,
            parent_message=parent_message,
            is_read=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        db.add(message)
        await db.commit()
        await db.refresh(message)

        return ApiResponse(
            success=True,
            data={
                'message': '消息发送成功',
                'message_id': message.id,
            }
        )
    except Exception as e:
        await db.rollback()
        import traceback
        print(f"Error sending private message: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=f"发送消息失败: {str(e)}")


@router.get("/unread-count", summary="获取未读消息总数")
async def get_unread_count(
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取用户的未读消息总数（包括群聊和私聊）
    
    Returns:
        未读消息统计
    """
    try:
        from shared.models.private_message import PrivateMessage

        # 私聊未读数
        private_unread_query = select(func.count(PrivateMessage.id)).where(
            and_(
                PrivateMessage.recipient == current_user.id,
                PrivateMessage.group == None,
                or_(
                    PrivateMessage.is_read == False,
                    PrivateMessage.is_read == None
                )
            )
        )
        private_unread_result = await db.execute(private_unread_query)
        private_unread = private_unread_result.scalar() or 0

        # 群聊未读数
        group_unread_query = select(func.count(PrivateMessage.id)).where(
            and_(
                PrivateMessage.group != None,
                PrivateMessage.sender != current_user.id,
                or_(
                    PrivateMessage.is_read == False,
                    PrivateMessage.is_read == None
                )
            )
        )
        group_unread_result = await db.execute(group_unread_query)
        group_unread = group_unread_result.scalar() or 0

        return ApiResponse(
            success=True,
            data={
                'private_unread': private_unread,
                'group_unread': group_unread,
                'total_unread': private_unread + group_unread,
            }
        )
    except Exception as e:
        import traceback
        print(f"Error getting unread count: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=f"获取未读数失败: {str(e)}")


@router.post("/messages/{message_id}/read", summary="标记消息为已读")
async def mark_message_read(
        message_id: int,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    """
    标记消息为已读
    
    Args:
        message_id: 消息ID
        
    Returns:
        操作结果
    """
    try:
        from shared.models.private_message import PrivateMessage
        from datetime import datetime

        message_query = select(PrivateMessage).where(PrivateMessage.id == message_id)
        message_result = await db.execute(message_query)
        message = message_result.scalar_one_or_none()

        if not message:
            return ApiResponse(success=False, error="消息不存在")

        # 只能标记发给自己的消息
        if message.recipient != current_user.id and message.group is None:
            return ApiResponse(success=False, error="无权操作此消息")

        message.is_read = True
        message.read_at = datetime.now()
        message.updated_at = datetime.now()

        await db.commit()

        return ApiResponse(success=True, data={'message': '已标记为已读'})
    except Exception as e:
        await db.rollback()
        import traceback
        print(f"Error marking message as read: {e}\n{traceback.format_exc()}")
        return ApiResponse(success=False, error=f"操作失败: {str(e)}")
