'use client';

import {X} from 'lucide-react';

// ─── Types ────────────────────────────────────────────
export interface VIPPlan {
  id: number;
  name: string;
  description?: string;
  price: number;
  original_price?: number;
  duration_days: number;
  level: number;
  features?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface VIPFeature {
  id: number;
  code: string;
  name: string;
  description?: string;
  required_level: number;
  is_active: boolean;
  created_at?: string;
}

export interface Member {
  id: number;
  user_id: number;
  username: string;
  plan_name: string;
  level: number;
  starts_at?: string;
  expires_at?: string;
  is_active: boolean;
  amount: number;
  transaction_id?: string;
  status: string;
}

export interface VipMgmtData {
  stats: Record<string, any>;
  members: Member[];
  plans: VIPPlan[];
  features: VIPFeature[];
}

export interface PlanForm {
  name: string;
  description: string;
  price: string;
  original_price: string;
  duration_days: string;
  level: string;
  features: string;
}

export interface FeatureForm {
  code: string;
  name: string;
  description: string;
  required_level: string;
}

export const Modal: React.FC<{ open: boolean; title: string; onClose: () => void; children: React.ReactNode }> = ({
                                                                                                             open,
                                                                                                             title,
                                                                                                             onClose,
                                                                                                             children
                                                                                                           }) => {
  if (!open) return null;
  return <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
    <div
      className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto"
      onClick={e => e.stopPropagation()}>
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-800">
        <h3 className="font-bold text-gray-900 dark:text-white">{title}</h3>
        <button onClick={onClose} className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"><X
          className="w-4 h-4 text-gray-500 dark:text-gray-400"/></button>
      </div>
      <div className="px-6 py-4">{children}</div>
    </div>
  </div>;
};

export const Inp: React.FC<{
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
  className?: string;
  rows?: number
}> = ({label, value, onChange, type, placeholder, className, rows}) => (
  <div className={`mb-3 ${className || ''}`}>
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
