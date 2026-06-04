"""通知模块"""
import json
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import select, update

from shared.models import Notification
from src.extensions import get_async_db_session as get_async_db


async def create_notification(
        recipient_id: int,
        title: str,
        content: str,
        notification_type: str = 'info',
        related_id: Optional[int] = None,
        data: Optional[Dict[str, Any]] = None
) -> Notification:
    """
    创建通知
    
    Args:
        recipient_id: 接收者ID
        title: 通知标题
        content: 通知内容
        notification_type: 通知类型 ('info', 'warning', 'error', 'success')
        related_id: 相关对象ID
        data: 额外数据
    
    Returns:
        Notification: 创建的通知对象
    """
    notification = Notification(
        recipient_id=recipient_id,
        title=title,
        content=content,
        type=notification_type,
        related_id=related_id,
        data=json.dumps(data) if data else None
    )

    # 使用数据库会话
    async for session in get_async_db():
        session.add(notification)
        await session.commit()
        await session.refresh(notification)
        notification_id = notification.id  # 保存ID以供后续使用
        break

    # 重新查询完整的通知对象
    async for session in get_async_db():
        stmt = select(Notification).filter_by(id=notification_id)
        result = await session.execute(stmt)
        notification = result.scalar_one_or_none()
        break

    # 发送邮件通知（如果用户设置了邮件通知偏好）
    # if user and user.email and user.settings.get('email_notifications', True):
    #    send_notification_email(user, title, content)

    # 尝试通过WebSocket发送实时通知
    try:
        from src.extensions import socketio, SOCKETIO_AVAILABLE
        if SOCKETIO_AVAILABLE:
            # 发送实时通知到客户端
            socketio.emit('notification', {
                'id': notification.id,
                'title': title,
                'content': content,
                'type': notification_type,
                'timestamp': notification.created_at.isoformat(),
                'read': False
            }, room=f'user_{recipient_id}')
    except Exception as e:
        # 在serverless环境中，WebSocket可能不可用，记录警告但不抛出错误
        print(f"无法发送实时通知: {str(e)}")

    return notification


async def get_user_notifications(user_id: int, unread_only: bool = False, limit: int = 20):
    """
    获取用户通知
    
    Args:
        user_id: 用户ID
        unread_only: 是否只获取未读通知
        limit: 限制数量
    
    Returns:
        list: 通知列表
    """
    async for session in get_async_db():
        stmt = select(Notification).filter_by(recipient_id=user_id).order_by(
            Notification.created_at.desc()
        )

        if unread_only:
            stmt = stmt.filter_by(is_read=False)

        if limit:
            stmt = stmt.limit(limit)

        result = await session.execute(stmt)
        return result.scalars().all()


async def mark_notification_as_read(notification_id: int, user_id: int) -> bool:
    """
    标记通知为已读
    
    Args:
        notification_id: 通知ID
        user_id: 用户ID
    
    Returns:
        bool: 是否成功
    """
    async for session in get_async_db():
        stmt = select(Notification).filter_by(
            id=notification_id,
            recipient_id=user_id
        )
        result = await session.execute(stmt)
        notification = result.scalar_one_or_none()

        if notification and not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now()
            await session.commit()
            return True

    return False


async def mark_all_notifications_as_read(user_id: int) -> int:
    """
    标记所有通知为已读
    
    Args:
        user_id: 用户ID
    
    Returns:
        int: 更新的通知数量
    """
    async for session in get_async_db():
        stmt = update(Notification).where(
            Notification.recipient_id == user_id,
            Notification.is_read == False
        ).values(
            is_read=True,
            read_at=datetime.now()
        )

        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount


async def delete_notification(notification_id: int, user_id: int) -> bool:
    """
    删除通知
    
    Args:
        notification_id: 通知ID
        user_id: 用户ID
    
    Returns:
        bool: 是否成功
    """
    async for session in get_async_db():
        stmt = select(Notification).filter_by(
            id=notification_id,
            recipient_id=user_id
        )
        result = await session.execute(stmt)
        notification = result.scalar_one_or_none()

        if notification:
            await session.delete(notification)
            await session.commit()
            return True

    return False


async def get_unread_count(user_id: int) -> int:
    """
    获取未读通知数量
    
    Args:
        user_id: 用户ID
    
    Returns:
        int: 未读通知数量
    """
    async for session in get_async_db():
        from sqlalchemy import func
        stmt = select(func.count()).select_from(Notification).filter_by(
            recipient_id=user_id,
            is_read=False
        )
        result = await session.execute(stmt)
        return result.scalar()
