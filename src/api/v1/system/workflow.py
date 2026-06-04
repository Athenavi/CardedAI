"""
工作流 API
提供工作流定义、实例管理和执行监控的RESTful接口
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body

from src.api.v1.core.responses import ApiResponse
from shared.services.system.workflow_engine import workflow_engine
from src.auth.auth_deps import jwt_required_dependency as jwt_required

router = APIRouter(tags=["workflows"])


@router.post("/definitions", summary="注册工作流定义")
async def register_workflow(
        workflow_id: str = Body(..., description="工作流ID"),
        definition: Dict[str, Any] = Body(..., description="工作流定义"),
        current_user=Depends(jwt_required)
):
    """
    注册工作流定义
    
    Args:
        workflow_id: 工作流唯一标识
        definition: 工作流定义，包含节点和边的配置
        
    Returns:
        注册结果
    """
    try:
        workflow_engine.register_workflow(workflow_id, definition)

        return ApiResponse(
            success=True,
            data={'workflow_id': workflow_id},
            message="工作流定义注册成功"
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/definitions/{workflow_id}", summary="获取工作流定义")
async def get_workflow_definition(
        workflow_id: str,
        current_user=Depends(jwt_required)
):
    """
    获取工作流定义
    
    Args:
        workflow_id: 工作流ID
        
    Returns:
        工作流定义
    """
    definition = workflow_engine.workflows.get(workflow_id)

    if not definition:
        return ApiResponse(success=False, error="工作流定义不存在")

    return ApiResponse(
        success=True,
        data={
            'workflow_id': workflow_id,
            'definition': definition
        }
    )


@router.post("/instances", summary="创建工作流实例")
async def create_workflow_instance(
        workflow_id: str = Body(..., description="工作流ID"),
        context: Dict[str, Any] = Body(default={}, description="上下文数据"),
        current_user=Depends(jwt_required)
):
    """
    创建工作流实例
    
    Args:
        workflow_id: 工作流ID
        context: 初始上下文数据
        
    Returns:
        创建的实例ID
    """
    try:
        instance_id = workflow_engine.create_instance(workflow_id, context)

        return ApiResponse(
            success=True,
            data={
                'instance_id': instance_id,
                'workflow_id': workflow_id
            },
            message="工作流实例创建成功"
        )
    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=f"创建失败: {str(e)}")


@router.post("/instances/{instance_id}/execute", summary="执行工作流实例")
async def execute_workflow_instance(
        instance_id: str,
        current_user=Depends(jwt_required)
):
    """
    执行工作流实例
    
    Args:
        instance_id: 实例ID
        
    Returns:
        执行结果
    """
    try:
        import asyncio
        success = await asyncio.create_task(
            workflow_engine.execute_instance(instance_id)
        )

        instance = workflow_engine.get_instance(instance_id)

        return ApiResponse(
            success=success,
            data=instance,
            message="工作流执行成功" if success else "工作流执行失败"
        )
    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=f"执行失败: {str(e)}")


@router.get("/instances/{instance_id}", summary="获取工作流实例")
async def get_workflow_instance(
        instance_id: str,
        current_user=Depends(jwt_required)
):
    """
    获取工作流实例详情
    
    Args:
        instance_id: 实例ID
        
    Returns:
        实例详情
    """
    instance = workflow_engine.get_instance(instance_id)

    if not instance:
        return ApiResponse(success=False, error="工作流实例不存在")

    return ApiResponse(
        success=True,
        data=instance
    )


@router.post("/instances/{instance_id}/cancel", summary="取消工作流实例")
async def cancel_workflow_instance(
        instance_id: str,
        current_user=Depends(jwt_required)
):
    """
    取消工作流实例
    
    Args:
        instance_id: 实例ID
        
    Returns:
        取消结果
    """
    success = workflow_engine.cancel_instance(instance_id)

    if not success:
        return ApiResponse(success=False, error="无法取消该工作流实例")

    return ApiResponse(
        success=True,
        message="工作流实例已取消"
    )


@router.get("/instances/{instance_id}/history", summary="获取执行历史")
async def get_execution_history(
        instance_id: str,
        limit: int = 100,
        current_user=Depends(jwt_required)
):
    """
    获取工作流执行历史
    
    Args:
        instance_id: 实例ID
        limit: 返回数量限制
        
    Returns:
        执行历史记录
    """
    history = workflow_engine.get_execution_history(instance_id, limit)

    return ApiResponse(
        success=True,
        data={
            'instance_id': instance_id,
            'history': history,
            'total': len(history)
        }
    )


@router.get("/examples", summary="获取工作流示例")
async def get_workflow_examples(current_user=Depends(jwt_required)):
    """
    获取工作流示例模板
    
    Returns:
        示例列表
    """
    examples = {
        "article_publish_workflow": {
            "description": "文章发布审批工作流",
            "workflow_id": "article_publish",
            "definition": {
                "name": "文章发布审批",
                "description": "文章提交后需要经过编辑审批才能发布",
                "nodes": [
                    {
                        "id": "start",
                        "type": "start",
                        "config": {},
                    },
                    {
                        "id": "check_content",
                        "type": "action",
                        "config": {
                            "action_type": "validate_article",
                        },
                    },
                    {
                        "id": "approval",
                        "type": "approval",
                        "config": {
                            "approver": "editor",
                            "approval_type": "manual",
                        },
                    },
                    {
                        "id": "condition",
                        "type": "condition",
                        "config": {
                            "conditions": [
                                {"field": "approved", "operator": "equals", "value": True}
                            ]
                        },
                    },
                    {
                        "id": "publish",
                        "type": "action",
                        "config": {
                            "action_type": "publish_article",
                        },
                    },
                    {
                        "id": "reject",
                        "type": "action",
                        "config": {
                            "action_type": "notify_author",
                        },
                    },
                    {
                        "id": "end",
                        "type": "end",
                        "config": {},
                    }
                ],
                "edges": [
                    {"from": "start", "to": "check_content"},
                    {"from": "check_content", "to": "approval"},
                    {"from": "approval", "to": "condition"},
                    {"from": "condition", "to": "publish", "condition": "true"},
                    {"from": "condition", "to": "reject", "condition": "false"},
                    {"from": "publish", "to": "end"},
                    {"from": "reject", "to": "end"}
                ]
            }
        },
        "comment_moderation_workflow": {
            "description": "评论审核工作流",
            "workflow_id": "comment_moderation",
            "definition": {
                "name": "评论审核",
                "description": "新评论需要经过审核才能显示",
                "nodes": [
                    {
                        "id": "start",
                        "type": "start",
                        "config": {},
                    },
                    {
                        "id": "spam_check",
                        "type": "action",
                        "config": {
                            "action_type": "check_spam",
                        },
                    },
                    {
                        "id": "auto_approve",
                        "type": "condition",
                        "config": {
                            "conditions": [
                                {"field": "is_spam", "operator": "equals", "value": False}
                            ]
                        },
                    },
                    {
                        "id": "manual_review",
                        "type": "approval",
                        "config": {
                            "approver": "admin",
                        },
                    },
                    {
                        "id": "approve",
                        "type": "action",
                        "config": {
                            "action_type": "approve_comment",
                        },
                    },
                    {
                        "id": "reject",
                        "type": "action",
                        "config": {
                            "action_type": "reject_comment",
                        },
                    },
                    {
                        "id": "end",
                        "type": "end",
                        "config": {},
                    }
                ],
                "edges": [
                    {"from": "start", "to": "spam_check"},
                    {"from": "spam_check", "to": "auto_approve"},
                    {"from": "auto_approve", "to": "approve", "condition": "true"},
                    {"from": "auto_approve", "to": "manual_review", "condition": "false"},
                    {"from": "manual_review", "to": "approve", "condition": "true"},
                    {"from": "manual_review", "to": "reject", "condition": "false"},
                    {"from": "approve", "to": "end"},
                    {"from": "reject", "to": "end"}
                ]
            }
        },
        "user_registration_workflow": {
            "description": "用户注册审核工作流",
            "workflow_id": "user_registration",
            "definition": {
                "name": "用户注册审核",
                "description": "新用户注册需要邮箱验证和管理员审核",
                "nodes": [
                    {
                        "id": "start",
                        "type": "start",
                        "config": {},
                    },
                    {
                        "id": "send_verification",
                        "type": "action",
                        "config": {
                            "action_type": "send_email",
                        },
                    },
                    {
                        "id": "wait_verification",
                        "type": "delay",
                        "config": {
                            "seconds": 3600,
                        },
                    },
                    {
                        "id": "check_verified",
                        "type": "condition",
                        "config": {
                            "conditions": [
                                {"field": "email_verified", "operator": "equals", "value": True}
                            ]
                        },
                    },
                    {
                        "id": "admin_approval",
                        "type": "approval",
                        "config": {
                            "approver": "admin",
                        },
                    },
                    {
                        "id": "activate",
                        "type": "action",
                        "config": {
                            "action_type": "activate_user",
                        },
                    },
                    {
                        "id": "reject",
                        "type": "action",
                        "config": {
                            "action_type": "reject_registration",
                        },
                    },
                    {
                        "id": "end",
                        "type": "end",
                        "config": {},
                    }
                ],
                "edges": [
                    {"from": "start", "to": "send_verification"},
                    {"from": "send_verification", "to": "wait_verification"},
                    {"from": "wait_verification", "to": "check_verified"},
                    {"from": "check_verified", "to": "admin_approval", "condition": "true"},
                    {"from": "check_verified", "to": "reject", "condition": "false"},
                    {"from": "admin_approval", "to": "activate", "condition": "true"},
                    {"from": "admin_approval", "to": "reject", "condition": "false"},
                    {"from": "activate", "to": "end"},
                    {"from": "reject", "to": "end"}
                ]
            }
        }
    }

    return ApiResponse(
        success=True,
        data=examples
    )
