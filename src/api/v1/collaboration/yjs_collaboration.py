"""
Yjs 实时协作编辑 WebSocket API

基于 Yjs CRDT 算法的真正多人实时协作
支持二进制协议，性能更优
"""
import json
import uuid as uuid_lib
from typing import Optional

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.services.chat.yjs_collaboration import yjs_collaboration_service
from src.setting import settings
from src.extensions import get_async_db_session as get_async_db
from src.api.v1.core.responses import ApiResponse

router = APIRouter(tags=["collaboration-yjs"])


async def _verify_token(token: Optional[str], cookie: Optional[str]) -> Optional[dict]:
    """验证 JWT token 返回 payload"""
    token_str = token
    if not token_str and cookie:
        for part in cookie.split(';'):
            kv = part.strip().split('=', 1)
            if len(kv) == 2 and kv[0].strip() == 'access_token':
                token_str = kv[1].strip()
                break
    if not token_str:
        return None
    try:
        return jwt.decode(token_str, settings.SECRET_KEY, algorithms=["HS256"])
    except Exception:
        return None


@router.websocket("/ws/{document_id}")
async def yjs_websocket_endpoint(
        websocket: WebSocket,
        document_id: str,
        token: Optional[str] = Query(None, description="JWT token"),
        client_id: Optional[str] = Query(None, description="Client identifier"),
        article_id: Optional[int] = Query(None, description="Article ID"),
):
    """
    Yjs WebSocket 协作文档端点

    使用 Yjs 的二进制协议进行高效的实时协作
    支持：
    - 文档更新同步（二进制）
    - 感知状态（光标、选区等）
    - HTML 快照保存
    - JWT 鉴权
    """
    await websocket.accept()

    # JWT 鉴权
    cookie_header = websocket.headers.get('cookie', '')
    payload = await _verify_token(token, cookie_header)
    user_id = None
    user_name = None
    if payload:
        user_id = payload.get('user_id') or payload.get('sub')
        user_name = payload.get('username') or payload.get('sub', str(user_id or ''))

    # 生成客户端ID
    if not client_id:
        client_id = f"user_{user_id or 'anon'}_{uuid_lib.uuid4().hex[:8]}"

    print(f"[Yjs WS] Client {client_id} (user={user_id}) connecting to document {document_id}")

    # 获取或创建 Yjs 文档
    doc = yjs_collaboration_service.get_or_create_document(document_id, article_id)

    # 添加客户端
    doc.add_client(client_id, websocket)

    # 发送当前文档状态（如果存在）
    current_state = doc.get_state()
    if current_state:
        await websocket.send_bytes(current_state)

    # 发送欢迎消息（含 HTML 快照）
    await websocket.send_json({
        "type": "welcome",
        "document_id": document_id,
        "client_id": client_id,
        "user_id": user_id,
        "user_name": user_name,
        "article_id": doc.article_id,
        "has_html": bool(doc.html_snapshot),
        "html_snapshot": doc.html_snapshot or None,
        "clients": [
            {"client_id": cid}
            for cid in doc.clients.keys()
        ],
    })

    # 通知其他客户端有新用户加入
    await doc.broadcast_awareness({
        "type": "user_joined",
        "client_id": client_id,
        "user_id": user_id,
        "user_name": user_name,
        "client_count": len(doc.clients),
    }, exclude=client_id)

    try:
        while True:
            data = await websocket.receive()

            if "bytes" in data:
                # Yjs 二进制更新 — 直接广播给其他客户端
                update = data["bytes"]
                doc.update_state(update)
                await doc.broadcast_binary(update, exclude=client_id)

            elif "text" in data:
                try:
                    message = json.loads(data["text"])
                    msg_type = message.get("type")

                    if msg_type == "awareness":
                        awareness_state = message.get("state", {})
                        doc.awareness[client_id] = {
                            **awareness_state,
                            "client_id": client_id,
                            "user_id": user_id,
                            "user_name": user_name or awareness_state.get('user_name'),
                            "timestamp": doc.last_modified.isoformat(),
                        }
                        await doc.broadcast_awareness({
                            "type": "awareness",
                            "state": doc.awareness[client_id],
                        }, exclude=client_id)

                    elif msg_type == "html_snapshot":
                        # 前端保存 HTML 快照（用于保存到数据库）
                        html = message.get("html", "")
                        doc.update_html_snapshot(html)
                        # 广播给其他客户端（不通过 broadcast_awareness，直接发送 JSON）
                        if html:
                            for cid, client in doc.clients.items():
                                if cid != client_id:
                                    try:
                                        await client.send_json({
                                            "type": "html_snapshot",
                                            "client_id": client_id,
                                            "html": html,
                                        })
                                    except Exception as e:
                                        print(f"[Yjs WS] broadcast html error to {cid}: {e}")

                    elif msg_type == "save":
                        try:
                            async with get_async_db() as save_db:
                                success = await yjs_collaboration_service.save_to_database(
                                    document_id, save_db, user_id or 0, "协作编辑保存"
                                )
                            await websocket.send_json({
                                "type": "save_result",
                                "success": success,
                                "message": "保存成功" if success else "保存失败",
                            })
                        except Exception as save_err:
                            print(f"[Yjs] Save error: {save_err}")
                            await websocket.send_json({
                                "type": "save_result", "success": False, "error": str(save_err),
                            })

                    elif msg_type == "ping":
                        await websocket.send_json({"type": "pong"})
                        if doc.needs_auto_save() and doc.html_snapshot:
                            try:
                                async with get_async_db() as save_db:
                                    await yjs_collaboration_service.save_to_database(
                                        document_id, save_db, user_id or 0, "自动保存"
                                    )
                            except Exception:
                                pass

                except json.JSONDecodeError as e:
                    print(f"[Yjs WS] JSON parse error: {e}")

    except WebSocketDisconnect:
        print(f"[Yjs WS] Client {client_id} disconnected")
        doc.remove_client(client_id)
        await doc.broadcast_awareness({
            "type": "user_left",
            "client_id": client_id,
            "user_id": user_id,
            "client_count": len(doc.clients),
        })
        # 最后一个客户端离开时自动保存
        if len(doc.clients) == 0 and doc.html_snapshot:
            try:
                async with get_async_db() as save_db:
                    await yjs_collaboration_service.save_to_database(
                        document_id, save_db, user_id or 0, "协作编辑自动保存（断开）"
                    )
            except Exception as save_err:
                print(f"[Yjs] Final save error: {save_err}")
        yjs_collaboration_service.remove_document(document_id)

    except Exception as e:
        print(f"[Yjs WS] Error: {e}")
        import traceback
        traceback.print_exc()
        doc.remove_client(client_id)
        await doc.broadcast_awareness({
            "type": "user_left", "client_id": client_id,
            "client_count": len(doc.clients),
        })
        yjs_collaboration_service.remove_document(document_id)


@router.get("/documents")
async def list_yjs_documents():
    """获取所有活跃的 Yjs 文档列表"""
    documents = yjs_collaboration_service.get_active_documents()
    return {
        "success": True,
        "data": {
            "documents": documents,
            "count": len(documents)
        }
    }


@router.post("/save/{document_id}")
async def save_yjs_document(
        document_id: str,
        db: AsyncSession = Depends(get_async_db),
):
    """手动保存 Yjs 文档到数据库（HTTP 端点）"""
    try:
        success = await yjs_collaboration_service.save_to_database(
            document_id, db, 0, "HTTP 保存"
        )
        return ApiResponse(success=success, data={"message": "保存成功" if success else "无可保存内容"})
    except Exception as e:
        return ApiResponse(success=False, error=str(e))
