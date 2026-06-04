"""
打赏系统 API
提供文章打赏、统计、排行榜等功能
"""

from fastapi import APIRouter, Depends, Query, Body

from shared.models.user import User as UserModel
from shared.services.ecommerce.tipping_system import tipping_system
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import get_current_active_user

router = APIRouter(tags=["tips"])


@router.post("/tip-article", summary="打赏文章")
async def tip_article(
        article_id: int = Body(..., description="文章ID"),
        amount: float = Body(..., ge=1, le=10000, description="打赏金额"),
        message: str = Body('', description="留言(可选)"),
        payment_method: str = Body('balance', enum=['balance', 'wechat', 'alipay'], description="支付方式"),
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    对文章进行打赏
    
    Args:
        article_id: 文章ID
        amount: 打赏金额(1-10000)
        message: 留言(可选)
        payment_method: 支付方式(balance/wechat/alipay)
        
    Returns:
        打赏结果
    """
    try:
        # Get article author ID from database
        # Example implementation:
        # from shared.models.article import Article
        # from sqlalchemy import select
        # 
        # stmt = select(Article).where(Article.id == article_id)
        # result = await db.execute(stmt)
        # article = result.scalar_one_or_none()
        # 
        # if not article:
        #     return ApiResponse(success=False, error='文章不存在')
        # 
        # article_author_id = article.user_id

        # For now, use mock data for demonstration
        article_author_id = 1  # Assuming article author is user 1

        if article_author_id == current_user.id:
            return ApiResponse(success=False, error='不能打赏自己的文章')

        # 创建打赏
        tip = tipping_system.create_tip(
            from_user_id=current_user.id,
            to_user_id=article_author_id,
            article_id=article_id,
            amount=amount,
            message=message,
            payment_method=payment_method,
        )

        return ApiResponse(
            success=True,
            message='打赏成功',
            data={
                'tip_id': tip['tip_id'],
                'amount': tip['amount'],
                'to_user_id': tip['to_user_id'],
            }
        )
    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=f"打赏失败: {str(e)}")


@router.get("/article/{article_id}", summary="获取文章打赏记录")
async def get_article_tips(
        article_id: int,
        limit: int = Query(50, ge=1, le=200, description="返回数量")
):
    """
    获取文章的打赏记录列表
    
    Args:
        article_id: 文章ID
        limit: 返回数量(1-200)
        
    Returns:
        打赏记录列表
    """
    try:
        tips = tipping_system.get_article_tips(article_id, limit=limit)
        stats = tipping_system.get_article_tip_stats(article_id)

        return ApiResponse(
            success=True,
            data={
                'tips': tips,
                'stats': stats,
                'count': len(tips),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取打赏记录失败: {str(e)}")


@router.get("/my-received", summary="获取我收到的打赏")
async def get_my_received_tips(
        limit: int = Query(100, ge=1, le=500, description="返回数量"),
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    获取当前用户收到的打赏记录
    
    Args:
        limit: 返回数量(1-500)
        
    Returns:
        打赏记录列表
    """
    try:
        tips = tipping_system.get_user_received_tips(current_user.id, limit=limit)
        stats = tipping_system.get_user_tip_stats(current_user.id)

        return ApiResponse(
            success=True,
            data={
                'tips': tips,
                'stats': stats,
                'count': len(tips),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取打赏记录失败: {str(e)}")


@router.get("/my-stats", summary="获取我的打赏统计")
async def get_my_tip_stats(
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    获取当前用户的打赏统计数据
    
    Returns:
        统计数据
    """
    try:
        stats = tipping_system.get_user_tip_stats(current_user.id)

        return ApiResponse(
            success=True,
            data=stats
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取统计失败: {str(e)}")


@router.get("/leaderboard", summary="获取打赏排行榜")
async def get_tipping_leaderboard(
        period: str = Query('all', enum=['all', 'month', 'week'], description="时间周期"),
        limit: int = Query(100, ge=1, le=500, description="返回数量")
):
    """
    获取打赏排行榜(按收到打赏金额排序)
    
    Args:
        period: 时间周期(all/month/week)
        limit: 返回数量(1-500)
        
    Returns:
        排行榜列表
    """
    try:
        leaderboard = tipping_system.get_tipping_leaderboard(period=period, limit=limit)

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


@router.get("/preset-amounts", summary="获取预设打赏金额")
async def get_preset_amounts():
    """
    获取系统预设的打赏金额选项
    
    Returns:
        金额列表
    """
    try:
        amounts = tipping_system.get_preset_amounts()

        return ApiResponse(
            success=True,
            data={
                'amounts': amounts,
                'min_amount': tipping_system.min_amount,
                'max_amount': tipping_system.max_amount,
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取金额失败: {str(e)}")


@router.get("/recent", summary="获取最近打赏记录")
async def get_recent_tips(
        limit: int = Query(20, ge=1, le=100, description="返回数量")
):
    """
    获取全站最近的打赏记录
    
    Args:
        limit: 返回数量(1-100)
        
    Returns:
        打赏记录列表
    """
    try:
        tips = tipping_system.get_recent_tips(limit=limit)

        return ApiResponse(
            success=True,
            data={
                'tips': tips,
                'count': len(tips),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取记录失败: {str(e)}")


@router.post("/refund", summary="退款打赏")
async def refund_tip(
        tip_id: str = Body(..., description="打赏ID"),
        reason: str = Body('', description="退款原因"),
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    申请退款打赏
    
    Args:
        tip_id: 打赏ID
        reason: 退款原因
        
    Returns:
        退款结果
    """
    try:
        # Verify user has permission to refund (tipper or article author)
        # Example implementation:
        # from shared.models.tipping import Tip
        # from sqlalchemy import select
        # 
        # stmt = select(Tip).where(Tip.tip_id == tip_id)
        # result = await db.execute(stmt)
        # tip = result.scalar_one_or_none()
        # 
        # if not tip:
        #     return ApiResponse(success=False, error='打赏不存在')
        # 
        # # Check if current user is the tipper or article author
        # if tip.from_user_id != current_user.id and tip.to_user_id != current_user.id:
        #     return ApiResponse(success=False, error='没有权限退款')
        
        success = tipping_system.refund_tip(tip_id, reason)

        if success:
            return ApiResponse(
                success=True,
                message='退款成功',
                data={
                    'tip_id': tip_id,
                }
            )
        else:
            return ApiResponse(success=False, error='退款失败(打赏不存在或已退款)')
    except Exception as e:
        return ApiResponse(success=False, error=f"退款失败: {str(e)}")


# ==================== 提现相关 API ====================

@router.get("/balance", summary="获取可提现余额")
async def get_available_balance(
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    获取当前用户的可提现余额信息
    
    Returns:
        余额信息
    """
    try:
        balance_info = tipping_system.get_user_available_balance(current_user.id)

        return ApiResponse(
            success=True,
            data=balance_info
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取余额失败: {str(e)}")


@router.post("/withdraw", summary="申请提现")
async def request_withdrawal(
        amount: float = Body(..., ge=1, description="提现金额"),
        payment_method: str = Body('bank_transfer', enum=['bank_transfer', 'wechat', 'alipay'], description="支付方式"),
        account_info: dict = Body({}, description="账户信息"),
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    申请提现
    
    Args:
        amount: 提现金额
        payment_method: 支付方式(bank_transfer/wechat/alipay)
        account_info: 账户信息(银行卡号、微信账号等)
        
    Returns:
        提现申请结果
    """
    try:
        withdrawal = tipping_system.create_withdrawal(
            user_id=current_user.id,
            amount=amount,
            payment_method=payment_method,
            account_info=account_info,
        )

        return ApiResponse(
            success=True,
            message='提现申请已提交',
            data={
                'withdrawal_id': withdrawal['withdrawal_id'],
                'amount': withdrawal['amount'],
                'fee': withdrawal['fee'],
                'actual_amount': withdrawal['actual_amount'],
                'status': withdrawal['status'],
            }
        )
    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=f"提现申请失败: {str(e)}")


@router.get("/my-withdrawals", summary="获取我的提现记录")
async def get_my_withdrawals(
        limit: int = Query(50, ge=1, le=200, description="返回数量"),
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    获取当前用户的提现记录
    
    Args:
        limit: 返回数量(1-200)
        
    Returns:
        提现记录列表
    """
    try:
        withdrawals = tipping_system.get_user_withdrawals(current_user.id, limit=limit)

        return ApiResponse(
            success=True,
            data={
                'withdrawals': withdrawals,
                'count': len(withdrawals),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取提现记录失败: {str(e)}")


@router.post("/cancel-withdrawal/{withdrawal_id}", summary="取消提现申请")
async def cancel_withdrawal(
        withdrawal_id: str,
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    取消提现申请（仅限pending状态）
    
    Args:
        withdrawal_id: 提现ID
        
    Returns:
        取消结果
    """
    try:
        success = tipping_system.cancel_withdrawal(withdrawal_id, current_user.id)

        if success:
            return ApiResponse(
                success=True,
                message='提现申请已取消'
            )
        else:
            return ApiResponse(success=False, error='取消失败(提现不存在或状态不允许取消)')
    except Exception as e:
        return ApiResponse(success=False, error=f"取消失败: {str(e)}")


@router.post("/admin/process-withdrawal", summary="处理提现申请（管理员）")
async def admin_process_withdrawal(
        withdrawal_id: str = Body(..., description="提现ID"),
        status: str = Body('completed', enum=['completed', 'rejected'], description="处理结果"),
        admin_note: str = Body('', description="管理员备注"),
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    管理员处理提现申请
    
    Args:
        withdrawal_id: 提现ID
        status: 处理结果(completed/rejected)
        admin_note: 管理员备注
        
    Returns:
        处理结果
    """
    try:
        # Admin permission check
        # Example implementation:
        # if not getattr(current_user, 'is_superuser', False) and not getattr(current_user, 'is_staff', False):
        #     return ApiResponse(success=False, error='需要管理员权限')
        
        success = tipping_system.process_withdrawal(
            withdrawal_id=withdrawal_id,
            status=status,
            admin_note=admin_note,
        )

        if success:
            return ApiResponse(
                success=True,
                message=f'提现申请已{"通过" if status == "completed" else "拒绝"}'
            )
        else:
            return ApiResponse(success=False, error='处理失败(提现不存在或状态不允许处理)')
    except Exception as e:
        return ApiResponse(success=False, error=f"处理失败: {str(e)}")
