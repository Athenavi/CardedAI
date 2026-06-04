"""
用户积分系统 API
提供积分查询、兑换、排行榜等功能
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Body

from shared.models.user import User as UserModel
from shared.services.advanced_features.points_system import points_system
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import get_current_active_user, admin_required as admin_required_api

router = APIRouter(tags=["points"])


@router.get("/my-points", summary="获取我的积分")
async def get_my_points(
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    获取当前用户的积分余额
    
    Returns:
        当前积分数量
    """
    try:
        points = points_system.get_user_points(current_user.id)

        return ApiResponse(
            success=True,
            data={
                'points': points,
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取积分失败: {str(e)}")


@router.get("/my-stats", summary="获取我的积分统计")
async def get_my_stats(
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    获取当前用户的积分统计数据
    
    Returns:
        积分统计信息
    """
    try:
        stats = points_system.get_user_stats(current_user.id)

        return ApiResponse(
            success=True,
            data=stats
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取统计失败: {str(e)}")


@router.get("/my-history", summary="获取我的积分历史")
async def get_my_history(
        limit: int = Query(50, ge=1, le=200, description="返回数量"),
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    获取当前用户的积分历史记录
    
    Args:
        limit: 返回数量(1-200)
        
    Returns:
        积分历史记录列表
    """
    try:
        history = points_system.get_points_history(current_user.id, limit=limit)

        return ApiResponse(
            success=True,
            data={
                'history': history,
                'count': len(history),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取历史失败: {str(e)}")


@router.get("/leaderboard", summary="获取积分排行榜")
async def get_leaderboard(
        limit: int = Query(100, ge=1, le=500, description="返回数量"),
        period: str = Query('all', enum=['all', 'week', 'month'], description="时间周期")
):
    """
    获取积分排行榜
    
    Args:
        limit: 返回数量(1-500)
        period: 时间周期 (all/week/month)
        
    Returns:
        排行榜列表
    """
    try:
        leaderboard = points_system.get_leaderboard(limit=limit, period=period)

        return ApiResponse(
            success=True,
            data={
                'leaderboard': leaderboard,
                'count': len(leaderboard),
                'period': period,
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取排行榜失败: {str(e)}")


@router.get("/exchange-rules", summary="获取兑换规则")
async def get_exchange_rules():
    """
    获取积分兑换规则
    
    Returns:
        兑换规则列表
    """
    try:
        rules = points_system.get_exchange_rules()

        return ApiResponse(
            success=True,
            data={
                'rules': rules,
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取规则失败: {str(e)}")


@router.get("/points-rules", summary="获取积分规则")
async def get_points_rules():
    """
    获取积分获取规则
    
    Returns:
        积分规则列表
    """
    try:
        rules = points_system.get_points_rules()

        return ApiResponse(
            success=True,
            data={
                'rules': rules,
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取规则失败: {str(e)}")


@router.post("/exchange", summary="积分兑换")
async def exchange_points(
        item: str = Body(..., embed=True, description="兑换物品"),
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    使用积分兑换物品
    
    Args:
        item: 兑换物品名称
        
    Returns:
        兑换结果
    """
    try:
        result = points_system.exchange_points(current_user.id, item)

        if result['success']:
            return ApiResponse(
                success=True,
                message=result['message'],
                data={
                    'item': result['item'],
                    'cost': result['cost'],
                    'remaining_points': result['remaining_points'],
                }
            )
        else:
            return ApiResponse(
                success=False,
                error=result['message'],
                data={
                    'required': result.get('required'),
                    'current': result.get('current'),
                }
            )
    except Exception as e:
        return ApiResponse(success=False, error=f"兑换失败: {str(e)}")


@router.post("/record-action", summary="记录行为并发放积分")
async def record_action(
        action: str = Body(..., embed=True, description="行为类型"),
        article_id: Optional[int] = Body(None, description="文章ID"),
        comment_id: Optional[int] = Body(None, description="评论ID"),
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    记录用户行为并自动发放积分
    
    支持的行为类型:
    - article_published: 发布文章
    - comment_created: 发表评论
    - article_liked: 文章被点赞
    - comment_liked: 评论被点赞
    - daily_login: 每日登录
    - profile_completed: 完善资料
    
    Args:
        action: 行为类型
        article_id: 文章ID(可选)
        comment_id: 评论ID(可选)
        
    Returns:
        操作结果
    """
    try:
        success = points_system.record_action(
            current_user.id,
            action,
            article_id=article_id,
            comment_id=comment_id,
        )

        if success:
            current_points = points_system.get_user_points(current_user.id)
            return ApiResponse(
                success=True,
                message='积分已发放',
                data={
                    'action': action,
                    'current_points': current_points,
                }
            )
        else:
            return ApiResponse(
                success=False,
                error='未获得积分(可能已达上限或重复操作)'
            )
    except Exception as e:
        return ApiResponse(success=False, error=f"记录失败: {str(e)}")


# 管理员接口

@router.post("/admin/add-points", summary="手动添加积分")
async def admin_add_points(
        user_id: int = Body(..., description="目标用户ID"),
        points: int = Body(..., ge=1, description="积分数量"),
        reason: str = Body('', description="原因说明"),
        current_user: UserModel = Depends(admin_required_api)
):
    """
    管理员手动为用户添加积分
    
    Args:
        user_id: 目标用户ID
        points: 积分数量
        reason: 原因说明
        
    Returns:
        操作结果
    """
    try:
        success = points_system.add_points(user_id, points, f"Admin: {reason}")

        if success:
            return ApiResponse(
                success=True,
                message=f'成功为用户 {user_id} 添加 {points} 积分',
                data={
                    'user_id': user_id,
                    'points_added': points,
                    'new_balance': points_system.get_user_points(user_id),
                }
            )
        else:
            return ApiResponse(success=False, error='添加失败')
    except Exception as e:
        return ApiResponse(success=False, error=f"添加失败: {str(e)}")


@router.post("/admin/deduct-points", summary="手动扣除积分")
async def admin_deduct_points(
        user_id: int = Body(..., description="目标用户ID"),
        points: int = Body(..., ge=1, description="积分数量"),
        reason: str = Body('', description="原因说明"),
        current_user: UserModel = Depends(admin_required_api)
):
    """
    管理员手动扣除用户积分
    
    Args:
        user_id: 目标用户ID
        points: 积分数量
        reason: 原因说明
        
    Returns:
        操作结果
    """
    try:
        success = points_system.deduct_points(user_id, points, f"Admin: {reason}")

        if success:
            return ApiResponse(
                success=True,
                message=f'成功从用户 {user_id} 扣除 {points} 积分',
                data={
                    'user_id': user_id,
                    'points_deducted': points,
                    'new_balance': points_system.get_user_points(user_id),
                }
            )
        else:
            return ApiResponse(success=False, error='扣除失败(积分不足)')
    except Exception as e:
        return ApiResponse(success=False, error=f"扣除失败: {str(e)}")


@router.get("/admin/stats", summary="获取积分系统统计")
async def get_system_stats(
        current_user: UserModel = Depends(admin_required_api)
):
    """
    获取积分系统整体统计
    
    Returns:
        系统统计数据
    """
    try:
        # 简化实现
        total_users_with_points = len([
            uid for uid, points in points_system._user_points.items()
            if points > 0
        ])

        total_points_issued = sum(points_system._user_points.values())

        return ApiResponse(
            success=True,
            data={
                'total_users_with_points': total_users_with_points,
                'total_points_issued': total_points_issued,
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取统计失败: {str(e)}")
