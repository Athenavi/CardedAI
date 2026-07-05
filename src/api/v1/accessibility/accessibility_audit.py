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
        level: str = Body('AA', pattern='^(A|AA|AAA)$', description="审计级别"),
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
        level: str = Body('AA', pattern='^(A|AA|AAA)$', description="审计级别"),
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
    guidelines = {
        "version": "2.1",
        "principles": {
            "perceivable": {
                "name": "可感知",
                "description": "信息和用户界面组件必须以用户可感知的方式呈现",
                "guidelines": [
                    "1.1 文本替代：为所有非文本内容提供文本替代",
                    "1.2 时间基媒体：为音频和视频内容提供替代",
                    "1.3 适应性：内容应以不同方式呈现而不丢失信息",
                    "1.4 可辨别：使用户更容易看到和听到内容"
                ]
            },
            "operable": {
                "name": "可操作",
                "description": "用户界面组件和导航必须可操作",
                "guidelines": [
                    "2.1 键盘可访问：所有功能均可通过键盘操作",
                    "2.2 充足时间：为用户提供充足的时间阅读和使用内容",
                    "2.3 癫痫发作：内容不应导致癫痫发作",
                    "2.4 可导航：提供帮助用户导航的方法"
                ]
            },
            "understandable": {
                "name": "可理解",
                "description": "信息和用户界面操作必须可理解",
                "guidelines": [
                    "3.1 可读性：使文本内容可读和可理解",
                    "3.2 可预测：网页以可预测的方式呈现和操作",
                    "3.3 输入辅助：帮助用户避免和纠正错误"
                ]
            },
            "robust": {
                "name": "健壮性",
                "description": "内容必须有足够的健壮性以适应各种用户代理",
                "guidelines": [
                    "4.1 兼容性：最大化与当前和未来用户代理的兼容性"
                ]
            }
        },
        "conformance_levels": {
            "A": {
                "name": "A级",
                "description": "最低级别合规",
                "requirement": "满足所有A级成功标准"
            },
            "AA": {
                "name": "AA级",
                "description": "中级合规（推荐）",
                "requirement": "满足所有A级和AA级成功标准"
            },
            "AAA": {
                "name": "AAA级",
                "description": "最高级别合规",
                "requirement": "满足所有A级、AA级和AAA级成功标准"
            }
        }
    }

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
                    'level': 'A',
                },
                {
                    'task': '为视频添加字幕',
                    'priority': 'high',
                    'wcag_criterion': '1.2.2',
                    'level': 'A',
                },
                {
                    'task': '确保颜色对比度至少4.5:1',
                    'priority': 'high',
                    'wcag_criterion': '1.4.3',
                    'level': 'AA',
                },
                {
                    'task': '文本可以调整大小至200%',
                    'priority': 'medium',
                    'wcag_criterion': '1.4.4',
                    'level': 'AA',
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
                    'level': 'A',
                },
                {
                    'task': '提供跳过导航链接',
                    'priority': 'medium',
                    'wcag_criterion': '2.4.1',
                    'level': 'A',
                },
                {
                    'task': '页面有明确的标题',
                    'priority': 'high',
                    'wcag_criterion': '2.4.2',
                    'level': 'A',
                },
                {
                    'task': '焦点顺序合理',
                    'priority': 'medium',
                    'wcag_criterion': '2.4.3',
                    'level': 'A',
                },
                {
                    'task': '链接目的清晰',
                    'priority': 'medium',
                    'wcag_criterion': '2.4.4',
                    'level': 'A',
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
                    'level': 'A',
                },
                {
                    'task': '表单控件有标签',
                    'priority': 'high',
                    'wcag_criterion': '3.3.2',
                    'level': 'A',
                },
                {
                    'task': '错误提示清晰明确',
                    'priority': 'high',
                    'wcag_criterion': '3.3.1',
                    'level': 'A',
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
                    'level': 'A',
                },
                {
                    'task': '正确使用ARIA属性',
                    'priority': 'medium',
                    'wcag_criterion': '4.1.2',
                    'level': 'A',
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
