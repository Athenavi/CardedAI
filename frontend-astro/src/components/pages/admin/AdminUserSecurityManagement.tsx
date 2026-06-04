'use client';

import {lazy, Suspense, useState} from 'react';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {Key, Mail, Monitor, Shield} from 'lucide-react';

const LazyFieldPermissionsTab = lazy(() => import('./user-security/FieldPermissionsTab'));
const LazySessionsTab = lazy(() => import('./user-security/SessionsTab'));
const LazyEmailSubscriptionsTab = lazy(() => import('./user-security/EmailSubscriptionsTab'));

const TabSkeleton = () => (
  <div className="space-y-4 animate-pulse">
    <div className="h-8 w-48 bg-gray-200 dark:bg-gray-700 rounded-lg"/>
    <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded-xl"/>
    <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded-xl"/>
  </div>
);

type TabKey = 'field-permissions' | 'sessions' | 'email-subscriptions';
const TABS: { key: TabKey; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  {key: 'field-permissions', label: '字段权限', icon: Key},
  {key: 'sessions', label: '会话管理', icon: Monitor},
  {key: 'email-subscriptions', label: '邮件订阅', icon: Mail},
];

function UserSecurityInner() {
  const [tab, setTab] = useState<TabKey>('field-permissions');

  return (
    <AdminShell title="用户安全管理" actions={<Shield className="w-5 h-5 text-blue-500"/>}>
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
            {tab === 'field-permissions' && <LazyFieldPermissionsTab/>}
            {tab === 'sessions' && <LazySessionsTab/>}
            {tab === 'email-subscriptions' && <LazyEmailSubscriptionsTab/>}
          </Suspense>
        </div>
      </div>
    </AdminShell>
  );
}

export default function AdminUserSecurityManagement() {
  return (
    <AuthGuard>
      <QueryProvider>
        <UserSecurityInner/>
      </QueryProvider>
    </AuthGuard>
  );
}
