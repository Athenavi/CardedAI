"""
Agent 工具注册中心

提供动态工具管理能力：
- 注册 / 注销工具
- 工具调用（支持异步）
- 导出为 OpenAI function calling 格式
- 内置工具预注册（采集、搜索、通知、发布）
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Dict, List, Optional

from src.unified_logger import default_logger as logger


@dataclass
class ToolDefinition:
    """工具定义"""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    handler: Callable[..., Coroutine]  # async callable
    tool_type: str = "function"  # function / api / collector / transformer
    config: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AgentToolRegistry:
    """Agent 工具注册中心

    管理 Agent 可调用的工具集，支持：
    - 运行时动态注册 / 注销
    - 异步工具调用
    - OpenAI function calling 格式导出
    - 数据库持久化（可选）
    """

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    # ------------------------------------------------------------------
    # 工具注册
    # ------------------------------------------------------------------

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable[..., Coroutine],
        tool_type: str = "function",
        config: Optional[Dict[str, Any]] = None,
    ) -> ToolDefinition:
        """注册 Agent 可用的工具

        Args:
            name: 工具名称（唯一标识）
            description: 工具描述
            parameters: 参数 JSON Schema
            handler: 异步处理函数，签名 async def handler(**params) -> Any
            tool_type: 工具类型
            config: 附加配置

        Returns:
            ToolDefinition
        """
        tool = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
            tool_type=tool_type,
            config=config or {},
        )
        self._tools[name] = tool
        logger.info(f"[ToolRegistry] 注册工具: {name} ({tool_type})")
        return tool

    def unregister_tool(self, name: str) -> bool:
        """注销工具"""
        if name in self._tools:
            del self._tools[name]
            logger.info(f"[ToolRegistry] 注销工具: {name}")
            return True
        return False

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """获取工具定义"""
        return self._tools.get(name)

    def list_tools(self, tool_type: Optional[str] = None, active_only: bool = True) -> List[Dict[str, Any]]:
        """列出所有工具

        Args:
            tool_type: 按类型过滤
            active_only: 只返回活跃工具

        Returns:
            工具信息列表
        """
        result = []
        for tool in self._tools.values():
            if active_only and not tool.is_active:
                continue
            if tool_type and tool.tool_type != tool_type:
                continue
            result.append({
                "name": tool.name,
                "description": tool.description,
                "tool_type": tool.tool_type,
                "parameters": tool.parameters,
                "is_active": tool.is_active,
                "created_at": tool.created_at,
            })
        return result

    # ------------------------------------------------------------------
    # 工具调用
    # ------------------------------------------------------------------

    async def call_tool(self, name: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """调用工具

        Args:
            name: 工具名称
            params: 调用参数

        Returns:
            工具执行结果

        Raises:
            ValueError: 工具不存在或未激活
        """
        tool = self._tools.get(name)
        if tool is None:
            raise ValueError(f"工具不存在: {name}")
        if not tool.is_active:
            raise ValueError(f"工具未激活: {name}")

        logger.info(f"[ToolRegistry] 调用工具: {name}")
        try:
            result = await tool.handler(**(params or {}))
            logger.info(f"[ToolRegistry] 工具 {name} 调用成功")
            return result
        except Exception as exc:
            logger.error(f"[ToolRegistry] 工具 {name} 调用失败: {exc}")
            raise

    async def call_tool_safe(
        self, name: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """安全调用工具（捕获异常）

        Returns:
            {"success": bool, "result": Any, "error": str | None}
        """
        try:
            result = await self.call_tool(name, params)
            return {"success": True, "result": result, "error": None}
        except Exception as exc:
            return {"success": False, "result": None, "error": str(exc)}

    # ------------------------------------------------------------------
    # LLM Function Calling 格式
    # ------------------------------------------------------------------

    def get_tools_for_llm(self, tool_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """获取工具列表（OpenAI function calling 格式）

        Args:
            tool_names: 指定工具名称列表（None 表示全部）

        Returns:
            [{"type": "function", "function": {"name": ..., "description": ..., "parameters": ...}}]
        """
        result = []
        for name, tool in self._tools.items():
            if not tool.is_active:
                continue
            if tool_names and name not in tool_names:
                continue
            result.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            })
        return result

    def get_tool_names(self) -> List[str]:
        """获取所有活跃工具名称"""
        return [name for name, t in self._tools.items() if t.is_active]

    # ------------------------------------------------------------------
    # 数据库同步（可选）
    # ------------------------------------------------------------------

    async def sync_to_db(self) -> int:
        """将内存中的工具注册到数据库

        Returns:
            同步的工具数量
        """
        try:
            from datetime import datetime, timezone
            from src.extensions import get_db
            from shared.models.workflow.agent_tool import AgentTool

            count = 0
            with get_db() as db:
                for tool in self._tools.values():
                    existing = db.query(AgentTool).filter_by(name=tool.name).first()
                    if existing:
                        existing.description = tool.description
                        existing.tool_type = tool.tool_type
                        existing.schema = json.dumps(tool.parameters, ensure_ascii=False)
                        existing.config = json.dumps(tool.config, ensure_ascii=False)
                        existing.is_active = tool.is_active
                    else:
                        db_tool = AgentTool(
                            name=tool.name,
                            description=tool.description,
                            tool_type=tool.tool_type,
                            schema=json.dumps(tool.parameters, ensure_ascii=False),
                            config=json.dumps(tool.config, ensure_ascii=False),
                            is_active=tool.is_active,
                            created_at=datetime.now(timezone.utc),
                        )
                        db.add(db_tool)
                    count += 1
                db.flush()
                db.commit()
            return count
        except Exception as exc:
            logger.error(f"[ToolRegistry] 同步到数据库失败: {exc}")
            return 0

    async def load_from_db(self) -> int:
        """从数据库加载工具定义（仅加载元数据，handler 需要代码注册）

        Returns:
            加载的工具数量
        """
        try:
            from src.extensions import get_db
            from shared.models.workflow.agent_tool import AgentTool

            count = 0
            with get_db() as db:
                tools = db.query(AgentTool).filter_by(is_active=True).all()
                for t in tools:
                    if t.name not in self._tools:
                        # 数据库中有但内存中没有的工具，标记为外部工具
                        self._tools[t.name] = ToolDefinition(
                            name=t.name,
                            description=t.description or "",
                            parameters=json.loads(t.schema) if t.schema else {},
                            handler=self._external_tool_handler,
                            tool_type=t.tool_type or "external",
                            config=json.loads(t.config) if t.config else {},
                            is_active=t.is_active,
                        )
                        count += 1
            return count
        except Exception as exc:
            logger.warning(f"[ToolRegistry] 从数据库加载工具失败: {exc}")
            return 0

    @staticmethod
    async def _external_tool_handler(**kwargs) -> Dict[str, Any]:
        """外部工具的默认处理器"""
        return {
            "success": False,
            "error": "外部工具需要通过 API 调用，不支持直接调用",
        }


# ======================================================================
# 全局单例 & 内置工具注册
# ======================================================================

tool_registry = AgentToolRegistry()


async def _collect_data_handler(source_ids: List[int] = None, **kwargs) -> Dict[str, Any]:
    """数据采集工具 handler"""
    from shared.services.intel.collector_engine import collector_engine

    if not source_ids:
        return {"success": False, "error": "需要提供 source_ids"}

    results = []
    for sid in source_ids:
        try:
            outcome = await collector_engine.run_collection(sid)
            results.append({"source_id": sid, **outcome})
        except Exception as exc:
            results.append({"source_id": sid, "error": str(exc)})

    return {"success": True, "results": results}


async def _search_knowledge_handler(
    query: str = "",
    knowledge_base_id: int = None,
    top_k: int = 5,
    **kwargs,
) -> Dict[str, Any]:
    """知识库搜索工具 handler"""
    from shared.services.knowledge.rag_chain import rag_chain

    if not query:
        return {"success": False, "error": "需要提供 query"}
    if knowledge_base_id is None:
        return {"success": False, "error": "需要提供 knowledge_base_id"}

    result = await rag_chain.query(
        query=query,
        knowledge_base_id=knowledge_base_id,
        top_k=top_k,
    )
    return result


async def _send_notification_handler(
    channel: str = "log",
    message: str = "",
    recipients: List[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """通知发送工具 handler"""
    if channel == "log":
        logger.info(f"[Tool:send_notification] {message}")
        return {"success": True, "channel": "log"}
    elif channel == "email":
        try:
            from shared.services.notifications.email_service import email_service
            for r in (recipients or []):
                await email_service.send_email(to=r, subject="Workflow Notification", body=message)
            return {"success": True, "channel": "email", "recipients": recipients}
        except Exception as exc:
            return {"success": False, "error": str(exc)}
    elif channel == "webhook":
        webhook_url = kwargs.get("webhook_url", "")
        if not webhook_url:
            return {"success": False, "error": "需要 webhook_url"}
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(webhook_url, json={"text": message})
                resp.raise_for_status()
            return {"success": True, "channel": "webhook"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}
    else:
        return {"success": False, "error": f"未知渠道: {channel}"}


async def _publish_article_handler(
    title: str = "",
    content: str = "",
    category_id: int = None,
    **kwargs,
) -> Dict[str, Any]:
    """文章发布工具 handler（复用现有博客功能）"""
    from datetime import datetime, timezone
    from src.extensions import get_db

    try:
        with get_db() as db:
            from shared.models import Article
            article = Article(
                title=title,
                content=content,
                category_id=category_id,
                status="published",
                created_at=datetime.now(timezone.utc),
                published_at=datetime.now(timezone.utc),
            )
            db.add(article)
            db.flush()
            article_id = article.id
            db.commit()
            return {"success": True, "article_id": article_id, "title": title}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def _register_builtin_tools():
    """注册内置工具"""
    # 数据采集工具
    tool_registry.register_tool(
        name="collect_data",
        description="从指定数据源采集数据",
        parameters={
            "type": "object",
            "properties": {
                "source_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "数据源 ID 列表",
                },
            },
            "required": ["source_ids"],
        },
        handler=_collect_data_handler,
        tool_type="collector",
    )

    # RAG 搜索工具
    tool_registry.register_tool(
        name="search_knowledge",
        description="在知识库中搜索信息，基于语义相似度检索相关文档",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索查询语句",
                },
                "knowledge_base_id": {
                    "type": "integer",
                    "description": "知识库 ID",
                },
                "top_k": {
                    "type": "integer",
                    "description": "返回结果数量",
                    "default": 5,
                },
            },
            "required": ["query", "knowledge_base_id"],
        },
        handler=_search_knowledge_handler,
        tool_type="function",
    )

    # 通知工具
    tool_registry.register_tool(
        name="send_notification",
        description="发送通知到指定渠道（log/email/webhook）",
        parameters={
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "enum": ["log", "email", "webhook"],
                    "description": "通知渠道",
                    "default": "log",
                },
                "message": {
                    "type": "string",
                    "description": "通知消息内容",
                },
                "recipients": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "收件人列表（email 渠道）",
                },
                "webhook_url": {
                    "type": "string",
                    "description": "Webhook URL（webhook 渠道）",
                },
            },
            "required": ["message"],
        },
        handler=_send_notification_handler,
        tool_type="function",
    )

    # 文章发布工具
    tool_registry.register_tool(
        name="publish_article",
        description="发布文章到博客",
        parameters={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "文章标题",
                },
                "content": {
                    "type": "string",
                    "description": "文章内容（HTML 或 Markdown）",
                },
                "category_id": {
                    "type": "integer",
                    "description": "分类 ID",
                },
            },
            "required": ["title", "content"],
        },
        handler=_publish_article_handler,
        tool_type="function",
    )

    logger.info(f"[ToolRegistry] 内置工具注册完成: {tool_registry.get_tool_names()}")


# 启动时自动注册内置工具
_register_builtin_tools()
