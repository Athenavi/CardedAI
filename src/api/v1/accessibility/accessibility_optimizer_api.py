"""
无障碍优化 API

提供WCAG 2.1合规检查、ARIA建议、键盘导航测试等功能
"""

from typing import Optional

from fastapi import APIRouter, Depends, Body

from shared.services.accessibility.accessibility_optimizer import accessibility_optimizer
from src.api.v1.core.responses import ApiResponse
from src.api.v1.users.user_management import jwt_required

router = APIRouter(prefix="/accessibility-optimizer", tags=["Accessibility Optimizer"])


@router.post("/audit/comprehensive")
async def run_comprehensive_audit(
        html_content: str = Body(..., description="HTML内容"),
        url: Optional[str] = Body(None, description="页面URL"),
        level: str = Body("AA", description="WCAG级别 (A/AA/AAA)"),
        current_user=Depends(jwt_required)
):
    """
    运行全面的无障碍性审计
    
    检查HTML内容是否符合WCAG 2.1标准
    """
    report = accessibility_optimizer.run_comprehensive_audit(
        html_content=html_content,
        url=url,
        level=level
    )

    return ApiResponse(
        success=True,
        data=report
    )


@router.post("/aria/suggestions")
async def generate_aria_suggestions(
        html_content: str = Body(..., description="HTML内容"),
        current_user=Depends(jwt_required)
):
    """
    生成ARIA属性建议
    
    分析HTML并推荐合适的ARIA属性
    """
    suggestions = accessibility_optimizer.generate_aria_suggestions(html_content)

    return ApiResponse(
        success=True,
        data={
            "suggestions": suggestions,
            "total": len(suggestions)
        }
    )


@router.post("/keyboard/test")
async def test_keyboard_navigation(
        html_content: str = Body(..., description="HTML内容"),
        current_user=Depends(jwt_required)
):
    """
    测试键盘导航
    
    检查页面是否支持完整的键盘操作
    """
    result = accessibility_optimizer.test_keyboard_navigation(html_content)

    return ApiResponse(
        success=True,
        data=result
    )


@router.post("/contrast/check")
async def check_color_contrast(
        foreground: str = Body(..., description="前景色（十六进制）"),
        background: str = Body(..., description="背景色（十六进制）"),
        text_size: str = Body("normal", description="文字大小 (normal/large)"),
        current_user=Depends(jwt_required)
):
    """
    检查颜色对比度
    
    验证颜色组合是否符合WCAG对比度要求
    """
    result = accessibility_optimizer.check_color_contrast_compliance(
        foreground=foreground,
        background=background,
        text_size=text_size
    )

    return ApiResponse(
        success=True,
        data=result
    )


@router.get("/fix-template/{violation_type}")
async def get_fix_template(
        violation_type: str,
        current_user=Depends(jwt_required)
):
    """
    获取修复模板
    
    针对特定违规类型提供修复示例
    """
    template = accessibility_optimizer.get_fix_templates(violation_type)

    return ApiResponse(
        success=True,
        data=template
    )


@router.get("/wcag-guidelines")
async def get_wcag_guidelines(current_user=Depends(jwt_required)):
    """
    获取WCAG 2.1指南
    
    返回WCAG 2.1标准的详细信息
    """
    guidelines = accessibility_optimizer.get_wcag_guidelines()

    return ApiResponse(
        success=True,
        data=guidelines
    )


@router.get("/checklist")
async def get_accessibility_checklist(current_user=Depends(jwt_required)):
    """
    获取无障碍性检查清单
    
    提供完整的WCAG 2.1 AA级检查项目
    """
    checklist = {
        "perceivable": {
            "name": "可感知",
            "items": [
                {
                    "id": "1.1.1",
                    "title": "非文本内容",
                    "description": "所有非文本内容都有文本替代",
                    "checks": [
                        "所有图片有ALT文本",
                        "图标字体有aria-label",
                        "装饰性图片使用空ALT"
                    ]
                },
                {
                    "id": "1.3.1",
                    "title": "信息和关系",
                    "description": "可以通过程序确定信息和关系",
                    "checks": [
                        "标题按顺序使用（H1→H2→H3）",
                        "表单控件有关联的标签",
                        "使用语义化HTML元素"
                    ]
                },
                {
                    "id": "1.4.3",
                    "title": "对比度（最小）",
                    "description": "文本和背景的对比度至少4.5:1",
                    "checks": [
                        "普通文本对比度≥4.5:1",
                        "大文本对比度≥3:1",
                        "UI组件对比度≥3:1"
                    ]
                }
            ]
        },
        "operable": {
            "name": "可操作",
            "items": [
                {
                    "id": "2.1.1",
                    "title": "键盘",
                    "description": "所有功能都可以通过键盘操作",
                    "checks": [
                        "所有交互元素可通过Tab访问",
                        "没有键盘陷阱",
                        "自定义控件支持键盘操作"
                    ]
                },
                {
                    "id": "2.4.1",
                    "title": "绕过块",
                    "description": "提供跳过重复内容块的机制",
                    "checks": [
                        "有跳到主要内容的链接",
                        "导航区域有ARIA地标",
                        "重复内容可跳过"
                    ]
                },
                {
                    "id": "2.4.2",
                    "title": "页面标题",
                    "description": "每个页面都有描述性的标题",
                    "checks": [
                        "<title>元素存在",
                        "标题描述页面内容",
                        "标题在站点内唯一"
                    ]
                }
            ]
        },
        "understandable": {
            "name": "可理解",
            "items": [
                {
                    "id": "3.1.1",
                    "title": "语言",
                    "description": "页面的默认人类语言可以通过程序确定",
                    "checks": [
                        "HTML元素有lang属性",
                        "语言代码正确"
                    ]
                },
                {
                    "id": "3.3.2",
                    "title": "标签或说明",
                    "description": "当组件需要用户输入时，显示标签或说明",
                    "checks": [
                        "所有表单字段有标签",
                        "必需字段有标识",
                        "错误消息清晰"
                    ]
                }
            ]
        },
        "robust": {
            "name": "鲁棒",
            "items": [
                {
                    "id": "4.1.2",
                    "title": "名称、角色、值",
                    "description": "UI组件的名称和角色可以通过程序确定",
                    "checks": [
                        "自定义控件有适当的ARIA角色",
                        "状态变化通知辅助技术",
                        "ARIA属性使用正确"
                    ]
                }
            ]
        }
    }

    return ApiResponse(
        success=True,
        data=checklist
    )


@router.get("/best-practices")
async def get_best_practices(current_user=Depends(jwt_required)):
    """
    获取无障碍性最佳实践
    
    提供实用的无障碍性开发建议
    """
    practices = {
        "general": [
            {
                "title": "使用语义化HTML",
                "description": "优先使用原生HTML元素而非div+CSS模拟",
                "example": "使用<button>而非<div onclick='...'>"
            },
            {
                "title": "提供文本替代",
                "description": "所有非文本内容都应有文本替代",
                "example": "<img src='logo.png' alt='公司Logo'>"
            },
            {
                "title": "确保足够的对比度",
                "description": "文本和背景的对比度至少4.5:1",
                "tool": "WebAIM Contrast Checker"
            }
        ],
        "forms": [
            {
                "title": "关联标签和输入",
                "description": "使用<label for='id'>关联表单控件",
                "example": "<label for='email'>邮箱</label><input id='email' type='email'>"
            },
            {
                "title": "清晰的错误提示",
                "description": "错误消息应明确指出哪个字段有问题",
                "example": "<span role='alert'>邮箱格式不正确</span>"
            },
            {
                "title": "标记必需字段",
                "description": "使用aria-required或required属性",
                "example": "<input required aria-required='true'>"
            }
        ],
        "navigation": [
            {
                "title": "提供跳过链接",
                "description": "允许键盘用户跳过导航直达主要内容",
                "example": "<a href='#main'>跳到主要内容</a>"
            },
            {
                "title": "一致的导航",
                "description": "在整个站点保持导航结构一致",
                "tip": "使用相同的菜单顺序和位置"
            },
            {
                "title": "面包屑导航",
                "description": "帮助用户了解当前位置",
                "example": "<nav aria-label='面包屑'>...</nav>"
            }
        ],
        "interactive": [
            {
                "title": "可见的焦点指示器",
                "description": "确保键盘焦点清晰可见",
                "css": "button:focus { outline: 2px solid blue; }"
            },
            {
                "title": "足够的点击区域",
                "description": "触摸目标至少44x44像素",
                "css": ".button { min-width: 44px; min-height: 44px; }"
            },
            {
                "title": "反馈和状态",
                "description": "操作后提供明确的反馈",
                "example": "使用aria-live区域通知动态更新"
            }
        ],
        "media": [
            {
                "title": "视频字幕",
                "description": "为视频提供字幕",
                "format": "WebVTT (.vtt)"
            },
            {
                "title": "音频转录",
                "description": "为纯音频内容提供文本转录",
                "tip": "可以使用自动转录服务"
            },
            {
                "title": "动画控制",
                "description": "提供暂停或禁用动画的选项",
                "css": "@media (prefers-reduced-motion) { ... }"
            }
        ],
        "testing": [
            {
                "title": "键盘测试",
                "description": "仅使用键盘浏览整个网站",
                "keys": "Tab, Shift+Tab, Enter, Space, Esc"
            },
            {
                "title": "屏幕阅读器测试",
                "description": "使用NVDA、VoiceOver或JAWS测试",
                "tools": ["NVDA (Windows)", "VoiceOver (Mac)", "TalkBack (Android)"]
            },
            {
                "title": "自动化测试",
                "description": "使用工具进行初步检查",
                "tools": ["axe-core", "Lighthouse", "WAVE"]
            }
        ]
    }

    return ApiResponse(
        success=True,
        data=practices
    )


@router.get("/tools")
async def get_accessibility_tools(current_user=Depends(jwt_required)):
    """
    获取无障碍性测试工具推荐
    
    列出常用的无障碍性测试和开发工具
    """
    tools = {
        "browser_extensions": [
            {
                "name": "axe DevTools",
                "description": "浏览器扩展，自动检测无障碍性问题",
                "url": "https://www.deque.com/axe/devtools/",
                "platforms": ["Chrome", "Firefox", "Edge"]
            },
            {
                "name": "WAVE",
                "description": "Web无障碍性评估工具",
                "url": "https://wave.webaim.org/",
                "platforms": ["Chrome", "Firefox"]
            },
            {
                "name": "Lighthouse",
                "description": "Chrome内置的无障碍性审计工具",
                "url": "chrome://inspect/#lighthouse",
                "platforms": ["Chrome"]
            }
        ],
        "screen_readers": [
            {
                "name": "NVDA",
                "description": "免费开源的Windows屏幕阅读器",
                "url": "https://www.nvaccess.org/",
                "platform": "Windows",
                "cost": "免费"
            },
            {
                "name": "VoiceOver",
                "description": "Mac和iOS内置的屏幕阅读器",
                "platform": "macOS, iOS",
                "cost": "内置"
            },
            {
                "name": "JAWS",
                "description": "商业Windows屏幕阅读器",
                "url": "https://www.freedomscientific.com/products/software/jaws/",
                "platform": "Windows",
                "cost": "付费"
            }
        ],
        "online_tools": [
            {
                "name": "WebAIM Contrast Checker",
                "description": "检查颜色对比度",
                "url": "https://webaim.org/resources/contrastchecker/"
            },
            {
                "name": "W3C WCAG Quick Reference",
                "description": "WCAG 2.1快速参考指南",
                "url": "https://www.w3.org/WAI/WCAG21/quickref/"
            },
            {
                "name": "Accessible Color Generator",
                "description": "生成符合WCAG的颜色方案",
                "url": "https://accessible-colors.com/"
            }
        ],
        "development_libraries": [
            {
                "name": "React Aria",
                "description": "Adobe的无障碍React Hooks库",
                "url": "https://react-spectrum.adobe.com/react-aria/"
            },
            {
                "name": "Reach UI",
                "description": "无障碍优先的React组件库",
                "url": "https://reach.tech/"
            },
            {
                "name": "Headless UI",
                "description": "完全可访问、完全无样式的UI组件",
                "url": "https://headlessui.dev/"
            }
        ]
    }

    return ApiResponse(
        success=True,
        data=tools
    )


@router.get("/guide")
async def get_accessibility_guide(current_user=Depends(jwt_required)):
    """
    获取无障碍性开发指南
    """
    guide = {
        "overview": {
            "title": "无障碍性优化指南",
            "description": "帮助开发者创建所有人都能访问的网站和应用",
            "target_standard": "WCAG 2.1 AA级"
        },
        "getting_started": [
            "学习WCAG 2.1标准和四大原则",
            "安装无障碍性测试工具（axe、WAVE等）",
            "在开发过程中定期进行无障碍性检查",
            "邀请残障用户参与测试"
        ],
        "common_mistakes": [
            {
                "mistake": "忽略图片ALT文本",
                "impact": "屏幕阅读器用户无法理解图片内容",
                "fix": "为所有<img>添加描述性alt属性"
            },
            {
                "mistake": "仅用颜色传达信息",
                "impact": "色盲用户无法区分",
                "fix": "同时使用图标、文字或其他视觉提示"
            },
            {
                "mistake": "没有键盘焦点样式",
                "impact": "键盘用户不知道当前焦点位置",
                "fix": "为:focus状态添加明显的样式"
            },
            {
                "mistake": "表单缺少标签",
                "impact": "屏幕阅读器用户不知道输入什么",
                "fix": "使用<label>元素关联表单控件"
            }
        ],
        "resources": [
            {
                "name": "MDN Web Accessibility",
                "url": "https://developer.mozilla.org/en-US/docs/Web/Accessibility"
            },
            {
                "name": "WebAIM",
                "url": "https://webaim.org/"
            },
            {
                "name": "A11y Project",
                "url": "https://www.a11yproject.com/"
            }
        ]
    }

    return ApiResponse(
        success=True,
        data=guide
    )
