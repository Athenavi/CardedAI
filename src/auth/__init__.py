"""认证模块包初始化"""
from .auth_deps import (
    create_access_token,
    get_current_user,
    get_current_user_or_redirect,
    admin_required,
    admin_required_page,
    require_permission,
    require_role,
    require_permission_page,
    require_role_page,
    require_vip,
    jwt_required,
    jwt_required_page,
    jwt_optional_dependency,
    get_current_active_user,      # 向后兼容
    get_current_super_user,       # 向后兼容
)

from .user_manager import get_user_manager, get_user_db

# 保留旧别名
jwt_required_dependency = jwt_required
jwt_required_page_dependency = jwt_required_page
admin_required_api = admin_required
admin_required_page_dependency = admin_required_page