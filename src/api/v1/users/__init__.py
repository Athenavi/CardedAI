"""
用户模块 - 统一入口
整合所有用户相关功能：资料管理、设置、关注、屏蔽等

注意：所有子模块已合并到 unified_users.py 中
"""
from fastapi import APIRouter

# 导入统一的用户路由器
from src.api.v1.users.unified_users import router as unified_users_router

router = APIRouter(tags=["users"])

# 包含统一的用户路由
router.include_router(unified_users_router)
