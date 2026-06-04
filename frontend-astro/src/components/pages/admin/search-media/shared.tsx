'use client';


/* ─── Types ─────────────────────────────────────── */
export interface SearchIndex {
  id: number;
  article_id: number;
  indexed: boolean;
  last_indexed_at?: string;
  index_hash?: string;
  created_at?: string;
  updated_at?: string;
}

export interface MediaOptimization {
  id: number;
  media_id: number;
  webp_url?: string;
  sizes_json?: string;
  cdn_url?: string;
  optimization_status: string;
  created_at?: string;
  updated_at?: string;
}

export interface Pagination {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}
