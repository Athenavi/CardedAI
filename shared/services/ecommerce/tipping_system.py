"""
打赏系统服务
提供文章打赏、统计、排行榜等功能
"""


from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.unified_logger import default_logger as logger


class TippingSystem:
    """打赏系统"""

    def __init__(self):
        # 打赏记录 {tip_id: tip_info}
        self._tips = {}

        # 用户收到的打赏 {user_id: [tip_id, ...]}
        self._user_received_tips = defaultdict(list)

        # 文章收到的打赏 {article_id: [tip_id, ...]}
        self._article_tips = defaultdict(list)

        # 打赏ID计数器
        self._tip_counter = 0

        # 预设金额选项
        self._preset_amounts = [1, 2, 5, 10, 20, 50, 100, 200]

        # 最小/最大打赏金额
        self.min_amount = 1
        self.max_amount = 10000

        # 提现记录 {withdrawal_id: withdrawal_info}
        self._withdrawals = {}

        # 用户提现记录 {user_id: [withdrawal_id, ...]}
        self._user_withdrawals = defaultdict(list)

        # 提现ID计数器
        self._withdrawal_counter = 0

        # 最低提现金额
        self.min_withdrawal_amount = 50

        # 提现手续费比例 (0-1)
        self.withdrawal_fee_rate = 0.02  # 2%

    def create_tip(self, from_user_id: int, to_user_id: int,
                   article_id: int, amount: float,
                   message: str = '', payment_method: str = 'balance') -> Dict:
        """
        创建打赏记录
        
        Args:
            from_user_id: 打赏者ID
            to_user_id: 接收者ID
            article_id: 文章ID
            amount: 打赏金额
            message: 留言(可选)
            payment_method: 支付方式(balance/wechat/alipay)
            
        Returns:
            打赏记录
        """
        # 验证金额
        if amount < self.min_amount or amount > self.max_amount:
            raise ValueError(f"Amount must be between {self.min_amount} and {self.max_amount}")

        if from_user_id == to_user_id:
            raise ValueError("Cannot tip yourself")

        # 生成打赏ID
        self._tip_counter += 1
        tip_id = f"tip_{self._tip_counter}_{int(datetime.now().timestamp())}"

        # 创建打赏记录
        now = datetime.now()
        tip = {
            'tip_id': tip_id,
            'from_user_id': from_user_id,
            'to_user_id': to_user_id,
            'article_id': article_id,
            'amount': amount,
            'message': message,
            'payment_method': payment_method,
            'status': 'completed',  # completed/pending/refunded
            'created_at': now,
        }

        # 存储记录
        self._tips[tip_id] = tip
        self._user_received_tips[to_user_id].append(tip_id)
        self._article_tips[article_id].append(tip_id)

        logger.info(f"User {from_user_id} tipped {amount} to user {to_user_id} for article {article_id}")

        return tip

    def get_article_tips(self, article_id: int, limit: int = 50) -> List[Dict]:
        """
        获取文章的打赏记录
        
        Args:
            article_id: 文章ID
            limit: 返回数量
            
        Returns:
            打赏记录列表
        """
        tip_ids = self._article_tips.get(article_id, [])
        tips = []

        for tip_id in tip_ids[-limit:]:
            tip = self._tips.get(tip_id)
            if tip:
                tips.append({
                    'tip_id': tip['tip_id'],
                    'from_user_id': tip['from_user_id'],
                    'amount': tip['amount'],
                    'message': tip['message'],
                    'created_at': tip['created_at'].isoformat(),
                })

        # 按时间倒序
        tips.sort(key=lambda x: x['created_at'], reverse=True)

        return tips

    def get_user_received_tips(self, user_id: int,
                               limit: int = 100) -> List[Dict]:
        """
        获取用户收到的打赏
        
        Args:
            user_id: 用户ID
            limit: 返回数量
            
        Returns:
            打赏记录列表
        """
        tip_ids = self._user_received_tips.get(user_id, [])
        tips = []

        for tip_id in tip_ids[-limit:]:
            tip = self._tips.get(tip_id)
            if tip:
                tips.append({
                    'tip_id': tip['tip_id'],
                    'from_user_id': tip['from_user_id'],
                    'article_id': tip['article_id'],
                    'amount': tip['amount'],
                    'message': tip['message'],
                    'payment_method': tip['payment_method'],
                    'created_at': tip['created_at'].isoformat(),
                })

        # 按时间倒序
        tips.sort(key=lambda x: x['created_at'], reverse=True)

        return tips

    def get_user_tip_stats(self, user_id: int) -> Dict:
        """
        获取用户打赏统计
        
        Args:
            user_id: 用户ID
            
        Returns:
            统计数据
        """
        tip_ids = self._user_received_tips.get(user_id, [])

        total_amount = 0
        tip_count = 0
        unique_supporters = set()

        for tip_id in tip_ids:
            tip = self._tips.get(tip_id)
            if tip and tip['status'] == 'completed':
                total_amount += tip['amount']
                tip_count += 1
                unique_supporters.add(tip['from_user_id'])

        return {
            'total_amount': total_amount,
            'tip_count': tip_count,
            'unique_supporters': len(unique_supporters),
            'average_tip': total_amount / tip_count if tip_count > 0 else 0,
        }

    def get_article_tip_stats(self, article_id: int) -> Dict:
        """
        获取文章打赏统计
        
        Args:
            article_id: 文章ID
            
        Returns:
            统计数据
        """
        tip_ids = self._article_tips.get(article_id, [])

        total_amount = 0
        tip_count = 0

        for tip_id in tip_ids:
            tip = self._tips.get(tip_id)
            if tip and tip['status'] == 'completed':
                total_amount += tip['amount']
                tip_count += 1

        return {
            'total_amount': total_amount,
            'tip_count': tip_count,
        }

    def get_tipping_leaderboard(self, period: str = 'all',
                                limit: int = 100) -> List[Dict]:
        """
        获取打赏排行榜(按收到打赏金额排序)
        
        Args:
            period: 时间周期(all/month/week)
            limit: 返回数量
            
        Returns:
            排行榜列表
        """
        # 计算每个用户的总打赏金额
        user_totals = defaultdict(float)

        cutoff = None
        now = datetime.now()

        if period == 'week':
            cutoff = now - timedelta(days=7)
        elif period == 'month':
            cutoff = now - timedelta(days=30)

        for tip in self._tips.values():
            if tip['status'] != 'completed':
                continue

            if cutoff and tip['created_at'] < cutoff:
                continue

            user_totals[tip['to_user_id']] += tip['amount']

        # 排序
        leaderboard = [
            {
                'user_id': user_id,
                'total_amount': total,
                'rank': 0,
            }
            for user_id, total in user_totals.items()
        ]

        leaderboard.sort(key=lambda x: x['total_amount'], reverse=True)

        # 添加排名
        for i, entry in enumerate(leaderboard[:limit]):
            entry['rank'] = i + 1

        return leaderboard[:limit]

    def get_preset_amounts(self) -> List[float]:
        """
        获取预设打赏金额
        
        Returns:
            金额列表
        """
        return self._preset_amounts.copy()

    def refund_tip(self, tip_id: str, reason: str = '') -> bool:
        """
        退款打赏
        
        Args:
            tip_id: 打赏ID
            reason: 退款原因
            
        Returns:
            是否成功
        """
        tip = self._tips.get(tip_id)

        if not tip:
            return False

        if tip['status'] != 'completed':
            return False

        # 更新状态
        tip['status'] = 'refunded'
        tip['refunded_at'] = datetime.now()
        tip['refund_reason'] = reason

        logger.info(f"Refunded tip {tip_id}: {reason}")
        return True

    def get_recent_tips(self, limit: int = 20) -> List[Dict]:
        """
        获取最近的打赏记录(全站)
        
        Args:
            limit: 返回数量
            
        Returns:
            打赏记录列表
        """
        all_tips = list(self._tips.values())

        # 按时间排序
        all_tips.sort(key=lambda x: x['created_at'], reverse=True)

        recent_tips = []
        for tip in all_tips[:limit]:
            if tip['status'] == 'completed':
                recent_tips.append({
                    'tip_id': tip['tip_id'],
                    'from_user_id': tip['from_user_id'],
                    'to_user_id': tip['to_user_id'],
                    'article_id': tip['article_id'],
                    'amount': tip['amount'],
                    'message': tip['message'],
                    'created_at': tip['created_at'].isoformat(),
                })

        return recent_tips

    def create_withdrawal(self, user_id: int, amount: float,
                          payment_method: str = 'bank_transfer',
                          account_info: Optional[Dict] = None) -> Dict:
        """
        创建提现申请
        
        Args:
            user_id: 用户ID
            amount: 提现金额
            payment_method: 支付方式(bank_transfer/wechat/alipay)
            account_info: 账户信息
            
        Returns:
            提现记录
        """
        # 验证最低提现金额
        if amount < self.min_withdrawal_amount:
            raise ValueError(f"Minimum withdrawal amount is {self.min_withdrawal_amount}")

        # 获取用户可提现余额
        stats = self.get_user_tip_stats(user_id)
        available_balance = stats['total_amount']

        # 检查是否有足够的余额
        if amount > available_balance:
            raise ValueError(f"Insufficient balance. Available: {available_balance}, Requested: {amount}")

        # 计算手续费
        fee = amount * self.withdrawal_fee_rate
        actual_amount = amount - fee

        # 生成提现ID
        self._withdrawal_counter += 1
        withdrawal_id = f"wd_{self._withdrawal_counter}_{int(datetime.now().timestamp())}"

        # 创建提现记录
        now = datetime.now()
        withdrawal = {
            'withdrawal_id': withdrawal_id,
            'user_id': user_id,
            'amount': amount,
            'fee': fee,
            'actual_amount': actual_amount,
            'payment_method': payment_method,
            'account_info': account_info or {},
            'status': 'pending',  # pending/processing/completed/rejected
            'created_at': now,
            'processed_at': None,
            'admin_note': '',
        }

        # 存储记录
        self._withdrawals[withdrawal_id] = withdrawal
        self._user_withdrawals[user_id].append(withdrawal_id)

        logger.info(f"User {user_id} requested withdrawal of {amount} (fee: {fee})")

        return withdrawal

    def get_user_withdrawals(self, user_id: int, limit: int = 50) -> List[Dict]:
        """
        获取用户的提现记录
        
        Args:
            user_id: 用户ID
            limit: 返回数量
            
        Returns:
            提现记录列表
        """
        withdrawal_ids = self._user_withdrawals.get(user_id, [])
        withdrawals = []

        for wd_id in withdrawal_ids[-limit:]:
            wd = self._withdrawals.get(wd_id)
            if wd:
                withdrawals.append({
                    'withdrawal_id': wd['withdrawal_id'],
                    'amount': wd['amount'],
                    'fee': wd['fee'],
                    'actual_amount': wd['actual_amount'],
                    'payment_method': wd['payment_method'],
                    'status': wd['status'],
                    'created_at': wd['created_at'].isoformat(),
                    'processed_at': wd['processed_at'].isoformat() if wd['processed_at'] else None,
                    'admin_note': wd['admin_note'],
                })

        # 按时间倒序
        withdrawals.sort(key=lambda x: x['created_at'], reverse=True)

        return withdrawals

    def get_user_available_balance(self, user_id: int) -> Dict:
        """
        获取用户可提现余额
        
        Args:
            user_id: 用户ID
            
        Returns:
            余额信息
        """
        stats = self.get_user_tip_stats(user_id)
        total_earned = stats['total_amount']

        # 计算已提现金额
        withdrawal_ids = self._user_withdrawals.get(user_id, [])
        total_withdrawn = 0
        pending_withdrawal = 0

        for wd_id in withdrawal_ids:
            wd = self._withdrawals.get(wd_id)
            if wd:
                if wd['status'] in ['completed', 'processing']:
                    total_withdrawn += wd['amount']
                elif wd['status'] == 'pending':
                    pending_withdrawal += wd['amount']

        available_balance = total_earned - total_withdrawn - pending_withdrawal

        return {
            'total_earned': total_earned,
            'total_withdrawn': total_withdrawn,
            'pending_withdrawal': pending_withdrawal,
            'available_balance': max(0, available_balance),
            'min_withdrawal_amount': self.min_withdrawal_amount,
            'withdrawal_fee_rate': self.withdrawal_fee_rate,
        }

    def process_withdrawal(self, withdrawal_id: str, status: str = 'completed',
                           admin_note: str = '') -> bool:
        """
        处理提现申请（管理员操作）
        
        Args:
            withdrawal_id: 提现ID
            status: 新状态(completed/rejected)
            admin_note: 管理员备注
            
        Returns:
            是否成功
        """
        withdrawal = self._withdrawals.get(withdrawal_id)

        if not withdrawal:
            return False

        if withdrawal['status'] != 'pending':
            return False

        # 更新状态
        withdrawal['status'] = status
        withdrawal['processed_at'] = datetime.now()
        withdrawal['admin_note'] = admin_note

        logger.info(f"Withdrawal {withdrawal_id} {status} by admin: {admin_note}")
        return True

    def cancel_withdrawal(self, withdrawal_id: str, user_id: int) -> bool:
        """
        取消提现申请（用户操作，仅限pending状态）
        
        Args:
            withdrawal_id: 提现ID
            user_id: 用户ID
            
        Returns:
            是否成功
        """
        withdrawal = self._withdrawals.get(withdrawal_id)

        if not withdrawal:
            return False

        if withdrawal['user_id'] != user_id:
            return False

        if withdrawal['status'] != 'pending':
            return False

        # 更新状态
        withdrawal['status'] = 'cancelled'
        withdrawal['processed_at'] = datetime.now()

        logger.info(f"User {user_id} cancelled withdrawal {withdrawal_id}")
        return True


# 全局实例
tipping_system = TippingSystem()
