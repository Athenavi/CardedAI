'use client';

import React, {useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {EmptyState} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import {useConfirm} from '@/components/ui/confirm-provider';
import {ChevronLeft, ChevronRight, Mail, Trash2} from 'lucide-react';
import {EmailSubscription, Pagination} from './shared';

const EmailSubscriptionsTab: React.FC = () => {
  const confirm = useConfirm();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);

  const {data, isLoading} = useQuery({
    queryKey: ['email-subscriptions', page],
    queryFn: () => apiClient.get('/users/security/email-subscriptions', {page, per_page: 15}),
  });
  const items: EmailSubscription[] = data?.data?.email_subscriptions || [];
  const pagination: Pagination | undefined = data?.data?.pagination;

  const toggleMut = useMutation({
    mutationFn: ({id, subscribed}: {
      id: number;
      subscribed: boolean
    }) => apiClient.put(`/users/security/email-subscriptions/${id}`, {subscribed: !subscribed}),
    onSuccess: () => qc.invalidateQueries({queryKey: ['email-subscriptions']}),
  });
  const deleteMut = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/users/security/email-subscriptions/${id}`),
    onSuccess: () => qc.invalidateQueries({queryKey: ['email-subscriptions']}),
  });

  return (
    <>
      {isLoading ? <div className="animate-pulse space-y-2">{[1, 2, 3].map(i => <div key={i}
                                                                                     className="h-14 bg-gray-100 dark:bg-gray-800 rounded-xl"/>)}</div> :
        items.length === 0 ? <EmptyState icon={Mail} title="暂无邮件订阅" desc="用户的邮件订阅状态将在此显示"/> :
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
              <tr className="border-b border-gray-100 dark:border-gray-800">
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">ID</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">用户ID</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">订阅状态</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">创建时间</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">操作</th>
              </tr>
              </thead>
              <tbody>{items.map(s => (
                <tr key={s.id}
                    className="border-b border-gray-50 dark:border-gray-800/50 hover:bg-gray-50 dark:hover:bg-gray-800/30">
                  <td className="py-3 px-4 font-mono text-xs">#{s.id}</td>
                  <td className="py-3 px-4 font-medium text-gray-900 dark:text-white">用户#{s.user_id}</td>
                  <td className="py-3 px-4">
                    <button onClick={() => toggleMut.mutate({id: s.id, subscribed: s.subscribed})}
                            className={`px-2.5 py-1 text-[10px] rounded-full font-medium ${s.subscribed ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' : 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'}`}>
                      {s.subscribed ? '已订阅' : '未订阅'}
                    </button>
                  </td>
                  <td
                    className="py-3 px-4 text-xs text-gray-500 dark:text-gray-400">{s.created_at ? new Date(s.created_at).toLocaleString('zh-CN') : '—'}</td>
                  <td className="py-3 px-4 text-right">
                    <button onClick={async () => {
                      if (await confirm({message: '确定删除？', variant: 'danger'})) deleteMut.mutate(s.id);
                    }}
                            className="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 text-red-500"><Trash2
                      className="w-3.5 h-3.5"/></button>
                  </td>
                </tr>
              ))}</tbody>
            </table>
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

export default EmailSubscriptionsTab;
