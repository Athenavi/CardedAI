"""
成就徽章系统 API
提供徽章查询、进度追踪等功能
"""

from fastapi import APIRouter, Depends, Query, Body

from shared.models.user import User as UserModel
from shared.services.advanced_features.achievement_badge_system import achievement_badge_system
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import get_current_active_user, admin_required as admin_required_api

router = APIRouter(tags=["badges"])


@router.get("/my-badges", summary="获取我的徽章")
async def get_my_badges(
        category: str = Query(None, description="分类过滤"),
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    获取当前用户已获得的徽章
    
    Args:
        category: 分类过滤(writing/consistency/quality/community/social/special)
        
    Returns:
        徽章列表
    """
    try:
        badges = achievement_badge_system.get_user_badges(
            current_user.id,
            category=category
        )

        return ApiResponse(
            success=True,
            data={
                'badges': badges,
                'count': len(badges),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取徽章失败: {str(e)}")


@router.get("/available", summary="获取所有可用徽章")
async def get_available_badges(
        category: str = Query(None, description="分类过滤")
):
    """
    获取系统中所有可用的徽章
    
    Args:
        category: 分类过滤
        
    Returns:
        徽章列表
    """
    try:
        badges = achievement_badge_system.get_available_badges(category=category)

        return ApiResponse(
            success=True,
            data={
                'badges': badges,
                'count': len(badges),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取徽章列表失败: {str(e)}")


@router.get("/categories", summary="获取徽章分类")
async def get_badge_categories():
    """
    获取所有徽章分类
    
    Returns:
        分类列表
    """
    try:
        categories = achievement_badge_system.get_categories()

        return ApiResponse(
            success=True,
            data={
                'categories': categories,
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取分类失败: {str(e)}")


@router.get("/progress/{badge_key}", summary="获取徽章进度")
async def get_badge_progress(
        badge_key: str,
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    获取指定徽章的完成进度
    
    Args:
        badge_key: 徽章键
        
    Returns:
        进度信息
    """
    try:
        progress = achievement_badge_system.get_badge_progress(
            current_user.id,
            badge_key
        )

        if 'error' in progress:
            return ApiResponse(success=False, error=progress['error'])

        return ApiResponse(
            success=True,
            data=progress
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取进度失败: {str(e)}")


@router.get("/details/{badge_key}", summary="获取徽章详情")
async def get_badge_details(badge_key: str):
    """
    获取徽章详细信息
    
    Args:
        badge_key: 徽章键
        
    Returns:
        徽章详情
    """
    try:
        details = achievement_badge_system.get_badge_details(badge_key)

        if not details:
            return ApiResponse(success=False, error='徽章不存在')

        return ApiResponse(
            success=True,
            data=details
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取详情失败: {str(e)}")


@router.post("/check-and-award", summary="检查并授予徽章")
async def check_and_award_badges(
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    检查用户是否满足徽章条件并自动授予
    
    Returns:
        新获得的徽章列表
    """
    try:
        newly_awarded = achievement_badge_system.check_and_award_badges(
            current_user.id
        )

        return ApiResponse(
            success=True,
            message=f'获得 {len(newly_awarded)} 个新徽章',
            data={
                'newly_awarded': newly_awarded,
                'count': len(newly_awarded),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"检查徽章失败: {str(e)}")


# 管理员接口

@router.post("/admin/award", summary="手动授予徽章")
async def admin_award_badge(
        user_id: int = Body(..., description="目标用户ID"),
        badge_key: str = Body(..., description="徽章键"),
        current_user: UserModel = Depends(admin_required_api)
):
    """
    管理员手动为用户授予徽章
    
    Args:
        user_id: 目标用户ID
        badge_key: 徽章键
        
    Returns:
        操作结果
    """
    try:
        success = achievement_badge_system.manually_award_badge(user_id, badge_key)

        if success:
            badge_details = achievement_badge_system.get_badge_details(badge_key)
            return ApiResponse(
                success=True,
                message=f'成功为用户 {user_id} 授予徽章: {badge_details["name"]}',
                data={
                    'user_id': user_id,
                    'badge_key': badge_key,
                    'badge_name': badge_details['name'],
                }
            )
        else:
            return ApiResponse(success=False, error='授予失败(徽章不存在或已获得)')
    except Exception as e:
        return ApiResponse(success=False, error=f"授予失败: {str(e)}")


@router.get("/admin/stats", summary="获取徽章系统统计")
async def get_badge_system_stats(
        current_user: UserModel = Depends(admin_required_api)
):
    """
    获取徽章系统整体统计
    
    Returns:
        系统统计数据
    """
    try:
        total_badges = len(achievement_badge_system._badges)
        categories = achievement_badge_system.get_categories()

        # 简化统计
        total_awarded = sum(
            len(badges)
            for badges in achievement_badge_system._user_badges.values()
        )

        return ApiResponse(
            success=True,
            data={
                'total_badges': total_badges,
                'categories': categories,
                'total_awarded': total_awarded,
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取统计失败: {str(e)}")
