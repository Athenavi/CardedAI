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
from src.api.v1.core.responses import ApiResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ai"])


# ==================== 请求模型 ====================

class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]]
    llm_endpoint: str = "https://api.openai.com/v1"
    llm_key: str = ""
    model: str = "gpt-4o"
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096


# ==================== 核心逻辑 ====================

def _get_mcp_server():
    from src.mcp.server import mcp_server
    return mcp_server


def _build_openai_tools() -> List[Dict[str, Any]]:
    """将 MCP 工具列表转换为 OpenAI function calling 格式"""
    mcp = _get_mcp_server()
    tools = []
    for name, tool in mcp.tools.items():
        props = {}
        required = []
        for pname, pdef in tool["parameters"].items():
            ptype = pdef.get("type", "string")
            json_type = {"integer": "integer", "string": "string", "boolean": "boolean",
                         "array": "array", "number": "number"}.get(ptype, "string")
            props[pname] = {"type": json_type, "description": pdef.get("description", "")}
            if pdef.get("required", False):
                required.append(pname)
        tools.append({
            "type": "function",
            "function": {
                "name": name,
                "description": tool["description"],
                "parameters": {"type": "object", "properties": props, "required": required},
            },
        })
    return tools


async def _call_llm(messages, llm_endpoint, llm_key, model, tools, system_prompt=None,
                    temperature=0.7, max_tokens=4096) -> Dict:
    full = [{"role": "system", "content": system_prompt}] if system_prompt else []
    full.extend(messages)

    payload = {"model": model, "messages": full, "temperature": temperature, "max_tokens": max_tokens}
    if tools:
        payload["tools"] = tools

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{llm_endpoint.rstrip('/')}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {llm_key}", "Content-Type": "application/json"},
        )

    if resp.status_code != 200:
        return {"success": False, "error": f"LLM API error ({resp.status_code}): {resp.text[:300]}"}

    data = resp.json()
    choice = data.get("choices", [{}])[0]
    message = choice.get("message", {})
    result = {"success": True, "content": message.get("content", ""), "tool_calls": []}

    for tc in message.get("tool_calls", []):
        func = tc.get("function", {})
        try:
            arguments = json.loads(func.get("arguments", "{}"))
        except json.JSONDecodeError:
            arguments = {}
        result["tool_calls"].append({
            "id": tc.get("id", ""),
            "type": "function",
            "function": {"name": func.get("name", ""), "arguments": arguments},
        })

    return result


async def _execute_mcp_tool(tool_name: str, arguments: dict) -> dict:
    mcp = _get_mcp_server()
    result = await mcp._handle_tool_call({"name": tool_name, "arguments": arguments}, request_id="ai-chat")
    content = result.get("result", {}).get("content", [{}])[0].get("text", "")
    error = result.get("error", {}).get("message", "")
    if error:
        return {"success": False, "error": error}
    try:
        return {"success": True, "data": json.loads(content)}
    except (json.JSONDecodeError, TypeError):
        return {"success": True, "data": content}


# ==================== API 端点 ====================

@router.post("/mcp-chat", summary="MCP AI 对话代理")
async def mcp_chat(req: ChatRequest, current_user: UserModel = Depends(jwt_required)):
    if not req.llm_key:
        return ApiResponse(success=False, error="请提供 API Key (sk-...)")
    if not req.llm_endpoint:
        return ApiResponse(success=False, error="请提供 LLM 端点地址")

    try:
        sys_prompt = req.system_prompt or (
            "你是一个 CardedAI 站点管理助手。你可以通过以下工具帮助用户管理站点。\n\n"
            "使用规则：\n"
            "1. 优先使用工具完成用户请求\n"
            "2. 如果工具返回结果，基于结果给出友好的回复\n"
            "3. 如果工具调用失败，向用户解释错误原因\n"
            "4. 对于不确定的操作，先询问用户确认"
        )

        tools = _build_openai_tools()
        messages = list(req.messages)
        tool_results = []
        final_reply = ""

        for _ in range(10):
            llm_result = await _call_llm(
                messages=messages, llm_endpoint=req.llm_endpoint, llm_key=req.llm_key,
                model=req.model, tools=tools,
                system_prompt=sys_prompt if _ == 0 else None,
                temperature=req.temperature, max_tokens=req.max_tokens,
            )

            if not llm_result.get("success"):
                return ApiResponse(success=False, error=llm_result.get("error", "LLM 调用失败"))

            content = llm_result.get("content", "")
            tool_calls = llm_result.get("tool_calls", [])

            msg = {"role": "assistant", "content": content or None}
            if tool_calls:
                msg["tool_calls"] = [
                    {"id": tc["id"], "type": "function",
                     "function": {"name": tc["function"]["name"],
                                  "arguments": json.dumps(tc["function"]["arguments"], ensure_ascii=False)}}
                    for tc in tool_calls
                ]
            messages.append(msg)

            if not tool_calls:
                final_reply = content
                break

            for tc in tool_calls:
                exec_result = await _execute_mcp_tool(tc["function"]["name"], tc["function"]["arguments"])
                tool_results.append({"tool": tc["function"]["name"], "arguments": tc["function"]["arguments"],
                                      "result": exec_result})
                messages.append({"role": "tool", "tool_call_id": tc["id"],
                                  "content": json.dumps(exec_result, ensure_ascii=False)})

        return ApiResponse(success=True, data={
            "reply": final_reply,
            "tool_results": tool_results if tool_results else None,
        })

    except Exception as e:
        logger.error(f"[AI Chat] 错误: {e}")
        return ApiResponse(success=False, error=str(e))
