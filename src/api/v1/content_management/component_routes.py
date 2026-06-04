"""
预制组件库 API 路由
提供组件模板的查询和渲染功能
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query
from pydantic import BaseModel

from shared.services.content_management.component_library import component_library

router = APIRouter(prefix="/components", tags=["Component Library"])


class ComponentInfo(BaseModel):
    """组件信息"""
    name: str
    category: str
    description: str
    preview_html: str
    default_data: Dict[str, Any]
    customization_options: Dict[str, Any]


@router.get("/templates", response_model=List[ComponentInfo])
async def list_component_templates(
        category: Optional[str] = Query(None, description="按分类过滤")
):
    """P2-3: 获取所有组件模板
    
    Args:
        category: 可选，按分类过滤 (marketing, content, layout, forms)
        
    Returns:
        组件模板列表
    """
    if category:
        components = component_library.get_components_by_category(category)
    else:
        components = component_library.get_all_components()

    return [
        ComponentInfo(
            name=c.name,
            category=c.category,
            description=c.description,
            preview_html=c.preview_html,
            default_data=c.default_data,
            customization_options=c.customization_options
        )
        for c in components
    ]


@router.get("/categories", response_model=List[str])
async def list_component_categories():
    """P2-3: 获取所有组件分类
    
    Returns:
        分类名称列表
    """
    categories = set(c.category for c in component_library.get_all_components())
    return list(categories)


@router.get("/templates/{component_name}", response_model=ComponentInfo)
async def get_component_template(component_name: str):
    """P2-3: 获取单个组件模板详情
    
    Args:
        component_name: 组件名称
        
    Returns:
        组件模板信息
    """
    component = component_library.get_component(component_name)

    return ComponentInfo(
        name=component.name,
        category=component.category,
        description=component.description,
        preview_html=component.preview_html,
        default_data=component.default_data,
        customization_options=component.customization_options
    )


class RenderComponentRequest(BaseModel):
    """渲染组件请求"""
    component_name: str
    data: Optional[Dict[str, Any]] = None


class RenderComponentResponse(BaseModel):
    """渲染组件响应"""
    html: str


@router.post("/render", response_model=RenderComponentResponse)
async def render_component(req: RenderComponentRequest):
    """P2-3: 渲染组件为 HTML
    
    Args:
        req: 渲染请求，包含组件名称和自定义数据
        
    Returns:
        渲染后的 HTML
    """
    html = component_library.render_component(req.component_name, req.data)

    return RenderComponentResponse(html=html)


@router.get("/examples/{component_name}")
async def get_component_examples(component_name: str):
    """P2-3: 获取组件使用示例
    
    Args:
        component_name: 组件名称
        
    Returns:
        使用示例和最佳实践
    """
    examples = {
        "hero-section": {
            "basic": {
                "title": "Welcome to Our Platform",
                "subtitle": "Build amazing things with us",
                "cta_text": "Get Started",
                "alignment": "center"
            },
            "with_background_image": {
                "title": "Discover the Future",
                "subtitle": "Innovation starts here",
                "background_type": "image",
                "background_color": "from-gray-900 to-black"
            }
        },
        "features-grid": {
            "three_columns": {
                "title": "Why Choose Us",
                "columns": 3,
                "features": [
                    {"icon": "⚡", "title": "Fast", "description": "Lightning speed"},
                    {"icon": "🔒", "title": "Secure", "description": "Enterprise security"},
                    {"icon": "🤖", "title": "Smart", "description": "AI-powered"}
                ]
            }
        },
        "pricing-table": {
            "three_tiers": {
                "title": "Choose Your Plan",
                "plans": [
                    {
                        "name": "Free",
                        "price": "$0",
                        "period": "/mo",
                        "features": ["Basic features"],
                        "button_text": "Start Free"
                    },
                    {
                        "name": "Pro",
                        "price": "$29",
                        "period": "/mo",
                        "features": ["All features", "Priority support"],
                        "highlighted": True,
                        "button_style": "filled"
                    },
                    {
                        "name": "Enterprise",
                        "price": "$99",
                        "period": "/mo",
                        "features": ["Custom solutions", "Dedicated support"]
                    }
                ]
            }
        }
    }

    component_examples = examples.get(component_name, {})

    return {
        "component": component_name,
        "examples": component_examples,
        "documentation": f"See full documentation at /docs/components/{component_name}"
    }
