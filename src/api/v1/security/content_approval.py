"""
内容审批 API
提供多级审批、审批意见、审批历史等功能
"""
from typing import Optional, List

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import ApprovalRecord
from shared.services.security.content_approval_service import content_approval_service
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import jwt_required_dependency as jwt_required, get_current_user
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["approval"])


# ==================== 审批请求管理 ====================

@router.post("/request", summary="创建审批请求")
async def create_approval_request(
        content_type: str = Body(..., description="内容类型 (article/comment)"),
        content_id: int = Body(..., description="内容ID"),
        max_level: int = Body(1, ge=1, le=3, description="最大审批级别 (1-3)"),
        approvers: List[int] = Body(None, description="各级审批人ID列表"),
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db)
):
    """
    创建内容审批请求
    
    Args:
        content_type: 内容类型
        content_id: 内容ID
        max_level: 最大审批级别
        approvers: 各级审批人ID列表
        
    Returns:
        创建的审批请求
    """
    try:
        record = await content_approval_service.create_approval_request(
            db=db,
            content_type=content_type,
            content_id=content_id,
            applicant_id=current_user.id,
            max_level=max_level,
            approvers=approvers
        )

        return ApiResponse(
            success=True,
            data={
                'id': record.id,
                'content_type': record.content_type,
                'content_id': record.content_id,
                'current_level': record.current_level,
                'max_level': record.max_level,
                'status': record.status,
                'created_at': record.created_at.isoformat() if record.created_at else None,
            },
            message="Approval request created successfully"
        )

    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/{record_id}/approve", summary="审批通过")
async def approve_step(
        record_id: int,
        comment: Optional[str] = Body(None, description="审批意见"),
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db)
):
    """
    审批通过当前级别
    
    Args:
        record_id: 审批记录ID
        comment: 审批意见
        
    Returns:
        更新后的审批记录
    """
    try:
        record = await content_approval_service.approve_step(
            db=db,
            record_id=record_id,
            approver_id=current_user.id,
            comment=comment
        )

        return ApiResponse(
            success=True,
            data={
                'id': record.id,
                'status': record.status,
                'current_level': record.current_level,
                'completed_at': record.completed_at.isoformat() if record.completed_at else None,
            },
            message="Approved successfully"
        )

    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/{record_id}/reject", summary="审批拒绝")
async def reject_step(
        record_id: int,
        comment: Optional[str] = Body(None, description="拒绝意见"),
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db)
):
    """
    审批拒绝
    
    Args:
        record_id: 审批记录ID
        comment: 拒绝意见
        
    Returns:
        更新后的审批记录
    """
    try:
        record = await content_approval_service.reject_step(
            db=db,
            record_id=record_id,
            approver_id=current_user.id,
            comment=comment
        )

        return ApiResponse(
            success=True,
            data={
                'id': record.id,
                'status': record.status,
                'completed_at': record.completed_at.isoformat() if record.completed_at else None,
            },
            message="Rejected successfully"
        )

    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/{record_id}/cancel", summary="取消审批")
async def cancel_approval(
        record_id: int,
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db)
):
    """
    取消审批请求（仅申请人）
    
    Args:
        record_id: 审批记录ID
        
    Returns:
        更新后的审批记录
    """
    try:
        record = await content_approval_service.cancel_approval(
            db=db,
            record_id=record_id,
            user_id=current_user.id
        )

        return ApiResponse(
            success=True,
            data={
                'id': record.id,
                'status': record.status,
                'completed_at': record.completed_at.isoformat() if record.completed_at else None,
            },
            message="Approval cancelled successfully"
        )

    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# ==================== 审批查询 ====================

@router.get("/{record_id}/history", summary="获取审批历史")
async def get_approval_history(
        record_id: int,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取审批历史记录
    
    Args:
        record_id: 审批记录ID
        
    Returns:
        审批历史
    """
    try:
        history = await content_approval_service.get_approval_history(db, record_id)
        
        return ApiResponse(
            success=True,
            data=history
        )

    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/pending", summary="获取待审批列表")
async def get_pending_approvals(
        content_type: Optional[str] = Query(None, description="内容类型过滤"),
        page: int = Query(1, ge=1, description="页码"),
        per_page: int = Query(20, ge=1, le=100, description="每页数量"),
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取当前用户的待审批列表
    
    Args:
        content_type: 内容类型过滤
        page: 页码
        per_page: 每页数量
        
    Returns:
        待审批列表和分页信息
    """
    try:
        result = await content_approval_service.get_pending_approvals(
            db=db,
            approver_id=current_user.id,
            content_type=content_type,
            page=page,
            per_page=per_page
        )

        return ApiResponse(
            success=True,
            data=result
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/status/{content_type}/{content_id}", summary="检查审批状态")
async def check_approval_status(
        content_type: str,
        content_id: int,
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    检查内容的审批状态
    
    Args:
        content_type: 内容类型
        content_id: 内容ID
        
    Returns:
        审批状态信息
    """
    try:
        status = await content_approval_service.check_approval_status(
            db=db,
            content_type=content_type,
            content_id=content_id
        )

        if not status:
            return ApiResponse(
                success=True,
                data=None,
                message="No approval record found"
            )

        return ApiResponse(
            success=True,
            data=status
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/my-requests", summary="获取我的审批请求")
async def get_my_requests(
        status: Optional[str] = Query(None, description="状态过滤 (pending/approved/rejected/cancelled)"),
        page: int = Query(1, ge=1, description="页码"),
        per_page: int = Query(20, ge=1, le=100, description="每页数量"),
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取我提交的审批请求列表
    
    Args:
        status: 状态过滤
        page: 页码
        per_page: 每页数量
        
    Returns:
        审批请求列表和分页信息
    """
    try:
        from sqlalchemy import select, func

        query = select(ApprovalRecord).where(
            ApprovalRecord.applicant_id == current_user.id
        )

        if status:
            if status not in ['pending', 'approved', 'rejected', 'cancelled']:
                return ApiResponse(success=False, error="Invalid status")
            query = query.where(ApprovalRecord.status == status)

        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # 分页
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page).order_by(ApprovalRecord.created_at.desc())

        result = await db.execute(query)
        records = result.scalars().all()

        records_list = []
        for record in records:
            records_list.append({
                'id': record.id,
                'content_type': record.content_type,
                'content_id': record.content_id,
                'current_level': record.current_level,
                'max_level': record.max_level,
                'status': record.status,
                'created_at': record.created_at.isoformat() if record.created_at else None,
                'completed_at': record.completed_at.isoformat() if record.completed_at else None,
            })

        return ApiResponse(
            success=True,
            data={
                'requests': records_list,
                'pagination': {
                    'current_page': page,
                    'per_page': per_page,
                    'total': total,
                    'total_pages': (total + per_page - 1) // per_page
                }
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/stats", summary="获取审批统计")
async def get_approval_stats(
        days: int = Query(30, ge=1, le=365, description="统计天数"),
        current_user=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取审批统计数据
    
    Args:
        days: 统计天数
        
    Returns:
        统计数据
    """
    try:
        from sqlalchemy import select, func
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days)

        # 总审批数
        total_query = select(func.count()).select_from(ApprovalRecord).where(
            ApprovalRecord.created_at >= cutoff_date
        )
        total_result = await db.execute(total_query)
        total_count = total_result.scalar()

        # 按状态统计
        status_query = select(
            ApprovalRecord.status,
            func.count().label('count')
        ).where(
            ApprovalRecord.created_at >= cutoff_date
        ).group_by(ApprovalRecord.status)

        status_result = await db.execute(status_query)
        status_stats = [
            {'status': row[0], 'count': row[1]}
            for row in status_result.all()
        ]

        # 按内容类型统计
        type_query = select(
            ApprovalRecord.content_type,
            func.count().label('count')
        ).where(
            ApprovalRecord.created_at >= cutoff_date
        ).group_by(ApprovalRecord.content_type)

        type_result = await db.execute(type_query)
        type_stats = [
            {'content_type': row[0], 'count': row[1]}
            for row in type_result.all()
        ]

        # 平均审批时间
        completed_query = select(ApprovalRecord).where(
            ApprovalRecord.created_at >= cutoff_date,
            ApprovalRecord.completed_at.isnot(None)
        )
        completed_result = await db.execute(completed_query)
        completed_records = completed_result.scalars().all()

        avg_time = 0
        if completed_records:
            total_seconds = sum(
                (r.completed_at - r.created_at).total_seconds()
                for r in completed_records
            )
            avg_time = total_seconds / len(completed_records)

        return ApiResponse(
            success=True,
            data={
                'period_days': days,
                'total_approvals': total_count,
                'by_status': status_stats,
                'by_content_type': type_stats,
                'average_approval_time_seconds': avg_time,
                'average_approval_time_hours': avg_time / 3600,
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# 导入datetime
from datetime import datetime
