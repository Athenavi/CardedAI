'use client';

import React, {lazy, Suspense} from 'react';
import {AdminShell} from '@/components/admin/AdminShell';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';

const LazyGroupsTab = lazy(() => import('./chat-groups/GroupsTab'));
const __LazyGroupMembersPanel = lazy(() => import('./chat-groups/GroupMembersPanel'));
const __LazyGroupInvitesPanel = lazy(() => import('./chat-groups/GroupInvitesPanel'));

const TabSkeleton = () => (
  <div className="space-y-4 animate-pulse">
    <div className="h-8 w-48 bg-gray-200 dark:bg-gray-700 rounded-lg"/>
    <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded-xl"/>
    <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded-xl"/>
  </div>
);

const AdminChatGroupsManagementInner: React.FC = () => {
  return (
    <AdminShell title="群聊管理">
      <div className="p-6 max-w-7xl mx-auto">
        <Suspense fallback={<TabSkeleton/>}>
          <LazyGroupsTab/>
        </Suspense>
      </div>
    </AdminShell>
  );
};


export default function AdminChatGroupsManagement() {
  return (
    <AuthGuard>
      <QueryProvider>
        <AdminChatGroupsManagementInner/>
      </QueryProvider>
    </AuthGuard>
  );
}
