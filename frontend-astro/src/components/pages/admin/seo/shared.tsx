'use client';


/* ─── Types ─────────────────────────────────────── */
export interface ArticleSEO {
  id: number;
  article_id: number;
  title: string;
  meta_title?: string;
  meta_description?: string;
  focus_keyword?: string;
  canonical_url?: string;
  og_title?: string;
  og_description?: string;
  og_image?: string;
  robots_directive?: string;
  schema_type?: string;
  seo_score?: number;
  created_at?: string;
  updated_at?: string;
}

export interface ShareStat {
  id: number;
  article_id: number;
  article_title?: string;
  platform: string;
  share_count: number;
  click_count: number;
  last_shared_at?: string;
  created_at?: string;
}

export interface SearchHistory {
  id: number;
  query: string;
  user_id?: number;
  results_count: number;
  ip_address?: string;
  created_at?: string;
}

export interface SEODashboard {
  total_articles_with_seo: number;
  avg_seo_score: number;
  top_keywords: { keyword: string; count: number }[];
  traffic_sources: { source: string; visits: number }[];
  recent_issues: { type: string; message: string; article_id?: number }[];
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

export const ScoreBadge: React.FC<{ score?: number }> = ({score}) => {
  if (score === undefined || score === null) return <span className="text-xs text-gray-400">未评分</span>;
  const color = score >= 80 ? 'text-green-600 bg-green-50 dark:bg-green-900/20' :
    score >= 60 ? 'text-yellow-600 bg-yellow-50 dark:bg-yellow-900/20' :
      'text-red-600 bg-red-50 dark:bg-red-900/20';
  return <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${color}`}>{score}分</span>;
};
