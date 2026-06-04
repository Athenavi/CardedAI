'use client';


/* ─── Types ─────────────────────────────────────── */
export interface RevenueRecord {
  id: number;
  user_id: number;
  username?: string;
  revenue_type: string;
  amount: number;
  platform_fee: number;
  user_earnings: number;
  description?: string;
  status: string;
  created_at?: string;
}

export interface RevenueSharingConfig {
  id: number;
  revenue_type: string;
  platform_percentage: number;
  user_percentage: number;
  min_payout_amount: number;
  payout_cycle: string;
  is_active: boolean;
  description?: string;
}

export interface PayoutRequest {
  id: number;
  user_id: number;
  username?: string;
  amount: number;
  payment_method: string;
  payment_account: string;
  status: string;
  admin_notes?: string;
  processed_at?: string;
  created_at?: string;
}

export interface UserRevenueStats {
  user_id: number;
  username?: string;
  total_earnings: number;
  total_payouts: number;
  pending_balance: number;
  available_balance: number;
  last_payout_at?: string;
}

export const MoneyDisplay: React.FC<{ amount: number; className?: string }> = ({amount, className = ''}) => (
  <span className={`font-medium ${className}`}>¥{amount.toFixed(2)}</span>
);

export const StatusBadge: React.FC<{ status: string }> = ({status}) => {
  const colors: Record<string, string> = {
    pending: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400',
    confirmed: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
    approved: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
    completed: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
    rejected: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400',
    cancelled: 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400',
  };
  const labels: Record<string, string> = {
    pending: '待处理', confirmed: '已确认', approved: '已批准',
    completed: '已完成', rejected: '已拒绝', cancelled: '已取消',
  };
  return (
    <span
      className={`px-2 py-0.5 text-[10px] rounded-full font-medium ${colors[status] || 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'}`}>
      {labels[status] || status}
    </span>
  );
};

export const StatCard: React.FC<{ icon: React.ElementType; label: string; value: string; color: string }> = ({
                                                                                                        icon: Icon,
                                                                                                        label,
                                                                                                        value,
                                                                                                        color
                                                                                                      }) => (
  <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4">
    <div className="flex items-center gap-3">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${color}`}>
        <Icon className="w-5 h-5 text-white"/>
      </div>
      <div>
        <div className="text-xs text-gray-500 dark:text-gray-400">{label}</div>
        <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">{value}</div>
      </div>
    </div>
  </div>
);
