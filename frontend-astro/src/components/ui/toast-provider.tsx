/**
 * Toast 通知系统 - 轻量级、可堆叠的通知组件
 * 支持 success / error / warning / info 四种类型
 * 自动消失、手动关闭、进度条
 */

'use client';

import React, {createContext, useCallback, useContext, useEffect, useRef, useState} from 'react';
import {CheckCircle, XCircle, AlertTriangle, Info, X} from 'lucide-react';

// ═══ Types ═══
export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
    id: string;
    type: ToastType;
    title: string;
    message?: string;
    duration?: number;
    dismissible?: boolean;
}

interface ToastContextValue {
    toasts: Toast[];
    addToast: (toast: Omit<Toast, 'id'>) => void;
    removeToast: (id: string) => void;
    success: (title: string, message?: string) => void;
    error: (title: string, message?: string) => void;
    warning: (title: string, message?: string) => void;
    info: (title: string, message?: string) => void;
}

// ═══ Context ═══
const ToastContext = createContext<ToastContextValue | null>(null);

// ═══ Icon Map ═══
const iconMap: Record<ToastType, React.FC<{ className?: string }>> = {
    success: CheckCircle,
    error: XCircle,
    warning: AlertTriangle,
    info: Info,
};

const colorMap: Record<ToastType, string> = {
    success: 'text-emerald-500',
    error: 'text-red-500',
    warning: 'text-amber-500',
    info: 'text-blue-500',
};

// ═══ Toast Item Component ═══
const ToastItem: React.FC<{ toast: Toast; onRemove: (id: string) => void }> = ({toast, onRemove}) => {
    const [removing, setRemoving] = useState(false);
    const Icon = iconMap[toast.type];
    const timerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

    const dismiss = useCallback(() => {
        setRemoving(true);
        setTimeout(() => onRemove(toast.id), 300);
    }, [toast.id, onRemove]);

    useEffect(() => {
        const duration = toast.duration ?? 4000;
        if (duration > 0) {
            timerRef.current = setTimeout(dismiss, duration);
        }
        return () => {
            if (timerRef.current) clearTimeout(timerRef.current);
        };
    }, [toast.duration, dismiss]);

    const handleMouseEnter = () => {
        if (timerRef.current) clearTimeout(timerRef.current);
    };

    const handleMouseLeave = () => {
        const duration = toast.duration ?? 4000;
        if (duration > 0) {
            timerRef.current = setTimeout(dismiss, duration);
        }
    };

    return (
        <div
            className={`toast toast-${toast.type} ${removing ? 'removing' : ''} relative overflow-hidden`}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
            role="alert"
            aria-live="assertive"
        >
            <Icon className={`w-5 h-5 flex-shrink-0 mt-0.5 ${colorMap[toast.type]}`}/>
            <div className="flex-1 min-w-0">
                <p className="font-semibold text-sm">{toast.title}</p>
                {toast.message && <p className="text-xs mt-0.5 opacity-80">{toast.message}</p>}
            </div>
            {(toast.dismissible ?? true) && (
                <button
                    onClick={dismiss}
                    className="flex-shrink-0 p-1 rounded-lg hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
                    aria-label="关闭"
                >
                    <X className="w-4 h-4"/>
                </button>
            )}
            {/* Progress bar */}
            {(toast.duration ?? 4000) > 0 && (
                <div
                    className={`toast-progress ${toast.type === 'success' ? 'bg-emerald-500' : toast.type === 'error' ? 'bg-red-500' : toast.type === 'warning' ? 'bg-amber-500' : 'bg-blue-500'}`}
                    style={{animationDuration: `${toast.duration ?? 4000}ms`}}
                />
            )}
        </div>
    );
};

// ═══ Toast Container ═══
const ToastContainer: React.FC<{ toasts: Toast[]; onRemove: (id: string) => void }> = ({toasts, onRemove}) => {
    if (toasts.length === 0) return null;
    return (
        <div className="toast-container" aria-label="通知">
            {toasts.map(toast => (
                <ToastItem key={toast.id} toast={toast} onRemove={onRemove}/>
            ))}
        </div>
    );
};

// ═══ Provider ═══
let toastCounter = 0;

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({children}) => {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const removeToast = useCallback((id: string) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    }, []);

    const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
        const id = `toast-${++toastCounter}`;
        setToasts(prev => [...prev.slice(-4), {...toast, id}]); // max 5 toasts
    }, []);

    const success = useCallback((title: string, message?: string) => {
        addToast({type: 'success', title, message});
    }, [addToast]);

    const error = useCallback((title: string, message?: string) => {
        addToast({type: 'error', title, message, duration: 6000});
    }, [addToast]);

    const warning = useCallback((title: string, message?: string) => {
        addToast({type: 'warning', title, message});
    }, [addToast]);

    const info = useCallback((title: string, message?: string) => {
        addToast({type: 'info', title, message});
    }, [addToast]);

    return (
        <ToastContext.Provider value={{toasts, addToast, removeToast, success, error, warning, info}}>
            {children}
            <ToastContainer toasts={toasts} onRemove={removeToast}/>
        </ToastContext.Provider>
    );
};

// ═══ Hook ═══
export function useToast() {
    const ctx = useContext(ToastContext);
    if (!ctx) throw new Error('useToast must be used within a ToastProvider');
    return ctx;
}

export default ToastProvider;
