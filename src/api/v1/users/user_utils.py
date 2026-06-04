"""
用户工具 API
提供用户登录状态检查等辅助功能
"""


from fastapi import APIRouter, Depends

from src.auth import jwt_required_dependency as jwt_required

router = APIRouter(tags=["user-utils"])


@router.get('/check-login')
async def check_login_status(current_user=Depends(jwt_required)):
    """
    检查用户登录状态
    
    Returns:
        登录状态信息
    """
    return {
        'logged_in': True,
        'message': 'User is logged in',
        'user_id': current_user.id if hasattr(current_user, 'id') else None
    }
