'use client';

import React, {lazy, Suspense, useState} from 'react';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {BarChart3, Database, Globe, Shield, Upload} from 'lucide-react';
import {Toast} from './integrations/shared';

const TABS = [
  {key: 'oauth', label: 'OAuth 登录', icon: Globe, color: 'from-blue-500 to-indigo-500'},
  {key: 'sso', label: 'SSO 企业认证', icon: Shield, color: 'from-emerald-500 to-teal-500'},
  {key: 'analytics', label: '统计分析', icon: BarChart3, color: 'from-orange-500 to-amber-500'},
  {key: 'ipfs', label: 'IPFS 存储', icon: Database, color: 'from-purple-500 to-violet-500'},
  {key: 'import', label: '数据导入', icon: Upload, color: 'from-pink-500 to-rose-500'},
];

const TabSkeleton = () => (
  <div className="animate-pulse space-y-4">
    <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded-xl w-1/3"/>
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {[1, 2, 3, 4].map(i => <div key={i} className="h-24 bg-gray-200 dark:bg-gray-700 rounded-2xl"/>)}
    </div>
    <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded-2xl"/>
  </div>
);

const LazyOAuthTab = lazy(() => import('./integrations/OAuthTab'));
const LazySSOTab = lazy(() => import('./integrations/SSOTab'));
const LazyAnalyticsTab = lazy(() => import('./integrations/AnalyticsTab'));
const LazyIPFSTab = lazy(() => import('./integrations/IPFSTab'));
const LazyImportTab = lazy(() => import('./integrations/ImportTab'));

const TAB_COMPONENTS: Record<string, React.LazyExoticComponent<React.ComponentType<any>>> = {
  oauth: LazyOAuthTab,
  sso: LazySSOTab,
  analytics: LazyAnalyticsTab,
  ipfs: LazyIPFSTab,
  import: LazyImportTab,
};

function IntegrationsInner() {
  const [activeTab, setActiveTab] = useState('oauth');
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);

  const showToast = (message: string, type: 'success' | 'error' | 'info' = 'success') => {
    setToast({message, type});
    setTimeout(() => setToast(null), 3000);
  };

  const ActiveComponent = TAB_COMPONENTS[activeTab];

  return (
    <AdminShell title="集成管理" actions={
      <div className="text-xs text-gray-400">管理第三方登录 · 统计 · 存储 · 数据迁移</div>
    }>
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)}/>}

      {/* Tab Bar */}
      <div className="flex gap-1.5 mb-6 overflow-x-auto pb-1 scrollbar-hide">
        {TABS.map(t => {
          const Icon = t.icon;
          const isActive = activeTab === t.key;
          return (
            <button key={t.key} onClick={() => setActiveTab(t.key)}
                    className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-xl whitespace-nowrap transition-all ${
                      isActive
                        ? `bg-gradient-to-r ${t.color} text-white shadow-lg shadow-blue-500/20`
                        : 'bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 hover:border-gray-300'
                    }`}>
              <Icon className="w-4 h-4"/>{t.label}
            </button>
          );
        })}
      </div>

      {/* Tab Content - Lazy loaded */}
      <Suspense fallback={<TabSkeleton/>}>
        {ActiveComponent && <ActiveComponent showToast={showToast}/>}
      </Suspense>
    </AdminShell>
  );
}

export default function AdminIntegrations() {
  return <AuthGuard><QueryProvider><IntegrationsInner/></QueryProvider></AuthGuard>;
}
