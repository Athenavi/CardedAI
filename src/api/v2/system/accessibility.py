"""
无障碍支持 API - V2 版本
提供 WCAG 2.1 标准的无障碍功能
"""
from typing import Optional

from fastapi import APIRouter, Depends

from shared.models.user import User
from shared.services.system.accessibility_service import AccessibilityService
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required

router = APIRouter(prefix="/accessibility", tags=["Accessibility"])

# 初始化无障碍服务
accessibility_service = AccessibilityService()


@router.get("/config", summary="获取无障碍配置")
async def get_accessibility_config(
        current_user: User = Depends(jwt_required)
):
    """
    获取当前用户的无障碍配置
    
    返回用户的个性化无障碍设置，包括：
    - 键盘导航启用状态
    - 屏幕阅读器支持
    - 高对比度模式
    - 字体大小
    - 动画减少选项
    """
    try:
        config = accessibility_service.get_accessibility_config()

        return ApiResponse(
            success=True,
            data=config
        )

    except Exception as e:
        return ApiResponse(
            success=False,
            error=f"获取配置失败: {str(e)}"
        )


@router.post("/config", summary="更新无障碍配置")
async def update_accessibility_config(
        keyboard_navigation: Optional[bool] = None,
        screen_reader_support: Optional[bool] = None,
        high_contrast_mode: Optional[bool] = None,
        font_size: Optional[str] = None,
        reduce_motion: Optional[bool] = None,
        focus_visible: Optional[bool] = None,
        skip_links: Optional[bool] = None,
        current_user: User = Depends(jwt_required)
):
    """
    更新用户的无障碍配置
    
    参数:
    - keyboard_navigation: 启用键盘导航
    - screen_reader_support: 启用屏幕阅读器支持
    - high_contrast_mode: 启用高对比度模式
    - font_size: 字体大小 (small, medium, large, x-large)
    - reduce_motion: 减少动画效果
    - focus_visible: 显示焦点轮廓
    - skip_links: 启用跳过链接
    
    所有参数都是可选的，只更新提供的参数
    """
    try:
        # 构建配置字典
        config = {}
        if keyboard_navigation is not None:
            config['keyboard_navigation'] = keyboard_navigation
        if screen_reader_support is not None:
            config['screen_reader_support'] = screen_reader_support
        if high_contrast_mode is not None:
            config['high_contrast_mode'] = high_contrast_mode
        if font_size is not None:
            config['font_size'] = font_size
        if reduce_motion is not None:
            config['reduce_motion'] = reduce_motion
        if focus_visible is not None:
            config['focus_visible'] = focus_visible
        if skip_links is not None:
            config['skip_links'] = skip_links

        updated_config = accessibility_service.update_accessibility_config(
            user_id=current_user.id,
            config=config
        )

        return ApiResponse(
            success=True,
            data=updated_config,
            message="无障碍配置更新成功"
        )

    except ValueError as e:
        return ApiResponse(
            success=False,
            error=str(e)
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=f"更新配置失败: {str(e)}"
        )


@router.get("/skip-links", summary="获取跳过链接")
async def get_skip_links():
    """
    获取页面跳过链接
    
    跳过链接允许键盘用户快速跳转到页面的主要部分，
    避免逐个遍历导航菜单等元素。
    """
    try:
        skip_links = accessibility_service.generate_skip_links()

        return ApiResponse(
            success=True,
            data={
                'skip_links': skip_links,
                'usage': '在页面顶部添加这些链接，第一个 Tab 焦点应该是"跳到主要内容"'
            }
        )

    except Exception as e:
        return ApiResponse(
            success=False,
            error=f"获取跳过链接失败: {str(e)}"
        )


@router.get("/keyboard-shortcuts", summary="获取键盘快捷键")
async def get_keyboard_shortcuts():
    """
    获取系统键盘快捷键列表
    
    返回所有可用的键盘快捷键及其功能说明
    """
    try:
        shortcuts = accessibility_service.generate_keyboard_shortcuts()

        return ApiResponse(
            success=True,
            data={
                'shortcuts': shortcuts,
                'tips': [
                    '按 Alt+H 随时查看此帮助',
                    '使用 Tab 键在元素间移动',
                    '使用 Shift+Tab 反向移动',
                    '按 Enter 或 Space 激活按钮和链接'
                ]
            }
        )

    except Exception as e:
        return ApiResponse(
            success=False,
            error=f"获取快捷键失败: {str(e)}"
        )


@router.get("/aria-labels/{element_type}", summary="获取 ARIA 标签")
async def get_aria_labels(element_type: str):
    """
    获取指定元素类型的 ARIA 标签建议
    
    参数:
    - element_type: 元素类型 (button, link, navigation, search, form, dialog, alert, menu, tablist)
    
    返回推荐的 ARIA 属性配置
    """
    try:
        aria_labels = accessibility_service.generate_aria_labels(element_type)

        if not aria_labels:
            return ApiResponse(
                success=False,
                error=f"不支持的元素类型: {element_type}"
            )

        return ApiResponse(
            success=True,
            data={
                'element_type': element_type,
                'aria_attributes': aria_labels,
                'example': '<div ' + ' '.join([f'{k}="{v}"' for k, v in aria_labels.items()]) + '></div>'
            }
        )

    except Exception as e:
        return ApiResponse(
            success=False,
            error=f"获取 ARIA 标签失败: {str(e)}"
        )


@router.get("/css/high-contrast", summary="获取高对比度 CSS")
async def get_high_contrast_css():
    """
    获取高对比度模式的 CSS 样式
    
    可以在页面中应用这些样式以启用高对比度模式
    """
    try:
        css = accessibility_service.get_high_contrast_css()

        return ApiResponse(
            success=True,
            data={
                'css': css,
                'usage': '将 .high-contrast 类添加到 body 元素以启用高对比度模式'
            },
            headers={'Content-Type': 'text/css'}
        )

    except Exception as e:
        return ApiResponse(
            success=False,
            error=f"获取 CSS 失败: {str(e)}"
        )


@router.get("/css/font-size/{size}", summary="获取字体大小 CSS")
async def get_font_size_css(size: str):
    """
    获取指定字体大小的 CSS 样式
    
    参数:
    - size: 字体大小级别 (small, medium, large, x-large)
    """
    try:
        css = accessibility_service.get_font_size_css(size)

        return ApiResponse(
            success=True,
            data={
                'size': size,
                'css': css,
                'usage': f'将 .font-size-{size} 类添加到 body 元素'
            },
            headers={'Content-Type': 'text/css'}
        )

    except Exception as e:
        return ApiResponse(
            success=False,
            error=f"获取 CSS 失败: {str(e)}"
        )


@router.get("/css/reduce-motion", summary="获取减少动画 CSS")
async def get_reduce_motion_css():
    """
    获取减少动画效果的 CSS 样式
    
    禁用不必要的动画，适合对运动敏感的用户
    """
    try:
        css = accessibility_service.get_reduce_motion_css()

        return ApiResponse(
            success=True,
            data={
                'css': css,
                'usage': '将 .reduce-motion 类添加到 body 元素，或依赖媒体查询自动应用'
            },
            headers={'Content-Type': 'text/css'}
        )

    except Exception as e:
        return ApiResponse(
            success=False,
            error=f"获取 CSS 失败: {str(e)}"
        )


@router.post("/validate", summary="验证无障碍性")
async def validate_accessibility(
        html_content: str
):
    """
    验证 HTML 内容的无障碍性
    
    检查常见的无障碍问题，如：
    - 图片缺少 alt 属性
    - 表单缺少 label
    - 标题层级不正确
    - 缺少语言属性
    
    参数:
    - html_content: 要验证的 HTML 内容
    """
    try:
        result = accessibility_service.validate_accessibility(html_content)

        return ApiResponse(
            success=True,
            data=result,
            message=f"验证完成，得分: {result['score']}/100"
        )

    except Exception as e:
        return ApiResponse(
            success=False,
            error=f"验证失败: {str(e)}"
        )


@router.get("/guide", summary="获取无障碍指南")
async def get_accessibility_guide():
    """
    获取完整的无障碍使用指南
    
    包括：
    - 键盘导航说明
    - 屏幕阅读器支持
    - 视觉辅助选项
    - 跳过链接使用
    - WCAG 合规信息
    """
    try:
        guide = accessibility_service.get_accessibility_guide()

        return ApiResponse(
            success=True,
            data=guide
        )

    except Exception as e:
        return ApiResponse(
            success=False,
            error=f"获取指南失败: {str(e)}"
        )


@router.get("/wcag-compliance", summary="获取 WCAG 合规信息")
async def get_wcag_compliance():
    """
    获取 WCAG 2.1 合规信息
    
    返回系统符合的 WCAG 标准和级别
    """
    return ApiResponse(
        success=True,
        data={
            'standard': 'WCAG 2.1',
            'level': 'AA',
            'compliant_principles': [
                {
                    'principle': 'Perceivable (可感知)',
                    'guidelines': [
                        '1.1 文本替代',
                        '1.2 时间基媒体',
                        '1.3 适应性',
                        '1.4 可辨别'
                    ]
                },
                {
                    'principle': 'Operable (可操作)',
                    'guidelines': [
                        '2.1 键盘可访问',
                        '2.2 足够的时间',
                        '2.3 癫痫发作',
                        '2.4 可导航'
                    ]
                },
                {
                    'principle': 'Understandable (可理解)',
                    'guidelines': [
                        '3.1 可读',
                        '3.2 可预测',
                        '3.3 输入辅助'
                    ]
                },
                {
                    'principle': 'Robust (健壮)',
                    'guidelines': [
                        '4.1 兼容'
                    ]
                }
            ],
            'features': [
                '键盘导航支持',
                '屏幕阅读器优化',
                '高对比度模式',
                '字体大小调整',
                '动画减少选项',
                'ARIA 标签',
                '跳过链接',
                '焦点管理',
                '错误提示',
                '表单验证'
            ],
            'testing_tools': [
                'WAVE Web Accessibility Evaluator',
                'axe DevTools',
                'Lighthouse Accessibility Audit',
                'NVDA Screen Reader',
                'VoiceOver (macOS/iOS)'
            ]
        }
    )
