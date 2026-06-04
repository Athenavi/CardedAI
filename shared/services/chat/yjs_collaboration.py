"""
Yjs 实时协作编辑服务

基于 Yjs CRDT 算法实现真正的多人实时协作编辑
使用 y-websocket 协议进行数据同步
"""
import asyncio
from datetime import datetime
from typing import Dict, Optional

from fastapi import WebSocket


class YjsDocument:
    """Yjs 协作文档 - 管理单个文档的协作状态"""

    def __init__(self, document_id: str, article_id: Optional[int] = None):
        self.document_id = document_id
        self.article_id = article_id
        self.clients: Dict[str, WebSocket] = {}  # {client_id: websocket}
        self.created_at = datetime.now()
        self.last_modified = datetime.now()
        self.last_saved = datetime.now()

        # Yjs 文档状态（二进制）
        self.state: bytes = b''

        # 前端定期发送的 HTML 快照（用于保存到数据库）
        self.html_snapshot: str = ''

        # 用户感知状态（光标、选区等）
        self.awareness: Dict[str, dict] = {}

        # 自动保存配置
        self.auto_save_interval = 30  # 秒
        self._auto_save_task: Optional[asyncio.Task] = None

    def add_client(self, client_id: str, websocket: WebSocket):
        """添加客户端连接"""
        self.clients[client_id] = websocket

    def remove_client(self, client_id: str):
        """移除客户端连接"""
        if client_id in self.clients:
            del self.clients[client_id]
        # 清理感知状态
        self.awareness.pop(client_id, None)

    async def broadcast_binary(self, data: bytes, exclude: Optional[str] = None):
        """广播二进制更新给所有连接的客户端"""
        disconnected = []

        for client_id, client in self.clients.items():
            if client_id != exclude:
                try:
                    await client.send_bytes(data)
                except Exception as e:
                    print(f"[Yjs] Broadcast error for client {client_id}: {e}")
                    disconnected.append(client_id)

        # 清理断开的连接
        for client_id in disconnected:
            self.remove_client(client_id)

    async def broadcast_awareness(self, awareness_state: dict, exclude: Optional[str] = None):
        """广播感知状态（光标等）"""
        disconnected = []

        for client_id, client in self.clients.items():
            if client_id != exclude:
                try:
                    await client.send_json({
                        'type': 'awareness',
                        'state': awareness_state
                    })
                except Exception as e:
                    print(f"[Yjs] Awareness broadcast error for client {client_id}: {e}")
                    disconnected.append(client_id)

        # 清理断开的连接
        for client_id in disconnected:
            self.remove_client(client_id)

    def update_state(self, update: bytes):
        """更新文档状态"""
        # 合并 Yjs 更新
        # 注意：实际应用中需要使用 y-py 库来处理 Yjs 更新
        # 这里简化处理，仅存储最新的更新
        self.state = update
        self.last_modified = datetime.now()

    def get_state(self) -> bytes:
        """获取文档状态"""
        return self.state

    def needs_auto_save(self) -> bool:
        """检查是否需要自动保存"""
        now = datetime.now()
        elapsed = (now - self.last_saved).total_seconds()
        return elapsed >= self.auto_save_interval

    def update_html_snapshot(self, html: str):
        """更新 HTML 快照（由前端发送）"""
        self.html_snapshot = html
        self.last_modified = datetime.now()

    def get_info(self) -> dict:
        """获取文档信息"""
        return {
            "document_id": self.document_id,
            "article_id": self.article_id,
            "client_count": len(self.clients),
            "last_modified": self.last_modified.isoformat(),
            "has_content": len(self.state) > 0,
            "has_html": bool(self.html_snapshot),
        }


class YjsCollaborationService:
    """Yjs 协作服务管理器"""

    def __init__(self):
        self.documents: Dict[str, YjsDocument] = {}

    def get_or_create_document(self, document_id: str, article_id: Optional[int] = None) -> YjsDocument:
        """获取或创建 Yjs 文档"""
        if document_id not in self.documents:
            doc = YjsDocument(document_id, article_id)
            self.documents[document_id] = doc
            print(f"[Yjs] Created new document: {document_id}")
        return self.documents[document_id]

    def remove_document(self, document_id: str):
        """删除文档（当没有客户端时）"""
        if document_id in self.documents:
            doc = self.documents[document_id]
            if len(doc.clients) == 0:
                del self.documents[document_id]
                print(f"[Yjs] Removed document: {document_id}")

    def get_active_documents(self) -> list:
        """获取所有活跃的文档"""
        return [
            doc.get_info()
            for doc in self.documents.values()
            if len(doc.clients) > 0
        ]

    async def save_to_database(self, document_id: str, db_session, author_id: int,
                               change_summary: str = "协作编辑保存"):
        """将 Yjs 文档保存到数据库（使用前端发送的 HTML 快照）"""
        from datetime import datetime
        from sqlalchemy import select
        from shared.models.article_content import ArticleContent
        from shared.models.article_revision import ArticleRevision

        doc = self.documents.get(document_id)
        if not doc or not doc.article_id:
            return False

        try:
            article_id = doc.article_id

            if doc.html_snapshot:
                # 更新文章内容
                result = await db_session.execute(
                    select(ArticleContent).where(ArticleContent.article == article_id)
                )
                content_obj = result.scalar_one_or_none()
                if content_obj:
                    content_obj.content = doc.html_snapshot
                    content_obj.updated_at = datetime.now()
                else:
                    from shared.models.article_content import ArticleContent as AC
                    db_session.add(AC(
                        article=article_id, content=doc.html_snapshot,
                        created_at=datetime.now(), updated_at=datetime.now(),
                    ))

                # 创建修订记录
                revision = ArticleRevision(
                    article_id=article_id,
                    author_id=author_id,
                    content=doc.html_snapshot[:500],
                    change_summary=change_summary,
                    created_at=datetime.now(),
                )
                db_session.add(revision)

                await db_session.commit()
                print(f"[Yjs] Saved document {document_id} (article {article_id}) to database")

            doc.last_saved = datetime.now()
            return True

        except Exception as e:
            print(f"[Yjs] Error saving to database: {e}")
            import traceback
            traceback.print_exc()
            return False


# 全局实例
yjs_collaboration_service = YjsCollaborationService()
