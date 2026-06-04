"""
登录安全 API
提供异常检测、频繁失败锁定、设备指纹识别等功能
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.user import User as UserModel
from shared.services.users.login_security_service import login_security_service
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import get_current_active_user, admin_required as admin_required_api
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["security"])


# 注意：以下旧API端点已弃用，因为登录安全服务已重构为基于数据库的异步实现
# 新的实现在登录流程中自动记录，无需单独调用

# @router.post("/check-lock", summary="检查账户锁定状态")
# async def check_account_lock(
#         user_id: int = Body(..., embed=True, description="用户ID"),
# ):
#     """
#     检查用户账户是否被锁定
#     
#     Args:
#         user_id: 用户ID
#         
#     Returns:
#         锁定状态
#     """
#     try:
#         result = login_security_service.check_user_locked(user_id)
#
#         return ApiResponse(
#             success=True,
#             data=result
#         )
#     except Exception as e:
#         return ApiResponse(success=False, error=f"检查失败: {str(e)}")
#
#
# @router.post("/record-failure", summary="记录登录失败")
# async def record_login_failure(
#         request: Request,
#         user_id: int = Body(..., embed=True, description="用户ID"),
# ):
#     """
#     记录登录失败(登录接口调用)
#     
#     Args:
#         user_id: 用户ID
#         
#     Returns:
#         检查结果(是否被锁定)
#     """
#     try:
#         ip_address = request.client.host if request.client else 'unknown'
#         user_agent = request.headers.get('user-agent', '')
#
#         result = login_security_service.record_login_failure(
#             user_id=user_id,
#             ip_address=ip_address,
#             user_agent=user_agent,
#         )
#
#         return ApiResponse(
#             success=True,
#             data=result
#         )
#     except Exception as e:
#         return ApiResponse(success=False, error=f"记录失败: {str(e)}")
#
#
# @router.post("/record-success", summary="记录登录成功")
# async def record_login_success(
#         request: Request,
#         current_user: UserModel = Depends(get_current_active_user)
# ):
#     """
#     记录登录成功(登录后调用)
#     
#     Returns:
#         安全检查结果和告警
#     """
#     try:
#         ip_address = request.client.host if request.client else 'unknown'
#         user_agent = request.headers.get('user-agent', '')
#
#         # 解析设备信息
#         device_info = {
#             'platform': request.headers.get('sec-ch-ua-platform', 'Unknown'),
#             'browser': request.headers.get('sec-ch-ua', 'Unknown'),
#         }
#
#         result = login_security_service.record_login_success(
#             user_id=current_user.id,
#             ip_address=ip_address,
#             user_agent=user_agent,
#             device_info=device_info,
#         )
#
#         return ApiResponse(
#             success=True,
#             data=result
#         )
#     except Exception as e:
#         return ApiResponse(success=False, error=f"记录失败: {str(e)}")


@router.get("/my-history", summary="获取我的登录历史")
async def get_my_login_history(
        limit: int = Query(50, ge=1, le=200, description="返回数量"),
        current_user: UserModel = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取当前用户的登录历史记录
    
    Args:
        limit: 返回数量(1-200)
        
    Returns:
        登录历史列表
    """
    try:
        history = await login_security_service.get_login_history_async(
            username=current_user.username,
            limit=limit,
            db=db
        )

        return ApiResponse(
            success=True,
            data={
                'history': history,
                'count': len(history),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取历史失败: {str(e)}")


@router.get("/my-stats", summary="获取我的安全统计")
async def get_my_security_stats(
        current_user: UserModel = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取当前用户的安全统计数据
    
    Returns:
        统计数据
    """
    try:
        stats = await login_security_service.get_security_stats_async(
            username=current_user.username,
            db=db
        )

        return ApiResponse(
            success=True,
            data=stats
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取统计失败: {str(e)}")


# 管理员接口

@router.get("/admin/locked-users", summary="获取被锁定的用户列表")
async def get_locked_users(
        current_user: UserModel = Depends(admin_required_api),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取所有当前被锁定的用户
    
    Returns:
        锁定用户列表
    """
    try:
        locked_users = await login_security_service.get_locked_users_async(db=db)

        return ApiResponse(
            success=True,
            data={
                'locked_users': locked_users,
                'count': len(locked_users),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取列表失败: {str(e)}")


# @router.post("/admin/unlock", summary="手动解锁用户")
# async def unlock_user(
#         user_id: int = Body(..., embed=True, description="用户ID"),
#         current_user: UserModel = Depends(admin_required_api)
# ):
#     """
#     管理员手动解锁用户
#     
#     Args:
#         user_id: 用户ID
#         
#     Returns:
#         操作结果
#     """
#     try:
#         success = login_security_service.unlock_user(user_id)
#
#         if success:
#             return ApiResponse(
#                 success=True,
#                 message=f'用户 {user_id} 已解锁'
#             )
#         else:
#             return ApiResponse(success=False, error='用户未被锁定')
#     except Exception as e:
#         return ApiResponse(success=False, error=f"解锁失败: {str(e)}")


@router.get("/admin/user-history/{username}", summary="查看用户登录历史")
async def admin_get_user_history(
        username: str,
        limit: int = Query(50, ge=1, le=200, description="返回数量"),
        current_user: UserModel = Depends(admin_required_api),
        db: AsyncSession = Depends(get_async_db)
):
    """
    管理员查看指定用户的登录历史
    
    Args:
        username: 目标用户名
        limit: 返回数量
        
    Returns:
        登录历史列表
    """
    try:
        history = await login_security_service.get_login_history_async(
            username=username,
            limit=limit,
            db=db
        )

        return ApiResponse(
            success=True,
            data={
                'username': username,
                'history': history,
                'count': len(history),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取历史失败: {str(e)}")


@router.get("/admin/user-stats/{username}", summary="查看用户安全统计")
async def admin_get_user_stats(
        username: str,
        current_user: UserModel = Depends(admin_required_api),
        db: AsyncSession = Depends(get_async_db)
):
    """
    管理员查看指定用户的安全统计
    
    Args:
        username: 目标用户名
        
    Returns:
        统计数据
    """
    try:
        stats = await login_security_service.get_security_stats_async(
            username=username,
            db=db
        )

        return ApiResponse(
            success=True,
            data=stats
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取统计失败: {str(e)}")
