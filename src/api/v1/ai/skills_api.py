"""
AI Agent Skills API

提供 Skills 的管理、执行和查询接口
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Body, Query

from shared.services.ai.core_skills import register_core_skills
from shared.services.ai.skills_framework import (
    skill_registry,
    SkillContext,
    SkillCategory,
)
from src.api.v1.core.responses import ApiResponse
from src.api.v1.users.user_management import jwt_required

router = APIRouter(prefix="/ai-skills", tags=["AI Agent Skills"])

# 自动注册核心 Skills
register_core_skills()


@router.get("/list")
async def list_skills(
        category: Optional[str] = Query(None, description="过滤分类"),
        tag: Optional[str] = Query(None, description="过滤标签"),
        current_user=Depends(jwt_required)
):
    """
    列出所有可用的 Skills
    
    可按分类或标签过滤
    """
    try:
        cat_enum = SkillCategory(category) if category else None
        skills = skill_registry.list_skills(category=cat_enum, tag=tag)

        return ApiResponse(
            success=True,
            data={
                "skills": skills,
                "total": len(skills),
                "categories": skill_registry.get_categories()
            }
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e)
        )


@router.get("/info/{skill_name}")
async def get_skill_info(
        skill_name: str,
        current_user=Depends(jwt_required)
):
    """
    获取 Skill 详细信息
    
    包括元数据、状态、执行统计等
    """
    skill = skill_registry.get_skill(skill_name)

    if not skill:
        return ApiResponse(
            success=False,
            error=f"Skill not found: {skill_name}"
        )

    return ApiResponse(
        success=True,
        data=skill.get_info()
    )


@router.post("/execute/{skill_name}")
async def execute_skill(
        skill_name: str,
        parameters: dict = Body(..., description="Skill 参数"),
        current_user=Depends(jwt_required)
):
    """
    执行 Skill
    
    在沙箱环境中安全执行指定的 Skill
    """
    # 创建执行上下文
    context = SkillContext(
        user_id=current_user.id,
        request_id=str(uuid.uuid4()),
        parameters=parameters
    )

    # 执行 Skill
    result = await skill_registry.execute_skill(skill_name, context)

    if result.success:
        return ApiResponse(
            success=True,
            data=result.to_dict()
        )
    else:
        return ApiResponse(
            success=False,
            error=result.error
        )


@router.post("/activate/{skill_name}")
async def activate_skill(
        skill_name: str,
        current_user=Depends(jwt_required)
):
    """
    激活 Skill
    
    将 Skill 状态设置为活跃，使其可被执行
    """
    skill = skill_registry.get_skill(skill_name)

    if not skill:
        return ApiResponse(
            success=False,
            error=f"Skill not found: {skill_name}"
        )

    await skill.on_activate()

    return ApiResponse(
        success=True,
        message=f"Skill '{skill_name}' activated"
    )


@router.post("/deactivate/{skill_name}")
async def deactivate_skill(
        skill_name: str,
        current_user=Depends(jwt_required)
):
    """
    停用 Skill
    
    将 Skill 状态设置为非活跃，阻止其执行
    """
    skill = skill_registry.get_skill(skill_name)

    if not skill:
        return ApiResponse(
            success=False,
            error=f"Skill not found: {skill_name}"
        )

    await skill.on_deactivate()

    return ApiResponse(
        success=True,
        message=f"Skill '{skill_name}' deactivated"
    )


@router.get("/categories")
async def get_skill_categories(current_user=Depends(jwt_required)):
    """
    获取 Skill 分类统计
    
    返回每个分类下的 Skill 数量
    """
    categories = skill_registry.get_categories()

    return ApiResponse(
        success=True,
        data={
            "categories": categories,
            "total_categories": len([c for c in categories.values() if c > 0])
        }
    )


@router.get("/templates")
async def get_skill_templates(current_user=Depends(jwt_required)):
    """
    获取 Skill 使用模板
    
    提供常见使用场景的参数模板
    """
    templates = {
        "content_creation": {
            "generate_outline": {
                "description": "生成文章大纲",
                "parameters": {
                    "action": "generate_outline",
                    "topic": "你的主题"
                }
            },
            "expand_paragraph": {
                "description": "扩写段落",
                "parameters": {
                    "action": "expand_paragraph",
                    "text": "要扩写的文本"
                }
            },
            "optimize_title": {
                "description": "优化标题",
                "parameters": {
                    "action": "optimize_title",
                    "title": "原始标题"
                }
            }
        },
        "seo_optimization": {
            "generate_meta_description": {
                "description": "生成 Meta 描述",
                "parameters": {
                    "action": "generate_meta_description",
                    "content": "文章内容"
                }
            },
            "analyze_keyword_density": {
                "description": "分析关键词密度",
                "parameters": {
                    "action": "analyze_keyword_density",
                    "content": "文章内容",
                    "keyword": "目标关键词"
                }
            }
        },
        "plugin_generation": {
            "create_plugin": {
                "description": "生成插件代码",
                "parameters": {
                    "name": "my-plugin",
                    "description": "插件功能描述"
                }
            }
        }
    }

    return ApiResponse(
        success=True,
        data=templates
    )


@router.get("/guide")
async def get_skills_guide(current_user=Depends(jwt_required)):
    """
    获取 Skills 使用指南
    """
    guide = {
        "overview": {
            "title": "AI Agent Skills 系统",
            "description": "FastBlog 的 AI Agent Skills 提供可扩展的 AI 功能，支持内容创作、SEO优化、代码生成等任务。",
            "version": "1.0.0"
        },
        "features": [
            "模块化设计 - 每个 Skill 独立开发和部署",
            "安全沙箱 - 所有 Skill 在隔离环境中执行",
            "权限控制 - 基于角色的访问控制",
            "执行监控 - 实时监控 Skill 执行状态和性能",
            "易于扩展 - 简单的 API 即可添加新 Skills"
        ],
        "available_skills": [
            {
                "name": "content_creator",
                "description": "AI 辅助内容创作",
                "capabilities": [
                    "文章大纲生成",
                    "段落扩写/缩写",
                    "标题优化建议",
                    "关键词提取"
                ]
            },
            {
                "name": "seo_optimizer",
                "description": "SEO 优化工具",
                "capabilities": [
                    "Meta 描述生成",
                    "关键词密度分析",
                    "可读性评分",
                    "内部链接建议"
                ]
            },
            {
                "name": "plugin_generator",
                "description": "插件代码生成",
                "capabilities": [
                    "根据描述生成插件框架",
                    "自动生成文档",
                    "标准目录结构"
                ]
            },
            {
                "name": "theme_builder",
                "description": "主题样式生成",
                "capabilities": [
                    "CSS 代码生成",
                    "配色方案建议",
                    "响应式设计"
                ]
            },
            {
                "name": "data_migrator",
                "description": "数据迁移助手",
                "capabilities": [
                    "WordPress 数据导入",
                    "Halo 数据迁移",
                    "格式转换"
                ]
            }
        ],
        "usage_example": {
            "step_1": "列出可用 Skills: GET /ai-skills/list",
            "step_2": "查看 Skill 详情: GET /ai-skills/info/content_creator",
            "step_3": "执行 Skill: POST /ai-skills/execute/content_creator",
            "example_request": {
                "parameters": {
                    "action": "generate_outline",
                    "topic": "Python 编程入门"
                }
            }
        },
        "development": {
            "create_custom_skill": [
                "继承 BaseSkill 类",
                "实现 execute 方法",
                "定义 SkillMetadata",
                "注册到 skill_registry"
            ],
            "documentation": "参考 shared/services/ai/skills_framework.py"
        },
        "security": {
            "sandbox": "所有 Skills 在沙箱中执行，限制资源访问",
            "timeout": "默认执行超时 30 秒",
            "memory_limit": "最大内存使用 256MB",
            "permissions": "基于用户角色的权限验证"
        }
    }

    return ApiResponse(
        success=True,
        data=guide
    )
