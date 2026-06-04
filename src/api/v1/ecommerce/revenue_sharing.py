"""
收益分成 API
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from shared.services.ecommerce.revenue_sharing_service import RevenueSharingService
from src.extensions import get_db

router = APIRouter(tags=["收益分成"])


# ==================== Pydantic 模型 ====================

class RevenueRecordCreate(BaseModel):
    """创建收益记录请求"""
    user_id: int = Field(..., description="用户ID")
    revenue_type: str = Field(..., description="收益类型")
    amount: float = Field(..., description="收益金额")
    description: Optional[str] = Field(None, description="描述")
    reference_id: Optional[int] = Field(None, description="关联记录ID")
    reference_type: Optional[str] = Field(None, description="关联记录类型")


class PayoutRequestCreate(BaseModel):
    """创建提现申请请求"""
    amount: float = Field(..., description="提现金额")
    payment_method: str = Field(..., description="支付方式: alipay, wechat, bank_transfer")
    payment_account: str = Field(..., description="支付账号")
    account_name: Optional[str] = Field(None, description="账户姓名")


class SharingConfigUpdate(BaseModel):
    """更新分成配置请求"""
    platform_percentage: Optional[float] = Field(None, description="平台分成百分比")
    creator_percentage: Optional[float] = Field(None, description="创作者分成百分比")
    min_payout_amount: Optional[float] = Field(None, description="最低提现金额")
    description: Optional[str] = Field(None, description="描述")


# ==================== 依赖注入 ====================

def get_revenue_service(db: Session = Depends(get_db)) -> RevenueSharingService:
    """获取收益服务实例"""
    return RevenueSharingService(db)


# ==================== 收益记录 API ====================

@router.post("/records", response_model=dict)
def create_revenue_record(
        record: RevenueRecordCreate,
        service: RevenueSharingService = Depends(get_revenue_service)
):
    """创建收益记录"""
    try:
        # 转换收益类型
        try:
            revenue_type = RevenueType(record.revenue_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的收益类型: {record.revenue_type}")

        new_record = service.record_revenue(
            user_id=record.user_id,
            revenue_type=revenue_type,
            amount=record.amount,
            description=record.description,
            reference_id=record.reference_id,
            reference_type=record.reference_type
        )

        return {
            "success": True,
            "data": {"id": new_record.id},
            "message": "收益记录创建成功"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/records", response_model=dict)
def list_revenue_records(
        user_id: int = Query(..., description="用户ID"),
        revenue_type: Optional[str] = Query(None, description="收益类型"),
        status: Optional[str] = Query(None, description="状态"),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        service: RevenueSharingService = Depends(get_revenue_service)
):
    """获取收益记录列表"""
    rev_type = None
    if revenue_type:
        try:
            rev_type = RevenueType(revenue_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的收益类型: {revenue_type}")

    records = service.list_user_revenues(
        user_id=user_id,
        revenue_type=rev_type,
        status=status,
        skip=skip,
        limit=limit
    )

    return {
        "success": True,
        "data": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "revenue_type": r.revenue_type.value,
                "amount": r.amount,
                "platform_fee": r.platform_fee,
                "creator_earnings": r.creator_earnings,
                "description": r.description,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ],
        "total": len(records)
    }


@router.get("/summary/{user_id}", response_model=dict)
def get_revenue_summary(
        user_id: int,
        start_date: Optional[datetime] = Query(None, description="开始日期"),
        end_date: Optional[datetime] = Query(None, description="结束日期"),
        service: RevenueSharingService = Depends(get_revenue_service)
):
    """获取用户收益汇总"""
    summary = service.get_user_revenue_summary(user_id, start_date, end_date)

    return {
        "success": True,
        "data": summary
    }


# ==================== 用户统计 API ====================

@router.get("/stats/{user_id}", response_model=dict)
def get_user_stats(
        user_id: int,
        service: RevenueSharingService = Depends(get_revenue_service)
):
    """获取用户收益统计"""
    stats = service.get_user_stats(user_id)

    return {
        "success": True,
        "data": {
            "user_id": stats.user_id,
            "total_earnings": stats.total_earnings,
            "total_paid": stats.total_paid,
            "pending_earnings": stats.pending_earnings,
            "available_balance": stats.available_balance,
            "last_payout_at": stats.last_payout_at.isoformat() if stats.last_payout_at else None,
            "updated_at": stats.updated_at.isoformat() if stats.updated_at else None,
        }
    }


# ==================== 提现管理 API ====================

@router.post("/payouts", response_model=dict)
def create_payout_request(
        payout: PayoutRequestCreate,
        user_id: int = Query(..., description="用户ID"),
        service: RevenueSharingService = Depends(get_revenue_service)
):
    """创建提现申请"""
    try:
        new_payout = service.create_payout_request(
            user_id=user_id,
            amount=payout.amount,
            payment_method=payout.payment_method,
            payment_account=payout.payment_account,
            account_name=payout.account_name
        )

        return {
            "success": True,
            "data": {"id": new_payout.id},
            "message": "提现申请提交成功"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/payouts", response_model=dict)
def list_payout_requests(
        user_id: Optional[int] = Query(None, description="用户ID"),
        status: Optional[str] = Query(None, description="状态"),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        service: RevenueSharingService = Depends(get_revenue_service)
):
    """获取提现申请列表"""
    payouts = service.list_payout_requests(
        user_id=user_id,
        status=status,
        skip=skip,
        limit=limit
    )

    return {
        "success": True,
        "data": [
            {
                "id": p.id,
                "user_id": p.user_id,
                "amount": p.amount,
                "payment_method": p.payment_method,
                "payment_account": p.payment_account,
                "account_name": p.account_name,
                "status": p.status,
                "admin_notes": p.admin_notes,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "processed_at": p.processed_at.isoformat() if p.processed_at else None,
            }
            for p in payouts
        ],
        "total": len(payouts)
    }


@router.post("/payouts/{payout_id}/approve", response_model=dict)
def approve_payout(
        payout_id: int,
        admin_id: int = Query(..., description="管理员ID"),
        notes: Optional[str] = Query(None, description="备注"),
        service: RevenueSharingService = Depends(get_revenue_service)
):
    """批准提现"""
    try:
        payout = service.approve_payout(payout_id, admin_id, notes)
        if not payout:
            raise HTTPException(status_code=404, detail="提现申请不存在")

        return {
            "success": True,
            "data": {"id": payout.id, "status": payout.status},
            "message": "提现已批准"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/payouts/{payout_id}/complete", response_model=dict)
def complete_payout(
        payout_id: int,
        admin_id: int = Query(..., description="管理员ID"),
        notes: Optional[str] = Query(None, description="备注"),
        service: RevenueSharingService = Depends(get_revenue_service)
):
    """完成提现"""
    try:
        payout = service.complete_payout(payout_id, admin_id, notes)
        if not payout:
            raise HTTPException(status_code=404, detail="提现申请不存在")

        return {
            "success": True,
            "data": {"id": payout.id, "status": payout.status},
            "message": "提现已完成"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/payouts/{payout_id}/reject", response_model=dict)
def reject_payout(
        payout_id: int,
        admin_id: int = Query(..., description="管理员ID"),
        notes: Optional[str] = Query(None, description="备注"),
        service: RevenueSharingService = Depends(get_revenue_service)
):
    """拒绝提现"""
    try:
        payout = service.reject_payout(payout_id, admin_id, notes)
        if not payout:
            raise HTTPException(status_code=404, detail="提现申请不存在")

        return {
            "success": True,
            "data": {"id": payout.id, "status": payout.status},
            "message": "提现已拒绝"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 分成配置 API ====================

@router.get("/configs", response_model=dict)
def list_sharing_configs(
        service: RevenueSharingService = Depends(get_revenue_service)
):
    """获取所有分成配置"""
    configs = []
    for rev_type in RevenueType:
        config = service.get_sharing_config(rev_type)
        if config:
            configs.append({
                "revenue_type": config.revenue_type.value,
                "platform_percentage": config.platform_percentage,
                "creator_percentage": config.creator_percentage,
                "min_payout_amount": config.min_payout_amount,
                "is_active": config.is_active,
                "description": config.description,
            })

    return {
        "success": True,
        "data": configs
    }


@router.put("/configs/{revenue_type}", response_model=dict)
def update_sharing_config(
        revenue_type: str,
        config_update: SharingConfigUpdate,
        service: RevenueSharingService = Depends(get_revenue_service)
):
    """更新分成配置"""
    try:
        rev_type = RevenueType(revenue_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的收益类型: {revenue_type}")

    updated = service.update_sharing_config(
        rev_type,
        **config_update.dict(exclude_unset=True)
    )

    if not updated:
        raise HTTPException(status_code=404, detail="配置不存在")

    return {
        "success": True,
        "data": {"revenue_type": updated.revenue_type.value},
        "message": "配置更新成功"
    }


# ==================== 平台统计 API ====================

@router.get("/stats/platform", response_model=dict)
def get_platform_stats(
        start_date: Optional[datetime] = Query(None, description="开始日期"),
        end_date: Optional[datetime] = Query(None, description="结束日期"),
        service: RevenueSharingService = Depends(get_revenue_service)
):
    """获取平台统计"""
    stats = service.get_platform_stats(start_date, end_date)

    return {
        "success": True,
        "data": stats
    }
