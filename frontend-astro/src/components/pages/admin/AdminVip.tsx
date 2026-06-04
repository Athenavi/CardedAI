'use client';

import {lazy, Suspense, useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {Crown, Package, Shield} from 'lucide-react';
import {AdminShell} from '@/components/admin/AdminShell';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {apiClient} from '@/lib/api/base-client';
import {VipMgmtData} from './vip/shared';

const LazyPlansTab = lazy(() => import('./vip/PlansTab'));
const LazyFeaturesTab = lazy(() => import('./vip/FeaturesTab'));
const LazyMembersTab = lazy(() => import('./vip/MembersTab'));

type Tab = 'members' | 'plans' | 'features';

const TabSkeleton = () => (
  <div className="space-y-4 animate-pulse">
    <div className="h-8 w-48 bg-gray-200 dark:bg-gray-700 rounded-lg"/>
    <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded-xl"/>
    <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded-xl"/>
  </div>
);

const tabs = [
  {key: 'members' as const, label: '会员列表', icon: Crown},
  {key: 'plans' as const, label: '套餐管理', icon: Package},
  {key: 'features' as const, label: '功能管理', icon: Shield},
];

function VipAdminInner() {
  const [activeTab, setActiveTab] = useState<Tab>('members');
  const {data: mgmt, isLoading, refetch} = useQuery({
    queryKey: ['admin-vip'],
    queryFn: async () => {
      const r = await apiClient.get('/dashboard/vip-management');
      return (r.success && r.data) ? (r.data as VipMgmtData) : {stats: {}, members: [], plans: [], features: []};
    },
  });

  return (
    <AdminShell title="VIP 会员管理" actions={
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
        {isLoading ? (
          <TabSkeleton/>
        ) : (
          <Suspense fallback={<TabSkeleton/>}>
            {activeTab === 'members' && <LazyMembersTab members={mgmt?.members || []} stats={mgmt?.stats || {}}/>}
            {activeTab === 'plans' && <LazyPlansTab plans={mgmt?.plans || []} onChanged={() => refetch()}/>}
            {activeTab === 'features' && <LazyFeaturesTab features={mgmt?.features || []} onChanged={() => refetch()}/>}
          </Suspense>
        )}
      </div>
    </AdminShell>
  );
}

export default function AdminVip() {
  return (
    <AuthGuard>
      <QueryProvider>
        <VipAdminInner/>
      </QueryProvider>
    </AuthGuard>
  );
}
