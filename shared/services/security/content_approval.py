"""
内容审批工作流服务

实现草稿→审核→发布的完整工作流
支持多级审批和审批评论
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ApprovalStatus(Enum):
    """审批状态"""
    DRAFT = 'draft'  # 草稿
    PENDING_REVIEW = 'pending_review'  # 待审核
    UNDER_REVIEW = 'under_review'  # 审核中
    APPROVED = 'approved'  # 已批准
    REJECTED = 'rejected'  # 已拒绝
    PUBLISHED = 'published'  # 已发布


class ContentApprovalWorkflow:
    """
    内容审批工作流服务
    
    管理内容的审批流程
    """

    def __init__(self):
        """初始化工作流服务"""
        # 存储审批记录 {content_id: approval_data}
        self.approvals: Dict[int, Dict[str, Any]] = {}

        # 审批历史 {content_id: [approval_history]}
        self.approval_history: Dict[int, List[Dict[str, Any]]] = {}

    def submit_for_approval(
            self,
            content_id: int,
            content_type: str,
            author_id: int,
            author_name: str,
            title: str,
            reviewers: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        提交内容审批
        
        Args:
            content_id: 内容ID
            content_type: 内容类型 (article, page, etc.)
            author_id: 作者ID
            author_name: 作者名称
            title: 标题
            reviewers: 审核人ID列表
        
        Returns:
            审批记录
        """
        approval_data = {
            'content_id': content_id,
            'content_type': content_type,
            'author_id': author_id,
            'author_name': author_name,
            'title': title,
            'status': ApprovalStatus.PENDING_REVIEW.value,
            'submitted_at': datetime.now().isoformat(),
            'reviewers': reviewers or [],
            'current_reviewer_index': 0,
            'comments': [],
            'final_decision': None,
            'completed_at': None,
        }

        self.approvals[content_id] = approval_data
        self.approval_history[content_id] = [{
            'action': 'submitted',
            'user_id': author_id,
            'user_name': author_name,
            'timestamp': datetime.now().isoformat(),
            'comment': '提交审批',
        }]

        return approval_data

    def start_review(
            self,
            content_id: int,
            reviewer_id: int,
            reviewer_name: str
    ) -> Dict[str, Any]:
        """
        开始审核
        
        Args:
            content_id: 内容ID
            reviewer_id: 审核人ID
            reviewer_name: 审核人名称
        
        Returns:
            更新后的审批记录
        """
        if content_id not in self.approvals:
            raise ValueError(f"Approval record not found for content {content_id}")

        approval = self.approvals[content_id]

        if approval['status'] != ApprovalStatus.PENDING_REVIEW.value:
            raise ValueError(f"Content is not pending review (current status: {approval['status']})")

        approval['status'] = ApprovalStatus.UNDER_REVIEW.value

        self._add_history(content_id, 'started_review', reviewer_id, reviewer_name, '开始审核')

        return approval

    def approve_content(
            self,
            content_id: int,
            reviewer_id: int,
            reviewer_name: str,
            comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        批准内容
        
        Args:
            content_id: 内容ID
            reviewer_id: 审核人ID
            reviewer_name: 审核人名称
            comment: 审批意见
        
        Returns:
            更新后的审批记录
        """
        if content_id not in self.approvals:
            raise ValueError(f"Approval record not found for content {content_id}")

        approval = self.approvals[content_id]

        if approval['status'] != ApprovalStatus.UNDER_REVIEW.value:
            raise ValueError(f"Content is not under review (current status: {approval['status']})")

        # 添加审批意见
        if comment:
            approval['comments'].append({
                'reviewer_id': reviewer_id,
                'reviewer_name': reviewer_name,
                'action': 'approve',
                'comment': comment,
                'timestamp': datetime.now().isoformat(),
            })

        # 检查是否还有更多审核人
        if approval['reviewers'] and approval['current_reviewer_index'] < len(approval['reviewers']) - 1:
            # 还有更多审核人
            approval['current_reviewer_index'] += 1
            next_reviewer = approval['reviewers'][approval['current_reviewer_index']]

            self._add_history(
                content_id,
                'approved_by_reviewer',
                reviewer_id,
                reviewer_name,
                f'审核人 {reviewer_name} 批准，等待下一位审核人'
            )
        else:
            # 所有审核人都已批准
            approval['status'] = ApprovalStatus.APPROVED.value
            approval['final_decision'] = 'approved'
            approval['completed_at'] = datetime.now().isoformat()

            self._add_history(
                content_id,
                'approved',
                reviewer_id,
                reviewer_name,
                comment or '批准发布'
            )

        return approval

    def reject_content(
            self,
            content_id: int,
            reviewer_id: int,
            reviewer_name: str,
            reason: str
    ) -> Dict[str, Any]:
        """
        拒绝内容
        
        Args:
            content_id: 内容ID
            reviewer_id: 审核人ID
            reviewer_name: 审核人名称
            reason: 拒绝原因
        
        Returns:
            更新后的审批记录
        """
        if content_id not in self.approvals:
            raise ValueError(f"Approval record not found for content {content_id}")

        approval = self.approvals[content_id]

        if approval['status'] != ApprovalStatus.UNDER_REVIEW.value:
            raise ValueError(f"Content is not under review (current status: {approval['status']})")

        # 添加拒绝意见
        approval['comments'].append({
            'reviewer_id': reviewer_id,
            'reviewer_name': reviewer_name,
            'action': 'reject',
            'comment': reason,
            'timestamp': datetime.now().isoformat(),
        })

        approval['status'] = ApprovalStatus.REJECTED.value
        approval['final_decision'] = 'rejected'
        approval['completed_at'] = datetime.now().isoformat()

        self._add_history(
            content_id,
            'rejected',
            reviewer_id,
            reviewer_name,
            reason
        )

        return approval

    def publish_content(
            self,
            content_id: int,
            publisher_id: int,
            publisher_name: str
    ) -> Dict[str, Any]:
        """
        发布内容
        
        Args:
            content_id: 内容ID
            publisher_id: 发布者ID
            publisher_name: 发布者名称
        
        Returns:
            更新后的审批记录
        """
        if content_id not in self.approvals:
            raise ValueError(f"Approval record not found for content {content_id}")

        approval = self.approvals[content_id]

        if approval['status'] != ApprovalStatus.APPROVED.value:
            raise ValueError(f"Content is not approved (current status: {approval['status']})")

        approval['status'] = ApprovalStatus.PUBLISHED.value

        self._add_history(
            content_id,
            'published',
            publisher_id,
            publisher_name,
            '内容已发布'
        )

        return approval

    def resubmit_content(
            self,
            content_id: int,
            author_id: int,
            author_name: str
    ) -> Dict[str, Any]:
        """
        重新提交被拒绝的内容
        
        Args:
            content_id: 内容ID
            author_id: 作者ID
            author_name: 作者名称
        
        Returns:
            更新后的审批记录
        """
        if content_id not in self.approvals:
            raise ValueError(f"Approval record not found for content {content_id}")

        approval = self.approvals[content_id]

        if approval['status'] != ApprovalStatus.REJECTED.value:
            raise ValueError(f"Content is not rejected (current status: {approval['status']})")

        # 重置审批状态
        approval['status'] = ApprovalStatus.PENDING_REVIEW.value
        approval['current_reviewer_index'] = 0
        approval['final_decision'] = None
        approval['completed_at'] = None

        self._add_history(
            content_id,
            'resubmitted',
            author_id,
            author_name,
            '重新提交审批'
        )

        return approval

    def get_approval_status(self, content_id: int) -> Optional[Dict[str, Any]]:
        """
        获取审批状态
        
        Args:
            content_id: 内容ID
        
        Returns:
            审批记录
        """
        return self.approvals.get(content_id)

    def get_pending_approvals(
            self,
            reviewer_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取待审批列表
        
        Args:
            reviewer_id: 审核人ID过滤
        
        Returns:
            待审批列表
        """
        pending = []

        for approval in self.approvals.values():
            if approval['status'] in [
                ApprovalStatus.PENDING_REVIEW.value,
                ApprovalStatus.UNDER_REVIEW.value
            ]:
                # 如果指定了审核人，只返回该审核人的待审内容
                if reviewer_id:
                    if reviewer_id in approval['reviewers']:
                        pending.append(approval)
                else:
                    pending.append(approval)

        return pending

    def get_approval_history(self, content_id: int) -> List[Dict[str, Any]]:
        """
        获取审批历史
        
        Args:
            content_id: 内容ID
        
        Returns:
            审批历史列表
        """
        return self.approval_history.get(content_id, [])

    def get_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取审批统计
        
        Args:
            hours: 统计最近多少小时
        
        Returns:
            统计信息
        """
        cutoff = datetime.now().timestamp() - (hours * 3600)

        stats = {
            'total_submissions': 0,
            'pending': 0,
            'under_review': 0,
            'approved': 0,
            'rejected': 0,
            'published': 0,
            'avg_review_time_hours': 0,
        }

        review_times = []

        for approval in self.approvals.values():
            submitted_at = datetime.fromisoformat(approval['submitted_at']).timestamp()

            if submitted_at < cutoff:
                continue

            stats['total_submissions'] += 1
            stats[approval['status'].replace('-', '_')] = stats.get(approval['status'].replace('-', '_'), 0) + 1

            # 计算审核时间
            if approval.get('completed_at'):
                completed_at = datetime.fromisoformat(approval['completed_at']).timestamp()
                review_time = (completed_at - submitted_at) / 3600
                review_times.append(review_time)

        if review_times:
            stats['avg_review_time_hours'] = sum(review_times) / len(review_times)

        return stats

    def _add_history(
            self,
            content_id: int,
            action: str,
            user_id: int,
            user_name: str,
            comment: str
    ):
        """
        添加历史记录
        
        Args:
            content_id: 内容ID
            action: 操作类型
            user_id: 用户ID
            user_name: 用户名称
            comment: 注释
        """
        if content_id not in self.approval_history:
            self.approval_history[content_id] = []

        self.approval_history[content_id].append({
            'action': action,
            'user_id': user_id,
            'user_name': user_name,
            'timestamp': datetime.now().isoformat(),
            'comment': comment,
        })


# 全局实例
approval_workflow = ContentApprovalWorkflow()

# 导出
__all__ = ['ContentApprovalWorkflow', 'approval_workflow', 'ApprovalStatus']
