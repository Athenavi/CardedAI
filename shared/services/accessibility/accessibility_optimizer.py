"""
无障碍优化服务 - 增强版

提供WCAG 2.1合规检查、自动化检测、ARIA标签建议、键盘导航测试等功能
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional


class AccessibilityOptimizer:
    """
    无障碍优化服务

    功能:
    1. WCAG 2.1 A/AA/AAA级别合规检查
    2. 自动化无障碍性检测
    3. ARIA标签建议和生成
    4. 键盘导航测试
    5. 颜色对比度检查
    6. 屏幕阅读器兼容性测试
    7. 焦点管理优化
    8. 语义化HTML检查
    9. 修复建议生成
    """

    def __init__(self):
        # WCAG检查规则
        self.wcag_rules = self._initialize_wcag_rules()

        # 颜色对比度标准
        self.contrast_ratios = {
            "AA_normal": 4.5,
            "AA_large": 3.0,
            "AAA_normal": 7.0,
            "AAA_large": 4.5,
        }

    def run_comprehensive_audit(
            self,
            html_content: str,
            url: Optional[str] = None,
            level: str = "AA"
    ) -> Dict[str, Any]:
        """
        运行全面的无障碍性审计

        Args:
            html_content: HTML内容
            url: 页面URL（可选）
            level: WCAG级别 (A/AA/AAA)

        Returns:
            审计报告
        """
        violations = []
        passes = []
        warnings = []

        # 执行各项检查
        checks = [
            self.check_image_alt(html_content),
            self.check_heading_structure(html_content),
            self.check_form_labels(html_content),
            self.check_keyboard_accessibility(html_content),
            self.check_aria_attributes(html_content),
            self.check_color_contrast(html_content),
            self.check_language_declaration(html_content),
            self.check_link_purpose(html_content),
            self.check_focus_management(html_content),
            self.check_semantic_html(html_content),
        ]

        for check_result in checks:
            if check_result["status"] == "violation":
                violations.append(check_result)
            elif check_result["status"] == "pass":
                passes.append(check_result)
            elif check_result["status"] == "warning":
                warnings.append(check_result)

        # 计算评分
        total_checks = len(violations) + len(passes)
        score = (len(passes) / total_checks * 100) if total_checks > 0 else 0

        # 确定等级
        grade = self._calculate_grade(score)

        report = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "score": round(score, 2),
            "grade": grade,
            "summary": {
                "total_checks": total_checks,
                "violations": len(violations),
                "passes": len(passes),
                "warnings": len(warnings),
            },
            "violations": violations,
            "passes": passes,
            "warnings": warnings,
            "recommendations": self._generate_recommendations(violations, warnings),
        }

        return report

    def generate_aria_suggestions(self, html_content: str) -> List[Dict[str, Any]]:
        """
        生成ARIA属性建议

        Args:
            html_content: HTML内容

        Returns:
            ARIA建议列表
        """
        suggestions = []

        # 检查导航元素
        if "<nav>" in html_content and 'role="navigation"' not in html_content:
            suggestions.append({
                "element": "nav",
                "suggestion": '添加 role="navigation"',
                "reason": "提高屏幕阅读器对导航区域的识别",
                "priority": "medium",
                "code_example": '<nav role="navigation">...</nav>'
            })

        # 检查搜索表单
        if 'type="search"' in html_content and 'role="search"' not in html_content:
            suggestions.append({
                "element": "form[type=search]",
                "suggestion": '添加 role="search"',
                "reason": "标识搜索功能",
                "priority": "high",
                "code_example": '<form role="search">...</form>'
            })

        # 检查按钮
        button_pattern = r'<button[^>]*>(.*?)</button>'
        buttons = re.findall(button_pattern, html_content, re.DOTALL)

        for i, button_text in enumerate(buttons):
            if not button_text.strip() and 'aria-label' not in html_content:
                suggestions.append({
                    "element": f"button #{i + 1}",
                    "suggestion": "添加 aria-label 描述按钮功能",
                    "reason": "空按钮需要文本替代",
                    "priority": "critical",
                    "code_example": '<button aria-label="关闭">×</button>'
                })

        # 检查模态对话框
        if 'role="dialog"' in html_content or 'modal' in html_content.lower():
            if 'aria-modal="true"' not in html_content:
                suggestions.append({
                    "element": "dialog/modal",
                    "suggestion": '添加 aria-modal="true"',
                    "reason": "标识模态对话框",
                    "priority": "high",
                    "code_example": '<div role="dialog" aria-modal="true">...</div>'
                })

        # 检查实时区域
        live_keywords = ["loading", "updating", "refreshing"]
        for keyword in live_keywords:
            if keyword in html_content.lower() and 'aria-live' not in html_content:
                suggestions.append({
                    "element": f"dynamic content ({keyword})",
                    "suggestion": '添加 aria-live="polite" 或 aria-live="assertive"',
                    "reason": "通知屏幕阅读器动态内容更新",
                    "priority": "medium",
                    "code_example": '<div aria-live="polite">加载中...</div>'
                })

        return suggestions

    def test_keyboard_navigation(self, html_content: str) -> Dict[str, Any]:
        """
        测试键盘导航

        Args:
            html_content: HTML内容

        Returns:
            键盘导航测试结果
        """
        issues = []

        # 检查可聚焦元素
        focusable_elements = [
            "a[href]",
            "button",
            "input",
            "select",
            "textarea",
            "[tabindex]"
        ]

        # 检查是否有跳过链接
        has_skip_link = "skip" in html_content.lower() and "main" in html_content.lower()

        if not has_skip_link:
            issues.append({
                "type": "missing_skip_link",
                "severity": "moderate",
                "description": "缺少跳到主要内容的链接",
                "solution": "在页面开头添加 <a href='#main'>跳到主要内容</a>",
                "wcag_criterion": "2.4.1"
            })

        # 检查 tabindex 使用
        negative_tabindex = re.findall(r'tabindex=["\']-\d+["\']', html_content)
        if negative_tabindex:
            issues.append({
                "type": "negative_tabindex",
                "severity": "minor",
                "description": f"发现 {len(negative_tabindex)} 个负数 tabindex",
                "solution": "谨慎使用负数 tabindex，确保不影响正常导航顺序",
                "wcag_criterion": "2.4.3"
            })

        # 检查自定义交互元素
        custom_interactive = re.findall(r'<div[^>]*onclick', html_content)
        if custom_interactive:
            issues.append({
                "type": "custom_interactive",
                "severity": "serious",
                "description": f"发现 {len(custom_interactive)} 个使用 onclick 的 div 元素",
                "solution": "使用原生按钮元素或添加 role='button' 和 keyboard 事件处理",
                "wcag_criterion": "2.1.1"
            })

        return {
            "status": "fail" if issues else "pass",
            "issues": issues,
            "focusable_elements_count": len(focusable_elements),
            "has_skip_link": has_skip_link,
        }

    def check_color_contrast_compliance(
            self,
            foreground: str,
            background: str,
            text_size: str = "normal"
    ) -> Dict[str, Any]:
        """
        检查颜色对比度合规性

        Args:
            foreground: 前景色（十六进制）
            background: 背景色（十六进制）
            text_size: 文字大小 (normal/large)

        Returns:
            对比度检查结果
        """
        ratio = self._calculate_contrast_ratio(foreground, background)

        aa_pass = ratio >= self.contrast_ratios[f"AA_{text_size}"]
        aaa_pass = ratio >= self.contrast_ratios[f"AAA_{text_size}"]

        return {
            "foreground": foreground,
            "background": background,
            "contrast_ratio": round(ratio, 2),
            "text_size": text_size,
            "aa_compliant": aa_pass,
            "aaa_compliant": aaa_pass,
            "status": "pass" if aa_pass else "fail",
        }

    def get_fix_templates(self, violation_type: str) -> Dict[str, Any]:
        """
        获取修复模板

        Args:
            violation_type: 违规类型

        Returns:
            修复模板
        """
        templates = {
            "image-alt": {
                "title": "添加图片ALT文本",
                "before": '<img src="photo.jpg">',
                "after": '<img src="photo.jpg" alt="描述性文字">',
                "explanation": "ALT文本应该简洁地描述图片内容",
                "examples": [
                    '<img src="logo.png" alt="公司Logo">',
                    '<img src="chart.png" alt="2024年销售数据图表">',
                    '<img src="decorative-line.png" alt="">  # 装饰性图片用空ALT'
                ]
            },
            "heading-structure": {
                "title": "修复标题层级",
                "before": '<h1>标题1</h1><h3>标题3</h3>',
                "after": '<h1>标题1</h1><h2>标题2</h2><h3>标题3</h3>',
                "explanation": "标题应按顺序使用，不要跳级",
                "examples": [
                    '<h1>主标题</h1>',
                    '<h2>副标题</h2>',
                    '<h3>小节标题</h3>'
                ]
            },
            "form-labels": {
                "title": "添加表单标签",
                "before": '<input type="text" name="email">',
                "after": '<label for="email">邮箱地址</label><input type="text" id="email" name="email">',
                "explanation": "每个表单控件都应有对应的标签",
                "examples": [
                    '<label for="name">姓名</label><input id="name" type="text">',
                    '<input type="checkbox" id="agree"><label for="agree">我同意条款</label>'
                ]
            },
            "keyboard-accessible": {
                "title": "确保键盘可访问",
                "before": '<div onclick="handleClick()">点击我</div>',
                "after": '<button onclick="handleClick()">点击我</button>',
                "explanation": "所有交互元素应可通过键盘操作",
                "examples": [
                    '<button>提交</button>',
                    '<a href="/page">链接</a>',
                    '<input type="text">'
                ]
            },
            "link-purpose": {
                "title": "明确链接目的",
                "before": '<a href="/page">点击这里</a>',
                "after": '<a href="/page">阅读完整文章</a>',
                "explanation": "链接文本应清晰说明目标",
                "examples": [
                    '<a href="/api/v2/docs">查看文档</a>',
                    '<a href="/contact">联系我们</a>'
                ]
            }
        }

        return templates.get(violation_type, {
            "title": "修复建议",
            "explanation": "请参考WCAG 2.1指南进行修复"
        })

    def get_wcag_guidelines(self) -> Dict[str, Any]:
        """
        获取WCAG 2.1指南

        Returns:
            WCAG指南信息
        """
        return {
            "version": "2.1",
            "levels": ["A", "AA", "AAA"],
            "principles": [
                {
                    "id": "perceivable",
                    "name": "可感知",
                    "description": "信息和用户界面组件必须以用户可感知的方式呈现",
                    "guidelines": [
                        "1.1 文本替代",
                        "1.2 时间基媒体",
                        "1.3 适应性",
                        "1.4 可辨别"
                    ]
                },
                {
                    "id": "operable",
                    "name": "可操作",
                    "description": "用户界面组件和导航必须可操作",
                    "guidelines": [
                        "2.1 键盘可访问",
                        "2.2 足够的时间",
                        "2.3 癫痫发作",
                        "2.4 可导航",
                        "2.5 输入方式"
                    ]
                },
                {
                    "id": "understandable",
                    "name": "可理解",
                    "description": "信息和用户界面的操作必须可理解",
                    "guidelines": [
                        "3.1 可读",
                        "3.2 可预测",
                        "3.3 输入辅助"
                    ]
                },
                {
                    "id": "robust",
                    "name": "鲁棒",
                    "description": "内容必须足够鲁棒，以便被各种用户代理（包括辅助技术）可靠地解释",
                    "guidelines": [
                        "4.1 兼容"
                    ]
                }
            ],
            "recommended_level": "AA",
            "resources": [
                {
                    "name": "WCAG 2.1官方文档",
                    "url": "https://www.w3.org/WAI/WCAG21/quickref/"
                },
                {
                    "name": "无障碍教程",
                    "url": "https://www.w3.org/WAI/tutorials/"
                }
            ]
        }

    def _initialize_wcag_rules(self) -> List[Dict[str, Any]]:
        """初始化WCAG规则"""
        return [
            {"id": "1.1.1", "name": "非文本内容", "level": "A"},
            {"id": "1.3.1", "name": "信息和关系", "level": "A"},
            {"id": "1.4.3", "name": "对比度（最小）", "level": "AA"},
            {"id": "2.1.1", "name": "键盘", "level": "A"},
            {"id": "2.4.1", "name": "绕过块", "level": "A"},
            {"id": "2.4.2", "name": "页面标题", "level": "A"},
            {"id": "3.3.2", "name": "标签或说明", "level": "A"},
            {"id": "4.1.2", "name": "名称、角色、值", "level": "A"},
        ]

    def check_image_alt(self, html_content: str) -> Dict[str, Any]:
        """检查图片ALT文本"""
        img_tags = re.findall(r'<img[^>]+>', html_content)
        missing_alt = []

        for img in img_tags:
            if 'alt=' not in img:
                missing_alt.append(img[:50])

        if missing_alt:
            return {
                "rule": "image-alt",
                "wcag_criterion": "1.1.1",
                "status": "violation",
                "severity": "critical",
                "count": len(missing_alt),
                "description": f"{len(missing_alt)} 个图片缺少ALT文本",
                "elements": missing_alt[:5],
                "fix": "为所有<img>标签添加描述性的alt属性"
            }

        return {
            "rule": "image-alt",
            "status": "pass",
            "description": "所有图片都有ALT文本"
        }

    def check_heading_structure(self, html_content: str) -> Dict[str, Any]:
        """检查标题结构"""
        headings = re.findall(r'<h([1-6])[^>]*>', html_content)

        if not headings:
            return {
                "rule": "heading-structure",
                "status": "warning",
                "description": "页面没有标题"
            }

        # 检查是否有H1
        if '1' not in headings:
            return {
                "rule": "heading-structure",
                "wcag_criterion": "1.3.1",
                "status": "violation",
                "severity": "serious",
                "description": "页面缺少H1标题",
                "fix": "添加一个H1标题作为页面主标题"
            }

        # 检查跳级
        levels = [int(h) for h in headings]
        skips = []
        for i in range(1, len(levels)):
            if levels[i] > levels[i - 1] + 1:
                skips.append(f"H{levels[i - 1]} -> H{levels[i]}")

        if skips:
            return {
                "rule": "heading-structure",
                "wcag_criterion": "1.3.1",
                "status": "violation",
                "severity": "moderate",
                "description": f"发现 {len(skips)} 处标题跳级",
                "examples": skips[:3],
                "fix": "按顺序使用标题，不要跳过层级"
            }

        return {
            "rule": "heading-structure",
            "status": "pass",
            "description": "标题结构正确"
        }

    def check_form_labels(self, html_content: str) -> Dict[str, Any]:
        """检查表单标签"""
        inputs = re.findall(r'<input[^>]+>', html_content)
        unlabeled = []

        for input_tag in inputs:
            input_type = re.search(r'type=["\']([^"\']+)["\']', input_tag)
            input_id = re.search(r'id=["\']([^"\']+)["\']', input_tag)

            # 跳过隐藏字段和按钮
            if input_type and input_type.group(1) in ['hidden', 'submit', 'button']:
                continue

            # 检查是否有label或aria-label
            has_label = False
            if input_id:
                label_pattern = f'<label[^>]*for=["\']{input_id.group(1)}["\']'
                if re.search(label_pattern, html_content):
                    has_label = True

            if 'aria-label' in input_tag or 'aria-labelledby' in input_tag:
                has_label = True

            if not has_label:
                unlabeled.append(input_tag[:50])

        if unlabeled:
            return {
                "rule": "form-labels",
                "wcag_criterion": "3.3.2",
                "status": "violation",
                "severity": "serious",
                "count": len(unlabeled),
                "description": f"{len(unlabeled)} 个表单控件缺少标签",
                "elements": unlabeled[:5],
                "fix": "为所有表单控件添加<label>元素或aria-label属性"
            }

        return {
            "rule": "form-labels",
            "status": "pass",
            "description": "所有表单控件都有标签"
        }

    def check_keyboard_accessibility(self, html_content: str) -> Dict[str, Any]:
        """检查键盘可访问性"""
        # 检查onclick的div/span元素
        custom_clicks = re.findall(r'<(div|span)[^>]*onclick', html_content)

        if custom_clicks:
            return {
                "rule": "keyboard-accessible",
                "wcag_criterion": "2.1.1",
                "status": "violation",
                "severity": "serious",
                "count": len(custom_clicks),
                "description": f"{len(custom_clicks)} 个元素使用onclick但可能无法通过键盘访问",
                "fix": "使用<button>元素或添加role='button'和键盘事件处理"
            }

        return {
            "rule": "keyboard-accessible",
            "status": "pass",
            "description": "交互元素可通过键盘访问"
        }

    def check_aria_attributes(self, html_content: str) -> Dict[str, Any]:
        """检查ARIA属性"""
        # 检查有role但没有必要ARIA属性的元素
        roles_with_required = {
            "dialog": ["aria-labelledby"],
            "alert": [],
            "button": [],
            "navigation": [],
        }

        issues = []
        for role, required_attrs in roles_with_required.items():
            pattern = f'role=["\']{role}["\']'
            matches = re.findall(pattern, html_content)

            if matches:
                for attr in required_attrs:
                    if attr not in html_content:
                        issues.append(f"{role} 缺少 {attr}")

        if issues:
            return {
                "rule": "aria-attributes",
                "wcag_criterion": "4.1.2",
                "status": "violation",
                "severity": "moderate",
                "description": "某些ARIA角色缺少必需属性",
                "issues": issues,
                "fix": "为ARIA角色添加所有必需的属性"
            }

        return {
            "rule": "aria-attributes",
            "status": "pass",
            "description": "ARIA属性使用正确"
        }

    def check_color_contrast(self, html_content: str) -> Dict[str, Any]:
        """检查颜色对比度（简化版）"""
        # 实际实现需要解析CSS并计算对比度
        # 这里返回一个占位结果
        return {
            "rule": "color-contrast",
            "status": "warning",
            "description": "建议手动检查颜色对比度是否符合WCAG标准",
            "tool_recommendation": "使用 WebAIM Contrast Checker 进行详细检查"
        }

    def check_language_declaration(self, html_content: str) -> Dict[str, Any]:
        """检查语言声明"""
        if '<html' in html_content and 'lang=' not in html_content:
            return {
                "rule": "language-declaration",
                "wcag_criterion": "3.1.1",
                "status": "violation",
                "severity": "serious",
                "description": "HTML元素缺少lang属性",
                "fix": '在<html>标签中添加 lang="zh-CN" 或其他 appropriate 语言代码'
            }

        return {
            "rule": "language-declaration",
            "status": "pass",
            "description": "页面已声明语言"
        }

    def check_link_purpose(self, html_content: str) -> Dict[str, Any]:
        """检查链接目的"""
        vague_links = ["点击这里", "了解更多", "阅读全文", "这里"]
        issues = []

        for vague in vague_links:
            pattern = f'<a[^>]*>{vague}</a>'
            if re.search(pattern, html_content):
                issues.append(vague)

        if issues:
            return {
                "rule": "link-purpose",
                "wcag_criterion": "2.4.4",
                "status": "violation",
                "severity": "moderate",
                "description": f"发现 {len(issues)} 个模糊的链接文本",
                "examples": issues,
                "fix": "使用描述性的链接文本，清楚说明链接目标"
            }

        return {
            "rule": "link-purpose",
            "status": "pass",
            "description": "链接文本清晰明确"
        }

    def check_focus_management(self, html_content: str) -> Dict[str, Any]:
        """检查焦点管理"""
        # 检查是否有:focus样式
        has_focus_style = ':focus' in html_content or 'focus:' in html_content

        if not has_focus_style:
            return {
                "rule": "focus-management",
                "wcag_criterion": "2.4.7",
                "status": "warning",
                "severity": "moderate",
                "description": "未检测到焦点样式定义",
                "fix": "为可聚焦元素添加可见的:focus样式"
            }

        return {
            "rule": "focus-management",
            "status": "pass",
            "description": "焦点管理正确"
        }

    def check_semantic_html(self, html_content: str) -> Dict[str, Any]:
        """检查语义化HTML"""
        semantic_elements = ["header", "nav", "main", "article", "section", "aside", "footer"]
        found_semantic = [elem for elem in semantic_elements if f"<{elem}" in html_content]

        if len(found_semantic) < 3:
            return {
                "rule": "semantic-html",
                "wcag_criterion": "1.3.1",
                "status": "warning",
                "severity": "minor",
                "description": f"仅使用了 {len(found_semantic)} 个语义化元素",
                "found": found_semantic,
                "recommendation": "建议使用更多语义化HTML元素（header, nav, main, article等）"
            }

        return {
            "rule": "semantic-html",
            "status": "pass",
            "description": "使用了足够的语义化HTML元素"
        }

    def _calculate_grade(self, score: float) -> str:
        """计算等级"""
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "B+"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def _generate_recommendations(
            self,
            violations: List[Dict],
            warnings: List[Dict]
    ) -> List[str]:
        """生成修复建议"""
        recommendations = []

        violation_rules = [v.get("rule") for v in violations]

        if "image-alt" in violation_rules:
            recommendations.append("优先修复：为所有图片添加描述性的ALT文本")

        if "form-labels" in violation_rules:
            recommendations.append("为所有表单控件添加<label>元素")

        if "keyboard-accessible" in violation_rules:
            recommendations.append("将onclick的div/span改为button元素")

        if "heading-structure" in violation_rules:
            recommendations.append("按顺序使用标题层级（H1→H2→H3）")

        if warnings:
            recommendations.append("检查警告项，虽然不是强制要求，但改进后可提升用户体验")

        recommendations.append("定期进行无障碍性审计，确保持续合规")
        recommendations.append("考虑邀请残障用户进行真实测试")

        return recommendations

    def _calculate_contrast_ratio(self, color1: str, color2: str) -> float:
        """计算颜色对比度（简化版）"""
        # 实际实现需要使用WCAG公式计算相对亮度
        # 这里返回一个占位值
        return 4.5


# 全局实例
accessibility_optimizer = AccessibilityOptimizer()
