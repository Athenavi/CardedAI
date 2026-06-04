"""
站内私信系统 API
提供一对一私信功能、消息列表、未读提醒等
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.private_message import PrivateMessage
from shared.models.user import User
from shared.models.user_block import UserBlock
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["private-messages"])


@router.post("/send")
async def send_private_message(
        recipient_id: int = Query(..., description="接收者ID"),
        content: str = Query(..., description="消息内容"),
        message_type: str = Query("text", description="消息类型: text/image/file"),
        attachment_url: Optional[str] = Query(None, description="附件URL"),
        parent_message_id: Optional[int] = Query(None, description="父消息ID(回复)"),
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    发送私信
    
    Args:
        recipient_id: 接收者用户ID
        content: 消息内容
        message_type: 消息类型(text/image/file)
        attachment_url: 附件URL(图片或文件)
        parent_message_id: 如果是回复消息,指定父消息ID
    """
    try:
        # 验证接收者是否存在
        user_query = select(User).where(User.id == recipient_id)
        user_result = await db.execute(user_query)
        recipient = user_result.scalar_one_or_none()

        if not recipient:
            return ApiResponse(success=False, error="接收者不存在")

        # 不能给自己发消息
        if recipient_id == current_user.id:
            return ApiResponse(success=False, error="不能给自己发送消息")

        # 检查是否被对方屏蔽
        block_check_query = select(UserBlock).where(
            and_(
                UserBlock.blocker == recipient_id,
                UserBlock.blocked_user == current_user.id
            )
        )
        block_check_result = await db.execute(block_check_query)
        is_blocked = block_check_result.scalar_one_or_none()

        if is_blocked:
            return ApiResponse(success=False, error="您已被该用户屏蔽，无法发送消息")

        # 检查是否屏蔽了对方
        my_block_query = select(UserBlock).where(
            and_(
                UserBlock.blocker == current_user.id,
                UserBlock.blocked_user == recipient_id
            )
        )
        my_block_result = await db.execute(my_block_query)
        i_blocked = my_block_result.scalar_one_or_none()

        if i_blocked:
            return ApiResponse(success=False, error="您已屏蔽该用户，请先取消屏蔽")

        # 如果指定了父消息,验证父消息存在且属于该会话
        if parent_message_id:
            parent_query = select(PrivateMessage).where(
                PrivateMessage.id == parent_message_id,
                or_(
                    and_(
                        PrivateMessage.sender == current_user.id,
                        PrivateMessage.recipient == recipient_id
                    ),
                    and_(
                        PrivateMessage.sender == recipient_id,
                        PrivateMessage.recipient == current_user.id
                    )
                )
            )
            parent_result = await db.execute(parent_query)
            parent_msg = parent_result.scalar_one_or_none()

            if not parent_msg:
                return ApiResponse(success=False, error="父消息不存在或不属于当前会话")

        # 创建新消息
        new_message = PrivateMessage(
            sender=current_user.id,
            recipient=recipient_id,
            content=content,
            message_type=message_type,
            attachment_url=attachment_url,
            parent_message=parent_message_id,
            is_read=False,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        db.add(new_message)
        await db.commit()
        await db.refresh(new_message)

        # WebSocket real-time push notification
        # Example implementation:
        # from src.api.v1.websocket import broadcast_to_user
        # 
        # notification = {
        #     'type': 'new_message',
        #     'message_id': new_message.id,
        #     'sender_id': current_user.id,
        #     'recipient_id': recipient_id,
        #     'content': content[:100],  # Preview
        #     'created_at': new_message.created_at.isoformat(),
        # }
        # 
        # await broadcast_to_user(recipient_id, notification)

        return ApiResponse(
            success=True,
            data={
                "message_id": new_message.id,
                "created_at": new_message.created_at.isoformat()
            },
            message="消息发送成功"
        )

    except Exception as e:
        import traceback
        print(f"Error in send_private_message: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/conversations")
async def get_conversations(
        page: int = Query(1, ge=1, description="页码"),
        per_page: int = Query(20, ge=1, le=100, description="每页数量"),
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取会话列表(按联系人分组,显示最新消息)
    
    返回与当前用户有过对话的所有用户及其最新消息
    """
    try:
        # 计算偏移量
        offset = (page - 1) * per_page

        # 查询所有与当前用户相关的消息的对方用户ID和最新消息时间
        # 使用子查询获取每个联系人的最新消息
        subquery = (
            select(
                func.case(
                    (PrivateMessage.sender == current_user.id, PrivateMessage.recipient),
                    else_=PrivateMessage.sender
                ).label('contact_id'),
                func.max(PrivateMessage.created_at).label('last_message_time'),
                func.count(
                    func.case(
                        (and_(
                            PrivateMessage.is_read == False,
                            PrivateMessage.recipient == current_user.id
                        ), 1),
                        else_=None
                    )
                ).label('unread_count')
            )
            .where(
                or_(
                    PrivateMessage.sender == current_user.id,
                    PrivateMessage.recipient == current_user.id
                ),
                # 排除被删除的消息
                func.case(
                    (PrivateMessage.sender == current_user.id, PrivateMessage.is_deleted_by_sender),
                    else_=PrivateMessage.is_deleted_by_recipient
                ) == False
            )
            .group_by(
                func.case(
                    (PrivateMessage.sender == current_user.id, PrivateMessage.recipient),
                    else_=PrivateMessage.sender
                )
            )
            .order_by(desc('last_message_time'))
            .offset(offset)
            .limit(per_page)
            .subquery()
        )

        # 获取总数
        count_query = select(func.count()).select_from(subquery)
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 获取联系人信息和最新消息
        query = (
            select(
                User.id,
                User.username,
                User.profile_picture,
                subquery.c.last_message_time,
                subquery.c.unread_count
            )
            .join(subquery, User.id == subquery.c.contact_id)
            .order_by(desc(subquery.c.last_message_time))
        )

        result = await db.execute(query)
        conversations = []

        for row in result.fetchall():
            conversations.append({
                "user_id": row.id,
                "username": row.username,
                "avatar": row.profile_picture,
                "last_message_time": row.last_message_time.isoformat() if row.last_message_time else None,
                "unread_count": row.unread_count or 0
            })

        return ApiResponse(
            success=True,
            data={
                "conversations": conversations,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
        )

    except Exception as e:
        import traceback
        print(f"Error in get_conversations: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/conversation/{user_id}")
async def get_conversation_messages(
        user_id: int,
        page: int = Query(1, ge=1, description="页码"),
        per_page: int = Query(50, ge=1, le=100, description="每页数量"),
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取与特定用户的对话消息历史
    
    Args:
        user_id: 对话的另一方用户ID
    """
    try:
        # 验证对方用户是否存在
        user_query = select(User).where(User.id == user_id)
        user_result = await db.execute(user_query)
        other_user = user_result.scalar_one_or_none()

        if not other_user:
            return ApiResponse(success=False, error="用户不存在")

        offset = (page - 1) * per_page

        # 查询双方之间的消息
        query = (
            select(PrivateMessage)
            .where(
                or_(
                    and_(
                        PrivateMessage.sender == current_user.id,
                        PrivateMessage.recipient == user_id,
                        PrivateMessage.is_deleted_by_sender == False
                    ),
                    and_(
                        PrivateMessage.sender == user_id,
                        PrivateMessage.recipient == current_user.id,
                        PrivateMessage.is_deleted_by_recipient == False
                    )
                )
            )
            .order_by(desc(PrivateMessage.created_at))
            .offset(offset)
            .limit(per_page)
        )

        result = await db.execute(query)
        messages = result.scalars().all()

        # 获取总数
        count_query = (
            select(func.count())
            .select_from(PrivateMessage)
            .where(
                or_(
                    and_(
                        PrivateMessage.sender == current_user.id,
                        PrivateMessage.recipient == user_id,
                        PrivateMessage.is_deleted_by_sender == False
                    ),
                    and_(
                        PrivateMessage.sender == user_id,
                        PrivateMessage.recipient == current_user.id,
                        PrivateMessage.is_deleted_by_recipient == False
                    )
                )
            )
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 标记收到的消息为已读
        unread_messages = [
            msg for msg in messages
            if msg.recipient == current_user.id and not msg.is_read
        ]

        if unread_messages:
            for msg in unread_messages:
                msg.is_read = True
                msg.read_at = datetime.now()
            await db.commit()

        # 格式化消息列表
        message_list = []
        for msg in messages:
            message_list.append({
                "id": msg.id,
                "sender_id": msg.sender,
                "recipient_id": msg.recipient,
                "content": msg.content,
                "message_type": msg.message_type,
                "attachment_url": msg.attachment_url,
                "is_read": msg.is_read,
                "created_at": msg.created_at.isoformat(),
                "is_mine": msg.sender == current_user.id
            })

        # 反转列表,使消息按时间正序排列
        message_list.reverse()

        return ApiResponse(
            success=True,
            data={
                "messages": message_list,
                "other_user": {
                    "id": other_user.id,
                    "username": other_user.username,
                    "avatar": other_user.profile_picture
                },
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
        )

    except Exception as e:
        import traceback
        print(f"Error in get_conversation_messages: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.delete("/{message_id}")
async def delete_message(
        message_id: int,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    删除消息(软删除,仅对当前用户可见)
    
    Args:
        message_id: 消息ID
    """
    try:
        # 查询消息
        query = select(PrivateMessage).where(PrivateMessage.id == message_id)
        result = await db.execute(query)
        message = result.scalar_one_or_none()

        if not message:
            return ApiResponse(success=False, error="消息不存在")

        # 验证权限:只能删除自己发送或接收的消息
        if message.sender != current_user.id and message.recipient != current_user.id:
            return ApiResponse(success=False, error="无权删除此消息")

        # 软删除
        if message.sender == current_user.id:
            message.is_deleted_by_sender = True
        else:
            message.is_deleted_by_recipient = True

        message.updated_at = datetime.now()
        await db.commit()

        return ApiResponse(success=True, message="消息已删除")

    except Exception as e:
        import traceback
        print(f"Error in delete_message: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.post("/{message_id}/recall")
async def recall_message(
        message_id: int,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    撤回消息(仅发送者可在2分钟内撤回)
    
    Args:
        message_id: 消息ID
    """
    try:
        # 查询消息
        query = select(PrivateMessage).where(PrivateMessage.id == message_id)
        result = await db.execute(query)
        message = result.scalar_one_or_none()

        if not message:
            return ApiResponse(success=False, error="消息不存在")

        # 只有发送者可以撤回
        if message.sender != current_user.id:
            return ApiResponse(success=False, error="只有发送者可以撤回消息")

        # 检查是否在2分钟内
        time_diff = (datetime.now() - message.created_at).total_seconds()
        if time_diff > 120:
            return ApiResponse(success=False, error="超过2分钟,无法撤回消息")

        # 修改内容为撤回提示
        message.content = "[消息已撤回]"
        message.message_type = "system"
        message.updated_at = datetime.now()
        await db.commit()

        # WebSocket notification for message recall
        # Example implementation:
        # from src.api.v1.websocket import broadcast_to_user
        # 
        # notification = {
        #     'type': 'message_recalled',
        #     'message_id': message_id,
        #     'sender_id': current_user.id,
        #     'recipient_id': message.recipient,
        # }
        # 
        # await broadcast_to_user(message.recipient, notification)

        return ApiResponse(success=True, message="消息已撤回")

    except Exception as e:
        import traceback
        print(f"Error in recall_message: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/unread/count")
async def get_unread_count(
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取未读消息总数
    """
    try:
        query = (
            select(func.count())
            .select_from(PrivateMessage)
            .where(
                PrivateMessage.recipient == current_user.id,
                PrivateMessage.is_read == False,
                PrivateMessage.is_deleted_by_recipient == False
            )
        )

        result = await db.execute(query)
        count = result.scalar() or 0

        return ApiResponse(
            success=True,
            data={"unread_count": count}
        )

    except Exception as e:
        import traceback
        print(f"Error in get_unread_count: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))
