"""
Schema.org 结构化数据生成 API

提供自动生成各种 Schema.org JSON-LD 结构化数据的接口
支持: Article, Organization, Person, WebSite, FAQPage, BreadcrumbList, ImageObject, VideoObject
"""

from typing import List, Optional, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from shared.services.system.schema_generator import schema_generator
from src.api.v1.core.responses import ApiResponse
from src.api.v1.users.user_management import jwt_required

router = APIRouter(tags=["Schema.org"])


# ==================== 请求模型 ====================

class ArticleSchemaRequest(BaseModel):
    """文章 Schema 请求"""
    title: str = Field(..., description="文章标题")
    description: str = Field(..., description="文章描述")
    url: str = Field(..., description="文章 URL")
    author_name: str = Field(..., description="作者名称")
    author_url: Optional[str] = Field("", description="作者主页 URL")
    publish_date: Optional[str] = Field(None, description="发布日期 (ISO 8601)")
    modified_date: Optional[str] = Field(None, description="修改日期 (ISO 8601)")
    image_url: Optional[str] = Field("", description="特色图片 URL")
    keywords: Optional[List[str]] = Field(None, description="关键词列表")
    category: Optional[str] = Field("", description="分类")


class OrganizationSchemaRequest(BaseModel):
    """组织 Schema 请求"""
    name: str = Field(..., description="组织名称")
    url: str = Field(..., description="组织网址")
    logo_url: Optional[str] = Field("", description="Logo URL")
    description: Optional[str] = Field("", description="组织描述")
    social_profiles: Optional[Dict[str, str]] = Field(None, description="社交媒体资料 {platform: url}")
    contact_email: Optional[str] = Field("", description="联系邮箱")
    phone: Optional[str] = Field("", description="联系电话")


class PersonSchemaRequest(BaseModel):
    """人物 Schema 请求"""
    name: str = Field(..., description="姓名")
    job_title: Optional[str] = Field("", description="职位")
    description: Optional[str] = Field("", description="个人描述")
    image_url: Optional[str] = Field("", description="头像 URL")
    url: Optional[str] = Field("", description="个人主页 URL")
    social_profiles: Optional[Dict[str, str]] = Field(None, description="社交媒体资料")


class WebsiteSchemaRequest(BaseModel):
    """网站 Schema 请求"""
    name: str = Field(..., description="网站名称")
    url: str = Field(..., description="网站首页 URL")
    description: Optional[str] = Field("", description="网站描述")
    search_url: Optional[str] = Field("", description="搜索页面 URL（带占位符）")


class FAQItem(BaseModel):
    """FAQ 项目"""
    question: str = Field(..., description="问题")
    answer: str = Field(..., description="答案")


class FAQSchemaRequest(BaseModel):
    """FAQ Schema 请求"""
    questions: List[FAQItem] = Field(..., description="问题列表")


class BreadcrumbItem(BaseModel):
    """面包屑项目"""
    name: str = Field(..., description="名称")
    url: str = Field(..., description="URL")


class BreadcrumbSchemaRequest(BaseModel):
    """面包屑 Schema 请求"""
    items: List[BreadcrumbItem] = Field(..., description="面包屑项列表")


class ImageSchemaRequest(BaseModel):
    """图片 Schema 请求"""
    url: str = Field(..., description="图片 URL")
    caption: Optional[str] = Field("", description="图片说明")
    width: Optional[int] = Field(0, description="宽度")
    height: Optional[int] = Field(0, description="高度")


class VideoSchemaRequest(BaseModel):
    """视频 Schema 请求"""
    name: str = Field(..., description="视频标题")
    description: str = Field(..., description="视频描述")
    thumbnail_url: str = Field(..., description="缩略图 URL")
    upload_date: str = Field(..., description="上传日期 (ISO 8601)")
    content_url: Optional[str] = Field("", description="视频文件 URL")
    embed_url: Optional[str] = Field("", description="嵌入 URL")
    duration: Optional[str] = Field("", description="时长 (ISO 8601)")


# ==================== API 端点 ====================

@router.post("/article")
async def generate_article_schema(request: ArticleSchemaRequest, current_user=Depends(jwt_required)):
    """生成文章 Schema.org 结构化数据"""
    schema = schema_generator.generate_article_schema(
        title=request.title,
        description=request.description,
        url=request.url,
        author_name=request.author_name,
        author_url=request.author_url,
        publish_date=request.publish_date,
        modified_date=request.modified_date,
        image_url=request.image_url,
        keywords=request.keywords,
        category=request.category
    )

    return ApiResponse(
        success=True,
        data={
            "schema": schema,
            "json_ld": schema_generator.to_json_ld(schema),
            "script_tag": schema_generator.to_script_tag(schema)
        }
    )


@router.post("/organization")
async def generate_organization_schema(request: OrganizationSchemaRequest, current_user=Depends(jwt_required)):
    """生成组织 Schema.org 结构化数据"""
    schema = schema_generator.generate_organization_schema(
        name=request.name,
        url=request.url,
        logo_url=request.logo_url,
        description=request.description,
        social_profiles=request.social_profiles,
        contact_email=request.contact_email,
        phone=request.phone
    )

    return ApiResponse(
        success=True,
        data={
            "schema": schema,
            "json_ld": schema_generator.to_json_ld(schema),
            "script_tag": schema_generator.to_script_tag(schema)
        }
    )


@router.post("/person")
async def generate_person_schema(request: PersonSchemaRequest, current_user=Depends(jwt_required)):
    """生成人物 Schema.org 结构化数据"""
    schema = schema_generator.generate_person_schema(
        name=request.name,
        job_title=request.job_title,
        description=request.description,
        image_url=request.image_url,
        url=request.url,
        social_profiles=request.social_profiles
    )

    return ApiResponse(
        success=True,
        data={
            "schema": schema,
            "json_ld": schema_generator.to_json_ld(schema),
            "script_tag": schema_generator.to_script_tag(schema)
        }
    )


@router.post("/website")
async def generate_website_schema(request: WebsiteSchemaRequest, current_user=Depends(jwt_required)):
    """生成网站 Schema.org 结构化数据"""
    schema = schema_generator.generate_website_schema(
        name=request.name,
        url=request.url,
        description=request.description,
        search_url=request.search_url
    )

    return ApiResponse(
        success=True,
        data={
            "schema": schema,
            "json_ld": schema_generator.to_json_ld(schema),
            "script_tag": schema_generator.to_script_tag(schema)
        }
    )


@router.post("/faq")
async def generate_faq_schema(request: FAQSchemaRequest, current_user=Depends(jwt_required)):
    """生成 FAQ Schema.org 结构化数据"""
    questions = [{"question": q.question, "answer": q.answer} for q in request.questions]
    schema = schema_generator.generate_faq_schema(questions=questions)

    return ApiResponse(
        success=True,
        data={
            "schema": schema,
            "json_ld": schema_generator.to_json_ld(schema),
            "script_tag": schema_generator.to_script_tag(schema)
        }
    )


@router.post("/breadcrumb")
async def generate_breadcrumb_schema(request: BreadcrumbSchemaRequest, current_user=Depends(jwt_required)):
    """生成面包屑导航 Schema.org 结构化数据"""
    items = [{"name": item.name, "url": item.url} for item in request.items]
    schema = schema_generator.generate_breadcrumb_schema(items=items)

    return ApiResponse(
        success=True,
        data={
            "schema": schema,
            "json_ld": schema_generator.to_json_ld(schema),
            "script_tag": schema_generator.to_script_tag(schema)
        }
    )


@router.post("/image")
async def generate_image_schema(request: ImageSchemaRequest, current_user=Depends(jwt_required)):
    """生成图片 Schema.org 结构化数据"""
    schema = schema_generator.generate_image_schema(
        url=request.url,
        caption=request.caption,
        width=request.width,
        height=request.height
    )

    return ApiResponse(
        success=True,
        data={
            "schema": schema,
            "json_ld": schema_generator.to_json_ld(schema),
            "script_tag": schema_generator.to_script_tag(schema)
        }
    )


@router.post("/video")
async def generate_video_schema(request: VideoSchemaRequest, current_user=Depends(jwt_required)):
    """生成视频 Schema.org 结构化数据"""
    schema = schema_generator.generate_video_schema(
        name=request.name,
        description=request.description,
        thumbnail_url=request.thumbnail_url,
        upload_date=request.upload_date,
        content_url=request.content_url,
        embed_url=request.embed_url,
        duration=request.duration
    )

    return ApiResponse(
        success=True,
        data={
            "schema": schema,
            "json_ld": schema_generator.to_json_ld(schema),
            "script_tag": schema_generator.to_script_tag(schema)
        }
    )


@router.get("/types")
async def get_supported_schema_types(current_user=Depends(jwt_required)):
    """获取支持的 Schema.org 类型列表"""
    return ApiResponse(
        success=True,
        data={
            "types": [
                {"type": "Article", "endpoint": "/schema/article", "description": "文章"},
                {"type": "Organization", "endpoint": "/schema/organization", "description": "组织"},
                {"type": "Person", "endpoint": "/schema/person", "description": "人物"},
                {"type": "WebSite", "endpoint": "/schema/website", "description": "网站"},
                {"type": "FAQPage", "endpoint": "/schema/faq", "description": "常见问题"},
                {"type": "BreadcrumbList", "endpoint": "/schema/breadcrumb", "description": "面包屑导航"},
                {"type": "ImageObject", "endpoint": "/schema/image", "description": "图片"},
                {"type": "VideoObject", "endpoint": "/schema/video", "description": "视频"}
            ]
        }
    )
