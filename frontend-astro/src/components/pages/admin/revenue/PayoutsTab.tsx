'use client';

import React, {useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {EmptyState, Pagination} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import {useToast} from '@/components/ui/toast-provider';
import {Banknote, CheckCircle, XCircle} from 'lucide-react';
import {PayoutRequest, StatusBadge} from './shared';
import type {ApiResponse} from '@/lib/api/base-types';
const PayoutsTab: React.FC = () => {
  const toast = useToast();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');

  const {data, isLoading} = useQuery({
    queryKey: ['payout-requests', page, statusFilter],
    queryFn: () => apiClient.get('/shop/revenue/payouts', {
      page, per_page: 15,
      status: statusFilter || undefined,
    }),
  });

  const items: PayoutRequest[] = data?.data?.payouts || data?.data?.items || [];
  const total: number = data?.data?.total || 0;

  const approveMut = useMutation({
    mutationFn: (id: number) => apiClient.post(`/shop/revenue/payouts/${id}/approve`),
    onSuccess: (r: ApiResponse) => {
      if (r.success) qc.invalidateQueries({queryKey: ['payout-requests']});
      else toast.error(r.error || '操作失败');
    },
  });
  const completeMut = useMutation({
    mutationFn: (id: number) => apiClient.post(`/shop/revenue/payouts/${id}/complete`),
    onSuccess: (r: ApiResponse) => {
      if (r.success) qc.invalidateQueries({queryKey: ['payout-requests']});
      else toast.error(r.error || '操作失败');
    },
  });
  const rejectMut = useMutation({
    mutationFn: (id: number) => apiClient.post(`/shop/revenue/payouts/${id}/reject`),
    onSuccess: (r: ApiResponse) => {
      if (r.success) qc.invalidateQueries({queryKey: ['payout-requests']});
      else toast.error(r.error || '操作失败');
    },
  });

  return (
    <>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <select value={statusFilter} onChange={e => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
                  className="px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm dark:text-white">
            <option value="">全部状态</option>
            <option value="pending">待处理</option>
            <option value="approved">已批准</option>
            <option value="completed">已完成</option>
            <option value="rejected">已拒绝</option>
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-2">{[...Array(5)].map((_, i) => <div key={i}
                                                                     className="h-16 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse"/>)}</div>
      ) : items.length === 0 ? (
        <EmptyState icon={Banknote} title="暂无提现申请" desc="用户发起提现后将在此显示"/>
      ) : (
        <div
          className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
            <tr className="bg-gray-50 dark:bg-gray-800/50">
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">用户</th>
              <th className="text-right px-4 py-3 font-medium text-gray-500 dark:text-gray-400">金额</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">支付方式</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">收款账户</th>
              <th className="text-center px-4 py-3 font-medium text-gray-500 dark:text-gray-400">状态</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">申请时间</th>
              <th className="text-right px-4 py-3 font-medium text-gray-500 dark:text-gray-400">操作</th>
            </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {items.map(p => (
              <tr key={p.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/30">
                <td className="px-4 py-3 text-gray-900 dark:text-gray-100">{p.username || `用户#${p.user_id}`}</td>
                <td className="px-4 py-3 text-right font-medium text-green-600">¥{p.amount.toFixed(2)}</td>
                <td className="px-4 py-3 text-gray-500 dark:text-gray-400">{p.payment_method}</td>
                <td className="px-4 py-3 text-xs font-mono text-gray-500 dark:text-gray-400">{p.payment_account}</td>
                <td className="px-4 py-3 text-center"><StatusBadge status={p.status}/></td>
                <td className="px-4 py-3 text-xs text-gray-500 dark:text-gray-400">{p.created_at?.slice(0, 16)}</td>
                <td className="px-4 py-3 text-right">
                  {p.status === 'pending' && (
                    <div className="flex items-center justify-end gap-1">
                      <button onClick={() => approveMut.mutate(p.id)}
                              className="p-1.5 rounded hover:bg-green-50 dark:hover:bg-green-900/20" title="批准">
                        <CheckCircle className="w-3.5 h-3.5 text-green-500"/>
                      </button>
                      <button onClick={() => rejectMut.mutate(p.id)}
                              className="p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20" title="拒绝">
                        <XCircle className="w-3.5 h-3.5 text-red-500"/>
                      </button>
                    </div>
                  )}
                  {p.status === 'approved' && (
                    <button onClick={() => completeMut.mutate(p.id)}
                            className="px-2 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700">
                      标记完成
                    </button>
                  )}
                </td>
              </tr>
            ))}
            </tbody>
          </table>
          {total > 15 && (
            <div className="p-3 border-t border-gray-100 dark:border-gray-800">
              <Pagination page={page} totalPages={Math.ceil(total / 15)} onPageChange={setPage}/>
            </div>
          )}
        </div>
      )}
    </>
  );
};

export default PayoutsTab;
