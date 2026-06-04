"""
内容审批服务
提供多级审批、审批意见、审批历史和自动流转功能
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.functions import func

from shared.models.approval_record import ApprovalRecord
from shared.models.approval_step import ApprovalStep

from src.unified_logger import default_logger as logger


class ApprovalStatus(Enum):
    """审批状态"""
    PENDING = "pending"  # 待审批
    APPROVED = "approved"  # 已通过
    REJECTED = "rejected"  # 已拒绝
    CANCELLED = "cancelled"  # 已取消


class ContentApprovalService:
    """
    内容审批服务
    
    功能:
    1. 多级审批流程
    2. 审批意见记录
    3. 审批历史追踪
    4. 自动流转
    5. 审批通知
    """

    def __init__(self):
        pass

    async def create_approval_request(self, db, content_type: str, content_id: int,
                                      applicant_id: int, max_level: int = 1,
                                      approvers: List[int] = None) -> ApprovalRecord:
        """
        创建审批请求
        
        Args:
            db: 数据库会话
            content_type: 内容类型 (article/comment)
            content_id: 内容ID
            applicant_id: 申请人ID
            max_level: 最大审批级别
            approvers: 各级审批人ID列表
            
        Returns:
            创建的审批记录
        """
        from sqlalchemy import select

        # 检查是否已有待审批的记录
        stmt = select(ApprovalRecord).where(
            ApprovalRecord.content_type == content_type,
            ApprovalRecord.content_id == content_id,
            ApprovalRecord.status == ApprovalStatus.PENDING.value
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise ValueError("Content already has a pending approval request")

        # 创建审批记录
        record = ApprovalRecord(
            content_type=content_type,
            content_id=content_id,
            applicant_id=applicant_id,
            current_level=1,
            max_level=max_level,
            status=ApprovalStatus.PENDING.value
        )

        db.add(record)
        await db.flush()

        # 创建审批步骤
        if approvers:
            for i, approver_id in enumerate(approvers[:max_level], 1):
                step = ApprovalStep(
                    record_id=record.id,
                    level=i,
                    approver_id=approver_id
                )
                db.add(step)

        await db.commit()
        await db.refresh(record)

        logger.info(f"Approval request created: {content_type}#{content_id} by user {applicant_id}")
        return record

    async def approve_step(self, db, record_id: int, approver_id: int,
                           comment: str = None) -> ApprovalRecord:
        """
        审批通过
        
        Args:
            db: 数据库会话
            record_id: 审批记录ID
            approver_id: 审批人ID
            comment: 审批意见
            
        Returns:
            更新后的审批记录
        """
        from sqlalchemy import select

        stmt = select(ApprovalRecord).where(ApprovalRecord.id == record_id)
        result = await db.execute(stmt)
        record = result.scalar_one_or_none()

        if not record:
            raise ValueError("Approval record not found")

        if record.status != ApprovalStatus.PENDING.value:
            raise ValueError(f"Approval is {record.status}, cannot approve")

        # 查找当前级别的审批步骤
        stmt = select(ApprovalStep).where(
            ApprovalStep.record_id == record_id,
            ApprovalStep.level == record.current_level,
            ApprovalStep.approver_id == approver_id
        )
        result = await db.execute(stmt)
        step = result.scalar_one_or_none()

        if not step:
            raise ValueError("You are not the approver for this level")

        if step.action:
            raise ValueError("This step has already been reviewed")

        # 更新审批步骤
        step.action = 'approved'
        step.comment = comment
        step.reviewed_at = datetime.now()

        # 检查是否是最后一级
        if record.current_level >= record.max_level:
            # 所有级别都已通过
            record.status = ApprovalStatus.APPROVED.value
            record.completed_at = datetime.now()
        else:
            # 流转到下一级
            record.current_level += 1

        await db.commit()
        await db.refresh(record)

        logger.info(
            f"Approval step approved: record {record_id} level {record.current_level - 1} by user {approver_id}")
        return record

    async def reject_step(self, db, record_id: int, approver_id: int,
                          comment: str = None) -> ApprovalRecord:
        """
        审批拒绝
        
        Args:
            db: 数据库会话
            record_id: 审批记录ID
            approver_id: 审批人ID
            comment: 拒绝意见
            
        Returns:
            更新后的审批记录
        """
        from sqlalchemy import select

        stmt = select(ApprovalRecord).where(ApprovalRecord.id == record_id)
        result = await db.execute(stmt)
        record = result.scalar_one_or_none()

        if not record:
            raise ValueError("Approval record not found")

        if record.status != ApprovalStatus.PENDING.value:
            raise ValueError(f"Approval is {record.status}, cannot reject")

        # 查找当前级别的审批步骤
        stmt = select(ApprovalStep).where(
            ApprovalStep.record_id == record_id,
            ApprovalStep.level == record.current_level,
            ApprovalStep.approver_id == approver_id
        )
        result = await db.execute(stmt)
        step = result.scalar_one_or_none()

        if not step:
            raise ValueError("You are not the approver for this level")

        if step.action:
            raise ValueError("This step has already been reviewed")

        # 更新审批步骤
        step.action = 'rejected'
        step.comment = comment
        step.reviewed_at = datetime.now()

        # 拒绝后直接结束审批
        record.status = ApprovalStatus.REJECTED.value
        record.completed_at = datetime.now()

        await db.commit()
        await db.refresh(record)

        logger.info(f"Approval step rejected: record {record_id} level {record.current_level} by user {approver_id}")
        return record

    async def cancel_approval(self, db, record_id: int, user_id: int) -> ApprovalRecord:
        """
        取消审批（仅申请人或管理员）
        
        Args:
            db: 数据库会话
            record_id: 审批记录ID
            user_id: 用户ID
            
        Returns:
            更新后的审批记录
        """
        from sqlalchemy import select

        stmt = select(ApprovalRecord).where(ApprovalRecord.id == record_id)
        result = await db.execute(stmt)
        record = result.scalar_one_or_none()

        if not record:
            raise ValueError("Approval record not found")

        if record.status != ApprovalStatus.PENDING.value:
            raise ValueError(f"Approval is {record.status}, cannot cancel")

        # 只有申请人可以取消
        if record.applicant_id != user_id:
            raise ValueError("Only the applicant can cancel the approval")

        record.status = ApprovalStatus.CANCELLED.value
        record.completed_at = datetime.now()

        await db.commit()
        await db.refresh(record)

        logger.info(f"Approval cancelled: record {record_id} by user {user_id}")
        return record

    async def get_approval_history(self, db, record_id: int) -> Dict[str, Any]:
        """
        获取审批历史
        
        Args:
            db: 数据库会话
            record_id: 审批记录ID
            
        Returns:
            审批历史
        """
        from sqlalchemy import select
        from shared.models.user import User

        # 获取审批记录
        stmt = select(ApprovalRecord).where(ApprovalRecord.id == record_id)
        result = await db.execute(stmt)
        record = result.scalar_one_or_none()

        if not record:
            raise ValueError("Approval record not found")

        # 获取审批步骤
        stmt = (
            select(ApprovalStep, User)
            .join(User, ApprovalStep.approver_id == User.id, isouter=True)
            .where(ApprovalStep.record_id == record_id)
            .order_by(ApprovalStep.level)
        )
        result = await db.execute(stmt)
        steps = result.all()

        steps_list = []
        for step, user in steps:
            steps_list.append({
                'id': step.id,
                'level': step.level,
                'approver_id': step.approver_id,
                'approver_name': user.username if user else None,
                'action': step.action,
                'comment': step.comment,
                'reviewed_at': step.reviewed_at.isoformat() if step.reviewed_at else None,
                'created_at': step.created_at.isoformat() if step.created_at else None,
            })

        return {
            'record': {
                'id': record.id,
                'content_type': record.content_type,
                'content_id': record.content_id,
                'applicant_id': record.applicant_id,
                'current_level': record.current_level,
                'max_level': record.max_level,
                'status': record.status,
                'created_at': record.created_at.isoformat() if record.created_at else None,
                'completed_at': record.completed_at.isoformat() if record.completed_at else None,
            },
            'steps': steps_list
        }

    async def get_pending_approvals(self, db, approver_id: int,
                                    content_type: str = None,
                                    page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        获取待审批列表
        
        Args:
            db: 数据库会话
            approver_id: 审批人ID
            content_type: 内容类型过滤
            page: 页码
            per_page: 每页数量
            
        Returns:
            待审批列表和分页信息
        """
        from sqlalchemy import select, func

        # 查找当前用户需要审批的记录
        query = (
            select(ApprovalRecord)
            .join(ApprovalStep, ApprovalRecord.id == ApprovalStep.record_id)
            .where(
                ApprovalRecord.status == ApprovalStatus.PENDING.value,
                ApprovalStep.level == ApprovalRecord.current_level,
                ApprovalStep.approver_id == approver_id
            )
        )

        if content_type:
            query = query.where(ApprovalRecord.content_type == content_type)

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
                'applicant_id': record.applicant_id,
                'current_level': record.current_level,
                'max_level': record.max_level,
                'status': record.status,
                'created_at': record.created_at.isoformat() if record.created_at else None,
            })

        return {
            'approvals': records_list,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }
        }

    async def check_approval_status(self, db, content_type: str, content_id: int) -> Optional[Dict[str, Any]]:
        """
        检查内容的审批状态
        
        Args:
            db: 数据库会话
            content_type: 内容类型
            content_id: 内容ID
            
        Returns:
            审批状态信息
        """
        from sqlalchemy import select

        stmt = select(ApprovalRecord).where(
            ApprovalRecord.content_type == content_type,
            ApprovalRecord.content_id == content_id
        ).order_by(ApprovalRecord.created_at.desc())

        result = await db.execute(stmt)
        record = result.scalar_one_or_none()

        if not record:
            return None

        return {
            'id': record.id,
            'status': record.status,
            'current_level': record.current_level,
            'max_level': record.max_level,
            'created_at': record.created_at.isoformat() if record.created_at else None,
            'completed_at': record.completed_at.isoformat() if record.completed_at else None,
        }


# 全局实例
content_approval_service = ContentApprovalService()
