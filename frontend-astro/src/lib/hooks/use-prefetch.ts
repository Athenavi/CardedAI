/**
 * 链接预取 Hook - 鼠标悬停时预加载页面资源
 */

import {useCallback, useRef} from 'react';

export function usePrefetch() {
  const timers = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());
  const loading = useRef<Set<string>>(new Set());

  const prefetch = useCallback((url: string, delay = 400) => {
    const existing = timers.current.get(url);
    if (existing) clearTimeout(existing);
    if (!existing) timers.current.delete(url);

    if (loading.current.has(url)) return;

    const timer = setTimeout(async () => {
      loading.current.add(url);

      try {
        await fetch(url, {
          credentials: 'include',
          headers: {'X-Prefetch': 'true'},
        });
      } catch { /* 忽略预取失败 */ }

      loading.current.delete(url);
    }, delay);

    timers.current.set(url, timer);
  }, []);

  const prefetchModule = useCallback((loader: () => Promise<any>, delay = 200) => {
    const timer = setTimeout(() => {
      loader().catch(() => {});
    }, delay);
    return () => clearTimeout(timer);
  }, []);

  return {prefetch, prefetchModule};
}

/**
 * 预取特定路由的数据
 * 支持 React Query 预填充
 */
export async function prefetchRoute(path: string, queryClient?: any) {
  if (!queryClient) return;

  // 根据路由预取对应数据
  const routeMap: Record<string, Array<[string[], () => Promise<any>]>> = {
    '/admin': [[['dashboard'], async () => { const m = await import('@/lib/api/dashboard-service'); return (m as any).getDashboard?.() || {}; }]],
    '/articles': [[['articles'], async () => { const m = await import('@/lib/api/article-service'); return (m as any).getArticles?.({page: 1, per_page: 10}) || {}; }]],
  };

  const queries = routeMap[path];
  if (!queries) return;

  for (const [key, fn] of queries) {
    try {
      await queryClient.prefetchQuery({
        queryKey: key,
        queryFn: fn,
        staleTime: 60_000,
      });
    } catch { /* 忽略 */ }
  }
}