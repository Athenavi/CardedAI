'use client';


/* ─── Types ─────────────────────────────────────── */
export interface Site {
  id: number;
  name: string;
  domain: string;
  description?: string;
  is_active: boolean;
  theme?: string;
  logo_url?: string;
  additional_domains?: string[];
  user_count?: number;
  content_count?: number;
  created_at?: string;
  updated_at?: string;
}

export interface SiteUser {
  id: number;
  user_id: number;
  username: string;
  email?: string;
  role: string;
  joined_at?: string;
}

export interface ContentMapping {
  id: number;
  source_site_id: number;
  target_site_id: number;
  source_site_name?: string;
  target_site_name?: string;
  content_type: string;
  content_id: number;
  mapped_content_id?: number;
  sync_status: string;
  last_synced_at?: string;
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
    {active ? '活跃' : '停用'}
  </span>
);
