'use client';

import React, {lazy, Suspense, useState} from 'react';
import {BarChart3, Clock, FileText} from 'lucide-react';
import {AdminShell} from '@/components/admin/AdminShell';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';

const LazyPendingTab = lazy(() => import('./approval/PendingTab'));
const LazyMyRequestsTab = lazy(() => import('./approval/MyRequestsTab'));
const LazyHistoryTab = lazy(() => import('./approval/HistoryTab'));

const TabSkeleton = () => (
  <div className="space-y-4 animate-pulse">
    <div className="h-8 w-48 bg-gray-200 dark:bg-gray-700 rounded-lg"/>
    <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded-xl"/>
    <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded-xl"/>
  </div>
);

const AdminContentApprovalInner: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'pending' | 'my-requests' | 'history'>('pending');

  const tabs = [
    {key: 'pending' as const, label: '待审批', icon: Clock},
    {key: 'my-requests' as const, label: '我的申请', icon: FileText},
    {key: 'history' as const, label: '统计历史', icon: BarChart3},
  ];

  return (
    <AdminShell title="内容审批管理" actions={
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
          {activeTab === 'pending' && <LazyPendingTab/>}
          {activeTab === 'my-requests' && <LazyMyRequestsTab/>}
          {activeTab === 'history' && <LazyHistoryTab/>}
        </Suspense>
      </div>
    </AdminShell>
  );
};


export default function AdminContentApproval() {
  return (
    <AuthGuard>
      <QueryProvider>
        <AdminContentApprovalInner/>
      </QueryProvider>
    </AuthGuard>
  );
}
