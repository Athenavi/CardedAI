'use client';

import React from 'react';

/* ─── Types ─────────────────────────────────────── */
export interface PaymentGateway {
  id: number;
  name: string;
  provider: string;
  config_data?: string;
  is_active: boolean;
  supported_currencies?: string;
  created_at?: string;
  updated_at?: string;
}

export interface PaymentTransaction {
  id: number;
  user_id: number;
  order_id: string;
  gateway_id?: number;
  amount: number;
  currency: string;
  status: string;
  transaction_id?: string;
  payment_method?: string;
  extra_metadata?: string;
  created_at?: string;
  updated_at?: string;
}

export interface TaxConfig {
  id: number;
  country: string;
  region?: string;
  tax_type: string;
  rate: number;
  description?: string;
  is_active: boolean;
  effective_from?: string;
  effective_to?: string;
  created_at?: string;
}

export interface Pagination {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

/* ─── Helper Components ────────────────────────── */
export const Input: React.FC<{
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
  rows?: number
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

export const Badge: React.FC<{ active: boolean; activeText?: string; inactiveText?: string }> = ({
                                                                                                   active,
                                                                                                   activeText = '启用',
                                                                                                   inactiveText = '禁用'
                                                                                                 }) => (
  <span
    className={`px-2 py-0.5 text-[10px] rounded-full font-medium ${active ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' : 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'}`}>
    {active ? activeText : inactiveText}
  </span>
);

export const StatusBadge: React.FC<{ status: string }> = ({status}) => {
  const colors: Record<string, string> = {
    completed: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
    pending: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400',
    failed: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400',
    refunded: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
    cancelled: 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400',
  };
  return <span
    className={`px-2 py-0.5 text-[10px] rounded-full font-medium ${colors[status] || 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'}`}>{status}</span>;
};
