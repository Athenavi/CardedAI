'use client';


import {useQuery} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {apiClient} from '@/lib/api/base-client';
import {CheckSquare, Handshake, MessageSquare, Users} from 'lucide-react';

function CollabInner() {
    const {data: workspaces, isLoading} = useQuery<any[]>({
    queryKey: ['admin-collab-workspaces'],
    queryFn: async () => {
      const r = await apiClient.get('/collaboration/team/workspaces');
      return r.success && r.data ? (Array.isArray(r.data) ? r.data : r.data.workspaces||[]) : [];
    },
  });
  const {data: comments} = useQuery({
    queryKey: ['admin-collab-comments'],
    queryFn: async () => {
      const r = await apiClient.get('/collaboration/comments/statistics');
      return r.success && r.data ? r.data : {};
    },
  });

  return (
    <AdminShell title="协作管理">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-white dark:bg-gray-900 rounded-2xl border p-5">
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-1"><Handshake
            className="w-4 h-4"/>工作区
          </div>
          <p className="text-2xl font-bold">{workspaces?.length || 0}</p></div>
        <div className="bg-white dark:bg-gray-900 rounded-2xl border p-5">
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-1"><Users
            className="w-4 h-4"/>评论数
          </div>
          <p className="text-2xl font-bold">{comments?.total_comments || '—'}</p></div>
        <div className="bg-white dark:bg-gray-900 rounded-2xl border p-5">
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-1"><MessageSquare
            className="w-4 h-4"/>已解决
          </div>
          <p className="text-2xl font-bold">{comments?.resolved || '—'}</p></div>
        <div className="bg-white dark:bg-gray-900 rounded-2xl border p-5">
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-1"><CheckSquare
            className="w-4 h-4"/>待处理
          </div>
          <p className="text-2xl font-bold">{comments?.pending || '—'}</p></div>
      </div>
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center"><div className="animate-spin w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full mx-auto"/></div>
        ) : !workspaces?.length ? (
          <div className="p-12 text-center text-gray-400"><Handshake className="w-10 h-10 mx-auto mb-3 opacity-40"/><p>暂无工作区</p></div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-800 border-b">
            <tr>
              <th
                className="px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase text-left">名称
              </th>
              <th
                className="px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase text-left hidden sm:table-cell">成员
              </th>
              <th
                className="px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase text-left hidden md:table-cell">任务
              </th>
              <th
                className="px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase text-left">状态
              </th>
            </tr>
            </thead>
            <tbody className="divide-y">
            {workspaces.map((w:any,i:number) => (
              <tr key={w.id||i} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                <td className="px-5 py-4"><span className="text-sm font-medium text-gray-900 dark:text-white">{w.name||'工作区'}</span></td>
                <td
                  className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400 hidden sm:table-cell">{w.member_count || w.members?.length || 0}</td>
                <td
                  className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400 hidden md:table-cell">{w.task_count || 0}</td>
                <td className="px-5 py-4"><span
                  className={`px-2 py-0.5 text-xs rounded-full ${w.is_active !== false ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' : 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'}`}>{w.is_active !== false ? '活跃' : '已归档'}</span>
                </td>
              </tr>
            ))}
          </tbody></table>
        )}
      </div>
    </AdminShell>
  );
}
export default function AdminCollaboration() { return <AuthGuard><QueryProvider><CollabInner/></QueryProvider></AuthGuard>; }
