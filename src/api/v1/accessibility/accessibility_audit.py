"""
无障碍性审计 API

提供WCAG 2.1标准的自动化审计功能
"""

from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Body

from shared.services.advanced_features.accessibility_auditor import accessibility_auditor
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required

router = APIRouter()


@router.post("", summary="审计页面", description="审计单个页面的无障碍性")
async def audit_page(
        html_content: str = Body(..., description="HTML内容"),
        url: Optional[str] = Body(None, description="页面URL"),
        level: str = Body('AA', regex='^(A|AA|AAA)$', description="审计级别"),
        current_user=Depends(jwt_required),
):
    """审计页面"""
    report = accessibility_auditor.audit_page(
        html_content=html_content,
        url=url,
        level=level
    )

    return ApiResponse(
        success=True,
        data=report
    )


@router.post("/batch", summary="批量审计", description="审计多个页面")
async def audit_batch(
        pages: List[dict] = Body(..., description="页面列表 [{url, html}]"),
        level: str = Body('AA', regex='^(A|AA|AAA)$', description="审计级别"),
        current_user=Depends(jwt_required),
):
    """批量审计"""
    # 检查权限
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    report = accessibility_auditor.audit_multiple_pages(
        pages=pages,
        level=level
    )

    return ApiResponse(
        success=True,
        data=report
    )


@router.get("/guidelines", summary="WCAG指南", description="获取WCAG 2.1指南说明")
async def get_wcag_guidelines():
    """获取WCAG指南"""
    guidelines = accessibility_auditor.get_wcag_guidelines()

    return ApiResponse(
        success=True,
        data=guidelines
    )


@router.get("/checklist", summary="检查清单", description="获取无障碍性检查清单")
async def get_accessibility_checklist():
    """获取检查清单"""
    checklist = {
        'perceivable': {
            'title': '可感知性',
            'items': [
                {
                    'task': '为所有图片添加ALT文本',
                    'priority': 'high',
                    'wcag_criterion': '1.1.1',
                },
                {
                    'task': '为视频添加字幕',
                    'priority': 'high',
                    'wcag_criterion': '1.2.2',
                },
                {
                    'task': '确保颜色对比度至少4.5:1',
                    'priority': 'high',
                    'wcag_criterion': '1.4.3',
                },
                {
                    'task': '文本可以调整大小至200%',
                    'priority': 'medium',
                    'wcag_criterion': '1.4.4',
                },
            ]
        },
        'operable': {
            'title': '可操作性',
            'items': [
                {
                    'task': '所有功能可通过键盘访问',
                    'priority': 'high',
                    'wcag_criterion': '2.1.1',
                },
                {
                    'task': '提供跳过导航链接',
                    'priority': 'medium',
                    'wcag_criterion': '2.4.1',
                },
                {
                    'task': '页面有明确的标题',
                    'priority': 'high',
                    'wcag_criterion': '2.4.2',
                },
                {
                    'task': '焦点顺序合理',
                    'priority': 'medium',
                    'wcag_criterion': '2.4.3',
                },
                {
                    'task': '链接目的清晰',
                    'priority': 'medium',
                    'wcag_criterion': '2.4.4',
                },
            ]
        },
        'understandable': {
            'title': '可理解性',
            'items': [
                {
                    'task': '声明页面语言',
                    'priority': 'high',
                    'wcag_criterion': '3.1.1',
                },
                {
                    'task': '表单控件有标签',
                    'priority': 'high',
                    'wcag_criterion': '3.3.2',
                },
                {
                    'task': '错误提示清晰明确',
                    'priority': 'high',
                    'wcag_criterion': '3.3.1',
                },
            ]
        },
        'robust': {
            'title': '鲁棒性',
            'items': [
                {
                    'task': '使用有效的HTML',
                    'priority': 'high',
                    'wcag_criterion': '4.1.1',
                },
                {
                    'task': '正确使用ARIA属性',
                    'priority': 'medium',
                    'wcag_criterion': '4.1.2',
                },
            ]
        }
    }

    return ApiResponse(
        success=True,
        data=checklist
    )


@router.get("/tools", summary="辅助工具", description="获取无障碍性测试工具推荐")
async def get_accessibility_tools():
    """获取工具推荐"""
    tools = {
        'automated_testing': {
            'title': '自动化测试工具',
            'tools': [
                {
                    'name': 'axe-core',
                    'description': '强大的无障碍性测试引擎',
                    'url': 'https://www.deque.com/axe/',
                    'integration': '可集成到浏览器扩展、CI/CD',
                },
                {
                    'name': 'Lighthouse',
                    'description': 'Google的网页质量审计工具',
                    'url': 'https://developers.google.com/web/tools/lighthouse',
                    'integration': 'Chrome DevTools内置',
                },
                {
                    'name': 'WAVE',
                    'description': 'Web无障碍性评估工具',
                    'url': 'https://wave.webaim.org/',
                    'integration': '在线工具和浏览器扩展',
                },
            ]
        },
        'screen_readers': {
            'title': '屏幕阅读器',
            'tools': [
                {
                    'name': 'NVDA',
                    'description': '免费开源的Windows屏幕阅读器',
                    'platform': 'Windows',
                    'url': 'https://www.nvaccess.org/',
                },
                {
                    'name': 'JAWS',
                    'description': '商业Windows屏幕阅读器',
                    'platform': 'Windows',
                    'url': 'https://www.freedomscientific.com/products/software/jaws/',
                },
                {
                    'name': 'VoiceOver',
                    'description': 'Mac和iOS内置屏幕阅读器',
                    'platform': 'macOS, iOS',
                    'url': 'https://www.apple.com/accessibility/',
                },
                {
                    'name': 'TalkBack',
                    'description': 'Android内置屏幕阅读器',
                    'platform': 'Android',
                    'url': 'https://support.google.com/accessibility/android/answer/6283677',
                },
            ]
        },
        'color_contrast': {
            'title': '颜色对比度检查工具',
            'tools': [
                {
                    'name': 'Contrast Checker',
                    'description': 'WebAIM的对比度检查器',
                    'url': 'https://webaim.org/resources/contrastchecker/',
                },
                {
                    'name': 'Color Contrast Analyzer',
                    'description': 'Microsoft的对比度分析器',
                    'url': 'https://www.microsoft.com/en-us/download/details.aspx?id=59110',
                },
            ]
        },
        'keyboard_testing': {
            'title': '键盘测试',
            'methods': [
                '使用Tab键遍历所有交互元素',
                '检查焦点顺序是否合理',
                '验证所有功能都可以通过键盘操作',
                '确认焦点指示器可见',
                '测试键盘快捷键（如果有）',
            ]
        }
    }

    return ApiResponse(
        success=True,
        data=tools
    )