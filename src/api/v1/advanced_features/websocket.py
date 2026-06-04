"""
实时协作 WebSocket API
"""
from typing import Optional

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from shared.services.chat.collaboration import collaboration_service, Step
from src.api.v1.collaboration.collaboration_invites import invitations_db
from src.setting import settings

router = APIRouter(tags=["websocket"])


def verify_token_from_cookie(cookie: str) -> Optional[int]:
    """从cookie中验证token并返回user_id"""
    if not cookie:
        print("[WebSocket] No cookie provided")
        return None

    try:
        # 解析cookie获取access_token
        cookies = cookie.split(';')
        access_token = None
        for c in cookies:
            parts = c.strip().split('=', 1)
            if len(parts) == 2:
                name, value = parts
                if name.strip() == 'access_token':
                    access_token = value.strip()
                    break

        if not access_token:
            print("[WebSocket] No access_token found in cookie")
            print(f"[WebSocket] Cookie content: {cookie}")
            return None

        print(f"[WebSocket] Found access_token: {access_token[:20]}...")

        # 解码JWT token
        payload = jwt.decode(
            access_token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        user_id = payload.get('user_id')
        print(f"[WebSocket] Token verified, user_id: {user_id}")
        return user_id
    except jwt.ExpiredSignatureError:
        print("[WebSocket] Token expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"[WebSocket] Invalid token: {e}")
        return None
    except Exception as e:
        print(f"[WebSocket] Token verification failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


@router.websocket("/collaborate/{invite_id}")
async def collaborate_websocket(
        websocket: WebSocket,
        invite_id: str,
        token: Optional[str] = Query(None, description="认证token")
):
    """
    实时协作编辑 WebSocket
    
    Args:
        websocket: WebSocket 连接
        invite_id: 邀请ID（UUID）
        token: 认证token（通过URL参数传递）
    """
    # 验证用户身份
    user_id = None

    if token:
        try:
            # 解码JWT token
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"]
            )
            # JWT token中使用'sub'字段存储user_id
            user_id = payload.get('sub') or payload.get('user_id')
            if user_id:
                user_id = int(user_id)  # 确保是整数
            print(f"[WebSocket] Token verified from URL param, payload: {payload}, user_id: {user_id}")
        except jwt.ExpiredSignatureError:
            print("[WebSocket] Token expired")
        except jwt.InvalidTokenError as e:
            print(f"[WebSocket] Invalid token: {e}")
        except Exception as e:
            print(f"[WebSocket] Token verification failed: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("[WebSocket] No token provided in URL")

    if not user_id:
        # 认证失败，关闭连接
        await websocket.close(code=4003, reason="Authentication required")
        return

    print(f"[WebSocket] User {user_id} connecting to invite {invite_id}")

    # 接受WebSocket连接（必须先accept才能发送消息）
    await websocket.accept()
    print(f"[WebSocket] Connection accepted for user {user_id}")

    invitation = invitations_db.get(invite_id)

    if not invitation:
        print(f"[WebSocket] Invitation {invite_id} not found")
        await websocket.close(code=4004, reason="Invitation not found")
        return

    # 检查邀请是否过期
    from datetime import datetime
    if datetime.now() > invitation["expires_at"]:
        print(f"[WebSocket] Invitation {invite_id} expired")
        await websocket.close(code=4010, reason="Invitation expired")
        return

    article_id = invitation.get("article_id")
    if not article_id:
        print(f"[WebSocket] No article_id in invitation {invite_id}")
        await websocket.close(code=4005, reason="Invalid invitation")
        return

    print(f"[WebSocket] Invite {invite_id} maps to article {article_id}")

    # 获取或创建协作文档（使用invite_id作为文档ID）
    doc = collaboration_service.get_or_create_document(invite_id)
    doc.article_id = article_id  # 设置文章ID

    # 如果是新创建的文档，从数据库加载初始内容
    if not doc.content:
        try:
            from shared.models.article_content import ArticleContent
            from sqlalchemy import select
            from src.utils.database.unified_manager import db_manager

            async with db_manager.get_session() as db_session:
                content_query = select(ArticleContent).where(
                    ArticleContent.article == article_id
                )
                result = await db_session.execute(content_query)
                content_obj = result.scalar_one_or_none()

                if content_obj:
                    doc.set_content(content_obj.content)
                    print(f"[WebSocket] Loaded initial content for article {article_id}")
                else:
                    print(f"[WebSocket] No content found for article {article_id}")
        except Exception as e:
            print(f"[WebSocket] Failed to load initial content: {e}")
            import traceback
            traceback.print_exc()

    # 检查用户是否已有活跃连接
    existing_client_id = None
    for cid in doc.clients.keys():
        if cid.startswith(f"user_{user_id}_"):
            existing_client_id = cid
            break

    if existing_client_id:
        print(f"[WebSocket] User {user_id} already has an active connection: {existing_client_id}")
        await websocket.close(code=4009, reason="You already have an active collaboration session")
        return

    # 添加客户端 - 使用唯一ID标识此连接
    import uuid
    client_id = f"user_{user_id}_{uuid.uuid4().hex[:8]}"
    doc.add_client(client_id, websocket)
    print(
        f"[WebSocket] Client {client_id} (user_id={user_id}) added to document {invite_id}, total clients: {len(doc.clients)}")

    # 发送当前文档内容
    print(f"[WebSocket] Sending init message, content length: {len(doc.content)}, version: {doc.version}")
    if doc.content:
        print(f"[WebSocket] Content preview: {doc.content[:100]}")
    else:
        print(f"[WebSocket] WARNING: Document content is empty!")

    await websocket.send_json({
        'type': 'init',
        'content': doc.content,
        'version': doc.version,
        'document_id': invite_id
    })

    # 广播用户加入消息，包含用户列表
    user_list = [
        {
            'id': cid,
            'name': f'User {cid.split("_")[1][:8]}',  # 从 client_id 提取用户ID
            'color': '#958DF1'  # 默认颜色
        }
        for cid in doc.clients.keys()
    ]

    print(f"[WebSocket] Broadcasting user_joined to {len(doc.clients)} clients")
    print(f"[WebSocket] User list: {user_list}")

    # 直接向所有客户端发送用户列表更新
    for cid, client in doc.clients.items():
        try:
            await client.send_json({
                'type': 'user_joined',
                'client_id': client_id,
                'client_count': len(doc.clients),
                'users': user_list
            })
            print(f"[WebSocket] Sent user_joined to {cid}")
        except Exception as e:
            print(f"Error broadcasting to {cid}: {e}")

    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()

            # 处理操作
            op_type = data.get('type')

            if op_type == 'awareness':
                # 处理 awareness 更新
                doc.awareness[client_id] = data.get('state', {})
                await doc.broadcast_awareness({
                    'clientId': client_id,
                    'state': data.get('state', {})
                }, exclude=client_id)
            elif op_type == 'step':
                # 处理编辑步骤
                step_data = data.get('step', {})
                new_content = data.get('content', '')

                print(f"[WebSocket] Received step from {client_id}, content length: {len(new_content)}")

                step = Step.from_dict(step_data)
                success = doc.apply_step(step, new_content)

                if success:
                    print(f"[WebSocket] Step applied successfully, broadcasting to other clients...")
                    print(f"[WebSocket] Document has {len(doc.clients)} clients total")
                    # 广播给其他客户端
                    await doc.broadcast_step(step, exclude=client_id)
                    print(f"[WebSocket] Broadcast completed")

                    # 检查是否需要自动保存
                    if doc.needs_auto_save():
                        print(f"[WebSocket] Auto-save triggered for document {invite_id}")
                        # Auto-save to database
                        # Example implementation:
                        # from shared.models.article import Article
                        # content = doc.get_content()
                        # 
                        # stmt = select(Article).where(Article.id == article_id)
                        # result = await db.execute(stmt)
                        # article = result.scalar_one_or_none()
                        # 
                        # if article:
                        #     article.content = content
                        #     article.updated_at = datetime.now()
                        #     await db.commit()
                        #     doc.mark_saved()
                else:
                    print(f"[WebSocket] Failed to apply step")
            else:
                print(f"[WebSocket] Unknown operation type: {op_type}")

    except WebSocketDisconnect:
        # 用户断开连接
        print(f"[WebSocket] User {user_id} disconnected")
        doc.remove_client(client_id)

        # 广播用户离开消息，包含更新后的用户列表
        user_list = [
            {
                'id': cid,
                'name': f'User {cid.split("_")[1][:8]}',
                'color': '#958DF1'
            }
            for cid in doc.clients.keys()
        ]

        # 直接向所有客户端发送用户列表更新
        for cid, client in doc.clients.items():
            try:
                await client.send_json({
                    'type': 'user_left',
                    'client_id': client_id,
                    'client_count': len(doc.clients),
                    'users': user_list
                })
            except Exception as e:
                print(f"Error broadcasting to {cid}: {e}")

    except Exception as e:
        # 其他错误
        print(f"[WebSocket] Error: {e}")
        import traceback
        traceback.print_exc()
        doc.remove_client(client_id)

        # 广播用户离开消息
        user_list = [
            {
                'id': cid,
                'name': f'User {cid.split("_")[1][:8]}',
                'color': '#958DF1'
            }
            for cid in doc.clients.keys()
        ]

        # 直接向所有客户端发送用户列表更新
        for cid, client in doc.clients.items():
            try:
                await client.send_json({
                    'type': 'user_left',
                    'client_id': client_id,
                    'client_count': len(doc.clients),
                    'users': user_list
                })
            except Exception as e:
                print(f"Error broadcasting to {cid}: {e}")


# 群聊连接管理
class ChatGroupManager:
    """群聊 WebSocket 管理器"""

    def __init__(self):
        self.groups: dict[int, dict] = {}  # group_id -> {"clients": {client_id: websocket}}

    async def join_group(self, group_id: int, client_id: str, websocket: WebSocket, user_id: int):
        """加入群聊"""
        if group_id not in self.groups:
            self.groups[group_id] = {"clients": {}}

        self.groups[group_id]["clients"][client_id] = {
            "websocket": websocket,
            "user_id": user_id
        }

        # 广播用户加入消息
        await self.broadcast_to_group(group_id, {
            'type': 'user_joined',
            'user_id': user_id,
            'client_id': client_id,
            'online_count': len(self.groups[group_id]["clients"])
        }, exclude=client_id)

    async def leave_group(self, group_id: int, client_id: str):
        """离开群聊"""
        if group_id in self.groups and client_id in self.groups[group_id]["clients"]:
            del self.groups[group_id]["clients"][client_id]

            # 广播用户离开消息
            await self.broadcast_to_group(group_id, {
                'type': 'user_left',
                'client_id': client_id,
                'online_count': len(self.groups[group_id]["clients"])
            })

            # 如果群聊没有客户端了，清理
            if not self.groups[group_id]["clients"]:
                del self.groups[group_id]

    async def broadcast_to_group(self, group_id: int, message: dict, exclude: str = None):
        """向群聊广播消息"""
        if group_id not in self.groups:
            return

        disconnected = []
        for client_id, client_info in self.groups[group_id]["clients"].items():
            if client_id == exclude:
                continue
            try:
                await client_info["websocket"].send_json(message)
            except Exception as e:
                print(f"[ChatGroup] Error broadcasting to {client_id}: {e}")
                disconnected.append(client_id)

        # 清理断开的连接
        for client_id in disconnected:
            await self.leave_group(group_id, client_id)

    async def send_message_to_group(self, group_id: int, message_data: dict, sender_id: int):
        """发送消息到群聊"""
        await self.broadcast_to_group(group_id, {
            'type': 'new_message',
            'message': message_data,
            'sender_id': sender_id
        })


# 全局群聊管理器实例
chat_group_manager = ChatGroupManager()


@router.websocket("/chat/{group_id}")
async def chat_websocket(
        websocket: WebSocket,
        group_id: int,
        token: Optional[str] = Query(None, description="认证token")
):
    """
    群聊 WebSocket
    
    Args:
        websocket: WebSocket 连接
        group_id: 群聊 ID
        token: 认证token
    """
    print(f"[ChatGroup] WebSocket connection attempt for group {group_id}")
    print(f"[ChatGroup] Token provided: {'Yes' if token else 'No'}")
    
    # 验证用户身份
    user_id = None

    if token:
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"]
            )
            user_id = payload.get('sub') or payload.get('user_id')
            if user_id:
                user_id = int(user_id)
            print(f"[ChatGroup] Token verified, user_id: {user_id}")
        except Exception as e:
            print(f"[ChatGroup] Token verification failed: {e}")
            import traceback
            traceback.print_exc()

    if not user_id:
        print(f"[ChatGroup] Authentication failed, closing connection")
        await websocket.close(code=4003, reason="Authentication required")
        return

    # 验证用户是否是群聊成员
    try:
        from shared.models.chat_group_member import ChatGroupMember
        from sqlalchemy import select
        from src.utils.database.unified_manager import db_manager

        async with db_manager.get_session() as db_session:
            stmt = select(ChatGroupMember).where(
                (ChatGroupMember.group == group_id) &
                (ChatGroupMember.user == user_id)
            )
            result = await db_session.execute(stmt)
            member = result.scalar_one_or_none()

            if not member:
                await websocket.close(code=4003, reason="Not a member of this group")
                return
    except Exception as e:
        print(f"[ChatGroup] Failed to verify membership: {e}")
        await websocket.close(code=500, reason="Internal error")
        return

    # 接受连接
    await websocket.accept()

    # 生成客户端ID
    import uuid
    client_id = f"user_{user_id}_{uuid.uuid4().hex[:8]}"

    # 加入群聊
    await chat_group_manager.join_group(group_id, client_id, websocket, user_id)

    print(f"[ChatGroup] User {user_id} joined group {group_id} as {client_id}")

    try:
        while True:
            data = await websocket.receive_json()
            op_type = data.get('type')

            if op_type == 'send_message':
                # 处理发送消息
                content = data.get('content', '')
                message_type = data.get('message_type', 'text')
                attachment_url = data.get('attachment_url')
                parent_message = data.get('parent_message')

                if not content:
                    await websocket.send_json({
                        'type': 'error',
                        'message': 'Content is required'
                    })
                    continue

                # 创建消息记录
                try:
                    from shared.models.private_message import PrivateMessage
                    from datetime import datetime
                    from src.utils.database.unified_manager import db_manager

                    async with db_manager.get_session() as db_session:
                        new_message = PrivateMessage(
                            sender=user_id,
                            recipient=None,  # 群聊不需要recipient
                            group=group_id,
                            content=content,
                            message_type=message_type,
                            attachment_url=attachment_url,
                            parent_message=parent_message,
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        db_session.add(new_message)
                        await db_session.commit()
                        await db_session.refresh(new_message)

                        message_data = new_message.to_dict()

                        # 更新群聊的最后消息时间
                        from shared.models.chat_group import ChatGroup
                        from sqlalchemy import update

                        update_stmt = (
                            update(ChatGroup)
                            .where(ChatGroup.id == group_id)
                            .values(
                                last_message_at=datetime.now(),
                                updated_at=datetime.now()
                            )
                        )
                        await db_session.execute(update_stmt)
                        await db_session.commit()

                    # 广播消息到群聊
                    await chat_group_manager.send_message_to_group(
                        group_id, message_data, user_id
                    )

                except Exception as e:
                    print(f"[ChatGroup] Failed to save message: {e}")
                    import traceback
                    traceback.print_exc()
                    await websocket.send_json({
                        'type': 'error',
                        'message': 'Failed to send message'
                    })

            elif op_type == 'typing':
                # 处理正在输入状态
                await chat_group_manager.broadcast_to_group(
                    group_id,
                    {
                        'type': 'user_typing',
                        'user_id': user_id,
                        'client_id': client_id
                    },
                    exclude=client_id
                )

            elif op_type == 'read':
                # 处理已读状态
                message_ids = data.get('message_ids', [])
                if message_ids:
                    try:
                        from shared.models.private_message import PrivateMessage
                        from datetime import datetime
                        from sqlalchemy import update
                        from src.utils.database.unified_manager import db_manager

                        async with db_manager.get_session() as db_session:
                            update_stmt = (
                                update(PrivateMessage)
                                .where(PrivateMessage.id.in_(message_ids))
                                .values(
                                    is_read=True,
                                    read_at=datetime.now()
                                )
                            )
                            await db_session.execute(update_stmt)
                            await db_session.commit()
                    except Exception as e:
                        print(f"[ChatGroup] Failed to mark messages as read: {e}")

    except WebSocketDisconnect:
        print(f"[ChatGroup] User {user_id} disconnected from group {group_id}")
        await chat_group_manager.leave_group(group_id, client_id)

    except Exception as e:
        print(f"[ChatGroup] Error: {e}")
        import traceback
        traceback.print_exc()
        await chat_group_manager.leave_group(group_id, client_id)
