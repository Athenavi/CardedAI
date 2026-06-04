"""
页面构建器 API 路由
提供页面的创建、保存、加载、发布和删除功能
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.page_builder import PageBuilder
from src.auth.auth_deps import jwt_required_dependency as jwt_required
from shared.models.user import User
from src.utils.database.main import get_async_session

router = APIRouter(prefix="/page-builder", tags=["Page Builder"])


class PageCreateRequest(BaseModel):
    """创建页面请求"""
    title: str
    slug: str
    blocks_data: list = []  # JSON 数组
    template_name: Optional[str] = None
    is_published: bool = False


class PageUpdateRequest(BaseModel):
    """更新页面请求"""
    title: Optional[str] = None
    blocks_data: Optional[list] = None
    template_name: Optional[str] = None
    is_published: Optional[bool] = None


class PageResponse(BaseModel):
    """页面响应"""
    id: int
    title: str
    slug: str
    blocks_data: list
    template_name: Optional[str] = None
    is_published: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.post("/pages", response_model=PageResponse)
async def create_page(
        req: PageCreateRequest,
        current_user: User = Depends(jwt_required)
):
    """P2-1: 创建新页面
    
    Args:
        req: 页面创建请求
        current_user: 当前登录用户
        
    Returns:
        创建的页面对象
    """
    async for db in get_async_session():
        # 检查 slug 是否已存在
        existing = await db.execute(
            select(PageBuilder).where(PageBuilder.slug == req.slug)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"Slug '{req.slug}' 已存在")

        # 创建新页面
        new_page = PageBuilder(
            title=req.title,
            slug=req.slug,
            blocks_data=str(req.blocks_data),  # 存储为 JSON 字符串
            template_name=req.template_name,
            is_published=req.is_published,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(new_page)
        await db.commit()
        await db.refresh(new_page)

        # 解析 blocks_data 为列表返回
        import json
        try:
            blocks = json.loads(new_page.blocks_data)
        except:
            blocks = []

        return PageResponse(
            id=new_page.id,
            title=new_page.title,
            slug=new_page.slug,
            blocks_data=blocks,
            template_name=new_page.template_name,
            is_published=new_page.is_published,
            created_at=new_page.created_at.isoformat() if new_page.created_at else None,
            updated_at=new_page.updated_at.isoformat() if new_page.updated_at else None
        )


@router.get("/pages", response_model=List[PageResponse])
async def list_pages(
        skip: int = Query(0, ge=0),
        limit: int = Query(20, ge=1, le=100),
        published_only: bool = Query(False),
        current_user: User = Depends(jwt_required)
):
    """P2-1: 获取页面列表
    
    Args:
        skip: 跳过数量
        limit: 限制数量
        published_only: 仅返回已发布页面
        
    Returns:
        页面列表
    """
    async for db in get_async_session():
        query = select(PageBuilder)

        if published_only:
            query = query.where(PageBuilder.is_published == True)

        query = query.order_by(desc(PageBuilder.created_at)).offset(skip).limit(limit)

        result = await db.execute(query)
        pages = result.scalars().all()

        import json
        response_list = []
        for page in pages:
            try:
                blocks = json.loads(page.blocks_data)
            except:
                blocks = []

            response_list.append(PageResponse(
                id=page.id,
                title=page.title,
                slug=page.slug,
                blocks_data=blocks,
                template_name=page.template_name,
                is_published=page.is_published,
                created_at=page.created_at.isoformat() if page.created_at else None,
                updated_at=page.updated_at.isoformat() if page.updated_at else None
            ))

        return response_list


@router.get("/pages/{page_id}", response_model=PageResponse)
async def get_page(
        page_id: int,
        current_user: User = Depends(jwt_required)
):
    """P2-1: 获取单个页面详情
    
    Args:
        page_id: 页面 ID
        
    Returns:
        页面对象
    """
    async for db in get_async_session():
        result = await db.execute(
            select(PageBuilder).where(PageBuilder.id == page_id)
        )
        page = result.scalar_one_or_none()

        if not page:
            raise HTTPException(status_code=404, detail="页面不存在")

        import json
        try:
            blocks = json.loads(page.blocks_data)
        except:
            blocks = []

        return PageResponse(
            id=page.id,
            title=page.title,
            slug=page.slug,
            blocks_data=blocks,
            template_name=page.template_name,
            is_published=page.is_published,
            created_at=page.created_at.isoformat() if page.created_at else None,
            updated_at=page.updated_at.isoformat() if page.updated_at else None
        )


@router.put("/pages/{page_id}", response_model=PageResponse)
async def update_page(
        page_id: int,
        req: PageUpdateRequest,
        current_user: User = Depends(jwt_required)
):
    """P2-1: 更新页面
    
    Args:
        page_id: 页面 ID
        req: 更新请求
        
    Returns:
        更新后的页面对象
    """
    async for db in get_async_session():
        result = await db.execute(
            select(PageBuilder).where(PageBuilder.id == page_id)
        )
        page = result.scalar_one_or_none()

        if not page:
            raise HTTPException(status_code=404, detail="页面不存在")

        # 更新字段
        if req.title is not None:
            page.title = req.title
        if req.blocks_data is not None:
            page.blocks_data = str(req.blocks_data)
        if req.template_name is not None:
            page.template_name = req.template_name
        if req.is_published is not None:
            page.is_published = req.is_published

        page.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(page)

        import json
        try:
            blocks = json.loads(page.blocks_data)
        except:
            blocks = []

        return PageResponse(
            id=page.id,
            title=page.title,
            slug=page.slug,
            blocks_data=blocks,
            template_name=page.template_name,
            is_published=page.is_published,
            created_at=page.created_at.isoformat() if page.created_at else None,
            updated_at=page.updated_at.isoformat() if page.updated_at else None
        )


@router.delete("/pages/{page_id}")
async def delete_page(
        page_id: int,
        current_user: User = Depends(jwt_required)
):
    """P2-1: 删除页面
    
    Args:
        page_id: 页面 ID
        
    Returns:
        删除结果
    """
    async for db in get_async_session():
        result = await db.execute(
            select(PageBuilder).where(PageBuilder.id == page_id)
        )
        page = result.scalar_one_or_none()

        if not page:
            raise HTTPException(status_code=404, detail="页面不存在")

        await db.delete(page)
        await db.commit()

        return {"success": True, "message": "页面已删除"}


@router.post("/pages/{page_id}/publish")
async def publish_page(
        page_id: int,
        current_user: User = Depends(jwt_required)
):
    """P2-1: 发布页面
    
    Args:
        page_id: 页面 ID
        
    Returns:
        发布结果
    """
    async for db in get_async_session():
        result = await db.execute(
            select(PageBuilder).where(PageBuilder.id == page_id)
        )
        page = result.scalar_one_or_none()

        if not page:
            raise HTTPException(status_code=404, detail="页面不存在")

        page.is_published = True
        page.updated_at = datetime.utcnow()

        await db.commit()

        return {"success": True, "message": "页面已发布"}


@router.post("/pages/{page_id}/unpublish")
async def unpublish_page(
        page_id: int,
        current_user: User = Depends(jwt_required)
):
    """P2-1: 取消发布页面
    
    Args:
        page_id: 页面 ID
        
    Returns:
        取消发布结果
    """
    async for db in get_async_session():
        result = await db.execute(
            select(PageBuilder).where(PageBuilder.id == page_id)
        )
        page = result.scalar_one_or_none()

        if not page:
            raise HTTPException(status_code=404, detail="页面不存在")

        page.is_published = False
        page.updated_at = datetime.utcnow()

        await db.commit()

        return {"success": True, "message": "页面已取消发布"}


@router.get("/pages/slug/{slug}", response_model=PageResponse)
async def get_page_by_slug(slug: str):
    """P2-1: 通过 slug 获取公开页面（无需认证）
    
    Args:
        slug: 页面路径标识
        
    Returns:
        页面对象（仅已发布的）
    """
    async for db in get_async_session():
        result = await db.execute(
            select(PageBuilder).where(
                (PageBuilder.slug == slug) &
                (PageBuilder.is_published == True)
            )
        )
        page = result.scalar_one_or_none()

        if not page:
            raise HTTPException(status_code=404, detail="页面不存在或未发布")

        import json
        try:
            blocks = json.loads(page.blocks_data)
        except:
            blocks = []

        return PageResponse(
            id=page.id,
            title=page.title,
            slug=page.slug,
            blocks_data=blocks,
            template_name=page.template_name,
            is_published=page.is_published,
            created_at=page.created_at.isoformat() if page.created_at else None,
            updated_at=page.updated_at.isoformat() if page.updated_at else None
        )


# P6-4: 预建页面模板库
PAGE_TEMPLATES = [
    {
        "id": "landing-page",
        "name": "Landing Page",
        "category": "营销",
        "description": "高转化率的产品落地页，包含 Hero、特性、CTA、评价等模块",
        "preview_image": "/templates/landing-page.png",
        "blocks": [
            {
                "type": "hero-section",
                "data": {
                    "title": "打造您的下一个伟大产品",
                    "subtitle": "快速启动，轻松扩展",
                    "cta_text": "立即开始",
                    "cta_link": "/signup"
                },
                "styles": {"backgroundColor": "#f8fafc", "padding": 80}
            },
            {
                "type": "features-grid",
                "data": {
                    "title": "为什么选择我们",
                    "features": [
                        {"icon": "zap", "title": "极速性能", "desc": "毫秒级响应"},
                        {"icon": "shield", "title": "安全可靠", "desc": "企业级加密"},
                        {"icon": "globe", "title": "全球部署", "desc": "CDN 加速"}
                    ]
                },
                "styles": {"padding": 60}
            },
            {
                "type": "testimonials",
                "data": {
                    "title": "用户评价",
                    "testimonials": [
                        {"name": "张三", "role": "CEO", "quote": "这个产品改变了我们的工作方式！"},
                        {"name": "李四", "role": "CTO", "quote": "技术架构非常先进"}
                    ]
                },
                "styles": {"backgroundColor": "#ffffff", "padding": 60}
            },
            {
                "type": "cta-section",
                "data": {
                    "title": "准备好开始了吗？",
                    "subtitle": "加入 10,000+ 满意用户",
                    "button_text": "免费注册",
                    "button_link": "/signup"
                },
                "styles": {"backgroundColor": "#3b82f6", "color": "#ffffff", "padding": 80}
            }
        ]
    },
    {
        "id": "about-page",
        "name": "About Us",
        "category": "企业",
        "description": "公司介绍页面，展示团队、使命和价值观",
        "preview_image": "/templates/about-page.png",
        "blocks": [
            {
                "type": "hero-section",
                "data": {
                    "title": "关于我们",
                    "subtitle": "创新、协作、卓越",
                    "background_image": "/images/team.jpg"
                },
                "styles": {"padding": 100}
            },
            {
                "type": "team-members",
                "data": {
                    "title": "核心团队",
                    "members": [
                        {"name": "王五", "role": "创始人 & CEO", "avatar": "/avatars/1.jpg"},
                        {"name": "赵六", "role": "CTO", "avatar": "/avatars/2.jpg"},
                        {"name": "孙七", "role": "设计总监", "avatar": "/avatars/3.jpg"}
                    ]
                },
                "styles": {"padding": 60}
            }
        ]
    },
    {
        "id": "contact-page",
        "name": "Contact",
        "category": "企业",
        "description": "联系页面，包含表单和地图",
        "preview_image": "/templates/contact-page.png",
        "blocks": [
            {
                "type": "contact-form",
                "data": {
                    "title": "联系我们",
                    "subtitle": "有任何问题？随时留言",
                    "fields": ["name", "email", "message"]
                },
                "styles": {"padding": 60}
            }
        ]
    },
    {
        "id": "pricing-page",
        "name": "Pricing",
        "category": "营销",
        "description": "价格对比页面，支持多套餐展示",
        "preview_image": "/templates/pricing-page.png",
        "blocks": [
            {
                "type": "pricing-table",
                "data": {
                    "title": "选择适合您的方案",
                    "plans": [
                        {"name": "免费版", "price": "¥0", "features": ["基础功能", "社区支持"]},
                        {"name": "专业版", "price": "¥99/月", "features": ["全部功能", "优先支持"],
                         "highlighted": True},
                        {"name": "企业版", "price": "定制", "features": ["专属服务", "SLA 保障"]}
                    ]
                },
                "styles": {"padding": 80}
            }
        ]
    },
    {
        "id": "faq-page",
        "name": "FAQ",
        "category": "支持",
        "description": "常见问题解答页面",
        "preview_image": "/templates/faq-page.png",
        "blocks": [
            {
                "type": "faq-section",
                "data": {
                    "title": "常见问题",
                    "faqs": [
                        {"question": "如何开始使用？", "answer": "注册账号后即可免费试用"},
                        {"question": "支持哪些支付方式？", "answer": "支付宝、微信、信用卡"}
                    ]
                },
                "styles": {"padding": 60}
            }
        ]
    },
    {
        "id": "blog-homepage",
        "name": "Blog Homepage",
        "category": "博客",
        "description": "博客首页，展示最新文章和分类",
        "preview_image": "/templates/blog-homepage.png",
        "blocks": [
            {
                "type": "hero-section",
                "data": {
                    "title": "技术博客",
                    "subtitle": "分享前沿技术与实践经验"
                },
                "styles": {"padding": 80}
            }
        ]
    },
    {
        "id": "portfolio-page",
        "name": "Portfolio",
        "category": "作品集",
        "description": "作品展示页面，适合设计师和开发者",
        "preview_image": "/templates/portfolio-page.png",
        "blocks": [
            {
                "type": "features-grid",
                "data": {
                    "title": "精选作品",
                    "features": [
                        {"icon": "image", "title": "项目 A", "desc": "Web 应用开发"},
                        {"icon": "image", "title": "项目 B", "desc": "移动 App 设计"}
                    ]
                },
                "styles": {"padding": 60}
            }
        ]
    },
    {
        "id": "event-page",
        "name": "Event Landing",
        "category": "营销",
        "description": "活动报名页面，包含倒计时和报名表单",
        "preview_image": "/templates/event-page.png",
        "blocks": [
            {
                "type": "hero-section",
                "data": {
                    "title": "2026 技术大会",
                    "subtitle": "2026年10月15日 · 北京",
                    "cta_text": "立即报名",
                    "countdown": True
                },
                "styles": {"backgroundColor": "#1e293b", "color": "#ffffff", "padding": 100}
            }
        ]
    },
    {
        "id": "documentation-page",
        "name": "Documentation",
        "category": "支持",
        "description": "文档中心页面，侧边栏导航 + 内容区",
        "preview_image": "/templates/documentation-page.png",
        "blocks": [
            {
                "type": "features-grid",
                "data": {
                    "title": "快速开始",
                    "features": [
                        {"icon": "book", "title": "安装指南", "desc": "5分钟快速上手"},
                        {"icon": "code", "title": "API 参考", "desc": "完整接口文档"}
                    ]
                },
                "styles": {"padding": 60}
            }
        ]
    },
    {
        "id": "coming-soon-page",
        "name": "Coming Soon",
        "category": "营销",
        "description": "即将上线页面，收集邮箱订阅",
        "preview_image": "/templates/coming-soon-page.png",
        "blocks": [
            {
                "type": "hero-section",
                "data": {
                    "title": "即将上线",
                    "subtitle": "敬请期待我们的新产品",
                    "email_signup": True
                },
                "styles": {"backgroundColor": "#0f172a", "color": "#ffffff", "padding": 120}
            }
        ]
    }
]


@router.get("/templates")
async def list_templates():
    """P6-4: 获取所有预建页面模板
    
    Returns:
        模板列表
    """
    return PAGE_TEMPLATES


@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    """P6-4: 获取单个模板详情
    
    Args:
        template_id: 模板 ID
        
    Returns:
        模板对象
    """
    template = next((t for t in PAGE_TEMPLATES if t["id"] == template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return template


@router.post("/pages/from-template")
async def create_page_from_template(
        template_id: str,
        title: str,
        slug: str,
        current_user: User = Depends(jwt_required)
):
    """P6-4: 从模板创建页面
    
    Args:
        template_id: 模板 ID
        title: 页面标题
        slug: 页面路径
        
    Returns:
        创建的页面对象
    """
    template = next((t for t in PAGE_TEMPLATES if t["id"] == template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    async for db in get_async_session():
        # 检查 slug 是否已存在
        existing = await db.execute(
            select(PageBuilder).where(PageBuilder.slug == slug)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"Slug '{slug}' 已存在")

        import json
        # 创建新页面
        new_page = PageBuilder(
            title=title,
            slug=slug,
            blocks_data=json.dumps(template["blocks"]),
            template_name=template_id,
            is_published=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(new_page)
        await db.commit()
        await db.refresh(new_page)

        try:
            blocks = json.loads(new_page.blocks_data)
        except:
            blocks = []

        return PageResponse(
            id=new_page.id,
            title=new_page.title,
            slug=new_page.slug,
            blocks_data=blocks,
            template_name=new_page.template_name,
            is_published=new_page.is_published,
            created_at=new_page.created_at.isoformat() if new_page.created_at else None,
            updated_at=new_page.updated_at.isoformat() if new_page.updated_at else None
        )
