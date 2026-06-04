"""
统一SEO管理 API

提供SEO分析、评分和优化建议功能
"""

from typing import Optional, List

from fastapi import APIRouter, Query, Body

from shared.services.seo.seo_analyzer import seo_analyzer
from src.api.v1.core.responses import ApiResponse

router = APIRouter()


@router.post("/analyze", summary="分析SEO", description="分析内容的SEO质量")
async def analyze_seo(
        title: str = Body(..., description="页面标题"),
        description: str = Body(..., description="页面描述"),
        content: str = Body(..., description="页面内容"),
        keywords: Optional[List[str]] = Body(None, description="目标关键词列表"),
        h1_headings: Optional[List[str]] = Body(None, description="H1标题列表"),
        h2_headings: Optional[List[str]] = Body(None, description="H2标题列表"),
        h3_headings: Optional[List[str]] = Body(None, description="H3标题列表"),
        images: Optional[List[dict]] = Body(None, description="图片列表 [{src, alt}]"),
        internal_links: int = Body(0, description="内部链接数量"),
):
    """分析SEO"""
    headings = {}
    if h1_headings:
        headings['h1'] = h1_headings
    if h2_headings:
        headings['h2'] = h2_headings
    if h3_headings:
        headings['h3'] = h3_headings

    result = seo_analyzer.analyze_seo(
        title=title,
        description=description,
        content=content,
        keywords=keywords or [],
        headings=headings,
        images=images or [],
        internal_links=internal_links,
    )

    return ApiResponse(
        success=True,
        data=result
    )


@router.get("/quick-check", summary="快速检查", description="快速检查标题和描述的SEO")
async def quick_check(
        title: str = Query(..., description="页面标题"),
        description: str = Query(..., description="页面描述"),
):
    """快速检查"""
    title_analysis = seo_analyzer._analyze_title(title)
    description_analysis = seo_analyzer._analyze_description(description)

    overall_score = (title_analysis['score'] + description_analysis['score']) / 2

    suggestions = []
    suggestions.extend(title_analysis.get('suggestions', []))
    suggestions.extend(description_analysis.get('suggestions', []))

    return ApiResponse(
        success=True,
        data={
            'overall_score': round(overall_score * 100, 2),
            'grade': seo_analyzer._get_grade(overall_score),
            'title': title_analysis,
            'description': description_analysis,
            'suggestions': suggestions,
        }
    )


@router.get("/guidelines", summary="SEO指南", description="获取SEO最佳实践指南")
async def get_seo_guidelines():
    """获取SEO指南"""
    guidelines = {
        'title_optimization': {
            'title': '标题优化',
            'best_practices': [
                '长度控制在50-60个字符',
                '包含主要关键词',
                '具有吸引力和描述性',
                '避免关键词堆砌',
                '每个页面使用唯一的标题',
            ],
            'examples': {
                'good': 'Python编程入门教程 - 从零开始学习Python',
                'bad': 'Python | Python教程 | 学习Python | Python编程',
            }
        },
        'description_optimization': {
            'title': '描述优化',
            'best_practices': [
                '长度控制在150-160个字符',
                '清晰概括页面内容',
                '包含行动号召（CTA）',
                '自然融入关键词',
                '每个页面使用唯一的描述',
            ],
            'examples': {
                'good': '完整的Python编程入门教程，涵盖基础语法、数据结构、面向对象等核心概念。适合零基础学习者，通过实例快速掌握Python编程技能。',
                'bad': 'Python教程，Python学习，Python编程，Python入门...',
            }
        },
        'keyword_strategy': {
            'title': '关键词策略',
            'best_practices': [
                '选择2-5个核心关键词',
                '关键词密度保持在1-3%',
                '在标题、描述、H1中自然使用',
                '避免过度优化和堆砌',
                '关注长尾关键词',
            ],
            'density_guide': {
                'optimal': '1-3%',
                'acceptable': '0.5-4%',
                'too_low': '< 0.5%',
                'too_high': '> 4%',
            }
        },
        'content_structure': {
            'title': '内容结构',
            'best_practices': [
                '使用一个H1作为主标题',
                '使用多个H2组织主要章节',
                '使用H3细分小节',
                '保持清晰的层级关系',
                '每300-500词添加一个子标题',
            ],
            'recommended_length': '1500-2500词'
        },
        'readability': {
            'title': '可读性',
            'best_practices': [
                '使用简短的句子（平均15-20词）',
                '段落控制在3-5句',
                '使用列表和表格增强可读性',
                '避免复杂的术语或提供解释',
                '使用过渡词连接段落',
            ]
        },
        'internal_linking': {
            'title': '内部链接',
            'best_practices': [
                '每篇文章添加3-10个内部链接',
                '链接到相关内容',
                '使用描述性的锚文本',
                '避免链接到无关页面',
                '定期更新旧文章的链接',
            ]
        },
        'image_optimization': {
            'title': '图片优化',
            'best_practices': [
                '为所有图片添加ALT文本',
                'ALT文本应描述图片内容',
                '压缩图片文件大小',
                '使用适当的图片格式（WebP优先）',
                '添加图片标题和说明',
            ]
        },
        'scoring_system': {
            'title': '评分系统',
            'grades': {
                'A+ (90-100)': '优秀，SEO优化非常完善',
                'A (80-89)': '良好，SEO优化较好',
                'B (70-79)': '中等，需要一些改进',
                'C (60-69)': '一般，需要较多改进',
                'D (50-59)': '较差，需要大量改进',
                'F (<50)': '很差，需要全面优化',
            },
            'weights': {
                '标题长度': '15%',
                '描述质量': '15%',
                '关键词密度': '20%',
                '可读性': '15%',
                '内容长度': '15%',
                '标题结构': '10%',
                '内部链接': '5%',
                '图片ALT': '5%',
            }
        }
    }

    return ApiResponse(
        success=True,
        data=guidelines
    )
