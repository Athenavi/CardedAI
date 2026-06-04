'use client';

import {lazy, Suspense, useState} from 'react';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {CreditCard, DollarSign, Settings} from 'lucide-react';

const LazyGatewaysTab = lazy(() => import('./payment/GatewaysTab'));
const LazyTransactionsTab = lazy(() => import('./payment/TransactionsTab'));
const LazyTaxConfigsTab = lazy(() => import('./payment/TaxConfigsTab'));

const TabSkeleton = () => (
  <div className="space-y-4 animate-pulse">
    <div className="h-8 w-48 bg-gray-200 dark:bg-gray-700 rounded-lg"/>
    <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded-xl"/>
    <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded-xl"/>
  </div>
);

type TabKey = 'gateways' | 'transactions' | 'tax-configs';
const TABS: { key: TabKey; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  {key: 'gateways', label: '支付网关', icon: CreditCard},
  {key: 'transactions', label: '交易记录', icon: DollarSign},
  {key: 'tax-configs', label: '税务配置', icon: Settings},
];

function PaymentManagementInner() {
  const [tab, setTab] = useState<TabKey>('gateways');

  return (
    <AdminShell title="支付管理" actions={<CreditCard className="w-5 h-5 text-blue-500"/>}>
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
            {tab === 'gateways' && <LazyGatewaysTab/>}
            {tab === 'transactions' && <LazyTransactionsTab/>}
            {tab === 'tax-configs' && <LazyTaxConfigsTab/>}
          </Suspense>
        </div>
      </div>
    </AdminShell>
  );
}

export default function AdminPaymentManagement() {
  return (
    <AuthGuard>
      <QueryProvider>
        <PaymentManagementInner/>
      </QueryProvider>
    </AuthGuard>
  );
}
