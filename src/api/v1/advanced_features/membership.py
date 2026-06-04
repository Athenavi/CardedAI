"""
会员订阅 API - 统一会员/VIP功能模块
整合了原有的 vip.py 和 membership.py 功能
"""
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import VIPSubscription
from shared.models.article import Article
from shared.models.user import User
from shared.models.vip_feature import VIPFeature
from shared.services.core.membership import create_membership_service
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_session

router = APIRouter(tags=["membership"])


class CreateSubscriptionRequest(BaseModel):
    """创建订阅请求"""
    plan_id: int
    payment_amount: float
    transaction_id: Optional[str] = None


@router.get("/status")
async def get_vip_status(
        user_id: int = Query(..., description="用户ID"),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取用户 VIP 状态
    
    Args:
        user_id: 用户ID
        db: 数据库会话
        
    Returns:
        VIP 状态信息
    """
    try:
        service = create_membership_service(db)
        status = await service.get_user_vip_status(user_id)

        return {
            'success': True,
            'data': status,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check-access")
async def check_content_access(
        user_id: int = Query(..., description="用户ID"),
        article_id: int = Query(..., description="文章ID"),
        required_level: int = Query(0, ge=0, le=10, description="所需VIP等级"),
        db: AsyncSession = Depends(get_async_session)
):
    """
    检查内容访问权限
    
    Args:
        user_id: 用户ID
        article_id: 文章ID
        required_level: 所需VIP等级
        db: 数据库会话
        
    Returns:
        访问权限结果
    """
    try:
        service = create_membership_service(db)
        result = await service.check_content_access(user_id, article_id, required_level)

        return {
            'success': True,
            'data': result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subscribe")
async def create_subscription(
        request: CreateSubscriptionRequest,
        user_id: int = Query(..., description="用户ID"),
        db: AsyncSession = Depends(get_async_session)
):
    """
    创建订阅
    
    Args:
        request: 订阅请求
        user_id: 用户ID
        db: 数据库会话
        
    Returns:
        订阅结果
    """
    try:
        service = create_membership_service(db)
        result = await service.create_subscription(
            user_id=user_id,
            plan_id=request.plan_id,
            payment_amount=request.payment_amount,
            transaction_id=request.transaction_id
        )

        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cancel/{subscription_id}")
async def cancel_subscription(
        subscription_id: int,
        user_id: int = Query(..., description="用户ID"),
        db: AsyncSession = Depends(get_async_session)
):
    """
    取消订阅
    
    Args:
        subscription_id: 订阅ID
        user_id: 用户ID
        db: 数据库会话
        
    Returns:
        操作结果
    """
    try:
        service = create_membership_service(db)
        result = await service.cancel_subscription(subscription_id, user_id)

        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plans")
async def get_available_plans(
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取可用套餐列表
    
    Args:
        db: 数据库会话
        
    Returns:
        套餐列表
    """
    try:
        service = create_membership_service(db)
        plans = await service.get_available_plans()

        return {
            'success': True,
            'data': plans,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subscriptions")
async def get_user_subscriptions(
        user_id: int = Query(..., description="用户ID"),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取用户订阅历史
    
    Args:
        user_id: 用户ID
        db: 数据库会话
        
    Returns:
        订阅列表
    """
    try:
        service = create_membership_service(db)
        subscriptions = await service.get_user_subscriptions(user_id)

        return {
            'success': True,
            'data': subscriptions,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/features")
async def get_vip_features(
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取VIP特权功能
    """
    try:
        features_list = db.query(VIPFeature).filter_by(is_active=True).order_by(VIPFeature.required_level).all()

        # 按等级分组
        features_by_level: Dict[int, List[Dict[str, Any]]] = {}
        for feature in features_list:
            if feature.required_level not in features_by_level:
                features_by_level[feature.required_level] = []
            features_by_level[feature.required_level].append({
                "id": feature.id,
                "code": feature.code,
                "name": feature.name,
                "description": feature.description,
                "required_level": feature.required_level,
                "is_active": feature.is_active,
                "created_at": feature.created_at.isoformat() if feature.created_at else None
            })

        return ApiResponse(
            success=True,
            data={
                "features_by_level": features_by_level,
                "features": [{
                    "id": feature.id,
                    "code": feature.code,
                    "name": feature.name,
                    "description": feature.description,
                    "required_level": feature.required_level,
                    "is_active": feature.is_active,
                    "created_at": feature.created_at.isoformat() if feature.created_at else None
                } for feature in features_list]
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_vip_features: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/my-subscription")
async def get_my_subscription(
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取我的VIP订阅信息
    """
    try:
        # 获取当前用户
        user_query = select(User).where(User.id == current_user.id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()
        if not user:
            return ApiResponse(success=False, error="用户不存在", data=None)

        # 获取最新的有效订阅记录
        latest_subscription = db.query(VIPSubscription).filter(
            VIPSubscription.user_id == current_user.id,
            VIPSubscription.status == 1
        ).order_by(VIPSubscription.id.desc()).first()

        # 初始化 active_subscription
        active_subscription = None

        if latest_subscription:
            # 设置时区并检查订阅状态
            latest_subscription.expires_at = latest_subscription.expires_at.replace(tzinfo=datetime.timezone.utc)
            current_time = datetime.now(datetime.timezone.utc)

            # 更新过期状态
            if latest_subscription.expires_at <= current_time:
                latest_subscription.status = -1
                await db.commit()
            else:
                active_subscription = {
                    "id": latest_subscription.id,
                    "user_id": latest_subscription.user_id,
                    "plan_id": latest_subscription.plan_id,
                    "starts_at": latest_subscription.starts_at.isoformat() if latest_subscription.starts_at else None,
                    "expires_at": latest_subscription.expires_at.isoformat() if latest_subscription.expires_at else None,
                    "status": latest_subscription.status,
                    "payment_amount": float(
                        latest_subscription.payment_amount) if latest_subscription.payment_amount else None,
                    "transaction_id": latest_subscription.transaction_id,
                    "created_at": latest_subscription.created_at.isoformat() if latest_subscription.created_at else None
                }

        # 获取订阅历史
        subscription_history = db.query(VIPSubscription).filter(
            VIPSubscription.user_id == current_user.id
        ).order_by(VIPSubscription.id.desc()).all()

        return ApiResponse(
            success=True,
            data={
                "active_subscription": active_subscription,
                "subscription_history": [{
                    "id": sub.id,
                    "user_id": sub.user_id,
                    "plan_id": sub.plan_id,
                    "starts_at": sub.starts_at.isoformat() if sub.starts_at else None,
                    "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
                    "status": sub.status,
                    "payment_amount": float(sub.payment_amount) if sub.payment_amount else None,
                    "transaction_id": sub.transaction_id,
                    "created_at": sub.created_at.isoformat() if sub.created_at else None
                } for sub in subscription_history]
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_my_subscription: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))


@router.get("/premium-content")
async def get_premium_content(
        request: Request,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_session)
):
    """
    获取VIP专属内容
    """
    try:
        # 获取当前用户
        user_query = select(User).where(User.id == current_user.id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()
        if not user:
            return ApiResponse(success=False, error="用户不存在", data=None)

        # 获取VIP专属文章
        premium_articles = db.query(Article).filter(
            or_(
                Article.is_vip_only == True,
                Article.required_vip_level != 0
            ),
            Article.status == 1,
            Article.hidden == False
        ).filter(
            Article.required_vip_level <= user.vip_level
        ).order_by(Article.created_at.desc()).all() or []

        # 检查 user.vip_expires_at 是否为 None
        if user.vip_expires_at is not None:
            active_status = bool(user.vip_level != 0 and user.vip_expires_at > datetime.now())
        else:
            active_status = False

        return ApiResponse(
            success=True,
            data={
                "active_status": active_status,
                "current_vip_level": user.vip_level,
                "articles": [{
                    "id": article.id,
                    "title": article.title,
                    "slug": article.slug,
                    "excerpt": article.excerpt,
                    "cover_image": article.cover_image,
                    "views": article.views or 0,
                    "likes": article.likes or 0,
                    "required_vip_level": article.required_vip_level,
                    "created_at": article.created_at.isoformat() if article.created_at else None,
                    "updated_at": article.updated_at.isoformat() if article.updated_at else None,
                    "user_id": article.user,
                    "category_id": article.category,
                    "author": {
                        "id": article.user,
                        "username": "未知作者"
                    }
                } for article in premium_articles]
            }
        )
    except Exception as e:
        import traceback
        print(f"Error in get_premium_content: {str(e)}")
        print(traceback.format_exc())
        return ApiResponse(success=False, error=str(e))
