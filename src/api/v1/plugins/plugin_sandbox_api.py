"""
插件沙箱 API

提供插件安全执行的接口
"""

from fastapi import APIRouter, Depends, Body

from shared.services.plugin_sandbox import plugin_sandbox, ipc_communication
from src.api.v1.core.responses import ApiResponse
from src.api.v1.users.user_management import jwt_required

router = APIRouter(prefix="/plugin-sandbox", tags=["Plugin Sandbox"])


@router.post("/execute")
async def execute_plugin(
        plugin_id: str = Body(..., description="插件ID"),
        plugin_code: str = Body(..., description="插件代码"),
        function_name: str = Body("main", description="要执行的函数名"),
        arguments: dict = Body({}, description="函数参数"),
        current_user=Depends(jwt_required)
):
    """
    在沙箱中执行插件
    
    安全地执行插件代码，隔离于主机系统
    """
    # 验证代码安全性
    validation = plugin_sandbox.validate_plugin_code(plugin_code)

    if not validation["is_safe"]:
        return ApiResponse(
            success=False,
            error="Plugin code contains security issues",
            data={"issues": validation["issues"]}
        )

    # 执行插件
    result = await plugin_sandbox.execute_plugin(
        plugin_id=plugin_id,
        plugin_code=plugin_code,
        function_name=function_name,
        arguments=arguments
    )

    return ApiResponse(
        success=result.success,
        data=result.to_dict()
    )


@router.post("/validate")
async def validate_plugin_code(
        plugin_code: str = Body(..., description="插件代码"),
        current_user=Depends(jwt_required)
):
    """
    验证插件代码安全性
    
    检查插件代码是否包含危险操作
    """
    validation = plugin_sandbox.validate_plugin_code(plugin_code)

    return ApiResponse(
        success=True,
        data=validation
    )


@router.get("/active-plugins")
async def get_active_plugins(current_user=Depends(jwt_required)):
    """
    获取活跃插件列表
    
    查看当前正在运行的插件
    """
    active = plugin_sandbox.get_active_plugins()

    return ApiResponse(
        success=True,
        data={
            "active_plugins": active,
            "total": len(active)
        }
    )


@router.post("/terminate/{plugin_id}")
async def terminate_plugin(
        plugin_id: str,
        current_user=Depends(jwt_required)
):
    """
    终止插件执行
    
    强制停止指定的插件
    """
    plugin_sandbox.terminate_plugin(plugin_id)

    return ApiResponse(
        success=True,
        message=f"Plugin '{plugin_id}' terminated"
    )


@router.get("/history")
async def get_execution_history(
        limit: int = 10,
        current_user=Depends(jwt_required)
):
    """
    获取执行历史
    
    查看最近的插件执行记录
    """
    history = plugin_sandbox.get_execution_history(limit=limit)

    return ApiResponse(
        success=True,
        data={
            "history": history,
            "total": len(history)
        }
    )


@router.post("/ipc/send")
async def send_ipc_message(
        plugin_id: str = Body(..., description="插件ID"),
        message: dict = Body(..., description="消息内容"),
        current_user=Depends(jwt_required)
):
    """
    发送 IPC 消息到插件
    
    与运行中的插件进行通信
    """
    await ipc_communication.send_message(plugin_id, message)

    return ApiResponse(
        success=True,
        message="Message sent successfully"
    )


@router.get("/ipc/receive/{plugin_id}")
async def receive_ipc_message(
        plugin_id: str,
        timeout: int = 5,
        current_user=Depends(jwt_required)
):
    """
    从插件接收 IPC 消息
    
    获取插件发送的消息
    """
    message = await ipc_communication.receive_message(plugin_id, timeout)

    return ApiResponse(
        success=True,
        data={"message": message}
    )


@router.get("/config")
async def get_sandbox_config(current_user=Depends(jwt_required)):
    """
    获取沙箱配置
    
    查看当前的沙箱安全配置
    """
    config = plugin_sandbox.config

    return ApiResponse(
        success=True,
        data={
            "max_execution_time": config.max_execution_time,
            "max_memory_mb": config.max_memory_mb,
            "allowed_paths": config.allowed_paths,
            "allowed_network_hosts": config.allowed_network_hosts,
            "restricted_modules": config.restricted_modules,
        }
    )


@router.get("/guide")
async def get_sandbox_guide(current_user=Depends(jwt_required)):
    """
    获取沙箱使用指南
    """
    guide = {
        "overview": {
            "title": "插件沙箱执行环境",
            "description": "提供安全的插件执行环境，隔离插件与主机系统，防止恶意代码造成损害。",
            "version": "1.0.0"
        },
        "features": [
            "子进程隔离 - 插件在独立进程中运行",
            "文件系统限制 - 限制插件访问的文件路径",
            "网络请求控制 - 限制插件的网络访问范围",
            "资源监控 - 实时监控 CPU 和内存使用",
            "超时控制 - 自动终止长时间运行的插件",
            "IPC 通信 - 安全的进程间通信机制",
            "代码验证 - 执行前检查代码安全性"
        ],
        "security_measures": [
            {
                "name": "模块限制",
                "description": "禁止导入危险模块（os, sys, subprocess等）",
                "restricted": ["os", "sys", "subprocess", "socket", "multiprocessing"]
            },
            {
                "name": "函数限制",
                "description": "禁止调用危险函数（eval, exec, compile等）",
                "restricted": ["eval()", "exec()", "compile()", "__import__()"]
            },
            {
                "name": "文件系统保护",
                "description": "只允许访问指定的安全路径",
                "default_allowed": ["./plugins_data", "./media"]
            },
            {
                "name": "执行超时",
                "description": "默认 30 秒超时，防止无限循环",
                "timeout": "30 seconds"
            },
            {
                "name": "内存限制",
                "description": "限制最大内存使用量",
                "limit": "256 MB"
            }
        ],
        "usage_example": {
            "step_1": "验证代码安全性: POST /plugin-sandbox/validate",
            "step_2": "执行插件: POST /plugin-sandbox/execute",
            "step_3": "监控执行状态: GET /plugin-sandbox/active-plugins",
            "example_request": {
                "plugin_id": "my-plugin",
                "plugin_code": "def main():\n    return {'result': 'success'}",
                "function_name": "main",
                "arguments": {}
            }
        },
        "best_practices": [
            "始终在执行前验证插件代码",
            "设置合理的超时时间",
            "监控插件的资源使用情况",
            "定期清理执行历史记录",
            "使用 IPC 进行安全的进程间通信",
            "不要信任用户提供的插件代码"
        ],
        "api_endpoints": {
            "execution": [
                "POST /plugin-sandbox/execute - 执行插件",
                "POST /plugin-sandbox/validate - 验证代码",
                "GET /plugin-sandbox/active-plugins - 查看活跃插件",
                "POST /plugin-sandbox/terminate/{id} - 终止插件",
                "GET /plugin-sandbox/history - 查看执行历史"
            ],
            "communication": [
                "POST /plugin-sandbox/ipc/send - 发送消息",
                "GET /plugin-sandbox/ipc/receive/{id} - 接收消息"
            ],
            "configuration": [
                "GET /plugin-sandbox/config - 查看配置"
            ]
        }
    }

    return ApiResponse(
        success=True,
        data=guide
    )
