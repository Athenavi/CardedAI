"""
AI 聊天代理 API — 通过 MCP 工具与 LLM 对话完成系统操作

用户在前端填入自己的 LLM 端点和 API Key，通过自然语言调用 MCP 工具
（文章 CRUD、情报采集、知识库检索、工作流触发等）完成站点管理。
"""

import json
import logging
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.auth import jwt_required_dependency as jwt_required
from shared.models.user import User as UserModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ai"])


# ==================== 请求/响应模型 ====================

class ChatMessage(BaseModel):
    role: str  # user / assistant
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]]
    llm_endpoint: str = "https://api.openai.com/v1"
    llm_key: str = ""
    model: str = "gpt-4o"
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096


class ChatResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    reply: Optional[str] = None
    tool_results: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


# ==================== 核心逻辑 ====================

def _get_mcp_server():
    from src.mcp.server import mcp_server
    return mcp_server


def _build_openai_tools() -> List[Dict[str, Any]]:
    """将 MCP 工具列表转换为 OpenAI function calling 格式"""
    mcp = _get_mcp_server()
    tools = []
    for name, tool in mcp.tools.items():
        openai_tool = {
            "type": "function",
            "function": {
                "name": name,
                "description": tool["description"],
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        }
        # Convert MCP parameter format to JSON Schema
        params = tool["parameters"]
        props = {}
        required = []
        for pname, pdef in params.items():
            ptype = pdef.get("type", "string")
            json_type = {"integer": "integer", "string": "string", "boolean": "boolean",
                         "array": "array", "number": "number"}.get(ptype, "string")
            prop = {"type": json_type, "description": pdef.get("description", "")}
            props[pname] = prop
            if pdef.get("required", False):
                required.append(pname)
        openai_tool["function"]["parameters"]["properties"] = props
        openai_tool["function"]["parameters"]["required"] = required
        tools.append(openai_tool)
    return tools


async def _call_llm_with_tools(
    messages: List[Dict[str, Any]],
    llm_endpoint: str,
    llm_key: str,
    model: str,
    tools: List[Dict[str, Any]],
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> Dict[str, Any]:
    """调用 LLM，传入工具定义，返回响应"""
    full_messages = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    full_messages.extend(messages)

    payload = {
        "model": model,
        "messages": full_messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if tools:
        payload["tools"] = tools

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{llm_endpoint.rstrip('/')}/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {llm_key}",
                "Content-Type": "application/json",
            },
        )

    if resp.status_code != 200:
        return {"success": False, "error": f"LLM API error ({resp.status_code}): {resp.text[:300]}"}

    data = resp.json()
    choice = data.get("choices", [{}])[0]
    message = choice.get("message", {})

    result = {
        "success": True,
        "content": message.get("content", ""),
        "tool_calls": [],
        "finish_reason": choice.get("finish_reason", ""),
    }

    # Parse tool calls from OpenAI format
    raw_tool_calls = message.get("tool_calls", [])
    if raw_tool_calls:
        for tc in raw_tool_calls:
            func = tc.get("function", {})
            try:
                arguments = json.loads(func.get("arguments", "{}"))
            except json.JSONDecodeError:
                arguments = {}
            result["tool_calls"].append({
                "id": tc.get("id", ""),
                "type": "function",
                "function": {
                    "name": func.get("name", ""),
                    "arguments": arguments,
                },
            })

    return result


async def _execute_mcp_tool(tool_name: str, arguments: dict) -> dict:
    """通过 MCP Server 执行工具调用"""
    mcp = _get_mcp_server()
    result = await mcp._handle_tool_call(
        {"name": tool_name, "arguments": arguments},
        request_id="ai-chat",
    )
    # MCP returns JSON-RPC format; extract the result text
    content = result.get("result", {}).get("content", [{}])[0].get("text", "")
    error = result.get("error", {}).get("message", "")
    if error:
        return {"success": False, "error": error}
    try:
        data = json.loads(content)
        return {"success": True, "data": data}
    except (json.JSONDecodeError, TypeError):
        return {"success": True, "data": content}


# ==================== API 端点 ====================

@router.post("/mcp-chat", summary="MCP AI 对话代理")
async def mcp_chat(
    req: ChatRequest,
    current_user: UserModel = Depends(jwt_required),
):
    """
    AI 对话代理端点。

    用户传入 LLM 配置 + 消息历史，后端自动：
    1. 获取所有 MCP 工具定义
    2. 调用用户指定的 LLM（含工具定义）
    3. 如果 LLM 返回工具调用，执行并回传结果给 LLM
    4. 返回最终回复
    """
    if not req.llm_key:
        return ChatResponse(success=False, error="请提供 API Key (sk-...)")

    if not req.llm_endpoint:
        return ChatResponse(success=False, error="请提供 LLM 端点地址")

    try:
        # Build default system prompt
        sys_prompt = req.system_prompt or (
            "你是一个 CardedAI 站点管理助手。你可以通过以下工具帮助用户管理站点。\n\n"
            "使用规则：\n"
            "1. 优先使用工具完成用户请求\n"
            "2. 如果工具返回结果，基于结果给出友好的回复\n"
            "3. 如果工具调用失败，向用户解释错误原因\n"
            "4. 对于不确定的操作，先询问用户确认"
        )

        # Get MCP tools in OpenAI format
        tools = _build_openai_tools()

        # Call LLM (may loop for tool calls, max 10 rounds)
        messages = list(req.messages)
        tool_results = []
        max_rounds = 10

        for round_idx in range(max_rounds):
            llm_result = await _call_llm_with_tools(
                messages=messages,
                llm_endpoint=req.llm_endpoint,
                llm_key=req.llm_key,
                model=req.model,
                tools=tools,
                system_prompt=sys_prompt if round_idx == 0 else None,
                temperature=req.temperature,
                max_tokens=req.max_tokens,
            )

            if not llm_result.get("success"):
                return ChatResponse(success=False, error=llm_result.get("error", "LLM 调用失败"))

            # Add assistant message to history
            assistant_msg = {"role": "assistant", "content": llm_result.get("content") or None}
            tool_calls = llm_result.get("tool_calls", [])

            if tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["function"]["name"],
                            "arguments": json.dumps(tc["function"]["arguments"], ensure_ascii=False),
                        },
                    }
                    for tc in tool_calls
                ]

            messages.append(assistant_msg)

            if not tool_calls:
                # No tool calls → this is the final response
                return ChatResponse(
                    success=True,
                    reply=llm_result.get("content", ""),
                    tool_results=tool_results if tool_results else None,
                )

            # Execute each tool call
            for tc in tool_calls:
                tool_name = tc["function"]["name"]
                arguments = tc["function"]["arguments"]
                logger.info(f"[AI Chat] 执行工具: {tool_name}({arguments})")

                exec_result = await _execute_mcp_tool(tool_name, arguments)
                tool_results.append({
                    "tool": tool_name,
                    "arguments": arguments,
                    "result": exec_result,
                })

                # Add tool result as a message
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": json.dumps(exec_result, ensure_ascii=False),
                })

        # Max rounds reached, return last assistant message
        return ChatResponse(
            success=True,
            reply=llm_result.get("content", "") if llm_result else "已达到最大对话轮次",
            tool_results=tool_results if tool_results else None,
        )

    except Exception as e:
        logger.error(f"[AI Chat] 错误: {e}")
        return ChatResponse(success=False, error=str(e))
