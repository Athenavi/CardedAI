"""
AI 辅助内容创作 API

提供智能写作助手和自动 SEO 优化功能
"""

from typing import List

from fastapi import APIRouter, Depends, Body

from api.v1.users.user_management import jwt_required
from shared.services.ai.content_creator import ai_writing_assistant, seo_optimizer
from src.api.v1.core.responses import ApiResponse

router = APIRouter(prefix="/ai-content", tags=["AI Content Creation"])


@router.post("/generate-outline")
async def generate_outline(
        topic: str = Body(..., description="文章主题"),
        target_audience: str = Body("general", description="目标读者"),
        article_length: str = Body("medium", description="文章长度 (short/medium/long)"),
        tone: str = Body("professional", description="语气风格"),
        current_user=Depends(jwt_required)
):
    """
    生成文章大纲
    
    根据主题自动生成结构化的文章大纲
    """
    try:
        outline = await ai_writing_assistant.generate_article_outline(
            topic=topic,
            target_audience=target_audience,
            article_length=article_length,
            tone=tone
        )

        return ApiResponse(
            success=True,
            data=outline
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e)
        )


@router.post("/expand-paragraph")
async def expand_paragraph(
        text: str = Body(..., description="原始文本"),
        expansion_ratio: float = Body(1.5, description="扩展比例 (1.0-3.0)"),
        style: str = Body("detailed", description="扩展风格"),
        current_user=Depends(jwt_required)
):
    """
    扩写段落
    
    将简短的段落扩展为更详细的内容
    """
    try:
        result = await ai_writing_assistant.expand_paragraph(
            text=text,
            expansion_ratio=expansion_ratio,
            style=style
        )

        return ApiResponse(
            success=True,
            data=result
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e)
        )


@router.post("/optimize-title")
async def optimize_title(
        title: str = Body(..., description="原始标题"),
        optimization_type: str = Body("all", description="优化类型"),
        current_user=Depends(jwt_required)
):
    """
    优化标题
    
    生成多个标题优化建议，包括 SEO、吸引力、专业性等维度
    """
    try:
        result = await ai_writing_assistant.optimize_title(
            title=title,
            optimization_type=optimization_type
        )

        return ApiResponse(
            success=True,
            data=result
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e)
        )


@router.post("/extract-keywords")
async def extract_keywords(
        content: str = Body(..., description="文章内容"),
        max_keywords: int = Body(10, description="最大关键词数量"),
        current_user=Depends(jwt_required)
):
    """
    提取关键词
    
    从文章内容中提取重要关键词
    """
    try:
        result = await ai_writing_assistant.extract_keywords(
            content=content,
            max_keywords=max_keywords
        )

        return ApiResponse(
            success=True,
            data=result
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e)
        )


@router.post("/generate-meta-description")
async def generate_meta_description(
        content: str = Body(..., description="文章内容"),
        title: str = Body("", description="文章标题"),
        max_length: int = Body(160, description="最大长度"),
        current_user=Depends(jwt_required)
):
    """
    生成 Meta 描述
    
    为文章自动生成 SEO 友好的 Meta 描述
    """
    try:
        result = await seo_optimizer.generate_meta_description(
            content=content,
            title=title,
            max_length=max_length
        )

        return ApiResponse(
            success=True,
            data=result
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e)
        )


@router.post("/analyze-keyword-density")
async def analyze_keyword_density(
        content: str = Body(..., description="文章内容"),
        target_keywords: List[str] = Body(..., description="目标关键词列表"),
        current_user=Depends(jwt_required)
):
    """
    分析关键词密度
    
    检查文章中关键词的使用频率和密度
    """
    try:
        result = await seo_optimizer.analyze_keyword_density(
            content=content,
            target_keywords=target_keywords
        )

        return ApiResponse(
            success=True,
            data=result
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e)
        )


@router.post("/check-readability")
async def check_readability(
        content: str = Body(..., description="文章内容"),
        current_user=Depends(jwt_required)
):
    """
    检查可读性
    
    评估文章的可读性评分并提供改进建议
    """
    try:
        result = await seo_optimizer.check_readability(content=content)

        return ApiResponse(
            success=True,
            data=result
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e)
        )


@router.post("/suggest-internal-links")
async def suggest_internal_links(
        content: str = Body(..., description="文章内容"),
        available_articles: List[dict] = Body([], description="可用文章列表"),
        current_user=Depends(jwt_required)
):
    """
    建议内部链接
    
    基于文章内容推荐相关的内部链接
    """
    try:
        result = await seo_optimizer.suggest_internal_links(
            content=content,
            available_articles=available_articles
        )

        return ApiResponse(
            success=True,
            data=result
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e)
        )


@router.post("/full-seo-analysis")
async def full_seo_analysis(
        title: str = Body(..., description="文章标题"),
        content: str = Body(..., description="文章内容"),
        target_keywords: List[str] = Body([], description="目标关键词"),
        current_user=Depends(jwt_required)
):
    """
    完整 SEO 分析
    
    对文章进行全面的 SEO 分析和优化建议
    """
    try:
        # 并行执行多项分析
        meta_result = await seo_optimizer.generate_meta_description(
            content=content,
            title=title
        )

        readability_result = await seo_optimizer.check_readability(
            content=content
        )

        keyword_result = None
        if target_keywords:
            keyword_result = await seo_optimizer.analyze_keyword_density(
                content=content,
                target_keywords=target_keywords
            )

        analysis = {
            "title": title,
            "meta_description": meta_result,
            "readability": readability_result,
            "keyword_analysis": keyword_result,
            "overall_score": calculate_overall_seo_score(
                meta_result,
                readability_result,
                keyword_result
            ),
            "recommendations": generate_comprehensive_recommendations(
                meta_result,
                readability_result,
                keyword_result
            )
        }

        return ApiResponse(
            success=True,
            data=analysis
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e)
        )


@router.get("/history")
async def get_generation_history(
        limit: int = 10,
        current_user=Depends(jwt_required)
):
    """
    获取生成历史
    
    查看最近的 AI 生成记录
    """
    history = ai_writing_assistant.generation_history[-limit:]

    return ApiResponse(
        success=True,
        data={
            "writing_history": history,
            "seo_optimization_history": seo_optimizer.optimization_history[-limit:],
            "total_writing": len(ai_writing_assistant.generation_history),
            "total_seo": len(seo_optimizer.optimization_history)
        }
    )


@router.get("/guide")
async def get_ai_content_guide(current_user=Depends(jwt_required)):
    """
    获取 AI 内容创作使用指南
    """
    guide = {
        "overview": {
            "title": "AI 辅助内容创作系统",
            "description": "利用 AI 技术辅助内容创作，提高写作效率和质量。",
            "version": "1.0.0"
        },
        "features": [
            "智能大纲生成 - 根据主题自动生成结构化大纲",
            "段落扩写 - 将简短内容扩展为详细论述",
            "标题优化 - 生成多个标题变体供选择",
            "关键词提取 - 自动识别文章核心关键词",
            "Meta 描述生成 - 创建 SEO 友好的页面描述",
            "关键词密度分析 - 监控关键词使用频率",
            "可读性评分 - 评估文章易读程度",
            "内部链接建议 - 推荐相关内容链接"
        ],
        "use_cases": [
            {
                "scenario": "快速创建文章草稿",
                "steps": [
                    "1. 使用 generate-outline 生成大纲",
                    "2. 根据大纲撰写初稿",
                    "3. 使用 expand-paragraph 扩展关键段落",
                    "4. 使用 optimize-title 优化标题",
                    "5. 使用 full-seo-analysis 进行全面检查"
                ]
            },
            {
                "scenario": "SEO 优化现有文章",
                "steps": [
                    "1. 使用 check-readability 评估可读性",
                    "2. 使用 analyze-keyword-density 检查关键词",
                    "3. 使用 generate-meta-description 创建描述",
                    "4. 使用 suggest-internal-links 添加内链",
                    "5. 根据建议进行修改"
                ]
            }
        ],
        "best_practices": [
            "AI 生成的内容需要人工审核和编辑",
            "保持内容的真实性和准确性",
            "不要过度依赖自动化工具",
            "定期更新和优化已有内容",
            "关注用户体验而非仅追求 SEO"
        ],
        "api_endpoints": {
            "content_creation": [
                "POST /ai-content/generate-outline - 生成大纲",
                "POST /ai-content/expand-paragraph - 扩写段落",
                "POST /ai-content/optimize-title - 优化标题",
                "POST /ai-content/extract-keywords - 提取关键词"
            ],
            "seo_optimization": [
                "POST /ai-content/generate-meta-description - 生成 Meta 描述",
                "POST /ai-content/analyze-keyword-density - 分析关键词密度",
                "POST /ai-content/check-readability - 检查可读性",
                "POST /ai-content/suggest-internal-links - 建议内链",
                "POST /ai-content/full-seo-analysis - 完整 SEO 分析"
            ]
        }
    }

    return ApiResponse(
        success=True,
        data=guide
    )


# ==================== 辅助函数 ====================

def calculate_overall_seo_score(
        meta_result: dict,
        readability_result: dict,
        keyword_result: dict = None
) -> int:
    """计算整体 SEO 评分"""
    score = 0
    weight = 0

    # Meta 描述评分 (30%)
    if meta_result.get("optimal"):
        score += 30
    else:
        score += 15
    weight += 30

    # 可读性评分 (40%)
    readability_score = readability_result.get("score", 0)
    score += (readability_score / 100) * 40
    weight += 40

    # 关键词分析评分 (30%)
    if keyword_result:
        keyword_score = keyword_result.get("overall_score", 0)
        score += (keyword_score / 100) * 30
    else:
        score += 15  # 默认分数
    weight += 30

    return int(score) if weight > 0 else 0


def generate_comprehensive_recommendations(
        meta_result: dict,
        readability_result: dict,
        keyword_result: dict = None
) -> List[str]:
    """生成综合优化建议"""
    recommendations = []

    # Meta 描述建议
    if meta_result.get("recommendations"):
        recommendations.extend(meta_result["recommendations"])

    # 可读性建议
    if readability_result.get("recommendations"):
        recommendations.extend(readability_result["recommendations"])

    # 关键词建议
    if keyword_result and keyword_result.get("suggestions"):
        recommendations.extend(keyword_result["suggestions"])

    if not recommendations:
        recommendations.append("内容质量良好，继续保持")

    return recommendations
