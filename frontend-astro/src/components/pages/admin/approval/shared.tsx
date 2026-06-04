'use client';


/* ─── Types ─────────────────────────────────────── */
export interface ApprovalRecord {
  id: number;
  content_type: string;
  content_id: number;
  content_title?: string;
  requester_id: number;
  requester_name?: string;
  current_step: number;
  total_steps: number;
  status: string;
  priority?: string;
  reason?: string;
  admin_notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ApprovalStep {
  id: number;
  record_id: number;
  step_number: number;
  approver_id: number;
  approver_name?: string;
  status: string;
  notes?: string;
  action_at?: string;
}

export interface ApprovalStats {
  total_requests: number;
  pending_count: number;
  approved_count: number;
  rejected_count: number;
  cancelled_count: number;
  avg_approval_time_hours?: number;
  by_content_type: { type: string; count: number }[];
}

export const StatusBadge: React.FC<{ status: string }> = ({status}) => {
  const colors: Record<string, string> = {
    pending: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400',
    approved: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
    rejected: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400',
    cancelled: 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400',
  };
  const labels: Record<string, string> = {
    pending: '待审批', approved: '已通过', rejected: '已拒绝', cancelled: '已取消',
  };
  return (
    <span
      className={`px-2 py-0.5 text-[10px] rounded-full font-medium ${colors[status] || 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'}`}>
      {labels[status] || status}
    </span>
  );
};

export const PriorityBadge: React.FC<{ priority?: string }> = ({priority}) => {
  if (!priority) return null;
  const colors: Record<string, string> = {
    high: 'bg-red-100 dark:bg-red-900/30 text-red-600',
    medium: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600',
    low: 'bg-green-100 dark:bg-green-900/30 text-green-600',
  };
  const labels: Record<string, string> = {high: '高', medium: '中', low: '低'};
  return (
    <span
      className={`px-1.5 py-0.5 text-[10px] rounded-full font-medium ${colors[priority] || 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'}`}>
      {labels[priority] || priority}
    </span>
  );
};

export const StatCard: React.FC<{
  icon: React.ElementType;
  label: string;
  value: string | number;
  color: string
}> = ({icon: Icon, label, value, color}) => (
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
