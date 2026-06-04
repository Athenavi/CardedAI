"""
内容质量检测 API 端点
"""

from fastapi import APIRouter, Depends, Request

from shared.services.seo.content_quality import content_quality_service
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required

router = APIRouter(tags=["content-quality"])


@router.post("/analyze")
async def analyze_content_quality(
        request: Request,
        current_user=Depends(jwt_required)
):
    """
    分析文章内容质量
    
    请求体:
    - content: 文章内容
    - title: 文章标题（可选）
    - excerpt: 文章摘要（可选）
    
    返回:
    - score: 质量评分 (0-100)
    - grade: 等级 (A/B/C/D/F)
    - issues: 发现的问题列表
    - suggestions: 改进建议
    - readability: 可读性分析
    - keyword_density: 关键词密度分析
    - structure: 结构分析
    - tone: 语气分析
    - completeness: 完整性检查
    """
    try:
        body = await request.json()

        content = body.get('content', '')
        title = body.get('title', '')
        excerpt = body.get('excerpt', '')

        if not content:
            return ApiResponse(
                success=False,
                error="文章内容不能为空"
            )

        result = content_quality_service.analyze_content_quality(content, title, excerpt)

        return ApiResponse(
            success=True,
            data=result
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/check-grammar")
async def check_grammar(
        request: Request,
        current_user=Depends(jwt_required)
):
    """
    检查语法错误
    
    请求体:
    - content: 文章内容
    
    返回:
    - issues: 语法问题列表
    """
    try:
        body = await request.json()
        content = body.get('content', '')

        if not content:
            return ApiResponse(
                success=False,
                error="文章内容不能为空"
            )

        issues = content_quality_service._check_grammar(content)

        return ApiResponse(
            success=True,
            data={
                'issues': issues,
                'total_issues': len(issues)
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/analyze-readability")
async def analyze_readability(
        request: Request,
        current_user=Depends(jwt_required)
):
    """
    分析可读性
    
    请求体:
    - content: 文章内容
    
    返回:
    - score: 可读性评分
    - level: 难度级别
    - avg_sentence_length: 平均句子长度
    """
    try:
        body = await request.json()
        content = body.get('content', '')

        if not content:
            return ApiResponse(
                success=False,
                error="文章内容不能为空"
            )

        result = content_quality_service._analyze_readability(content)

        return ApiResponse(
            success=True,
            data=result
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/analyze-tone")
async def analyze_tone(
        request: Request,
        current_user=Depends(jwt_required)
):
    """
    分析语气风格
    
    请求体:
    - content: 文章内容
    
    返回:
    - issues: 语气问题列表
    - suggestions: 改进建议
    """
    try:
        body = await request.json()
        content = body.get('content', '')

        if not content:
            return ApiResponse(
                success=False,
                error="文章内容不能为空"
            )

        result = content_quality_service._analyze_tone(content)

        return ApiResponse(
            success=True,
            data=result
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))
