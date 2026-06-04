'use client';


/* ─── Types ─────────────────────────────────────── */
export interface ChatGroup {
  id: number;
  name: string;
  description?: string;
  avatar_url?: string;
  owner_id: number;
  owner_name?: string;
  member_count: number;
  max_members?: number;
  is_active: boolean;
  is_public: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ChatGroupMember {
  id: number;
  user_id: number;
  username: string;
  avatar_url?: string;
  role: string;
  joined_at?: string;
  last_active_at?: string;
}

export interface ChatGroupInvite {
  id: number;
  group_id: number;
  invite_code: string;
  created_by: number;
  max_uses?: number;
  current_uses: number;
  expires_at?: string;
  is_active: boolean;
  created_at?: string;
}

export const Input: React.FC<{
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
  rows?: number;
}> = ({label, value, onChange, type, placeholder, rows}) => (
  <div className="mb-3">
    <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">{label}</label>
    {rows ? (
      <textarea rows={rows} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white placeholder-gray-400 resize-none"/>
    ) : (
      <input type={type || 'text'} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
             className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white placeholder-gray-400"/>
    )}
  </div>
);

export const StatusBadge: React.FC<{ active: boolean }> = ({active}) => (
  <span
    className={`px-2 py-0.5 text-[10px] rounded-full font-medium ${active ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' : 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'}`}>
    {active ? '活跃' : '已停用'}
  </span>
);
