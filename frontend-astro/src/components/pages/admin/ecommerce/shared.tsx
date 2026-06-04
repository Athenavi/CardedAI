'use client';

import React from 'react';

/* ─── Types ─────────────────────────────────────── */
export interface Product {
  id: number;
  name: string;
  slug: string;
  description?: string;
  price: number;
  compare_price?: number;
  sku?: string;
  stock_quantity: number;
  is_active: boolean;
  is_digital: boolean;
  category?: string;
  image_url?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Order {
  id: number;
  order_number: string;
  user_id: number;
  username?: string;
  total_amount: number;
  currency: string;
  status: string;
  payment_status: string;
  payment_method?: string;
  shipping_address?: string;
  tracking_number?: string;
  items_count?: number;
  created_at?: string;
  updated_at?: string;
}

export interface OrderItem {
  id: number;
  order_id: number;
  product_id: number;
  product_name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

/* ─── Helper Components ────────────────────────── */
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

export const Select: React.FC<{
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}> = ({label, value, onChange, options}) => (
  <div className="mb-3">
    <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">{label}</label>
    <select value={value} onChange={e => onChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white">
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  </div>
);

export const MoneyDisplay: React.FC<{ amount: number; currency?: string }> = ({amount, currency = 'CNY'}) => (
  <span className="font-medium text-gray-900 dark:text-gray-100">
    {currency === 'CNY' ? '¥' : currency + ' '}{amount.toFixed(2)}
  </span>
);
