'use client';

import React from 'react';
import {
  AlertCircle,
  BarChart3,
  CheckCircle,
  Database,
  Globe,
  Loader,
  Shield,
  Upload,
  X,
  XCircle
} from 'lucide-react';

/* ═══════════════════════════════════════════
   Types
   ═══════════════════════════════════════════ */
export interface OAuthProvider {
  name: string;
  display_name?: string;
  configured?: boolean;
  icon?: string;
  client_id?: string;
  redirect_uri?: string;
}

export interface LinkedAccount {
  provider: string;
  provider_name?: string;
  provider_user_id?: string;
  email?: string;
  username?: string;
  bound_at?: string;
}

export interface GAConfig {
  id?: number;
  tracking_id?: string;
  measurement_id?: string;
  api_secret?: string;
  enable_page_view_tracking?: boolean;
  enable_event_tracking?: boolean;
  enable_user_behavior_analysis?: boolean;
  anonymize_ip?: boolean;
  sample_rate?: number;
  is_active?: boolean;
}

export interface BaiduConfig {
  id?: number;
  site_token?: string;
  api_key?: string;
  site_id?: number;
  site_name?: string;
  tracking_id?: string;
  enable_tracking?: boolean;
  enable_data_sync?: boolean;
  is_active?: boolean;
}

export interface IPFSFile {
  cid: string;
  name?: string;
  filename?: string;
  size?: number;
  content_type?: string;
  gateway_url?: string;
  pinned?: boolean;
  created_at?: string;
}

/* ═══════════════════════════════════════════
   Constants
   ═══════════════════════════════════════════ */
export const TABS = [
  {key: 'oauth', label: 'OAuth 登录', icon: Globe, color: 'from-blue-500 to-indigo-500'},
  {key: 'sso', label: 'SSO 企业认证', icon: Shield, color: 'from-emerald-500 to-teal-500'},
  {key: 'analytics', label: '统计分析', icon: BarChart3, color: 'from-orange-500 to-amber-500'},
  {key: 'ipfs', label: 'IPFS 存储', icon: Database, color: 'from-purple-500 to-violet-500'},
  {key: 'import', label: '数据导入', icon: Upload, color: 'from-pink-500 to-rose-500'},
];

export const PROVIDER_COLORS: Record<string, { bg: string; text: string }> = {
  github: {bg: 'bg-gray-900', text: 'text-white'},
  google: {bg: 'bg-blue-500', text: 'text-white'},
  wechat: {bg: 'bg-green-500', text: 'text-white'},
  qq: {bg: 'bg-blue-400', text: 'text-white'},
  microsoft: {bg: 'bg-blue-700', text: 'text-white'},
  weibo: {bg: 'bg-red-500', text: 'text-white'},
};

/* ═══════════════════════════════════════════
   Helper Components
   ═══════════════════════════════════════════ */
export const ProviderAvatar: React.FC<{ name: string; icon?: string; size?: 'sm' | 'md' | 'lg' }> = ({
                                                                                                       name,
                                                                                                       icon,
                                                                                                       size = 'md'
                                                                                                     }) => {
  const sz = size === 'sm' ? 'w-7 h-7 text-[10px]' : size === 'lg' ? 'w-11 h-11 text-sm' : 'w-9 h-9 text-xs';
  const colors = PROVIDER_COLORS[(icon || name || '').toLowerCase()];
  const bg = colors?.bg || 'bg-gradient-to-br from-blue-100 to-indigo-100 dark:from-blue-900/30 dark:to-indigo-900/30';
  const fg = colors?.text || 'text-blue-600 dark:text-blue-400';
  const label = (icon || name || '?').charAt(0).toUpperCase();
  return <div
    className={`${sz} rounded-xl ${bg} ${fg} flex items-center justify-center font-bold shrink-0`}>{label}</div>;
};

export const Toggle: React.FC<{ checked: boolean; onChange: (v: boolean) => void; disabled?: boolean }> = ({
                                                                                                             checked,
                                                                                                             onChange,
                                                                                                             disabled
                                                                                                           }) => (
  <button type="button" disabled={disabled} onClick={() => onChange(!checked)}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${checked ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'} ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}>
    <span
      className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${checked ? 'translate-x-6' : 'translate-x-1'}`}/>
  </button>
);

export const InputField: React.FC<{
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
  hint?: string;
  disabled?: boolean
}> =
  ({label, value, onChange, type = 'text', placeholder, hint, disabled}) => (
    <div>
      <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5">{label}</label>
      <input type={type} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
             disabled={disabled}
             className="w-full px-3 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder:text-gray-400 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all disabled:opacity-50"/>
      {hint && <p className="text-[11px] text-gray-400 mt-1">{hint}</p>}
    </div>
  );

export const ActionButton: React.FC<{
  onClick: () => void;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  variant?: 'primary' | 'danger' | 'ghost';
  loading?: boolean;
  disabled?: boolean;
  size?: 'sm' | 'md'
}> =
  ({onClick, icon: Icon, label, variant = 'primary', loading, disabled, size = 'md'}) => {
    const base = size === 'sm' ? 'px-2.5 py-1.5 text-xs gap-1' : 'px-4 py-2 text-sm gap-1.5';
    const colors = variant === 'primary' ? 'bg-blue-600 hover:bg-blue-700 text-white' :
      variant === 'danger' ? 'bg-red-600 hover:bg-red-700 text-white' :
        'bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300';
    return (
      <button onClick={onClick} disabled={disabled || loading}
              className={`${base} inline-flex items-center font-medium rounded-xl transition-colors ${colors} disabled:opacity-50`}>
        {loading ? <Loader className="w-3.5 h-3.5 animate-spin"/> : <Icon className="w-3.5 h-3.5"/>}
        {label}
      </button>
    );
  };

export const Toast: React.FC<{ message: string; type: 'success' | 'error' | 'info'; onClose: () => void }> = ({
                                                                                                                message,
                                                                                                                type,
                                                                                                                onClose
                                                                                                              }) => {
  const colorMap = {
    success: 'bg-green-50 border-green-200 text-green-800',
    error: 'bg-red-50 border-red-200 text-red-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800'
  };
  const iconMap = {success: CheckCircle, error: XCircle, info: AlertCircle};
  const Icon = iconMap[type];
  return (
    <div
      className={`fixed top-4 right-4 z-[100] flex items-center gap-2 px-4 py-3 rounded-xl border shadow-lg animate-in slide-in-from-right ${colorMap[type]}`}>
      <Icon className="w-4 h-4 shrink-0"/>
      <span className="text-sm font-medium">{message}</span>
      <button onClick={onClose} className="ml-2 p-0.5 hover:opacity-70"><X className="w-3.5 h-3.5"/></button>
    </div>
  );
};

// Placeholder for Ghost icon (not in lucide)
export function Ghost(props: any) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor"
         strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M9 10h.01"/>
      <path d="M15 10h.01"/>
      <path d="M12 2a8 8 0 0 0-8 8v12l3-3 2.5 2.5L12 19l2.5 2.5L17 19l3 3V10a8 8 0 0 0-8-8z"/>
    </svg>
  );
}
