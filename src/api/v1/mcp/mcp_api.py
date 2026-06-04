"""
MCP Server API 端点

提供 HTTP 接口供 AI 客户端调用
"""

from typing import Any

from fastapi import APIRouter, Depends, Request, Body

from src.api.v1.core.responses import ApiResponse
from src.api.v1.users.user_management import jwt_required
from src.mcp.server import mcp_server

router = APIRouter(prefix="/mcp", tags=["MCP Server"])


@router.post("/handle")
async def handle_mcp_request(
        request: Request,
        body: Dict[str, Any] = Body(...),
        current_user=Depends(jwt_required)
):
    """
    处理 MCP 请求
    
    统一的请求处理入口，支持资源读取、工具调用等
    """
    result = await mcp_server.handle_request(body)

    return ApiResponse(
        success=True,
        data=result
    )


@router.get("/info")
async def get_server_info(current_user=Depends(jwt_required)):
    """
    获取 MCP Server 信息
    
    返回服务器版本、支持的资源和工具数量
    """
    info = mcp_server.get_server_info()

    return ApiResponse(
        success=True,
        data=info
    )


@router.get("/resources")
async def list_resources(current_user=Depends(jwt_required)):
    """
    列出所有可用资源
    
    返回可访问的资源列表及其描述
    """
    resources = [
        {
            "uri": res["uri"],
            "name": res["name"],
            "description": res["description"],
            "mime_type": res["mime_type"],
        }
        for res in mcp_server.resources.values()
    ]

    return ApiResponse(
        success=True,
        data={
            "resources": resources,
            "total": len(resources)
        }
    )


@router.get("/tools")
async def list_tools(current_user=Depends(jwt_required)):
    """
    列出所有可用工具
    
    返回可调用的工具列表及其参数定义
    """
    tools = [
        {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["parameters"],
        }
        for tool in mcp_server.tools.values()
    ]

    return ApiResponse(
        success=True,
        data={
            "tools": tools,
            "total": len(tools)
        }
    )


@router.get("/prompts")
async def list_prompts(current_user=Depends(jwt_required)):
    """
    列出所有提示词模板
    
    返回可用的提示词模板列表
    """
    prompts = [
        {
            "name": name,
            "description": f"Template for {name}",
        }
        for name in mcp_server.prompts.keys()
    ]

    return ApiResponse(
        success=True,
        data={
            "prompts": prompts,
            "total": len(prompts)
        }
    )


@router.post("/test-connection")
async def test_connection(current_user=Depends(jwt_required)):
    """
    测试 MCP Server 连接
    
    用于客户端验证连接是否正常
    """
    return ApiResponse(
        success=True,
        data={
            "status": "connected",
            "server": mcp_server.name,
            "version": mcp_server.version,
        },
        message="MCP Server connection successful"
    )


@router.get("/guide")
async def get_mcp_guide(current_user=Depends(jwt_required)):
    """
    获取 MCP 使用指南
    """
    guide = {
        "overview": {
            "title": "Model Context Protocol (MCP) 集成",
            "description": "FastBlog 通过 MCP 协议与 AI 模型（如 Claude、Cursor）集成，提供标准化的内容管理接口。",
            "version": "1.0.0"
        },
        "features": [
            "资源访问 - 读取文章、分类、用户、媒体等内容",
            "工具调用 - 创建/更新/删除文章、搜索内容等",
            "提示词模板 - 预定义的写作和优化模板",
            "认证控制 - 基于 JWT 的安全访问",
            "实时同步 - 支持数据实时更新"
        ],
        "client_setup": {
            "claude_desktop": {
                "name": "Claude Desktop",
                "config_file": "~/Library/Application Support/Claude/claude_desktop_config.json",
                "example_config": {
                    "mcpServers": {
                        "fastblog": {
                            "command": "python",
                            "args": ["-m", "src.mcp.cli"],
                            "env": {
                                "FASTBLOG_API_URL": "http://localhost:8000",
                                "FASTBLOG_API_KEY": "your-api-key"
                            }
                        }
                    }
                }
            },
            "cursor_ide": {
                "name": "Cursor IDE",
                "instructions": "在 Cursor 设置中添加 MCP Server 配置，指向 FastBlog API 端点"
            }
        },
        "usage_examples": {
            "read_articles": {
                "description": "读取文章列表",
                "request": {
                    "method": "resources/read",
                    "params": {
                        "uri": "fastblog://articles"
                    }
                }
            },
            "create_article": {
                "description": "创建新文章",
                "request": {
                    "method": "tools/call",
                    "params": {
                        "name": "create_article",
                        "arguments": {
                            "title": "我的新文章",
                            "content": "文章内容...",
                            "status": "draft"
                        }
                    }
                }
            },
            "search_articles": {
                "description": "搜索文章",
                "request": {
                    "method": "tools/call",
                    "params": {
                        "name": "search_articles",
                        "arguments": {
                            "query": "Python",
                            "limit": 10
                        }
                    }
                }
            }
        },
        "available_resources": [
            {
                "uri": "fastblog://articles",
                "description": "访问博客文章列表和内容"
            },
            {
                "uri": "fastblog://categories",
                "description": "访问文章分类"
            },
            {
                "uri": "fastblog://users",
                "description": "访问用户信息"
            },
            {
                "uri": "fastblog://media",
                "description": "访问媒体文件库"
            },
            {
                "uri": "fastblog://settings",
                "description": "访问站点配置信息"
            }
        ],
        "available_tools": [
            {
                "name": "create_article",
                "description": "创建新文章"
            },
            {
                "name": "update_article",
                "description": "更新现有文章"
            },
            {
                "name": "delete_article",
                "description": "删除文章"
            },
            {
                "name": "search_articles",
                "description": "搜索文章"
            },
            {
                "name": "generate_seo_description",
                "description": "为文章生成 SEO 描述"
            },
            {
                "name": "upload_media",
                "description": "上传媒体文件"
            }
        ],
        "security": {
            "authentication": "所有 MCP 请求都需要有效的 JWT Token",
            "permissions": "工具调用会根据用户角色进行权限检查",
            "rate_limiting": "API 速率限制适用于所有 MCP 请求"
        }
    }

    return ApiResponse(
        success=True,
        data=guide
    )
