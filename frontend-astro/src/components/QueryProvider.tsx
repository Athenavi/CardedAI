'use client';

import React, {useState, Suspense, useEffect} from 'react';
import {QueryClient, QueryClientProvider} from '@tanstack/react-query';
import {ErrorBoundary} from '@/components/ui/ErrorBoundary';
import {ConfirmProvider} from '@/components/ui/confirm-provider';
import {I18nProvider} from '@/lib/i18n';

// 开发环境导入 React Profiler
const Profiler = typeof window !== 'undefined' && process.env.NODE_ENV === 'development'
  ? React.lazy(() => import('@/components/ReactProfiler').then(m => ({default: m.ReactProfiler})))
  : null;

// 初始化性能监控
let performanceInit = false;

export function QueryProvider({children}: {children: React.ReactNode}) {
  const [qc] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60_000,
        // v5: 替换已弃用的 gcTime 为 gcTime（内部更名为 garbageTime，但 API 仍兼容 gcTime）
        gcTime: 5 * 60_000,
        retry: (failureCount, error: any) => {
          // 网络错误重试，认证错误不重试
          if (error?.status === 401 || error?.status === 403) return false;
          return failureCount < 2;
        },
        retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10_000),
        refetchOnWindowFocus: false,
        refetchOnMount: true,
        refetchOnReconnect: true,
        // 预取优化：并行请求
        networkMode: 'online',
      },
      mutations: {
        retry: 0,
        networkMode: 'always',
      },
    },
  }));

  // 初始化性能监控（仅客户端、仅一次）
  useEffect(() => {
    if (performanceInit) return;
    performanceInit = true;

    // 初始化 Web Vitals 监控
    import('@/lib/performance').then(({initPerformanceMonitoring}) => {
      initPerformanceMonitoring();
    }).catch(() => {});

    // 开发环境：启用 why-did-you-render
    if (process.env.NODE_ENV === 'development') {
      import('react').then((R) => {
        import('why-did-you-render').then((WDYR) => {
          try {
            WDYR.default(R.default, {trackAllPureComponents: true});
          } catch {}
        }).catch(() => {});
      });
    }
  }, []);

  return (
      <ErrorBoundary>
        <I18nProvider>
          <QueryClientProvider client={qc}>
            <ConfirmProvider>
              {Profiler && process.env.NODE_ENV === 'development' ? (
                <Suspense fallback={children as any}>
                  {children}
                </Suspense>
              ) : (
                children
              )}
            </ConfirmProvider>
          </QueryClientProvider>
        </I18nProvider>
      </ErrorBoundary>
  );
}
