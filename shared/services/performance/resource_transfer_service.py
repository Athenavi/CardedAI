"""简化的资源传输服务（个人站长轻量版）"""


class ResourceTransferService:
    """资源传输服务"""

    async def transfer(self, source_url: str, destination: str) -> bool:
        """传输资源"""
        return True

    async def get_transfer_status(self, transfer_id: str) -> dict:
        return {'status': 'completed', 'transfer_id': transfer_id}


# 全局单例
transfer_service = ResourceTransferService()
