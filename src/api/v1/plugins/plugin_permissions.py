"""
插件权限管理 API

提供插件权限声明、验证、审计等功能
"""

from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, Query, Body
from pydantic import BaseModel, Field

from shared.services.plugins.plugin_audit import plugin_audit_logger
from shared.services.plugins.plugin_manager.manifest import PluginCapability
from shared.services.plugins.plugin_manager.core import plugin_manager
from src.api.v1.core.responses import ApiResponse
from src.api.v1.users.user_management import jwt_required

router = APIRouter(prefix="/plugin-permissions", tags=["Plugin Permissions"])


# ==================== 请求模型 ====================

class PluginCapabilityRequest(BaseModel):
    """插件能力声明"""
    resource: str = Field(..., description="资源类型")
    action: str = Field(..., description="操作类型")
    description: Optional[str] = Field(None, description="能力描述")


class CheckPermissionRequest(BaseModel):
    """检查权限请求"""
    plugin_slug: str = Field(..., description="插件标识")
    capability: str = Field(..., description="权限代码")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")


# ==================== API 端点 ====================

@router.post("/check")
async def check_plugin_permission(request: CheckPermissionRequest, current_user=Depends(jwt_required)):
    """
    检查插件权限

    验证插件是否具有指定的权限，并记录审计日志
    """
    plugin = plugin_manager.get_plugin(request.plugin_slug)
    if plugin is None:
        return ApiResponse(
            success=False,
            data={
                "plugin_slug": request.plugin_slug,
                "capability": request.capability,
                "granted": False,
                "message": f"插件 '{request.plugin_slug}' 不存在"
            }
        )

    has_permission = plugin.has_capability(request.capability)

    # 记录审计日志
    plugin_audit_logger.log_permission_check(
        plugin_slug=request.plugin_slug,
        capability=request.capability,
        granted=has_permission,
        context=request.context
    )

    return ApiResponse(
        success=True,
        data={
            "plugin_slug": request.plugin_slug,
            "capability": request.capability,
            "granted": has_permission,
            "message": "权限已授予" if has_permission else "权限被拒绝"
        }
    )


@router.get("/audit-logs")
async def get_audit_logs(
        plugin_slug: Optional[str] = Query(None, description="插件标识过滤"),
        action_type: Optional[str] = Query(None, description="操作类型过滤"),
        limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
        current_user=Depends(jwt_required)
):
    """
    获取插件权限审计日志

    查看插件的权限使用记录和API调用历史
    """
    logs = plugin_audit_logger.get_audit_logs(
        plugin_slug=plugin_slug,
        action_type=action_type,
        limit=limit
    )

    return ApiResponse(
        success=True,
        data={
            "logs": logs,
            "total": len(logs),
            "filters": {
                "plugin_slug": plugin_slug,
                "action_type": action_type
            }
        }
    )


@router.get("/statistics")
async def get_permission_statistics(
        plugin_slug: Optional[str] = Query(None, description="插件标识过滤"),
        current_user=Depends(jwt_required)
):
    """
    获取权限使用统计

    显示各插件的权限检查次数、授权/拒绝比例等统计数据
    """
    stats = plugin_audit_logger.get_permission_statistics(plugin_slug)

    return ApiResponse(
        success=True,
        data={
            "statistics": stats,
            "plugins_count": len(stats)
        }
    )


@router.post("/{plugin_slug}/detect-anomalies")
async def detect_plugin_anomalies(plugin_slug: str, current_user=Depends(jwt_required)):
    """
    检测插件异常行为

    分析插件的权限使用模式，检测可能的滥用或异常行为
    """
    anomalies = plugin_audit_logger.detect_anomalies(plugin_slug)

    return ApiResponse(
        success=True,
        data={
            "plugin_slug": plugin_slug,
            "anomalies": anomalies,
            "anomaly_count": len(anomalies),
            "severity_summary": {
                "critical": len([a for a in anomalies if a.get("severity") == "critical"]),
                "warning": len([a for a in anomalies if a.get("severity") == "warning"]),
                "info": len([a for a in anomalies if a.get("severity") == "info"])
            }
        }
    )


@router.post("/validate-capabilities")
async def validate_plugin_capabilities(
        capabilities: List[PluginCapabilityRequest] = Body(..., description="能力列表"),
        current_user=Depends(jwt_required)
):
    """
    验证插件能力声明

    检查插件声明的能力是否有效和合理
    """
    validation_results = []
    errors = []

    for cap_req in capabilities:
        try:
            # 创建能力对象进行验证
            capability = PluginCapability(
                resource=cap_req.resource,
                action=cap_req.action,
                description=cap_req.description
            )

            validation_results.append({
                "resource": capability.resource,
                "action": capability.action,
                "description": capability.description,
                "valid": True,
                "capability_code": f"{capability.resource}:{capability.action}"
            })

        except Exception as e:
            errors.append({
                "resource": cap_req.resource,
                "action": cap_req.action,
                "valid": False,
                "error": str(e)
            })

    return ApiResponse(
        success=len(errors) == 0,
        data={
            "validated_capabilities": validation_results,
            "errors": errors,
            "total": len(capabilities),
            "valid_count": len(validation_results),
            "invalid_count": len(errors)
        },
        message=f"验证完成：{len(validation_results)} 个有效，{len(errors)} 个无效"
    )


@router.get("/available-capabilities")
async def get_available_capabilities(current_user=Depends(jwt_required)):
    """
    获取所有可用的能力列表

    返回系统支持的所有资源类型和操作组合
    """
    capabilities = {
        "articles": {
            "read": "读取文章",
            "write": "创建/更新文章",
            "delete": "删除文章",
            "publish": "发布文章",
            "moderate": "审核文章"
        },
        "users": {
            "read": "读取用户信息",
            "write": "创建/更新用户",
            "delete": "删除用户",
            "manage_roles": "管理用户角色"
        },
        "categories": {
            "read": "读取分类",
            "write": "创建/更新分类",
            "delete": "删除分类"
        },
        "media": {
            "read": "读取媒体文件",
            "upload": "上传文件",
            "delete": "删除文件"
        },
        "settings": {
            "read": "读取设置",
            "write": "修改设置"
        },
        "comments": {
            "read": "读取评论",
            "write": "创建/更新评论",
            "delete": "删除评论",
            "moderate": "审核评论"
        },
        "tags": {
            "read": "读取标签",
            "write": "创建/更新标签",
            "delete": "删除标签"
        },
        "pages": {
            "read": "读取页面",
            "write": "创建/更新页面",
            "delete": "删除页面"
        },
        "filesystem": {
            "read": "读取文件系统",
            "write": "写入文件系统",
            "delete": "删除文件"
        },
        "database": {
            "read": "读取数据库",
            "write": "写入数据库"
        },
        "network": {
            "execute": "执行网络请求"
        },
        "email": {
            "send": "发送邮件"
        },
        "plugins": {
            "read": "读取插件信息",
            "activate": "激活/停用插件",
            "configure": "配置插件"
        },
        "themes": {
            "read": "读取主题信息",
            "activate": "激活主题",
            "customize": "自定义主题"
        }
    }

    # 转换为列表格式
    capability_list = []
    for resource, actions in capabilities.items():
        for action, description in actions.items():
            capability_list.append({
                "resource": resource,
                "action": action,
                "code": f"{resource}:{action}",
                "description": description
            })

    return ApiResponse(
        success=True,
        data={
            "capabilities": capability_list,
            "total": len(capability_list),
            "resources": list(capabilities.keys())
        }
    )


@router.post("/clear-old-logs")
async def clear_old_logs(
        days: int = Body(30, ge=1, le=365, description="保留天数"),
        current_user=Depends(jwt_required)
):
    """
    清理旧的审计日志

    删除指定天数之前的日志文件
    """
    plugin_audit_logger.clear_old_logs(days)

    return ApiResponse(
        success=True,
        message=f"已清理 {days} 天前的审计日志"
    )


@router.get("/guide")
async def get_permissions_guide(current_user=Depends(jwt_required)):
    """
    获取插件权限使用指南

    提供详细的权限声明和使用文档
    """
    guide = {
        "overview": {
            "title": "插件权限系统",
            "description": "FastBlog 插件权限系统基于能力（Capabilities）模型，插件必须声明其需要的权限才能访问相应的资源和功能。"
        },
        "how_to_declare": {
            "step_1": "在插件的 metadata.json 中添加 capabilities 字段",
            "step_2": "声明所需的最小权限集合（最小权限原则）",
            "step_3": "为每个权限提供清晰的描述",
            "example": {
                "metadata.json": {
                    "name": "Example Plugin",
                    "slug": "example-plugin",
                    "version": "1.0.0",
                    "capabilities": [
                        {
                            "resource": "articles",
                            "action": "read",
                            "description": "读取文章以生成相关文章推荐"
                        },
                        {
                            "resource": "articles",
                            "action": "write",
                            "description": "创建自动生成的草稿文章"
                        }
                    ]
                }
            }
        },
        "best_practices": [
            "遵循最小权限原则，只申请必要的权限",
            "为每个权限提供清晰的用途说明",
            "在代码中检查权限后再执行操作",
            "优雅处理权限被拒绝的情况",
            "定期审查和更新权限声明",
            "避免过度使用高频权限检查"
        ],
        "permission_format": {
            "format": "<resource>:<action>",
            "examples": [
                "articles:read - 读取文章",
                "articles:write - 创建/更新文章",
                "users:read - 读取用户信息",
                "media:upload - 上传文件",
                "settings:write - 修改设置"
            ]
        },
        "security_notes": [
            "所有权限使用都会被审计记录",
            "异常的权限使用模式会被自动检测",
            "频繁的权限检查可能导致性能问题",
            "权限拒绝率过高会触发安全告警",
            "插件沙箱会强制执行权限限制"
        ],
        "common_patterns": {
            "content_plugin": {
                "description": "内容相关插件通常需要",
                "capabilities": [
                    "articles:read",
                    "articles:write",
                    "categories:read",
                    "tags:read"
                ]
            },
            "media_plugin": {
                "description": "媒体处理插件通常需要",
                "capabilities": [
                    "media:read",
                    "media:upload",
                    "filesystem:read",
                    "filesystem:write"
                ]
            },
            "notification_plugin": {
                "description": "通知插件通常需要",
                "capabilities": [
                    "users:read",
                    "email:send",
                    "settings:read"
                ]
            }
        }
    }

    return ApiResponse(
        success=True,
        data=guide
    )
