"""简化的 AMP 服务（个人站长轻量版）"""


class AMPService:
    """AMP 加速页面服务"""

    def generate_amp_html(self, html_content: str) -> str:
        """生成 AMP 兼容 HTML"""
        return html_content


# 全局单例
amp_service = AMPService()
