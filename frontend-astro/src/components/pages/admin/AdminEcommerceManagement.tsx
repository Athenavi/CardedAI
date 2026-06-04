'use client';

import {lazy, Suspense, useState} from 'react';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {Package, ShoppingCart} from 'lucide-react';

const LazyProductsTab = lazy(() => import('./ecommerce/ProductsTab'));
const LazyOrdersTab = lazy(() => import('./ecommerce/OrdersTab'));

const TabSkeleton = () => (
  <div className="space-y-4 animate-pulse">
    <div className="h-8 w-48 bg-gray-200 dark:bg-gray-700 rounded-lg"/>
    <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded-xl"/>
    <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded-xl"/>
  </div>
);

type TabKey = 'products' | 'orders';
const TABS: { key: TabKey; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  {key: 'products', label: '商品管理', icon: Package},
  {key: 'orders', label: '订单管理', icon: ShoppingCart},
];

function EcommerceManagementInner() {
  const [tab, setTab] = useState<TabKey>('products');

  return (
    <AdminShell title="电商管理" actions={
      <ShoppingCart className="w-5 h-5 text-blue-500"/>
    }>
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
            {tab === 'products' && <LazyProductsTab/>}
            {tab === 'orders' && <LazyOrdersTab/>}
          </Suspense>
        </div>
      </div>
    </AdminShell>
  );
}

export default function AdminEcommerceManagement() {
  return (
    <AuthGuard>
      <QueryProvider>
        <EcommerceManagementInner/>
      </QueryProvider>
    </AuthGuard>
  );
}
