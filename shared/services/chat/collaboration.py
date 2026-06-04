"""
实时协作编辑服务

基于 ProseMirror collab 协议实现多人实时协作编辑功能
不依赖 y_py，使用纯 Python 实现 OT 算法
"""
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import WebSocket


class Step:
    """表示一个编辑步骤（操作）"""

    def __init__(self, step_type: str, data: dict, client_id: str, version: int):
        """
        Args:
            step_type: 步骤类型 ('replace', 'addMark', 'removeMark' 等)
            data: 步骤数据
            client_id: 客户端ID
            version: 文档版本号
        """
        self.step_type = step_type
        self.data = data
        self.client_id = client_id
        self.version = version
        self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        return {
            "stepType": self.step_type,
            "data": self.data,
            "clientID": self.client_id,
            "version": self.version,
            "timestamp": self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Step':
        step = cls(
            step_type=data["stepType"],
            data=data["data"],
            client_id=data["clientID"],
            version=data["version"]
        )
        if "timestamp" in data:
            step.timestamp = datetime.fromisoformat(data["timestamp"])
        return step


class CollaborativeDocument:
    """协作文档 - 基于 ProseMirror collab 协议"""

    def __init__(self, document_id: str):
        self.document_id = document_id
        self.clients: Dict[str, WebSocket] = {}  # {client_id: websocket}
        self.created_at = datetime.now()
        self.last_modified = datetime.now()
        self.last_saved = datetime.now()

        # 文档内容（HTML格式）
        self.content: str = ""

        # 步骤历史（用于协作同步）
        self.steps: List[Step] = []
        self.version: int = 0  # 当前版本号

        # 用户感知状态
        self.awareness: Dict[str, dict] = {}
        self.article_id: Optional[int] = None
        self.auto_save_interval = 30  # 自动保存间隔（秒）

    def add_client(self, client_id: str, websocket: WebSocket):
        """添加客户端连接"""
        self.clients[client_id] = websocket

    def remove_client(self, client_id: str):
        """移除客户端连接"""
        if client_id in self.clients:
            del self.clients[client_id]
        # 清理光标信息
        self.awareness.pop(client_id, None)

    async def broadcast_step(self, step: Step, exclude: Optional[str] = None):
        """广播步骤给所有连接的客户端"""
        disconnected = []
        step_data = step.to_dict()

        print(f"[Collab] Broadcasting step to {len(self.clients)} clients (excluding {exclude})")

        for client_id, client in self.clients.items():
            if client_id != exclude:
                try:
                    print(f"[Collab] Sending to client {client_id}")
                    await client.send_json({
                        'type': 'receive_steps',
                        'steps': [step_data],
                        'version': self.version
                    })
                    print(f"[Collab] Successfully sent to {client_id}")
                except Exception as e:
                    print(f"Broadcast error for client {client_id}: {e}")
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
                    print(f"Awareness broadcast error for client {client_id}: {e}")
                    disconnected.append(client_id)

        # 清理断开的连接
        for client_id in disconnected:
            self.remove_client(client_id)

    def apply_step(self, step: Step, new_content: str) -> bool:
        """应用步骤到文档 - 使用版本控制避免冲突"""
        try:
            # 检查版本号，确保是最新的
            if step.version < self.version:
                print(f"[Collab] Warning: Received old step version {step.version}, current is {self.version}")
                return False

            # 更新文档内容
            self.content = new_content

            # 记录步骤
            self.steps.append(step)
            self.version += 1
            self.last_modified = datetime.now()

            # 限制步骤历史长度，避免内存泄漏
            if len(self.steps) > 100:
                self.steps = self.steps[-50:]

            print(f"[Collab] Applied step type={step.step_type}, version {self.version}")
            return True

        except Exception as e:
            print(f"Error applying step: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_steps_since(self, version: int) -> List[Step]:
        """获取指定版本之后的所有步骤"""
        if version >= self.version:
            return []
        return self.steps[version:]

    def get_content_with_version(self) -> dict:
        """获取文档内容和版本号"""
        return {
            "content": self.content,
            "version": self.version,
            "last_modified": self.last_modified.isoformat()
        }

    def needs_auto_save(self) -> bool:
        """检查是否需要自动保存"""
        now = datetime.now()
        elapsed = (now - self.last_saved).total_seconds()
        return elapsed >= self.auto_save_interval

    def get_content(self) -> str:
        """获取文档内容"""
        return self.content

    def set_content(self, content: str):
        """设置文档内容"""
        self.content = content
        self.last_modified = datetime.now()

    def get_state(self) -> dict:
        """获取文档状态"""
        return {
            "document_id": self.document_id,
            "content": self.content,
            "article_id": self.article_id,
            "version": self.version,
            "step_count": len(self.steps),
            "awareness": self.awareness,
            "client_count": len(self.clients),
            "last_modified": self.last_modified.isoformat()
        }


class CollaborationService:
    """协作服务管理器"""

    def __init__(self):
        self.documents: Dict[str, CollaborativeDocument] = {}

    def get_or_create_document(self, document_id: str, article_id: Optional[int] = None) -> CollaborativeDocument:
        """获取或创建协作文档"""
        if document_id not in self.documents:
            doc = CollaborativeDocument(document_id)
            if article_id:
                doc.article_id = article_id
            self.documents[document_id] = doc
        return self.documents[document_id]

    def remove_document(self, document_id: str):
        """删除协作文档"""
        if document_id in self.documents:
            del self.documents[document_id]

    def get_active_documents(self) -> list:
        """获取所有活跃的协作文档"""
        return [
            {
                "document_id": doc.document_id,
                "article_id": doc.article_id,
                "client_count": len(doc.clients),
                "version": doc.version,
                "last_modified": doc.last_modified.isoformat()
            }
            for doc in self.documents.values()
            if len(doc.clients) > 0
        ]


# 全局实例
collaboration_service = CollaborationService()
