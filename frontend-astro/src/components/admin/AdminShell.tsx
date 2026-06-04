'use client';

import React, {lazy, Suspense, useState} from 'react';
import {Menu} from 'lucide-react';
import {ErrorBoundary} from '@/components/ui/ErrorBoundary';
import {ToastProvider} from '@/components/ui/toast-provider';
import {SidebarSkeleton} from './AdminSidebarSkeleton';

// 懒加载侧边栏组件 — 45+ lucide 图标被分离到独立 chunk
const DesktopSidebar = lazy(() =>
  import('./AdminSidebar').then(m => ({default: m.DesktopSidebar}))
);
const MobileSidebar = lazy(() =>
  import('./AdminSidebar').then(m => ({default: m.MobileSidebar}))
);

export const AdminShell: React.FC<{title: string; children: React.ReactNode; actions?: React.ReactNode}> = ({title, children, actions}) => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <ToastProvider>
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex">
      {/* Desktop sidebar — 懒加载 */}
      <Suspense fallback={<SidebarSkeleton collapsed={collapsed}/>}>
        <DesktopSidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)}/>
      </Suspense>

      {/* Mobile sidebar overlay — 懒加载 */}
      <Suspense fallback={null}>
        <MobileSidebar open={mobileOpen} onClose={() => setMobileOpen(false)}/>
      </Suspense>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        <header
            className="h-14 flex items-center justify-between px-4 lg:px-6 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 flex-shrink-0 safe-top">
          <div className="flex items-center gap-3">
            <button onClick={() => setMobileOpen(true)}
                    className="p-2 min-w-[44px] min-h-[44px] -ml-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 lg:hidden flex items-center justify-center">
              <Menu className="w-5 h-5"/></button>
            <h1 className="text-base sm:text-lg font-bold text-gray-900 dark:text-white truncate">{title}</h1>
          </div>
          <div className="flex items-center gap-2">{actions}</div>
        </header>
        <main className="flex-1 overflow-y-auto p-4 lg:p-6"><ErrorBoundary>{children}</ErrorBoundary></main>
      </div>
    </div>
    </ToastProvider>
  );
};
