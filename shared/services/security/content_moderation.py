"""简化的内容审核服务（个人站长轻量版）"""
from typing import Optional


class ContentModerationService:
    """内容审核服务（简化版 - 始终通过）"""

    async def moderate(self, content: str, content_type: str = 'text') -> dict:
        """审核内容"""
        return {'approved': True, 'reason': None, 'score': 0.0}


# 全局单例
content_moderation_service = ContentModerationService()
