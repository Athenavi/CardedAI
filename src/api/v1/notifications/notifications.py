"""
通知相关API - 处理用户通知功能
"""
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.notification import Notification
from shared.models.user import User
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db
from src.notification import mark_notification_as_read, get_user_notifications, mark_all_notifications_as_read

router = APIRouter(tags=["notifications"])


@router.post("/messages/read")
async def read_notification_api(
        nid: int = Query(..., alias="nid"),
        current_user: User = Depends(jwt_required)
):
    """
    标记通知为已读API
    """
    try:
        result = mark_notification_as_read(current_user.id, nid)
        return result
    except Exception as e:
        import traceback
        print(f"Error in read_notification_api: {str(e)}")
        print(traceback.format_exc())
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@router.get("/messages")
async def fetch_message_api(
        current_user: User = Depends(jwt_required)
):
    """
    获取用户通知API
    """
    try:
        result = get_user_notifications(current_user.id)
        return result
    except Exception as e:
        import traceback
        print(f"Error in fetch_message_api: {str(e)}")
        print(traceback.format_exc())
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@router.post("/messages/read_all")
async def mark_all_as_read_api(
        current_user: User = Depends(jwt_required)
):
    """
    标记所有通知为已读API
    """
    try:
        result = mark_all_notifications_as_read(current_user.id)
        return result
    except Exception as e:
        import traceback
        print(f"Error in mark_all_as_read_api: {str(e)}")
        print(traceback.format_exc())
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@router.delete("/messages/clean")
async def clean_notification_api(
        request: Request,
        nid: str = Query("all", alias="nid"),
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    清理通知API
    """
    try:
        from sqlalchemy import delete
        if nid == 'all':
            stmt = delete(Notification).where(Notification.recipient_id == current_user.id)
            await db.execute(stmt)
        else:
            stmt = delete(Notification).where(
                Notification.recipient_id == current_user.id,
                Notification.id == int(nid)
            )
            await db.execute(stmt)
        await db.commit()
        return {"success": True}
    except Exception as e:
        import traceback
        print(f"Error in clean_notification_api: {str(e)}")
        print(traceback.format_exc())
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@router.patch("/{notification_id}/read")
async def mark_notification_as_read_api(
        notification_id: int,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    标记通知为已读API (新格式)
    """
    try:
        from src.notification import mark_notification_as_read
        # 注意：mark_notification_as_read 函数的参数顺序是 (notification_id, user_id)
        success = mark_notification_as_read(notification_id, current_user.id)
        if success:
            return {"success": True, "message": "通知已标记为已读"}
        else:
            return JSONResponse({"success": False, "error": "无法标记通知为已读"}, status_code=400)
    except Exception as e:
        import traceback
        print(f"Error in mark_notification_as_read_api: {str(e)}")
        print(traceback.format_exc())
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@router.delete("/{notification_id}")
async def delete_notification_api(
        notification_id: int,
        current_user: User = Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    删除通知API
    """
    try:
        from src.notification import delete_notification
        success = delete_notification(notification_id, current_user.id)
        if success:
            return {"success": True, "message": "通知已删除"}
        else:
            return JSONResponse({"success": False, "error": "无法删除通知"}, status_code=400)
    except Exception as e:
        import traceback
        print(f"Error in delete_notification_api: {str(e)}")
        print(traceback.format_exc())
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@router.get("/")
async def get_notifications_api(
        current_user: User = Depends(jwt_required)
):
    """
    获取用户通知API
    """
    try:
        notifications = await get_user_notifications(current_user.id)

        # 转换通知数据为前端期望的格式
        notification_list = []
        for notif in notifications:
            notification_list.append({
                "id": notif.id,
                "title": notif.title,
                "content": notif.message,
                "date": notif.created_at.isoformat(),
                "type": notif.type,
                "read": notif.is_read,
                "avatar": f"/avatars/user_{current_user.id}.jpg",  # 使用用户头像
                "sender": "System",  # 系统通知
                "recipient": current_user.id
            })

        return {"success": True, "data": notification_list}
    except Exception as e:
        import traceback
        print(f"Error in get_notifications_api: {str(e)}")
        print(traceback.format_exc())
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)