/**
 * FastBlog 共享 Hooks 工具库
 * 消除跨组件的重复代码，提供统一的 hooks 实现
 */

import {useState, useEffect, useRef, useCallback, useMemo} from 'react';

/**
 * 防抖 Hook - 延迟更新值，减少频繁 API 请求
 * @param value 要防抖的值
 * @param delay 延迟毫秒数
 */
export function useDebounce<T>(value: T, delay: number): T {
    const [debouncedValue, setDebouncedValue] = useState(value);
    useEffect(() => {
        const timer = setTimeout(() => setDebouncedValue(value), delay);
        return () => clearTimeout(timer);
    }, [value, delay]);
    return debouncedValue;
}

/**
 * 防抖回调 Hook - 延迟执行回调函数
 */
export function useDebouncedCallback<T extends (...args: any[]) => any>(
    callback: T,
    delay: number
): T {
    const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const callbackRef = useRef(callback);
    callbackRef.current = callback;

    return useCallback(
        ((...args: any[]) => {
            if (timeoutRef.current) clearTimeout(timeoutRef.current);
            timeoutRef.current = setTimeout(() => callbackRef.current(...args), delay);
        }) as T,
        [delay]
    );
}

/**
 * 本地存储 Hook - 同步状态到 localStorage
 */
export function useLocalStorage<T>(key: string, initialValue: T): [T, (value: T | ((prev: T) => T)) => void] {
    const [storedValue, setStoredValue] = useState<T>(() => {
        if (typeof window === 'undefined') return initialValue;
        try {
            const item = window.localStorage.getItem(key);
            return item ? JSON.parse(item) : initialValue;
        } catch {
            return initialValue;
        }
    });

    const setValue = useCallback((value: T | ((prev: T) => T)) => {
        setStoredValue(prev => {
            const newValue = value instanceof Function ? value(prev) : value;
            if (typeof window !== 'undefined') {
                try {
                    window.localStorage.setItem(key, JSON.stringify(newValue));
                } catch {
                }
            }
            return newValue;
        });
    }, [key]);

    return [storedValue, setValue];
}

/**
 * 媒体查询 Hook - 响应式断点检测
 */
export function useMediaQuery(query: string): boolean {
    const [matches, setMatches] = useState(false);
    useEffect(() => {
        if (typeof window === 'undefined') return;
        const mq = window.matchMedia(query);
        setMatches(mq.matches);
        const handler = (e: MediaQueryListEvent) => setMatches(e.matches);
        mq.addEventListener('change', handler);
        return () => mq.removeEventListener('change', handler);
    }, [query]);
    return matches;
}

/**
 * 网络状态 Hook - 检测在线/离线
 */
export function useOnlineStatus(): boolean {
    const [isOnline, setIsOnline] = useState(() =>
        typeof navigator !== 'undefined' ? navigator.onLine : true
    );
    useEffect(() => {
        const handleOnline = () => setIsOnline(true);
        const handleOffline = () => setIsOnline(false);
        window.addEventListener('online', handleOnline);
        window.addEventListener('offline', handleOffline);
        return () => {
            window.removeEventListener('online', handleOnline);
            window.removeEventListener('offline', handleOffline);
        };
    }, []);
    return isOnline;
}

/**
 * Intersection Observer Hook - 懒加载/无限滚动
 */
export function useIntersectionObserver(
    options: IntersectionObserverInit = {}
): { ref: (node: Element | null) => void; isIntersecting: boolean } {
    const [isIntersecting, setIsIntersecting] = useState(false);
    const [node, setNode] = useState<Element | null>(null);

    const ref = useCallback((node: Element | null) => setNode(node), []);

    useEffect(() => {
        if (!node || typeof IntersectionObserver === 'undefined') return;
        const observer = new IntersectionObserver(([entry]) => {
            setIsIntersecting(entry.isIntersecting);
        }, options);
        observer.observe(node);
        return () => observer.disconnect();
    }, [node, options.threshold, options.root, options.rootMargin]);

    return {ref, isIntersecting};
}

/**
 * 前一个值 Hook - 用于对比前后值变化
 */
export function usePrevious<T>(value: T): T | undefined {
    const ref = useRef<T | undefined>(undefined);
    useEffect(() => {
        ref.current = value;
    }, [value]);
    return ref.current;
}

/**
 * 挂载状态 Hook - 判断组件是否已挂载
 */
export function useIsMounted(): () => boolean {
    const isMountedRef = useRef(false);
    useEffect(() => {
        isMountedRef.current = true;
        return () => {
            isMountedRef.current = false;
        };
    }, []);
    return useCallback(() => isMountedRef.current, []);
}

/**
 * 复制到剪贴板 Hook
 */
export function useCopyToClipboard(): [boolean, (text: string) => Promise<void>] {
    const [copied, setCopied] = useState(false);
    const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    const copy = useCallback(async (text: string) => {
        try {
            await navigator.clipboard.writeText(text);
            setCopied(true);
            if (timerRef.current) clearTimeout(timerRef.current);
            timerRef.current = setTimeout(() => setCopied(false), 2000);
        } catch {
            // Fallback for older browsers
            const ta = document.createElement('textarea');
            ta.value = text;
            ta.style.position = 'fixed';
            ta.style.left = '-9999px';
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
            setCopied(true);
            if (timerRef.current) clearTimeout(timerRef.current);
            timerRef.current = setTimeout(() => setCopied(false), 2000);
        }
    }, []);

    return [copied, copy];
}

/**
 * 分页计算 Hook - 统一分页逻辑
 */
export function usePagination({total, page, pageSize = 15}: {
    total: number; page: number; pageSize?: number;
}) {
    return useMemo(() => {
        const totalPages = Math.max(1, Math.ceil(total / pageSize));
        const delta = 2;
        const left = Math.max(2, page - delta);
        const right = Math.min(totalPages - 1, page + delta);
        const pages: (number | string)[] = [1];
        if (left > 2) pages.push('...');
        for (let i = left; i <= right; i++) pages.push(i);
        if (right < totalPages - 1) pages.push('...');
        if (totalPages > 1) pages.push(totalPages);
        return {totalPages, pages, hasPrev: page > 1, hasNext: page < totalPages};
    }, [total, page, pageSize]);
}
