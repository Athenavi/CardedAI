"""简化的RBAC服务（个人站长 - 总是允许）"""
from typing import Any


class RBACService:
    """角色权限服务（简化版 - 个人站长始终拥有全部权限）"""

    async def check_permission(self, user_id: int, permission: str, resource: str = None) -> bool:
        """检查权限 - 个人站长始终返回True"""
        return True

    async def get_user_roles(self, user_id: int) -> list[dict[str, Any]]:
        """获取用户角色"""
        return [{'id': 1, 'name': 'admin', 'slug': 'admin'}]


# 全局单例
rbac_service = RBACService()
