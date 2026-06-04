'use client';

import React, {lazy, Suspense, useState} from 'react';
import {Banknote, DollarSign, PieChart, Settings} from 'lucide-react';
import {AdminShell} from '@/components/admin/AdminShell';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';

const LazyRecordsTab = lazy(() => import('./revenue/RecordsTab'));
const LazyPayoutsTab = lazy(() => import('./revenue/PayoutsTab'));
const LazyConfigTab = lazy(() => import('./revenue/ConfigTab'));
const LazyStatsTab = lazy(() => import('./revenue/StatsTab'));

const TabSkeleton = () => (
  <div className="space-y-4 animate-pulse">
    <div className="h-8 w-48 bg-gray-200 dark:bg-gray-700 rounded-lg"/>
    <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded-xl"/>
    <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded-xl"/>
  </div>
);

const AdminRevenueManagementInner: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'records' | 'payouts' | 'config' | 'stats'>('records');

  const tabs = [
    {key: 'records' as const, label: '收益记录', icon: DollarSign},
    {key: 'payouts' as const, label: '提现管理', icon: Banknote},
    {key: 'config' as const, label: '分成配置', icon: Settings},
    {key: 'stats' as const, label: '平台统计', icon: PieChart},
  ];

  return (
    <AdminShell title="收益分成管理" actions={
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
          {activeTab === 'records' && <LazyRecordsTab/>}
          {activeTab === 'payouts' && <LazyPayoutsTab/>}
          {activeTab === 'config' && <LazyConfigTab/>}
          {activeTab === 'stats' && <LazyStatsTab/>}
        </Suspense>
      </div>
    </AdminShell>
  );
};

export default function AdminRevenueManagement() {
  return (
    <AuthGuard>
      <QueryProvider>
        <AdminRevenueManagementInner/>
      </QueryProvider>
    </AuthGuard>
  );
}
