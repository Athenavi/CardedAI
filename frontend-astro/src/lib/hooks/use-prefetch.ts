/**
 * 链接预取 Hook - 鼠标悬停时预加载页面资源
 *
 * 使用方式：
 * ```tsx
 * const prefetch = usePrefetch();
 * <a href="/page" onMouseEnter={() => prefetch('/page')}>Link</a>
 * ```
 */

import {useCallback, useRef} from 'react';

export function usePrefetch() {
  const timers = useRef<Map<string, number>>(new Map());
  const loading = useRef<Set<string>>(new Set());

  const prefetch = useCallback((url: string, delay = 400) => {
    // 清除之前的定时器
    const existing = timers.current.get(url);
    if (existing) clearTimeout(existing);
    if (!existing) timers.current.delete(url);

    // 正在加载则跳过
    if (loading.current.has(url)) return;

    // 延迟预取，避免快速移动触发过多请求
    const timer = setTimeout(async () => {
      loading.current.add(url);

      // 1. 预取数据（如果目标页面 expose 了 prefetch）
      try {
        const response = await fetch(url, {
          credentials: 'include',
          headers: {'X-Prefetch': 'true'},
        });
        if (!response.ok) return;
        // 不缓存响应体，只缓存 headers 中的 ETag
      } catch { /* 忽略预取失败 */ }

      // 2. 预加载关键资源
      const criticalAssets = [
        `/src/pages${url}.ts`,
      ];

      for (const asset of criticalAssets) {
        try {
          const link = document.createElement('link');
          link.rel = 'prefetch';
          link.as = 'script';
          link.href = asset;
          document.head.appendChild(link);
        } catch { /* 忽略 */ }
      }

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
  const routeMap: Record<string, Array<[string[], any]>> = {
    '/admin': [[['dashboard'], () => import('@/lib/api/dashboard-service').then(m => m.getDashboardStats())]],
    '/articles': [[['articles'], () => import('@/lib/api/article-service').then(m => m.getArticles({page: 1, per_page: 10}))]],
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