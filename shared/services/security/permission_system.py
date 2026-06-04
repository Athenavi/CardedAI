"""
细粒度权限管理系统
提供基于角色的访问控制（RBAC）和自定义权限
"""

from datetime import datetime, timezone
from typing import List, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.role import Role
from shared.models.user import User

# 预定义权限列表
PERMISSIONS = {
    # 文章权限
    "article": {
        "view": "查看文章",
        "create": "创建文章",
        "edit": "编辑文章",
        "delete": "删除文章",
        "publish": "发布文章",
        "edit_others": "编辑他人文章",
        "delete_others": "删除他人文章",
    },

    # 分类权限
    "category": {
        "view": "查看分类",
        "create": "创建分类",
        "edit": "编辑分类",
        "delete": "删除分类",
    },

    # 页面权限
    "page": {
        "view": "查看页面",
        "create": "创建页面",
        "edit": "编辑页面",
        "delete": "删除页面",
        "publish": "发布页面",
    },

    # 菜单权限
    "menu": {
        "view": "查看菜单",
        "create": "创建菜单",
        "edit": "编辑菜单",
        "delete": "删除菜单",
    },

    # 媒体权限
    "media": {
        "view": "查看媒体",
        "upload": "上传文件",
        "delete": "删除文件",
    },

    # 用户权限
    "user": {
        "view": "查看用户",
        "create": "创建用户",
        "edit": "编辑用户",
        "delete": "删除用户",
        "manage_roles": "管理角色",
    },

    # 插件权限
    "plugin": {
        "view": "查看插件",
        "install": "安装插件",
        "activate": "激活/停用插件",
        "delete": "删除插件",
        "configure": "配置插件",
    },

    # 主题权限
    "theme": {
        "view": "查看主题",
        "install": "安装主题",
        "activate": "激活主题",
        "delete": "删除主题",
        "customize": "自定义主题",
    },

    # 设置权限
    "settings": {
        "view": "查看设置",
        "edit": "编辑设置",
    },

    # 备份权限
    "backup": {
        "create": "创建备份",
        "restore": "恢复备份",
        "delete": "删除备份",
    },

    # 评论权限
    "comment": {
        "view": "查看评论",
        "approve": "审核评论",
        "edit": "编辑评论",
        "delete": "删除评论",
    },
}


class PermissionManager:
    """
    权限管理器
    提供细粒度的权限检查和管理功能
    """

    def __init__(self):
        self.permissions = PERMISSIONS

    def get_all_permissions(self) -> Dict[str, Dict[str, str]]:
        """获取所有可用权限"""
        return self.permissions

    def get_permission_label(self, resource: str, action: str) -> str:
        """
        获取权限标签
        
        Args:
            resource: 资源名称
            action: 操作名称
            
        Returns:
            权限描述
        """
        if resource in self.permissions and action in self.permissions[resource]:
            return self.permissions[resource][action]
        return f"{resource}.{action}"

    async def check_permission(
            self,
            db: AsyncSession,
            user_id: int,
            resource: str,
            action: str
    ) -> bool:
        """
        检查用户是否有指定权限
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            resource: 资源名称
            action: 操作名称
            
        Returns:
            是否有权限
        """
        try:
            # 获取用户
            user_query = select(User).where(User.id == user_id)
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()

            if not user:
                return False

            # 超级管理员拥有所有权限
            if user.role == 'admin' or user.is_superuser:
                return True

            # 获取用户角色
            role_query = select(Role).where(Role.id == user.role_id)
            role_result = await db.execute(role_query)
            role = role_result.scalar_one_or_none()

            if not role:
                return False

            # 检查角色权限
            permission_key = f"{resource}.{action}"

            if role.permissions:
                import json
                permissions = json.loads(role.permissions)
                return permission_key in permissions

            return False

        except Exception as e:
            print(f"权限检查失败: {e}")
            return False

    async def check_any_permission(
            self,
            db: AsyncSession,
            user_id: int,
            permissions: List[tuple]
    ) -> bool:
        """
        检查用户是否有任何一个权限
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            permissions: 权限列表 [(resource, action), ...]
            
        Returns:
            是否有任一权限
        """
        for resource, action in permissions:
            if await self.check_permission(db, user_id, resource, action):
                return True
        return False

    async def check_all_permissions(
            self,
            db: AsyncSession,
            user_id: int,
            permissions: List[tuple]
    ) -> bool:
        """
        检查用户是否有所有权限
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            permissions: 权限列表 [(resource, action), ...]
            
        Returns:
            是否有所有权限
        """
        for resource, action in permissions:
            if not await self.check_permission(db, user_id, resource, action):
                return False
        return True

    async def get_user_permissions(
            self,
            db: AsyncSession,
            user_id: int
    ) -> List[str]:
        """
        获取用户的所有权限
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            权限列表
        """
        try:
            user_query = select(User).where(User.id == user_id)
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()

            if not user:
                return []

            # 超级管理员返回所有权限
            if user.role == 'admin' or user.is_superuser:
                all_perms = []
                for resource, actions in self.permissions.items():
                    for action in actions.keys():
                        all_perms.append(f"{resource}.{action}")
                return all_perms

            # 获取角色权限
            role_query = select(Role).where(Role.id == user.role_id)
            role_result = await db.execute(role_query)
            role = role_result.scalar_one_or_none()

            if not role or not role.permissions:
                return []

            import json
            return json.loads(role.permissions)

        except Exception as e:
            print(f"获取用户权限失败: {e}")
            return []

    async def assign_role(
            self,
            db: AsyncSession,
            user_id: int,
            role_id: int
    ) -> bool:
        """
        为用户分配角色
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            role_id: 角色ID
            
        Returns:
            是否成功
        """
        try:
            user_query = select(User).where(User.id == user_id)
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()

            if not user:
                return False

            role_query = select(Role).where(Role.id == role_id)
            role_result = await db.execute(role_query)
            role = role_result.scalar_one_or_none()

            if not role:
                return False

            user.role_id = role_id
            user.updated_at = datetime.now(timezone.utc)

            await db.commit()
            return True

        except Exception as e:
            await db.rollback()
            print(f"分配角色失败: {e}")
            return False

    async def create_custom_role(
            self,
            db: AsyncSession,
            name: str,
            slug: str,
            permissions: List[str],
            description: str = ""
    ) -> Optional[Role]:
        """
        创建自定义角色
        
        Args:
            db: 数据库会话
            name: 角色名称
            slug: 角色标识
            permissions: 权限列表
            description: 角色描述
            
        Returns:
            创建的角色
        """
        try:
            import json

            now = datetime.now(timezone.utc)

            role = Role(
                name=name,
                slug=slug,
                description=description,
                permissions=json.dumps(permissions),
                is_system=False,
                created_at=now,
                updated_at=now
            )

            db.add(role)
            await db.commit()
            await db.refresh(role)

            return role

        except Exception as e:
            await db.rollback()
            print(f"创建角色失败: {e}")
            return None

    async def update_role_permissions(
            self,
            db: AsyncSession,
            role_id: int,
            permissions: List[str]
    ) -> bool:
        """
        更新角色权限
        
        Args:
            db: 数据库会话
            role_id: 角色ID
            permissions: 新权限列表
            
        Returns:
            是否成功
        """
        try:
            import json

            role_query = select(Role).where(Role.id == role_id)
            role_result = await db.execute(role_query)
            role = role_result.scalar_one_or_none()

            if not role:
                return False

            role.permissions = json.dumps(permissions)
            role.updated_at = datetime.now(timezone.utc)

            await db.commit()
            return True

        except Exception as e:
            await db.rollback()
            print(f"更新角色权限失败: {e}")
            return False


# 全局权限管理器实例
permission_manager = PermissionManager()


# 权限装饰器（用于FastAPI路由）
def require_permission(resource: str, action: str):
    """
    权限要求装饰器
    
    Usage:
        @router.post("/articles")
        @require_permission("article", "create")
        async def create_article(...):
            ...
    """

    def decorator(func):
        func._required_permission = (resource, action)
        return func

    return decorator
