"""
AI 辅助功能 API 路由
提供 AI 写作助手、SEO 优化及标签推荐接口
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from shared.services.ai.workflow_service import ai_workflow_service
from src.auth.auth_deps import jwt_required_dependency as jwt_required
from shared.models.user import User

router = APIRouter(prefix="/ai", tags=["AI Features"])


class WritingAssistRequest(BaseModel):
    context: str
    instruction: str  # e.g., "continue", "polish", "translate to English"


class SEOOptimizeRequest(BaseModel):
    title: str
    content: str


class TagRecommendRequest(BaseModel):
    content: str


@router.post("/assist/writing")
async def writing_assist(
        req: WritingAssistRequest,
        current_user: User = Depends(jwt_required)
):
    """P0-3: AI 辅助写作"""
    try:
        result = await ai_workflow_service.assist_writing(current_user.id, req.context, req.instruction)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assist/seo")
async def seo_optimize(
        req: SEOOptimizeRequest,
        current_user: User = Depends(jwt_required)
):
    """P0-4: 自动 SEO 优化建议"""
    try:
        result = await ai_workflow_service.optimize_seo(current_user.id, req.title, req.content)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assist/tags")
async def recommend_tags(
        req: TagRecommendRequest,
        current_user: User = Depends(jwt_required)
):
    """P0-5: 智能标签与分类推荐"""
    try:
        result = await ai_workflow_service.recommend_tags(current_user.id, req.content)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
