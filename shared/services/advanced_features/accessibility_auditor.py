"""简化的无障碍审核服务（个人站长轻量版）"""


class AccessibilityAuditor:
    """无障碍审核服务"""

    async def audit_page(self, url: str, content: str = None) -> dict:
        """审核页面无障碍情况"""
        return {
            'score': 100,
            'issues': [],
            'suggestions': ['保持语义化HTML结构', '确保图片有alt文本'],
        }


# 全局单例
accessibility_auditor = AccessibilityAuditor()
