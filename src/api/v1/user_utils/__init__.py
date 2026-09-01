"""
用户相关工具函数模块

该模块包含用户管理相关的各种工具函数：
- user_entities: 用户实体相关的业务逻辑
- user_profile: 用户资料管理相关功能
- qrlogin_utils: 二维码登录相关功能
"""
from src.utils.security.safe import validate_password_strength
from src.utils.security.password_validator import hash_password, verify_password
from .qrlogin_utils import *
from .user_entities import *

__all__ = [
    # 从 user_entities 导入的函数
    'auth_by_uid',
    'check_user_conflict',
    'db_save_bio',
    'change_username',
    'bind_email',
    'get_avatar',

    # 密码函数（直接来自 password_validator）
    'verify_password',
    'hash_password',

    # 从 qrlogin_utils 导入的函数
    'gen_qr_token',
    'validate_password_strength',
    'qr_login',
    'phone_scan_back',
    'check_qr_login_back',
]
