"""
预制模板库 API

提供模板浏览、预览和应用功能
"""

from typing import Optional

from fastapi import APIRouter, Depends

from shared.services.templates.template_library import template_library, TemplateCategory
from src.api.v1.core.responses import ApiResponse
from src.api.v1.users.user_management import jwt_required

router = APIRouter(prefix="/templates", tags=["Template Library"])


@router.get("/list")
async def list_templates(
        category: Optional[str] = None,
        search: Optional[str] = None,
        current_user=Depends(jwt_required)
):
    """
    列出所有可用模板
    
    可按分类或关键词搜索
    """
    cat_enum = TemplateCategory(category) if category else None
    templates = template_library.list_templates(category=cat_enum, search=search)

    return ApiResponse(
        success=True,
        data={
            "templates": templates,
            "total": len(templates),
            "categories": template_library.get_categories()
        }
    )


@router.get("/detail/{template_id}")
async def get_template_detail(
        template_id: str,
        current_user=Depends(jwt_required)
):
    """
    获取模板详情
    
    查看模板的完整信息和内容
    """
    template = template_library.get_template(template_id)

    if not template:
        return ApiResponse(
            success=False,
            error=f"Template not found: {template_id}"
        )

    return ApiResponse(
        success=True,
        data=template.to_dict()
    )


@router.get("/preview/{template_id}")
async def preview_template(
        template_id: str,
        current_user=Depends(jwt_required)
):
    """
    预览模板
    
    获取模板的预览内容
    """
    template = template_library.get_template(template_id)

    if not template:
        return ApiResponse(
            success=False,
            error=f"Template not found: {template_id}"
        )

    return ApiResponse(
        success=True,
        data={
            "template_id": template_id,
            "name": template.name,
            "blocks_data": template.blocks_data,
            "html_content": template.html_content,
            "preview_image": template.preview_image,
        }
    )


@router.get("/categories")
async def get_template_categories(current_user=Depends(jwt_required)):
    """
    获取模板分类
    
    查看所有可用的模板分类及数量
    """
    categories = template_library.get_categories()

    return ApiResponse(
        success=True,
        data={
            "categories": categories,
            "total_categories": len(categories)
        }
    )


@router.get("/popular")
async def get_popular_templates(
        limit: int = 10,
        current_user=Depends(jwt_required)
):
    """
    获取热门模板
    
    按受欢迎程度排序
    """
    all_templates = template_library.list_templates()

    # 按热度排序
    sorted_templates = sorted(
        all_templates,
        key=lambda x: x.get("metadata", {}).get("popularity", 0),
        reverse=True
    )

    return ApiResponse(
        success=True,
        data={
            "templates": sorted_templates[:limit],
            "total": len(sorted_templates)
        }
    )


@router.get("/guide")
async def get_templates_guide(current_user=Depends(jwt_required)):
    """
    获取模板使用指南
    """
    guide = {
        "overview": {
            "title": "预制模板库",
            "description": "快速开始内容创作的预制模板集合。",
            "version": "1.0.0"
        },
        "features": [
            "多种模板类型 - 页面、文章、邮件等",
            "即时预览 - 查看模板效果",
            "一键应用 - 快速应用到内容",
            "可自定义 - 修改模板内容",
            "持续更新 - 定期添加新模板"
        ],
        "template_types": [
            {
                "type": "landing_page",
                "name": "落地页",
                "description": "适合产品发布和活动推广",
                "use_cases": ["产品发布", "活动注册", "服务介绍"]
            },
            {
                "type": "about_page",
                "name": "关于页面",
                "description": "展示公司和团队信息",
                "use_cases": ["公司简介", "团队介绍", "品牌故事"]
            },
            {
                "type": "contact_page",
                "name": "联系页面",
                "description": "包含联系表单和信息",
                "use_cases": ["客户联系", "支持请求", "商务合作"]
            },
            {
                "type": "article_layout",
                "name": "文章布局",
                "description": "博客文章的标准布局",
                "use_cases": ["博客文章", "新闻报道", "教程"]
            },
            {
                "type": "email_template",
                "name": "邮件模板",
                "description": "电子邮件营销模板",
                "use_cases": ["欢迎邮件", "通知邮件", "营销邮件"]
            },
            {
                "type": "portfolio",
                "name": "作品集",
                "description": "展示作品和项目",
                "use_cases": ["个人作品集", "项目展示", "案例研究"]
            }
        ],
        "how_to_use": [
            "1. 浏览模板库，找到合适的模板",
            "2. 点击预览查看模板效果",
            "3. 点击'应用模板'将模板加载到编辑器",
            "4. 根据需要修改内容和样式",
            "5. 保存并发布"
        ],
        "best_practices": [
            "选择与目标匹配的模板类型",
            "保持内容简洁明了",
            "使用高质量的图片",
            "确保移动端友好",
            "定期更新模板内容"
        ],
        "api_endpoints": {
            "list_templates": "GET /templates/list - 列出模板",
            "get_detail": "GET /templates/detail/{id} - 获取详情",
            "preview": "GET /templates/preview/{id} - 预览模板",
            "get_categories": "GET /templates/categories - 获取分类",
            "get_popular": "GET /templates/popular - 获取热门模板"
        }
    }

    return ApiResponse(
        success=True,
        data=guide
    )
