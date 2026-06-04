'use client';

import React, {lazy, Suspense, useState} from 'react';
import {FileText, Search, Share2} from 'lucide-react';
import {AdminShell} from '@/components/admin/AdminShell';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';

const LazyArticleSEOTab = lazy(() => import('./seo/ArticleSEOTab'));
const LazyShareStatsTab = lazy(() => import('./seo/ShareStatsTab'));
const LazySearchHistoryTab = lazy(() => import('./seo/SearchHistoryTab'));

const TabSkeleton = () => (
  <div className="space-y-4 animate-pulse">
    <div className="h-8 w-48 bg-gray-200 dark:bg-gray-700 rounded-lg"/>
    <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded-xl"/>
    <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded-xl"/>
  </div>
);

const AdminSEOManagementInner: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'seo' | 'shares' | 'search'>('seo');

  const tabs = [
    {key: 'seo' as const, label: '文章 SEO', icon: FileText},
    {key: 'shares' as const, label: '分享统计', icon: Share2},
    {key: 'search' as const, label: '搜索历史', icon: Search},
  ];

  return (
    <AdminShell title="SEO 管理" actions={
      <div className="flex bg-gray-100 dark:bg-gray-800 rounded-lg p-0.5">
        {tabs.map(t => (
          <button key={t.key} onClick={() => setActiveTab(t.key)}
                  className={`px-3 py-1.5 text-sm rounded-md transition-colors ${activeTab === t.key ? 'bg-white dark:bg-gray-700 shadow-sm text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700'}`}>
            <t.icon className="w-4 h-4 inline mr-1"/>
            {t.label}
          </button>
        ))}
      </div>
    }>
      <div className="p-6 max-w-7xl mx-auto">
        <Suspense fallback={<TabSkeleton/>}>
          {activeTab === 'seo' && <LazyArticleSEOTab/>}
          {activeTab === 'shares' && <LazyShareStatsTab/>}
          {activeTab === 'search' && <LazySearchHistoryTab/>}
        </Suspense>
      </div>
    </AdminShell>
  );
};


export default function AdminSEOManagement() {
  return (
    <AuthGuard>
      <QueryProvider>
        <AdminSEOManagementInner/>
      </QueryProvider>
    </AuthGuard>
  );
}
