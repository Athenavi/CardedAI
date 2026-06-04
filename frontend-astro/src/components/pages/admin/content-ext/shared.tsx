'use client';


/* ─── Types ─────────────────────────────────────── */
export interface RevisionNote {
  id: number;
  revision_id: number;
  user_id: number;
  note_content: string;
  created_at?: string;
}

export interface MenuLocation {
  id: number;
  name: string;
  slug: string;
  description?: string;
  theme_supports?: string;
  created_at?: string;
  updated_at?: string;
}

export interface LocationAssignment {
  id: number;
  menu_id: number;
  location_id: number;
  menu_name?: string;
  location_name?: string;
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
