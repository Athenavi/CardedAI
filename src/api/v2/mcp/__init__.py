"""
V2 MCP Server API 路由

提供 MCP (Model Context Protocol) 的 HTTP/SSE 传输端点，
支持 AI Agent (Claude Desktop, Cursor IDE 等) 通过标准 HTTP 与 FastBlog 交互。

端点:
- POST /api/v2/mcp          - JSON-RPC 2.0 请求端点
- GET  /api/v2/mcp/sse      - SSE 长连接端点（Server-Sent Events）
- POST /api/v2/mcp/message  - SSE 消息注入（响应通过 SSE 流推送）
- GET  /api/v2/mcp/info     - 服务器信息
- GET  /api/v2/mcp/resources - 列出所有资源
- GET  /api/v2/mcp/tools    - 列出所有工具
- GET  /api/v2/mcp/prompts  - 列出所有提示词
"""

import json
import asyncio
import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from src.auth import jwt_required_dependency as jwt_required
from shared.models.user import User as UserModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["mcp"])

# SSE 连接注册表：session_id -> asyncio.Queue
# 每建立一个 SSE 连接，就在此注册一个队列；
# POST /message 将响应推入队列，SSE 事件循环从队列取出并推送给客户端。
_active_sse_queues: Dict[str, asyncio.Queue] = {}


# ==================== Pydantic 模型 ====================

class MCPRequest(BaseModel):
    """MCP JSON-RPC 2.0 请求"""
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[Any] = None


class MCPBatchRequest(BaseModel):
    """MCP 批量 JSON-RPC 请求"""
    requests: list[MCPRequest]


# ==================== 辅助函数 ====================

def _get_mcp_server():
    """延迟加载 MCP Server 全局实例"""
    from src.mcp.server import mcp_server
    return mcp_server


# ==================== 核心端点 ====================

@router.post("", summary="MCP JSON-RPC 请求端点")
async def mcp_jsonrpc(
    request: MCPRequest,
    current_user: UserModel = Depends(jwt_required),
):
    """
    处理 MCP JSON-RPC 2.0 请求

    这是 AI Agent 与 FastBlog 交互的主要入口。
    支持的 method:
    - resources/list: 列出所有可用资源
    - resources/read: 读取指定资源
    - tools/list: 列出所有可用工具
    - tools/call: 调用指定工具
    - prompts/list: 列出所有提示词模板
    - prompts/get: 获取指定提示词
    """
    try:
        mcp_server = _get_mcp_server()
        rpc_request = {
            "jsonrpc": request.jsonrpc,
            "method": request.method,
            "params": request.params or {},
            "id": request.id,
        }
        result = await mcp_server.handle_request(rpc_request)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"MCP JSON-RPC error: {e}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": request.id,
                "error": {"code": -32603, "message": str(e)},
            },
            status_code=500,
        )


@router.post("/batch", summary="MCP 批量 JSON-RPC 请求")
async def mcp_batch_jsonrpc(
    batch: MCPBatchRequest,
    current_user: UserModel = Depends(jwt_required),
):
    """
    批量处理多个 MCP JSON-RPC 请求

    所有请求并发执行，返回结果数组。
    """
    try:
        mcp_server = _get_mcp_server()

        async def process_one(req: MCPRequest):
            rpc_request = {
                "jsonrpc": req.jsonrpc,
                "method": req.method,
                "params": req.params or {},
                "id": req.id,
            }
            return await mcp_server.handle_request(rpc_request)

        results = await asyncio.gather(
            *[process_one(req) for req in batch.requests],
            return_exceptions=True,
        )
        responses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                responses.append({
                    "jsonrpc": "2.0",
                    "id": batch.requests[i].id,
                    "error": {"code": -32603, "message": str(result)},
                })
            else:
                responses.append(result)

        return JSONResponse(content=responses)
    except Exception as e:
        logger.error(f"MCP batch error: {e}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": str(e)},
            },
            status_code=500,
        )


# ==================== SSE 传输端点 ====================

@router.get("/sse", summary="MCP SSE 长连接端点")
async def mcp_sse(request: Request):
    """
    Server-Sent Events (SSE) 端点

    建立 SSE 长连接后，客户端可通过 POST /api/v2/mcp/message 发送请求，
    服务端通过此 SSE 流推送响应。

    MCP SSE 协议:
    1. 客户端连接 GET /api/v2/mcp/sse，获得 session_id
    2. 服务端发送 event: endpoint -> 告知消息注入 URL
    3. 客户端 POST JSON-RPC 到 /api/v2/mcp/message（可携带 session_id）
    4. 服务端处理请求后，通过 SSE event: message 推送结果
    """
    mcp_server = _get_mcp_server()
    session_id = uuid.uuid4().hex[:12]
    queue: asyncio.Queue = asyncio.Queue()
    _active_sse_queues[session_id] = queue

    async def event_generator():
        try:
            # 1. 发送 endpoint 信息（MCP SSE 规范）
            yield "event: endpoint\ndata: /api/v2/mcp/message\n\n"

            # 2. 发送 session_id，客户端可用来绑定消息
            yield f"event: session_id\ndata: {session_id}\n\n"

            # 3. 发送服务器信息
            info = mcp_server.get_server_info()
            yield f"event: info\ndata: {json.dumps(info, ensure_ascii=False)}\n\n"

            while True:
                if await request.is_disconnected():
                    break

                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"event: message\ndata: {json.dumps(message, ensure_ascii=False)}\n\n"
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"SSE error: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
        finally:
            _active_sse_queues.pop(session_id, None)
            logger.info(f"SSE session {session_id} closed")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/message", summary="SSE 消息注入端点")
async def mcp_sse_message(request: MCPRequest):
    """
    SSE 模式的消息注入端点

    客户端通过此端点发送 JSON-RPC 请求。
    - 如果有活跃的 SSE 连接，响应通过 SSE 流推送
    - 如果没有 SSE 连接，直接返回 JSON（向后兼容）
    """
    try:
        mcp_server = _get_mcp_server()
        rpc_request = {
            "jsonrpc": request.jsonrpc,
            "method": request.method,
            "params": request.params or {},
            "id": request.id,
        }
        result = await mcp_server.handle_request(rpc_request)

        # 尝试将结果推送到 SSE 队列（优先推送，兼容无 SSE 场景）
        if _active_sse_queues:
            for session_id, queue in list(_active_sse_queues.items()):
                try:
                    await queue.put(result)
                except Exception:
                    pass
            # SSE 模式下，消息端点返回 202 Accepted（告知客户端等待 SSE 推送）
            return JSONResponse(
                content={"status": "accepted", "session_count": len(_active_sse_queues)},
                status_code=202,
            )

        # 无 SSE 连接时：同步返回（向后兼容）
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"MCP message error: {e}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": request.id,
                "error": {"code": -32603, "message": str(e)},
            },
            status_code=500,
        )


# ==================== 信息端点 ====================

@router.get("/info", summary="获取 MCP 服务器信息")
async def mcp_info():
    """获取 MCP 服务器基本信息（名称、版本、资源/工具/提示词数量）"""
    try:
        mcp_server = _get_mcp_server()
        return JSONResponse(content=mcp_server.get_server_info())
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500,
        )


@router.get("/resources", summary="列出 MCP 资源")
async def mcp_resources():
    """列出所有已注册的 MCP 资源"""
    try:
        mcp_server = _get_mcp_server()
        result = await mcp_server.handle_request({
            "jsonrpc": "2.0",
            "method": "resources/list",
            "params": {},
            "id": "info",
        })
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500,
        )


@router.get("/tools", summary="列出 MCP 工具")
async def mcp_tools():
    """列出所有已注册的 MCP 工具"""
    try:
        mcp_server = _get_mcp_server()
        result = await mcp_server.handle_request({
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": "info",
        })
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500,
        )


@router.get("/prompts", summary="列出 MCP 提示词")
async def mcp_prompts():
    """列出所有已注册的 MCP 提示词模板"""
    try:
        mcp_server = _get_mcp_server()
        result = await mcp_server.handle_request({
            "jsonrpc": "2.0",
            "method": "prompts/list",
            "params": {},
            "id": "info",
        })
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500,
        )
