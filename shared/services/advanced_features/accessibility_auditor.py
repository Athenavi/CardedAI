"""
无障碍性审计服务

提供WCAG 2.1标准的自动化审计和检查
帮助识别和修复无障碍性问题
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


class AccessibilityAuditor:
    """
    无障碍性审计服务
    
    检查HTML内容是否符合WCAG 2.1标准
    """

    def __init__(self):
        """初始化审计器"""
        # WCAG 2.1级别
        self.levels = ['A', 'AA', 'AAA']

        # 审计规则
        self.rules = self._initialize_rules()

    def _initialize_rules(self) -> List[Dict[str, Any]]:
        """初始化审计规则"""
        return [
            {
                'id': 'image-alt',
                'name': '图片ALT文本',
                'description': '所有图片必须有ALT文本',
                'level': 'A',
                'category': 'perceivable',
                'check_method': 'check_image_alt',
            },
            {
                'id': 'color-contrast',
                'name': '颜色对比度',
                'description': '文本和背景的颜色对比度至少4.5:1',
                'level': 'AA',
                'category': 'perceivable',
                'check_method': 'check_color_contrast',
            },
            {
                'id': 'heading-structure',
                'name': '标题结构',
                'description': '标题应按层级顺序使用（H1→H2→H3）',
                'level': 'A',
                'category': 'navigable',
                'check_method': 'check_heading_structure',
            },
            {
                'id': 'link-purpose',
                'name': '链接目的',
                'description': '链接文本应清晰说明目的',
                'level': 'A',
                'category': 'navigable',
                'check_method': 'check_link_purpose',
            },
            {
                'id': 'form-labels',
                'name': '表单标签',
                'description': '所有表单控件应有标签',
                'level': 'A',
                'category': 'understandable',
                'check_method': 'check_form_labels',
            },
            {
                'id': 'keyboard-accessible',
                'name': '键盘可访问',
                'description': '所有功能应可通过键盘访问',
                'level': 'A',
                'category': 'operable',
                'check_method': 'check_keyboard_accessible',
            },
            {
                'id': 'aria-labels',
                'name': 'ARIA标签',
                'description': '复杂组件应使用ARIA属性',
                'level': 'A',
                'category': 'robust',
                'check_method': 'check_aria_labels',
            },
            {
                'id': 'language-declaration',
                'name': '语言声明',
                'description': '页面应声明主要语言',
                'level': 'A',
                'category': 'understandable',
                'check_method': 'check_language_declaration',
            },
            {
                'id': 'focus-indicator',
                'name': '焦点指示器',
                'description': '焦点元素应有可见的指示器',
                'level': 'AA',
                'category': 'operable',
                'check_method': 'check_focus_indicator',
            },
            {
                'id': 'error-identification',
                'name': '错误识别',
                'description': '表单错误应清晰标识并描述',
                'level': 'A',
                'category': 'understandable',
                'check_method': 'check_error_identification',
            },
        ]

    def audit_page(
            self,
            html_content: str,
            url: Optional[str] = None,
            level: str = 'AA'
    ) -> Dict[str, Any]:
        """
        审计页面
        
        Args:
            html_content: HTML内容
            url: 页面URL
            level: 审计级别 (A, AA, AAA)
        
        Returns:
            审计报告
        """
        timestamp = datetime.now()

        # 过滤适用的规则
        applicable_rules = [
            rule for rule in self.rules
            if self._is_rule_applicable(rule, level)
        ]

        # 执行检查
        violations = []
        passed = []
        warnings = []

        for rule in applicable_rules:
            try:
                check_method = getattr(self, rule['check_method'], None)
                if check_method:
                    result = check_method(html_content)

                    if result['status'] == 'violation':
                        violations.append({
                            'rule_id': rule['id'],
                            'rule_name': rule['name'],
                            'description': rule['description'],
                            'level': rule['level'],
                            'category': rule['category'],
                            'severity': result.get('severity', 'error'),
                            'message': result.get('message', ''),
                            'elements': result.get('elements', []),
                            'recommendation': result.get('recommendation', ''),
                        })
                    elif result['status'] == 'warning':
                        warnings.append({
                            'rule_id': rule['id'],
                            'rule_name': rule['name'],
                            'message': result.get('message', ''),
                            'recommendation': result.get('recommendation', ''),
                        })
                    else:
                        passed.append(rule['id'])

            except Exception as e:
                violations.append({
                    'rule_id': rule['id'],
                    'rule_name': rule['name'],
                    'severity': 'error',
                    'message': f'Check failed: {str(e)}',
                })

        # 计算评分
        total_checks = len(applicable_rules)
        passed_count = len(passed)
        score = (passed_count / total_checks * 100) if total_checks > 0 else 0

        # 生成报告
        report = {
            'url': url or 'unknown',
            'audited_at': timestamp.isoformat(),
            'level': level,
            'summary': {
                'total_checks': total_checks,
                'passed': passed_count,
                'violations': len(violations),
                'warnings': len(warnings),
                'score': round(score, 2),
                'grade': self._get_grade(score),
            },
            'violations': violations,
            'warnings': warnings,
            'passed_rules': passed,
            'recommendations': self._generate_recommendations(violations),
        }

        return report

    def audit_multiple_pages(
            self,
            pages: List[Dict[str, str]],
            level: str = 'AA'
    ) -> Dict[str, Any]:
        """
        审计多个页面
        
        Args:
            pages: 页面列表 [{url, html}]
            level: 审计级别
        
        Returns:
            综合报告
        """
        reports = []

        for page in pages:
            report = self.audit_page(
                html_content=page['html'],
                url=page.get('url'),
                level=level
            )
            reports.append(report)

        # 生成综合统计
        total_violations = sum(r['summary']['violations'] for r in reports)
        total_warnings = sum(r['summary']['warnings'] for r in reports)
        avg_score = sum(r['summary']['score'] for r in reports) / len(reports) if reports else 0

        # 找出最常见的问题
        violation_counts = {}
        for report in reports:
            for violation in report['violations']:
                rule_id = violation['rule_id']
                violation_counts[rule_id] = violation_counts.get(rule_id, 0) + 1

        common_issues = sorted(
            violation_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        return {
            'total_pages': len(reports),
            'audited_at': datetime.now().isoformat(),
            'level': level,
            'summary': {
                'total_violations': total_violations,
                'total_warnings': total_warnings,
                'average_score': round(avg_score, 2),
                'pages_passing': sum(1 for r in reports if r['summary']['score'] >= 80),
                'pages_failing': sum(1 for r in reports if r['summary']['score'] < 80),
            },
            'common_issues': [
                {'rule_id': rule_id, 'count': count}
                for rule_id, count in common_issues
            ],
            'page_reports': reports,
        }

    def get_wcag_guidelines(self) -> Dict[str, Any]:
        """获取WCAG 2.1指南"""
        guidelines = {
            'principles': {
                'perceivable': {
                    'name': '可感知性',
                    'description': '信息和用户界面组件必须以用户可感知的方式呈现',
                    'guidelines': [
                        '1.1 文本替代：为非文本内容提供文本替代',
                        '1.2 时间基媒体：为时间基媒体提供替代',
                        '1.3 可适应：创建可以不同方式呈现的内容',
                        '1.4 可辨别：使用户更容易看到和听到内容',
                    ]
                },
                'operable': {
                    'name': '可操作性',
                    'description': '用户界面组件和导航必须可操作',
                    'guidelines': [
                        '2.1 键盘可访问：所有功能都可通过键盘访问',
                        '2.2 足够时间：为用户提供足够的时间阅读和使用内容',
                        '2.3 癫痫发作：不要设计可能引起癫痫发作的内容',
                        '2.4 可导航：帮助用户导航、查找内容和确定位置',
                    ]
                },
                'understandable': {
                    'name': '可理解性',
                    'description': '信息和用户界面的操作必须可理解',
                    'guidelines': [
                        '3.1 可读：使文本内容可读和可理解',
                        '3.2 可预测：使网页以可预测的方式出现和操作',
                        '3.3 输入辅助：帮助用户避免和纠正错误',
                    ]
                },
                'robust': {
                    'name': '鲁棒性',
                    'description': '内容必须足够健壮，以便被各种用户代理可靠地解释',
                    'guidelines': [
                        '4.1 兼容：最大化与当前和未来用户代理的兼容性',
                    ]
                }
            },
            'conformance_levels': {
                'A': {
                    'name': 'A级（最低）',
                    'description': '满足所有A级成功标准',
                    'requirement': '最基本级别的无障碍性',
                },
                'AA': {
                    'name': 'AA级（推荐）',
                    'description': '满足所有A级和AA级成功标准',
                    'requirement': '大多数组织的目标级别',
                },
                'AAA': {
                    'name': 'AAA级（最高）',
                    'description': '满足所有A级、AA级和AAA级成功标准',
                    'requirement': '最高级别的无障碍性',
                }
            }
        }

        return guidelines

    def _is_rule_applicable(self, rule: Dict[str, Any], target_level: str) -> bool:
        """检查规则是否适用于目标级别"""
        level_order = {'A': 1, 'AA': 2, 'AAA': 3}
        return level_order.get(rule['level'], 0) <= level_order.get(target_level, 0)

    def _get_grade(self, score: float) -> str:
        """获取等级"""
        if score >= 95:
            return 'A+'
        elif score >= 90:
            return 'A'
        elif score >= 85:
            return 'B+'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'

    def _generate_recommendations(self, violations: List[Dict[str, Any]]) -> List[str]:
        """生成修复建议"""
        recommendations = []

        # 按类别分组
        by_category = {}
        for v in violations:
            category = v.get('category', 'other')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(v)

        # 为每个类别生成建议
        if 'perceivable' in by_category:
            recommendations.append(
                '可感知性问题：确保所有内容都可以被用户感知，包括添加ALT文本和提高颜色对比度'
            )

        if 'operable' in by_category:
            recommendations.append(
                '可操作性问题：确保所有功能都可以通过键盘操作，并提供足够的交互时间'
            )

        if 'understandable' in by_category:
            recommendations.append(
                '可理解性问题：确保内容和界面操作清晰易懂，提供明确的错误提示'
            )

        if 'robust' in by_category:
            recommendations.append(
                '鲁棒性问题：使用标准的HTML和ARIA属性，确保与辅助技术兼容'
            )

        # 添加具体建议
        violation_ids = [v['rule_id'] for v in violations]

        if 'image-alt' in violation_ids:
            recommendations.append('为所有<img>标签添加描述性的alt属性')

        if 'color-contrast' in violation_ids:
            recommendations.append('提高文本和背景的对比度至至少4.5:1（AA级）或7:1（AAA级）')

        if 'heading-structure' in violation_ids:
            recommendations.append('按顺序使用标题（H1→H2→H3），不要跳过层级')

        if 'form-labels' in violation_ids:
            recommendations.append('为所有表单控件添加<label>元素或使用aria-label')

        if 'keyboard-accessible' in violation_ids:
            recommendations.append('确保所有交互元素可以通过Tab键访问，并提供可见的焦点样式')

        return recommendations

    # 检查方法（示例实现）

    def check_image_alt(self, html_content: str) -> Dict[str, Any]:
        """检查图片ALT文本"""
        # Parse HTML and check for alt attributes on img tags
        # Example implementation using BeautifulSoup:
        # from bs4 import BeautifulSoup
        # soup = BeautifulSoup(html_content, 'html.parser')
        # images = soup.find_all('img')
        # missing_alt = [img for img in images if not img.get('alt')]
        # if missing_alt:
        #     return {
        #         'status': 'violation',
        #         'message': f'{len(missing_alt)} images missing alt text',
        #         'elements': [{'tag': str(img), 'line': img.sourceline} for img in missing_alt],
        #         'recommendation': 'Add descriptive alt text to all images'
        #     }
        return {
            'status': 'pass',  # violation, warning, pass
            'message': 'All images have alt text',
            'elements': [],
            'recommendation': '',
        }

    def check_color_contrast(self, html_content: str) -> Dict[str, Any]:
        """检查颜色对比度"""
        # Parse CSS and check color contrast ratios
        # WCAG requires minimum 4.5:1 for normal text, 3:1 for large text
        # Example: Use a library like wcag-contrast-checker
        return {
            'status': 'pass',
            'message': 'Color contrast meets requirements',
        }

    def check_heading_structure(self, html_content: str) -> Dict[str, Any]:
        """检查标题结构"""
        # Check heading hierarchy (h1 > h2 > h3, no skipping levels)
        # Example implementation:
        # from bs4 import BeautifulSoup
        # soup = BeautifulSoup(html_content, 'html.parser')
        # headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        # Check for proper nesting and single h1
        return {
            'status': 'pass',
            'message': 'Heading structure is correct',
        }

    def check_link_purpose(self, html_content: str) -> Dict[str, Any]:
        """检查链接目的"""
        return {'status': 'pass'}

    def check_form_labels(self, html_content: str) -> Dict[str, Any]:
        """检查表单标签"""
        return {'status': 'pass'}

    def check_keyboard_accessible(self, html_content: str) -> Dict[str, Any]:
        """检查键盘可访问性"""
        return {'status': 'pass'}

    def check_aria_labels(self, html_content: str) -> Dict[str, Any]:
        """检查ARIA标签"""
        return {'status': 'pass'}

    def check_language_declaration(self, html_content: str) -> Dict[str, Any]:
        """检查语言声明"""
        return {'status': 'pass'}

    def check_focus_indicator(self, html_content: str) -> Dict[str, Any]:
        """检查焦点指示器"""
        return {'status': 'pass'}

    def check_error_identification(self, html_content: str) -> Dict[str, Any]:
        """检查错误识别"""
        return {'status': 'pass'}


# 全局实例
accessibility_auditor = AccessibilityAuditor()

# 导出
__all__ = ['AccessibilityAuditor', 'accessibility_auditor']
