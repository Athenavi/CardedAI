'use client';

import React, {Suspense, lazy, ComponentType, useState, useEffect} from 'react';

/**
 * Admin 页面骨架屏 — 在懒加载组件加载期间显示
 */
function AdminPageSkeleton() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex">
      {/* Sidebar skeleton */}
      <aside
        className="hidden lg:flex flex-col w-56 border-r border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 flex-shrink-0">
        <div className="h-14 px-4 border-b border-gray-200 dark:border-gray-800 flex items-center">
          <div className="h-5 w-24 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"/>
        </div>
        <div className="flex-1 p-3 space-y-2 overflow-hidden">
          {Array.from({length: 15}).map((_, i) => (
            <div key={i} className="h-10 bg-gray-100 dark:bg-gray-800 rounded-xl animate-pulse"
                 style={{animationDelay: `${i * 50}ms`}}/>
          ))}
        </div>
      </aside>

      {/* Main content skeleton */}
      <div className="flex-1 flex flex-col min-w-0">
        <header
          className="h-14 flex items-center justify-between px-4 lg:px-6 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 flex-shrink-0">
          <div className="h-6 w-32 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"/>
          <div className="h-8 w-20 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse"/>
        </header>
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <div className="space-y-4">
            {/* Stats cards skeleton */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {Array.from({length: 4}).map((_, i) => (
                <div key={i}
                     className="h-24 bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 animate-pulse"
                     style={{animationDelay: `${i * 80}ms`}}/>
              ))}
            </div>
            {/* Table skeleton */}
            <div
              className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
              <div
                className="h-12 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 animate-pulse"/>
              {Array.from({length: 6}).map((_, i) => (
                <div key={i} className="h-16 border-b border-gray-100 dark:border-gray-800 animate-pulse"
                     style={{animationDelay: `${(i + 4) * 60}ms`}}/>
              ))}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

/**
 * 创建懒加载 Admin 页面组件
 *
 * 使用方式（在 .astro frontmatter 中）：
 * ```
 * import {createLazyAdmin} from '@/components/admin/LazyAdminPage';
 * const AdminArticles = createLazyAdmin(() => import('@/components/pages/admin/AdminArticles'));
 * ```
 *
 * 然后在模板中：
 * ```
 * <AdminArticles client:idle/>
 * ```
 *
 * 工作原理：
 * 1. 服务端渲染时显示骨架屏（快速 SSR）
 * 2. 客户端 hydration 后开始懒加载实际组件
 * 3. Suspense 在加载期间显示骨架屏
 * 4. 加载完成后渲染实际组件
 */
export function createLazyAdmin(loader: () => Promise<{ default: ComponentType<any> }>) {
  const LazyComponent = lazy(loader);

  const AdminLazyWrapper: React.FC<any> = (props) => {
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
      setMounted(true);
    }, []);

    // SSR 时渲染骨架屏，客户端 hydration 后加载实际组件
    if (!mounted) {
      return <AdminPageSkeleton/>;
    }

    return (
      <Suspense fallback={<AdminPageSkeleton/>}>
        <LazyComponent {...props} />
      </Suspense>
    );
  };

  // 设置 displayName 便于调试
  AdminLazyWrapper.displayName = 'AdminLazyWrapper';

  return AdminLazyWrapper;
}

export {AdminPageSkeleton};
