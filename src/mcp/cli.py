"""
MCP (Model Context Protocol) CLI — stdio 传输层

使用方式（在 MCP 客户端配置中）：
    "command": "python",
    "args": ["-m", "src.mcp.cli"]

MCP stdio 协议：
- 读取 stdin 获取 JSON-RPC 请求（每行一个 JSON 对象）
- 处理请求并输出 JSON-RPC 响应到 stdout（每行一个 JSON 对象）
- 日志输出到 stderr（不干扰 stdio 数据通道）
"""

import asyncio
import json
import sys
import traceback
from pathlib import Path

# 将项目根目录加入 sys.path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


def _log(msg: str) -> None:
    """输出日志到 stderr（避免污染 stdout 数据通道）"""
    print(f"[MCP-CLI] {msg}", file=sys.stderr, flush=True)


async def _read_message() -> dict | None:
    """从 stdin 读取一行 JSON-RPC 消息"""
    loop = asyncio.get_event_loop()
    line = await loop.run_in_executor(None, sys.stdin.readline)
    if not line:
        return None
    line = line.strip()
    if not line:
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError as e:
        _log(f"无效的 JSON-RPC 消息: {e}")
        return None


def _write_message(msg: dict) -> None:
    """输出 JSON-RPC 响应到 stdout"""
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


async def _handle_initialize(request: dict) -> dict:
    """处理 MCP initialize 请求——返回服务器能力"""
    _log("收到 initialize 请求")
    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "resources": {
                    "subscribe": True,
                    "listChanged": True,
                },
                "tools": {
                    "listChanged": True,
                },
                "prompts": {
                    "listChanged": True,
                },
                "logging": {},
            },
            "serverInfo": {
                "name": "fastblog-mcp",
                "version": "1.0.0",
            },
        },
    }


async def _handle_ping(request: dict) -> dict:
    """处理 ping 请求"""
    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "result": {},
    }


async def main():
    """MCP stdio 主循环"""
    _log(f"启动 MCP Server (项目根目录: {_project_root})")
    _log(f"Python: {sys.version}")

    # 延迟导入以避免启动时加载整个应用
    from src.mcp.server import mcp_server

    _log(f"MCP Server 已初始化: {mcp_server.get_server_info()}")

    initialized = False

    while True:
        request = await _read_message()
        if request is None:
            _log("stdin 已关闭，退出")
            break

        method = request.get("method", "")
        _log(f"收到请求: method={method}, id={request.get('id')}")

        try:
            # MCP 协议生命周期方法——由本 CLI 层处理
            if method == "initialize":
                response = await _handle_initialize(request)

            elif method == "initialized":
                initialized = True
                response = {"jsonrpc": "2.0", "id": request.get("id"), "result": {}}

            elif method == "ping":
                response = await _handle_ping(request)

            elif method == "notifications/initialized":
                initialized = True
                # 通知类消息不需要响应
                continue

            elif method == "notifications/cancelled":
                _log(f"请求被取消: {request.get('params', {})}")
                continue

            else:
                # 委托给 MCPServer 处理（resources/*, tools/*, prompts/*）
                response = await mcp_server.handle_request(request)

            _write_message(response)

        except Exception as exc:
            _log(f"处理请求失败: {exc}\n{traceback.format_exc()}")
            _write_message({
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(exc)}",
                },
            })


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        _log("收到中断信号，退出")
    except Exception as e:
        _log(f"致命错误: {e}\n{traceback.format_exc()}")
        sys.exit(1)
