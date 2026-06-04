'use client';

import React from 'react';

/** 侧边栏骨架屏 — 独立文件避免 AdminSidebar 动态/静态导入冲突 */
export function SidebarSkeleton({collapsed}: { collapsed: boolean }) {
  return (
    <div
      className={`hidden lg:flex flex-col border-r border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 transition-all ${collapsed ? 'w-16' : 'w-56'} flex-shrink-0`}>
      <div className="flex items-center justify-between h-14 px-4 border-b border-gray-200 dark:border-gray-800">
        {!collapsed && <div className="h-4 w-16 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"/>}
        <div className="w-7 h-7 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse"/>
      </div>
      <div className="flex-1 p-3 space-y-2">
        {Array.from({length: 12}).map((_, i) => (
          <div key={i} className="flex items-center gap-3 px-3 py-2">
            <div className="w-5 h-5 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"/>
            {!collapsed && <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"
                                style={{width: `${50 + Math.random() * 40}%`}}/>}
          </div>
        ))}
      </div>
    </div>
  );
}
