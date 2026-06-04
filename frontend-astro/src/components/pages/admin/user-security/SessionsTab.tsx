'use client';

import React, {useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {EmptyState} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import {useConfirm} from '@/components/ui/confirm-provider';
import {useToast} from '@/components/ui/toast-provider';
import {ChevronLeft, ChevronRight, Clock, Monitor, PowerOff, Smartphone, Trash2} from 'lucide-react';
import {UserSession, Pagination} from './shared';
import type {ApiResponse} from '@/lib/api/base-types';
const SessionsTab: React.FC = () => {
  const confirm = useConfirm();
  const toast = useToast();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);

  const {data, isLoading} = useQuery({
    queryKey: ['user-sessions', page],
    queryFn: () => apiClient.get('/users/security/sessions', {page, per_page: 15}),
  });
  const items: UserSession[] = data?.data?.sessions || [];
  const pagination: Pagination | undefined = data?.data?.pagination;

  const deactivateMut = useMutation({
    mutationFn: (id: number) => apiClient.post(`/users/security/sessions/${id}/deactivate`),
    onSuccess: (r: ApiResponse) => {
      if (r.success) qc.invalidateQueries({queryKey: ['user-sessions']}); else toast.error(r.error || '操作失败');
    },
  });
  const deleteMut = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/users/security/sessions/${id}`),
    onSuccess: () => qc.invalidateQueries({queryKey: ['user-sessions']}),
  });

  return (
    <>
      {isLoading ? <div className="animate-pulse space-y-2">{[1, 2, 3].map(i => <div key={i}
                                                                                     className="h-16 bg-gray-100 dark:bg-gray-800 rounded-xl"/>)}</div> :
        items.length === 0 ? <EmptyState icon={Monitor} title="暂无活跃会话" desc="用户登录会话将在此显示"/> :
          <div className="space-y-2">
            {items.map(s => (
              <div key={s.id}
                   className={`flex items-center justify-between p-4 rounded-xl border ${s.is_active ? 'bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700' : 'bg-gray-50 dark:bg-gray-800/50 border-gray-100 dark:border-gray-800 opacity-60'}`}>
                <div className="flex items-center gap-3">
                  {s.device_info?.toLowerCase().includes('mobile') ? <Smartphone className="w-4 h-4 text-gray-400"/> :
                    <Monitor className="w-4 h-4 text-gray-400"/>}
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-900 dark:text-white">用户#{s.user_id}</span>
                      <span
                        className={`px-1.5 py-0.5 text-[10px] rounded-full ${s.is_active ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' : 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'}`}>
                     {s.is_active ? '活跃' : '已失效'}
                   </span>
                    </div>
                    <div className="flex items-center gap-2 mt-0.5 text-[11px] text-gray-500 dark:text-gray-400">
                      {s.device_info && <span>{s.device_info}</span>}
                      {s.ip_address && <><span>·</span><span>{s.ip_address}</span></>}
                      {s.location && <><span>·</span><span>{s.location}</span></>}
                      {s.last_activity && <><span>·</span><span className="flex items-center gap-0.5"><Clock
                        className="w-3 h-3"/>{new Date(s.last_activity).toLocaleString('zh-CN')}</span></>}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  {s.is_active && (
                    <button onClick={async () => {
                      if (await confirm({
                        message: '确定要强制下线此会话？',
                        variant: 'warning'
                      })) deactivateMut.mutate(s.id);
                    }}
                            className="px-2.5 py-1 text-xs border border-yellow-200 dark:border-yellow-900/30 rounded-lg text-yellow-600 hover:bg-yellow-50 dark:hover:bg-yellow-900/10 flex items-center gap-1"
                            title="强制下线">
                      <PowerOff className="w-3 h-3"/>下线
                    </button>
                  )}
                  <button onClick={async () => {
                    if (await confirm({message: '确定删除此会话记录？', variant: 'danger'})) deleteMut.mutate(s.id);
                  }}
                          className="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 text-red-500"><Trash2
                    className="w-3.5 h-3.5"/></button>
                </div>
              </div>
            ))}
          </div>}
      {pagination && pagination.total_pages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <span className="text-xs text-gray-500 dark:text-gray-400">共 {pagination.total} 条</span>
          <div className="flex items-center gap-1">
            <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}
                    className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-30">
              <ChevronLeft className="w-4 h-4"/></button>
            <span className="text-xs text-gray-600 dark:text-gray-400 px-2">{page}/{pagination.total_pages}</span>
            <button disabled={page >= pagination.total_pages} onClick={() => setPage(p => p + 1)}
                    className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-30">
              <ChevronRight className="w-4 h-4"/></button>
          </div>
        </div>
      )}
    </>
  );
};

export default SessionsTab;
