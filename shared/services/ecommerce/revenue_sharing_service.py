"""
收益分成服务
提供收益计算、分成、提现等功能
"""
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from shared.models import RevenueSharingConfig, UserRevenueStats, PayoutRequest, RevenueRecord


class RevenueSharingService:
    """收益分成服务类"""

    def __init__(self, db_session: Session):
        self.db = db_session

    # ==================== 分成配置管理 ====================

    def create_sharing_config(self, revenue_type: str,
                              platform_percentage: float = 30.0,
                              creator_percentage: float = 70.0,
                              min_payout_amount: float = 100.0,
                              description: str = None) -> RevenueSharingConfig:
        """创建分成配置"""
        config = RevenueSharingConfig(
            revenue_type=revenue_type,
            platform_percentage=platform_percentage,
            creator_percentage=creator_percentage,
            min_payout_amount=min_payout_amount,
            description=description,
            is_active=True
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def get_sharing_config(self, revenue_type: str) -> Optional[RevenueSharingConfig]:
        """获取分成配置"""
        return self.db.query(RevenueSharingConfig).filter(
            RevenueSharingConfig.revenue_type == revenue_type
        ).first()

    def update_sharing_config(self, revenue_type: str, **kwargs) -> Optional[RevenueSharingConfig]:
        """更新分成配置"""
        config = self.get_sharing_config(revenue_type)
        if not config:
            return None

        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

        config.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(config)
        return config

    # ==================== 收益记录管理 ====================

    def record_revenue(self, user_id: int, revenue_type: str,
                       amount: float, description: str = None,
                       reference_id: int = None, reference_type: str = None) -> RevenueRecord:
        """记录收益"""
        # 获取分成配置
        config = self.get_sharing_config(revenue_type)
        if not config:
            # 使用默认配置
            platform_fee = amount * 0.3
            creator_earnings = amount * 0.7
        else:
            platform_fee = amount * (config.platform_percentage / 100)
            creator_earnings = amount * (config.creator_percentage / 100)

        # 创建收益记录
        record = RevenueRecord(
            user_id=user_id,
            revenue_type=revenue_type,
            amount=amount,
            platform_fee=platform_fee,
            creator_earnings=creator_earnings,
            description=description,
            reference_id=reference_id,
            reference_type=reference_type,
            status='pending'
        )
        self.db.add(record)

        # 更新用户收益统计
        self._update_user_stats(user_id, creator_earnings)

        self.db.commit()
        self.db.refresh(record)
        return record

    def confirm_revenue(self, record_id: int) -> Optional[RevenueRecord]:
        """确认收益"""
        record = self.db.query(RevenueRecord).filter(RevenueRecord.id == record_id).first()
        if not record:
            return None

        record.status = 'confirmed'
        record.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(record)
        return record

    def list_user_revenues(self, user_id: int,
                           revenue_type: str = None,
                           status: str = None,
                           skip: int = 0, limit: int = 100) -> List[RevenueRecord]:
        """获取用户收益列表"""
        query = self.db.query(RevenueRecord).filter(RevenueRecord.user_id == user_id)

        if revenue_type:
            query = query.filter(RevenueRecord.revenue_type == revenue_type)

        if status:
            query = query.filter(RevenueRecord.status == status)

        return query.order_by(RevenueRecord.created_at.desc()).offset(skip).limit(limit).all()

    # ==================== 用户收益统计 ====================

    def _update_user_stats(self, user_id: int, earnings: float):
        """更新用户收益统计"""
        stats = self.db.query(UserRevenueStats).filter(
            UserRevenueStats.user_id == user_id
        ).first()

        if not stats:
            stats = UserRevenueStats(
                user_id=user_id,
                total_earnings=earnings,
                pending_earnings=earnings,
                available_balance=earnings
            )
            self.db.add(stats)
        else:
            stats.total_earnings += earnings
            stats.pending_earnings += earnings
            stats.available_balance += earnings
            stats.updated_at = datetime.now()

    def get_user_stats(self, user_id: int) -> Optional[UserRevenueStats]:
        """获取用户收益统计"""
        stats = self.db.query(UserRevenueStats).filter(
            UserRevenueStats.user_id == user_id
        ).first()

        if not stats:
            # 如果不存在，创建一个
            stats = UserRevenueStats(user_id=user_id)
            self.db.add(stats)
            self.db.commit()
            self.db.refresh(stats)

        return stats

    def get_user_revenue_summary(self, user_id: int,
                                 start_date: datetime = None,
                                 end_date: datetime = None) -> Dict[str, Any]:
        """获取用户收益汇总"""
        query = self.db.query(RevenueRecord).filter(RevenueRecord.user_id == user_id)

        if start_date:
            query = query.filter(RevenueRecord.created_at >= start_date)
        if end_date:
            query = query.filter(RevenueRecord.created_at <= end_date)

        records = query.all()

        total_amount = sum(r.amount for r in records)
        total_platform_fee = sum(r.platform_fee for r in records)
        total_creator_earnings = sum(r.creator_earnings for r in records)

        # 按类型统计
        type_stats = {}
        for record in records:
            type_name = record.revenue_type.value
            if type_name not in type_stats:
                type_stats[type_name] = {
                    'count': 0,
                    'amount': 0,
                    'earnings': 0
                }
            type_stats[type_name]['count'] += 1
            type_stats[type_name]['amount'] += record.amount
            type_stats[type_name]['earnings'] += record.creator_earnings

        return {
            'total_records': len(records),
            'total_amount': round(total_amount, 2),
            'total_platform_fee': round(total_platform_fee, 2),
            'total_creator_earnings': round(total_creator_earnings, 2),
            'by_type': type_stats
        }

    # ==================== 提现管理 ====================

    def create_payout_request(self, user_id: int, amount: float,
                              payment_method: str, payment_account: str,
                              account_name: str = None) -> PayoutRequest:
        """创建提现申请"""
        # 检查用户余额
        stats = self.get_user_stats(user_id)
        if stats.available_balance < amount:
            raise ValueError("可用余额不足")

        # 检查最低提现金额
        config = self.get_sharing_config('advertisement')
        min_amount = config.min_payout_amount if config else 100.0
        if amount < min_amount:
            raise ValueError(f"提现金额不能低于 {min_amount}")

        # 创建提现申请
        payout = PayoutRequest(
            user_id=user_id,
            amount=amount,
            payment_method=payment_method,
            payment_account=payment_account,
            account_name=account_name,
            status='pending'
        )
        self.db.add(payout)

        # 冻结相应余额
        stats.available_balance -= amount
        stats.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(payout)
        return payout

    def approve_payout(self, payout_id: int, admin_id: int,
                       notes: str = None) -> Optional[PayoutRequest]:
        """批准提现"""
        payout = self.db.query(PayoutRequest).filter(PayoutRequest.id == payout_id).first()
        if not payout:
            return None

        payout.status = 'approved'
        payout.processed_by = admin_id
        payout.processed_at = datetime.now()
        payout.admin_notes = notes
        payout.updated_at = datetime.now()

        # 更新用户统计
        stats = self.get_user_stats(payout.user_id)
        stats.total_paid += payout.amount
        stats.pending_earnings -= payout.amount
        stats.last_payout_at = datetime.now()
        stats.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(payout)
        return payout

    def complete_payout(self, payout_id: int, admin_id: int,
                        notes: str = None) -> Optional[PayoutRequest]:
        """完成提现"""
        payout = self.db.query(PayoutRequest).filter(PayoutRequest.id == payout_id).first()
        if not payout:
            return None

        if payout.status != 'approved':
            raise ValueError("只能完成已批准的提现")

        payout.status = 'completed'
        payout.processed_by = admin_id
        payout.processed_at = datetime.now()
        payout.admin_notes = notes
        payout.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(payout)
        return payout

    def reject_payout(self, payout_id: int, admin_id: int,
                      notes: str = None) -> Optional[PayoutRequest]:
        """拒绝提现"""
        payout = self.db.query(PayoutRequest).filter(PayoutRequest.id == payout_id).first()
        if not payout:
            return None

        payout.status = 'rejected'
        payout.processed_by = admin_id
        payout.processed_at = datetime.now()
        payout.admin_notes = notes
        payout.updated_at = datetime.now()

        # 退还余额
        stats = self.get_user_stats(payout.user_id)
        stats.available_balance += payout.amount
        stats.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(payout)
        return payout

    def list_payout_requests(self, user_id: int = None,
                             status: str = None,
                             skip: int = 0, limit: int = 100) -> List[PayoutRequest]:
        """获取提现申请列表"""
        query = self.db.query(PayoutRequest)

        if user_id:
            query = query.filter(PayoutRequest.user_id == user_id)

        if status:
            query = query.filter(PayoutRequest.status == status)

        return query.order_by(PayoutRequest.created_at.desc()).offset(skip).limit(limit).all()

    # ==================== 平台统计 ====================

    def get_platform_stats(self, start_date: datetime = None,
                           end_date: datetime = None) -> Dict[str, Any]:
        """获取平台统计"""
        query = self.db.query(RevenueRecord)

        if start_date:
            query = query.filter(RevenueRecord.created_at >= start_date)
        if end_date:
            query = query.filter(RevenueRecord.created_at <= end_date)

        records = query.all()

        total_revenue = sum(r.amount for r in records)
        total_platform_fee = sum(r.platform_fee for r in records)
        total_creator_earnings = sum(r.creator_earnings for r in records)

        # 按类型统计
        type_stats = {}
        for record in records:
            type_name = record.revenue_type.value
            if type_name not in type_stats:
                type_stats[type_name] = {
                    'count': 0,
                    'revenue': 0,
                    'platform_fee': 0,
                    'creator_earnings': 0
                }
            type_stats[type_name]['count'] += 1
            type_stats[type_name]['revenue'] += record.amount
            type_stats[type_name]['platform_fee'] += record.platform_fee
            type_stats[type_name]['creator_earnings'] += record.creator_earnings

        # 提现统计
        payouts = self.db.query(PayoutRequest).all()
        total_payouts = sum(p.amount for p in payouts if p.status == 'completed')
        pending_payouts = sum(p.amount for p in payouts if p.status == 'pending')

        return {
            'total_revenue': round(total_revenue, 2),
            'total_platform_fee': round(total_platform_fee, 2),
            'total_creator_earnings': round(total_creator_earnings, 2),
            'total_payouts': round(total_payouts, 2),
            'pending_payouts': round(pending_payouts, 2),
            'by_type': type_stats
        }
