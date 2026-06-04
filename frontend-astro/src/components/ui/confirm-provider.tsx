/**
 * 确认对话框系统 - 替代浏览器原生 confirm()
 * 支持自定义标题、消息、确认/取消按钮文本、danger/warning 变体
 * 通过 React Context + Promise 实现 await confirm() 的异步模式
 */

'use client';

import React, {createContext, useCallback, useContext, useState} from 'react';
import {AlertTriangle, Trash2, Info} from 'lucide-react';

// ═══ Types ═══
export type ConfirmVariant = 'danger' | 'warning' | 'info';

export interface ConfirmOptions {
  title?: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: ConfirmVariant;
}

interface ConfirmContextValue {
  confirm: (options: ConfirmOptions) => Promise<boolean>;
}

// ═══ Context ═══
const ConfirmContext = createContext<ConfirmContextValue | null>(null);

// ═══ Config ═══
const variantConfig: Record<ConfirmVariant, {
  icon: React.FC<{ className?: string }>;
  iconColor: string;
  confirmBg: string;
  confirmHover: string;
  borderColor: string;
}> = {
  danger: {
    icon: Trash2,
    iconColor: 'text-red-500',
    confirmBg: 'bg-red-600',
    confirmHover: 'hover:bg-red-700',
    borderColor: 'border-red-200 dark:border-red-800',
  },
  warning: {
    icon: AlertTriangle,
    iconColor: 'text-amber-500',
    confirmBg: 'bg-amber-600',
    confirmHover: 'hover:bg-amber-700',
    borderColor: 'border-amber-200 dark:border-amber-800',
  },
  info: {
    icon: Info,
    iconColor: 'text-blue-500',
    confirmBg: 'bg-blue-600',
    confirmHover: 'hover:bg-blue-700',
    borderColor: 'border-blue-200 dark:border-blue-800',
  },
};

// ═══ Confirm Dialog Component ═══
const ConfirmDialog: React.FC<{
  options: ConfirmOptions;
  onConfirm: () => void;
  onCancel: () => void;
}> = ({options, onConfirm, onCancel}) => {
  const variant = options.variant || 'danger';
  const config = variantConfig[variant];
  const Icon = config.icon;
  const [loading, setLoading] = useState(false);

  const handleConfirm = async () => {
    setLoading(true);
    onConfirm();
  };

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 dark:bg-black/70 animate-in fade-in-0"
        onClick={onCancel}
      />
      {/* Dialog */}
      <div
        className={`relative bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border ${config.borderColor} w-full max-w-sm animate-in zoom-in-95 fade-in-0 duration-200`}>
        <div className="p-6">
          <div className="flex items-start gap-4">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
              variant === 'danger' ? 'bg-red-100 dark:bg-red-900/30' :
                variant === 'warning' ? 'bg-amber-100 dark:bg-amber-900/30' :
                  'bg-blue-100 dark:bg-blue-900/30'
            }`}>
              <Icon className={`w-5 h-5 ${config.iconColor}`}/>
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">
                {options.title || '确认操作'}
              </h3>
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                {options.message}
              </p>
            </div>
          </div>
        </div>
        <div
          className="flex items-center justify-end gap-3 px-6 py-4 bg-gray-50 dark:bg-gray-800/50 rounded-b-2xl border-t border-gray-100 dark:border-gray-800">
          <button
            onClick={onCancel}
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
          >
            {options.cancelText || '取消'}
          </button>
          <button
            onClick={handleConfirm}
            disabled={loading}
            className={`px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors disabled:opacity-50 ${config.confirmBg} ${config.confirmHover}`}
          >
            {loading ? '处理中...' : (options.confirmText || '确认')}
          </button>
        </div>
      </div>
    </div>
  );
};

// ═══ Provider ═══
export const ConfirmProvider: React.FC<{ children: React.ReactNode }> = ({children}) => {
  const [dialog, setDialog] = useState<{
    options: ConfirmOptions;
    resolve: (value: boolean) => void;
  } | null>(null);

  const confirm = useCallback((options: ConfirmOptions): Promise<boolean> => {
    return new Promise<boolean>((resolve) => {
      setDialog({options, resolve});
    });
  }, []);

  const handleConfirm = useCallback(() => {
    if (dialog) {
      dialog.resolve(true);
      setDialog(null);
    }
  }, [dialog]);

  const handleCancel = useCallback(() => {
    if (dialog) {
      dialog.resolve(false);
      setDialog(null);
    }
  }, [dialog]);

  return (
    <ConfirmContext.Provider value={{confirm}}>
      {children}
      {dialog && (
        <ConfirmDialog
          options={dialog.options}
          onConfirm={handleConfirm}
          onCancel={handleCancel}
        />
      )}
    </ConfirmContext.Provider>
  );
};

// ═══ Hook ═══
export function useConfirm() {
  const ctx = useContext(ConfirmContext);
  if (!ctx) throw new Error('useConfirm must be used within a ConfirmProvider');
  return ctx.confirm;
}

export default ConfirmProvider;
