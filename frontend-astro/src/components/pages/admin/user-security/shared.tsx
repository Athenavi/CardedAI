'use client';


/* ─── Types ─────────────────────────────────────── */
export interface FieldPermission {
  id: number;
  role_id: number;
  model_name: string;
  field_name: string;
  can_read: boolean;
  can_write: boolean;
  created_at?: string;
}

export interface UserSession {
  id: number;
  user_id: number;
  access_token?: string;
  refresh_token?: string;
  device_info?: string;
  ip_address?: string;
  location?: string;
  is_active: boolean;
  last_activity?: string;
  expires_at?: string;
  created_at?: string;
}

export interface EmailSubscription {
  id: number;
  user_id: number;
  subscribed: boolean;
  created_at?: string;
}

export interface Pagination {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

export const Input: React.FC<{
  label: string; value: string; onChange: (v: string) => void; type?: string; placeholder?: string; rows?: number;
}> = ({label, value, onChange, type, placeholder, rows}) => (
  <div className="mb-3">
    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{label}</label>
    {rows ? (
      <textarea value={value} onChange={e => onChange(e.target.value)} rows={rows} placeholder={placeholder}
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm dark:text-white"/>
    ) : (
      <input type={type || 'text'} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
             className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm dark:text-white"/>
    )}
  </div>
);
