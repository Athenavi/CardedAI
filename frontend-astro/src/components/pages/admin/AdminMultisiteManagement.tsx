'use client';

import React, {lazy, Suspense, useState} from 'react';
import {Globe, Link} from 'lucide-react';
import {AdminShell} from '@/components/admin/AdminShell';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';

const LazySitesTab = lazy(() => import('./multisite/SitesTab'));
const __LazySiteUsersPanel = lazy(() => import('./multisite/SiteUsersPanel'));
const LazyContentMappingsTab = lazy(() => import('./multisite/ContentMappingsTab'));

const TabSkeleton = () => (
  <div className="space-y-4 animate-pulse">
    <div className="h-8 w-48 bg-gray-200 dark:bg-gray-700 rounded-lg"/>
    <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded-xl"/>
    <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded-xl"/>
  </div>
);

const AdminMultisiteManagementInner: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'sites' | 'mappings'>('sites');

  return (
    <AdminShell title="多站点管理" actions={
      <div className="flex bg-gray-100 dark:bg-gray-800 rounded-lg p-0.5">
        <button onClick={() => setActiveTab('sites')}
                className={`px-4 py-1.5 text-sm rounded-md transition-colors ${activeTab === 'sites' ? 'bg-white dark:bg-gray-700 shadow-sm text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700'}`}>
          <Globe className="w-4 h-4 inline mr-1.5"/>站点管理
        </button>
        <button onClick={() => setActiveTab('mappings')}
                className={`px-4 py-1.5 text-sm rounded-md transition-colors ${activeTab === 'mappings' ? 'bg-white dark:bg-gray-700 shadow-sm text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700'}`}>
          <Link className="w-4 h-4 inline mr-1.5"/>内容映射
        </button>
      </div>
    }>
      <div className="p-6 max-w-7xl mx-auto">
        <Suspense fallback={<TabSkeleton/>}>
          {activeTab === 'sites' ? <LazySitesTab/> : <LazyContentMappingsTab/>}
        </Suspense>
      </div>
    </AdminShell>
  );
};


export default function AdminMultisiteManagement() {
  return (
    <AuthGuard>
      <QueryProvider>
        <AdminMultisiteManagementInner/>
      </QueryProvider>
    </AuthGuard>
  );
}
