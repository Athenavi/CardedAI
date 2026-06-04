'use client';

import {lazy, Suspense, useState} from 'react';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {Database, Search, Zap} from 'lucide-react';

const LazySearchIndexTab = lazy(() => import('./search-media/SearchIndexTab'));
const LazyMediaOptimizationTab = lazy(() => import('./search-media/MediaOptimizationTab'));

const TabSkeleton = () => (
  <div className="space-y-4 animate-pulse">
    <div className="h-8 w-48 bg-gray-200 dark:bg-gray-700 rounded-lg"/>
    <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded-xl"/>
    <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded-xl"/>
  </div>
);

type TabKey = 'search-index' | 'media-optimization';
const TABS: { key: TabKey; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  {key: 'search-index', label: '搜索索引', icon: Search},
  {key: 'media-optimization', label: '媒体优化', icon: Zap},
];

function SearchMediaInner() {
  const [tab, setTab] = useState<TabKey>('search-index');

  return (
    <AdminShell title="搜索与媒体管理" actions={<Database className="w-5 h-5 text-blue-500"/>}>
      <div className="space-y-6">
        <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 rounded-xl p-1">
          {TABS.map(t => (
            <button key={t.key} onClick={() => setTab(t.key)}
                    className={`flex-1 flex items-center justify-center gap-1.5 px-4 py-2.5 text-sm rounded-lg transition-colors ${tab === t.key ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm font-medium' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'}`}>
              <t.icon className="w-4 h-4"/>
              {t.label}
            </button>
          ))}
        </div>
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-5">
          <Suspense fallback={<TabSkeleton/>}>
            {tab === 'search-index' && <LazySearchIndexTab/>}
            {tab === 'media-optimization' && <LazyMediaOptimizationTab/>}
          </Suspense>
        </div>
      </div>
    </AdminShell>
  );
}

export default function AdminSearchMediaManagement() {
  return (
    <AuthGuard>
      <QueryProvider>
        <SearchMediaInner/>
      </QueryProvider>
    </AuthGuard>
  );
}
