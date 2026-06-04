/**
 * FastBlog 管理后台共享 UI 组件库
 * 统一设计语言，消除跨页面重复代码
 */

import React, {useEffect, useState} from 'react';
import {Loader, AlertTriangle, RefreshCw} from 'lucide-react';

/* ═══════════════════════════════════════════
   StatCard - 渐变统计卡片
   ═══════════════════════════════════════════ */
export const StatCard: React.FC<{
  icon: React.ComponentType<{ className?: string }>;
    label: string;
    value: string | number;
    gradient?: string;        /* gradient类 (e.g. "from-blue-500 to-blue-600") */
    color?: string;           /* solid bg类 (e.g. "bg-blue-500") 或 gradient类 */
    subtitle?: string;
    sub?: string;             /* subtitle 的别名 */
    change?: string | number;
    changeType?: 'up' | 'down' | 'neutral';
    trend?: number;           /* 数值型 change，自动判断 up/down */
    suffix?: string;
}> = ({icon: Icon, label, value, gradient, color, subtitle, sub, change, changeType, trend, suffix = ''}) => {
    const desc = subtitle || sub;
    const iconBg = gradient ? `bg-gradient-to-br ${gradient}` : (color || 'bg-gray-500');
    const overlayBg = gradient ? `bg-gradient-to-br ${gradient}` : '';
    /* 优先使用 change/changeType；否则由 trend 推导 */
    const displayChange = change !== undefined ? change : (trend !== undefined ? `${Math.abs(trend)}%` : undefined);
    const displayType = changeType ?? (trend !== undefined ? (trend >= 0 ? 'up' : 'down') : undefined);

    return (
        <div
            className="group relative bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/80 dark:border-gray-700/80 p-5 overflow-hidden hover:shadow-lg hover:-translate-y-0.5 transition-all duration-300">
            {overlayBg && <div
                className={`absolute top-0 right-0 w-24 h-24 ${overlayBg} opacity-[0.07] rounded-bl-[60px] group-hover:opacity-[0.12] transition-opacity`}/>}
            <div className="flex items-start justify-between relative">
                <div className="min-w-0 flex-1">
                    <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{label}</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1.5 tabular-nums">{value ?? '—'}{suffix}</p>
                    <div className="flex items-center gap-2 mt-1">
                        {desc && <p className="text-xs text-gray-400 dark:text-gray-500">{desc}</p>}
                        {displayChange !== undefined && displayChange !== null && (
                            <span className={`text-xs font-medium ${
                                displayType === 'up' ? 'text-emerald-600 dark:text-emerald-400' :
                                    displayType === 'down' ? 'text-red-600 dark:text-red-400' :
                                        'text-gray-500 dark:text-gray-400'
                            }`}>{displayType === 'up' ? '↑' : displayType === 'down' ? '↓' : ''}{displayChange}</span>
                        )}
                    </div>
                </div>
                <div
                    className={`w-10 h-10 rounded-xl ${iconBg} flex items-center justify-center shadow-lg shadow-gray-200/50 dark:shadow-gray-900/50 flex-shrink-0`}>
                    <Icon className="w-5 h-5 text-white"/>
                </div>
            </div>
        </div>
    );
};

/* ═══════════════════════════════════════════
   SectionTitle - 区域标题
   ═══════════════════════════════════════════ */
export const SectionTitle: React.FC<{
  icon: React.ComponentType<{ className?: string }>;
    title: string;
    subtitle?: string;
    action?: React.ReactNode;
}> = ({icon: Icon, title, subtitle, action}) => (
    <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
            <div
                className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
                <Icon className="w-4 h-4 text-white"/>
            </div>
            <div>
                <h3 className="font-semibold text-gray-900 dark:text-white">{title}</h3>
                {subtitle && <p className="text-xs text-gray-500 dark:text-gray-400">{subtitle}</p>}
            </div>
        </div>
        {action}
    </div>
);

/* ═══════════════════════════════════════════
   Modal - 带动画的模态框
   ═══════════════════════════════════════════ */
export const Modal: React.FC<{
    open: boolean;
    onClose: () => void;
    title: string;
    subtitle?: string;
    children: React.ReactNode;
    maxWidth?: string;
}> = ({open, onClose, title, subtitle, children, maxWidth = 'max-w-lg'}) => {
    const [isVisible, setIsVisible] = useState(false);
    const [isAnimating, setIsAnimating] = useState(false);

    useEffect(() => {
        if (open) {
            setIsVisible(true);
            requestAnimationFrame(() => setIsAnimating(true));
        } else {
            setIsAnimating(false);
            const timer = setTimeout(() => setIsVisible(false), 200);
            return () => clearTimeout(timer);
        }
    }, [open]);

    useEffect(() => {
        if (!open) return;
        const handler = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose();
        };
        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
    }, [open, onClose]);

    if (!isVisible) return null;
    return (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center sm:p-4" onClick={onClose}>
            <div
                className={`absolute inset-0 bg-black/50 backdrop-blur-sm transition-opacity duration-200 ${isAnimating ? 'opacity-100' : 'opacity-0'}`}/>
            <div
                className={`relative ${maxWidth} w-full bg-white dark:bg-gray-900 sm:rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 max-h-[90vh] sm:max-h-[85vh] flex flex-col transition-all duration-200 ${isAnimating ? 'scale-100 opacity-100 translate-y-0' : 'scale-95 opacity-0 translate-y-4'}`}
                onClick={e => e.stopPropagation()} style={{paddingBottom: 'env(safe-area-inset-bottom, 0px)'}}>
                <div className="px-4 sm:px-6 py-4 sm:py-5 border-b border-gray-100 dark:border-gray-800 flex-shrink-0">
                    <h2 className="text-base sm:text-lg font-bold text-gray-900 dark:text-white">{title}</h2>
                    {subtitle && <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{subtitle}</p>}
                </div>
                <div className="px-4 sm:px-6 py-3 sm:py-4 overflow-y-auto flex-1">{children}</div>
            </div>
        </div>
    );
};

/* ═══════════════════════════════════════════
   EmptyState - 空状态
   ═══════════════════════════════════════════ */
export const EmptyState: React.FC<{
  icon: React.ComponentType<{ className?: string }>;
    title: string;
    desc: string;
    action?: React.ReactNode;
}> = ({icon: Icon, title, desc, action}) => (
    <div className="flex flex-col items-center justify-center py-16 px-4">
        <div className="w-16 h-16 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-4">
            <Icon className="w-8 h-8 text-gray-300 dark:text-gray-600"/>
        </div>
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-1">{title}</h3>
        <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">{desc}</p>
        {action}
    </div>
);

/* ═══════════════════════════════════════════
   DeleteConfirm - 删除确认
   ═══════════════════════════════════════════ */
export const DeleteConfirm: React.FC<{
    title?: string;
    desc?: string;
    itemName?: string;
    onConfirm: () => void;
    onCancel: () => void;
    isPending?: boolean;
}> = ({title = '确认删除', desc, itemName, onConfirm, onCancel, isPending}) => (
    <div className="space-y-4">
        <div
            className="flex items-start gap-3 p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-800/30">
            <svg className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24"
                 stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"/>
            </svg>
            <div>
                <p className="text-sm font-medium text-red-800 dark:text-red-300">{title}</p>
                <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                    {desc || (itemName ? <>项目 <span
                        className="font-mono font-medium">{itemName}</span> 将被永久删除，此操作无法撤销。</> : '此操作无法撤销。')}
                </p>
            </div>
        </div>
        <div className="flex justify-end gap-2">
            <button onClick={onCancel}
                    className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 rounded-xl hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">取消
            </button>
            <button onClick={onConfirm} disabled={isPending}
                    className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-xl hover:bg-red-700 transition-colors disabled:opacity-50 flex items-center gap-2">
                {isPending && <Loader className="w-3.5 h-3.5 animate-spin"/>}
                {isPending ? '删除中…' : '确认删除'}
            </button>
        </div>
    </div>
);

/* ═══════════════════════════════════════════
   StatusBadge - 状态徽章
   ═══════════════════════════════════════════ */
export const StatusBadge: React.FC<{
    active: boolean;
    label?: string;
  activeText?: string;
  inactiveText?: string;
}> = ({active, label, activeText, inactiveText}) => (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 text-xs font-medium rounded-full ${
        active
            ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400'
            : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
    }`}>
    <span className={`w-1.5 h-1.5 rounded-full ${active ? 'bg-emerald-500 animate-pulse' : 'bg-gray-400'}`}/>
      {label || (active ? (activeText || '启用') : (inactiveText || '禁用'))}
  </span>
);

/* ═══════════════════════════════════════════
   Pagination - 分页组件
   ═══════════════════════════════════════════ */
export const Pagination: React.FC<{
    page: number;
    totalPages: number;
    onPageChange: (page: number) => void;
}> = ({page, totalPages, onPageChange}) => {
    if (totalPages <= 1) return null;
    const pages: (number | string)[] = [];
    const delta = 2;
    const left = Math.max(2, page - delta);
    const right = Math.min(totalPages - 1, page + delta);
    pages.push(1);
    if (left > 2) pages.push('...');
    for (let i = left; i <= right; i++) pages.push(i);
    if (right < totalPages - 1) pages.push('...');
    if (totalPages > 1) pages.push(totalPages);

    return (
        <div className="flex items-center justify-center gap-1.5">
            <button disabled={page <= 1} onClick={() => onPageChange(page - 1)}
                    className="p-2 rounded-lg border border-gray-200 dark:border-gray-700 disabled:opacity-30 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7"/>
                </svg>
            </button>
            {pages.map((p, i) =>
                p === '...' ? <span key={`e-${i}`} className="px-2 text-gray-400">…</span> :
                    <button key={p} onClick={() => onPageChange(p as number)}
                            className={`min-w-[36px] h-9 rounded-lg text-sm font-medium transition-colors ${
                                p === page ? 'bg-blue-600 text-white' : 'border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                            }`}>{p}</button>
            )}
            <button disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}
                    className="p-2 rounded-lg border border-gray-200 dark:border-gray-700 disabled:opacity-30 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7"/>
                </svg>
            </button>
        </div>
    );
};

/* ═══════════════════════════════════════════
   Skeleton - 骨架屏加载
   ═══════════════════════════════════════════ */
export const Skeleton: React.FC<{
    lines?: number;
    className?: string;
}> = ({lines = 5, className = ''}) => (
    <div className={`animate-pulse space-y-3 ${className}`}>
        {Array.from({length: lines}).map((_, i) => (
            <div key={i} className="flex items-center gap-4 px-5 py-4">
                <div className="w-16 h-5 bg-gray-200 dark:bg-gray-700 rounded-full"/>
                <div className="flex-1 h-4 bg-gray-200 dark:bg-gray-700 rounded max-w-[200px]"/>
                <div className="w-28 h-4 bg-gray-200 dark:bg-gray-700 rounded hidden md:block"/>
                <div className="w-16 h-4 bg-gray-200 dark:bg-gray-700 rounded"/>
                <div className="w-20 h-4 bg-gray-200 dark:bg-gray-700 rounded"/>
            </div>
        ))}
    </div>
);

export const StatSkeleton: React.FC<{ count?: number }> = ({count = 4}) => (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {Array.from({length: count}).map((_, i) => (
            <div key={i}
                 className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/80 dark:border-gray-700/80 p-5 animate-pulse">
                <div className="h-3 w-16 bg-gray-200 dark:bg-gray-700 rounded mb-3"/>
                <div className="h-7 w-12 bg-gray-200 dark:bg-gray-700 rounded mb-2"/>
                <div className="h-3 w-20 bg-gray-200 dark:bg-gray-700 rounded"/>
            </div>
        ))}
    </div>
);

/* ═══════════════════════════════════════════
   GradientBadge - 渐变徽章
   ═══════════════════════════════════════════ */
export const GradientBadge: React.FC<{
    gradient: string;
    children: React.ReactNode;
    className?: string;
}> = ({gradient, children, className = ''}) => (
    <span
        className={`inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-full bg-gradient-to-r ${gradient} text-white shadow-sm ${className}`}>
    {children}
  </span>
);

/* ═══════════════════════════════════════════
   TypeBadge - 类型徽章（带颜色配置）
   ═══════════════════════════════════════════ */
export const TypeBadge: React.FC<{
    type: string;
  config: Record<string, {
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    color: string;
    bg: string
  }>;
}> = ({type, config}) => {
    const c = config[type] || config.default || {label: type, icon: null, color: 'text-gray-600', bg: 'bg-gray-50'};
    const Icon = c.icon;
    return (
        <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full ${c.bg} ${c.color}`}>
      {Icon && <Icon className="w-3 h-3"/>}
            {c.label}
    </span>
    );
};

/* ═══════════════════════════════════════════
   QueryErrorFallback - React Query 错误展示
   ═══════════════════════════════════════════ */
export const QueryErrorFallback: React.FC<{
  error: Error | null;
  onRetry?: () => void;
  title?: string;
  desc?: string;
}> = ({error, onRetry, title = '数据加载失败', desc}) => (
  <div className="flex flex-col items-center justify-center py-12 px-4">
    <div
      className="w-14 h-14 rounded-2xl bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-800/30 flex items-center justify-center mb-4">
      <AlertTriangle className="w-7 h-7 text-red-500"/>
    </div>
    <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-1">{title}</h3>
    <p className="text-xs text-gray-500 dark:text-gray-400 mb-4 text-center max-w-sm">
      {desc || error?.message || '请求出错，请稍后重试'}
    </p>
    {onRetry && (
      <button onClick={onRetry}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-xl hover:bg-blue-700 transition-colors flex items-center gap-2">
        <RefreshCw className="w-3.5 h-3.5"/>
        重新加载
      </button>
    )}
  </div>
);

/* ═══════════════════════════════════════════
   QueryLoadingSkeleton - 通用查询加载骨架屏
   ═══════════════════════════════════════════ */
export const QueryLoadingSkeleton: React.FC<{
  rows?: number;
  variant?: 'table' | 'card';
}> = ({rows = 5, variant = 'table'}) => {
  if (variant === 'card') {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({length: rows}).map((_, i) => (
          <div key={i}
               className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-5 animate-pulse">
            <div className="h-4 w-24 bg-gray-200 dark:bg-gray-700 rounded mb-3"/>
            <div className="h-3 w-full bg-gray-200 dark:bg-gray-700 rounded mb-2"/>
            <div className="h-3 w-2/3 bg-gray-200 dark:bg-gray-700 rounded"/>
          </div>
        ))}
      </div>
    );
  }
  return (
    <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      <Skeleton lines={rows}/>
    </div>
  );
};
