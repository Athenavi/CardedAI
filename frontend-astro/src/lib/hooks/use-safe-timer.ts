/**
 * 安全定时器 Hooks - 自动清理防止内存泄漏
 *
 * 使用方式：
 * ```tsx
 * // 自动清理的 setInterval
 * useSafeInterval(() => { /* 定时任务 *\/ }, 1000);
 *
 * // 自动清理的 setTimeout
 * const {reset} = useSafeTimeout(() => { /* 延迟任务 *\/ }, 500);
 *
 * // 安全的事件监听器
 * useEventSafely(window, 'resize', handler);
 * ```
 */

import {useCallback, useEffect, useRef} from 'react';

/**
 * 自动清理的 setInterval
 * 组件卸载时自动 clearInterval
 */
export function useSafeInterval(
  callback: () => void,
  delay: number | null,
  deps: any[] = []
): void {
  const savedCallback = useRef(callback);

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback, ...deps]);

  useEffect(() => {
    if (delay === null) return;
    if (delay < 0) return;

    const interval = setInterval(() => savedCallback.current(), delay);
    return () => clearInterval(interval);
  }, [delay, ...deps]);
}

/**
 * 自动清理的 setTimeout
 * 返回 reset 函数用于重新设置定时器
 */
export function useSafeTimeout(
  callback: () => void,
  delay: number,
  deps: any[] = []
): { reset: () => void; clear: () => void } {
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const savedCallback = useRef(callback);

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback, ...deps]);

  const clear = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  const reset = useCallback((newDelay?: number) => {
    clear();
    if (newDelay !== undefined && newDelay >= 0) {
      timeoutRef.current = setTimeout(() => savedCallback.current(), newDelay);
    } else if (delay >= 0) {
      timeoutRef.current = setTimeout(() => savedCallback.current(), delay);
    }
  }, [delay, clear]);

  useEffect(() => {
    reset();
    return clear;
  }, [delay, ...deps, reset, clear]);

  return {reset, clear};
}

/**
 * 安全的事件监听器
 * 自动清理，支持一次性事件
 */
export function useEventSafely<T extends { addEventListener: (e: string, h: any, o?: any) => void; removeEventListener: (e: string, h: any, o?: any) => void }>(
  target: T | null,
  event: string,
  handler: (e: any) => void,
  options?: boolean | AddEventListenerOptions,
  deps: any[] = []
): void {
  const savedHandler = useRef(handler);

  useEffect(() => {
    savedHandler.current = handler;
  }, [handler, ...deps]);

  useEffect(() => {
    if (!target) return;
    const wrapped = (e: any) => savedHandler.current(e);
    target.addEventListener(event, wrapped, options);
    return () => target.removeEventListener(event, wrapped, options);
  }, [target, event, options, ...deps]);
}

/**
 * 一次性事件监听（自动清理）
 */
export function useEventOnce<T extends { addEventListener: (e: string, h: any) => void; removeEventListener: (e: string, h: any) => void }>(
  target: T | null,
  event: string,
  handler: (e: any) => void,
  deps: any[] = []
): void {
  const savedHandler = useRef(handler);

  useEffect(() => {
    savedHandler.current = handler;
  }, [handler, ...deps]);

  useEffect(() => {
    if (!target) return;
    const wrapped = (e: any) => {
      savedHandler.current(e);
      target.removeEventListener(event, wrapped);
    };
    target.addEventListener(event, wrapped);
    return () => target.removeEventListener(event, wrapped);
  }, [target, event, ...deps]);
}

/**
 * AbortController 管理 hook
 * 组件卸载时自动 abort 所有关联请求
 */
export function useAbortController() {
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    abortRef.current = new AbortController();
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  const signal = abortRef.current?.signal;

  const reset = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = new AbortController();
  }, []);

  return {signal: signal as AbortSignal | null, reset};
}