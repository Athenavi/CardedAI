"""
用户管理服务包

提供用户相关的核心服务:
- user_service: 用户数据库操作（CRUD、认证、搜索等）
- gravatar: Gravatar头像生成服务
- user_csv_service: 用户CSV导入/导出服务
"""

from .gravatar import GravatarService, gravatar_service
from .user_csv_service import UserCSVService, user_csv_service
from .user_service import (
    get_user_by_id,
    get_user_by_username,
    get_user_by_email,
    get_user_by_username_or_email,
    update_user_last_login,
    create_user_account,
    update_user_profile,
    check_password_async,
    set_user_password,
    deactivate_user,
    activate_user,
    count_users,
    search_users,
)

__all__ = [
    # 用户服务函数
    'get_user_by_id',
    'get_user_by_username',
    'get_user_by_email',
    'get_user_by_username_or_email',
    'update_user_last_login',
    'create_user_account',
    'update_user_profile',
    'check_password_async',
    'set_user_password',
    'deactivate_user',
    'activate_user',
    'count_users',
    'search_users',

    # Gravatar服务
    'GravatarService',
    'gravatar_service',

    # CSV服务
    'UserCSVService',
    'user_csv_service',
]
