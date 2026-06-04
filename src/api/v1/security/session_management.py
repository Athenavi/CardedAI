"""
会话管理 API
提供会话查看、远程注销、设备管理等功能
"""

from typing import Optional

from fastapi import APIRouter, Depends, Body, Request

from shared.models.user import User as UserModel
from shared.services.users.session_management_service import session_management_service
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import get_current_active_user, admin_required as admin_required_api

router = APIRouter(tags=["sessions"])


@router.get("/my-sessions", summary="获取我的活跃会话")
async def get_my_sessions(
        request: Request,
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    获取当前用户的所有活跃会话(设备列表)
    
    Returns:
        会话列表
    """
    try:
        sessions = session_management_service.get_user_sessions(current_user.id)

        # 标记当前会话：将 last_active 最新的作为当前设备
        if sessions:
            # 按 last_active 降序排序，第一个标记为 current
            sorted_sessions = sorted(
                sessions,
                key=lambda s: s.get('last_active', s.get('created_at', '')),
                reverse=True
            )
            if sorted_sessions:
                sorted_sessions[0]['is_current'] = True

        return ApiResponse(
            success=True,
            data={
                'sessions': sessions,
                'count': len(sessions),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取会话失败: {str(e)}")


@router.post("/revoke", summary="远程注销指定设备")
async def revoke_session(
        session_id: str = Body(..., embed=True, description="会话ID"),
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    远程注销指定的设备/会话
    
    Args:
        session_id: 要注销的会话ID
        
    Returns:
        操作结果
    """
    try:
        success = session_management_service.revoke_session(
            current_user.id,
            session_id
        )

        if success:
            return ApiResponse(
                success=True,
                message='设备已注销',
                data={
                    'session_id': session_id,
                }
            )
        else:
            return ApiResponse(success=False, error='会话不存在或已失效')
    except Exception as e:
        return ApiResponse(success=False, error=f"注销失败: {str(e)}")


@router.post("/revoke-all", summary="注销所有其他设备")
async def revoke_all_sessions(
        current_session_id: Optional[str] = Body(None, description="当前会话ID(不注销)"),
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    注销所有其他设备(保留当前设备)
    
    Args:
        current_session_id: 当前会话ID(可选，用于排除)
        
    Returns:
        操作结果
    """
    try:
        revoked_count = session_management_service.revoke_all_sessions(
            current_user.id,
            exclude_session_id=current_session_id
        )

        return ApiResponse(
            success=True,
            message=f'已注销 {revoked_count} 个设备',
            data={
                'revoked_count': revoked_count,
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"注销失败: {str(e)}")


@router.get("/security-alerts", summary="获取安全告警")
async def get_security_alerts(
        request: Request,
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    检测并获取安全告警(异地登录、新设备等)
    
    Returns:
        安全告警列表
    """
    try:
        # 获取请求信息
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get('user-agent', '')

        # 生成设备指纹
        device_info = {
            'platform': request.headers.get('sec-ch-ua-platform', 'Unknown'),
            'browser': request.headers.get('sec-ch-ua', 'Unknown'),
        }
        device_fingerprint = session_management_service._generate_device_fingerprint(
            device_info, user_agent
        )

        # 检测可疑活动
        alerts = session_management_service.detect_suspicious_activity(
            current_user.id,
            ip_address,
            device_fingerprint
        )

        return ApiResponse(
            success=True,
            data={
                'alerts': alerts,
                'count': len(alerts),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"检测失败: {str(e)}")


@router.get("/stats", summary="获取会话统计")
async def get_session_stats(
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    获取用户的会话统计信息
    
    Returns:
        统计数据
    """
    try:
        sessions = session_management_service.get_user_sessions(current_user.id)

        # 按设备类型统计
        device_types = {}
        for session in sessions:
            device_type = session['device_info'].get('platform', 'Unknown')
            device_types[device_type] = device_types.get(device_type, 0) + 1

        return ApiResponse(
            success=True,
            data={
                'total_sessions': len(sessions),
                'device_types': device_types,
                'max_sessions': session_management_service.max_sessions_per_user,
                'session_timeout_hours': session_management_service.session_timeout_hours,
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取统计失败: {str(e)}")


# 管理员接口

@router.get("/user-sessions/{user_id}", summary="查看用户会话(管理员)")
async def admin_get_user_sessions(
        user_id: int,
        current_user: UserModel = Depends(admin_required_api)
):
    """
    管理员查看指定用户的会话列表
    
    Args:
        user_id: 目标用户ID
        
    Returns:
        会话列表
    """
    try:
        sessions = session_management_service.get_user_sessions(user_id)

        return ApiResponse(
            success=True,
            data={
                'user_id': user_id,
                'sessions': sessions,
                'count': len(sessions),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取会话失败: {str(e)}")
