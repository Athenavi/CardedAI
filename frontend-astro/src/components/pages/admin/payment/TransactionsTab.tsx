'use client';

import React, {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {EmptyState} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import {ChevronLeft, ChevronRight, DollarSign, Search} from 'lucide-react';
import {StatusBadge} from './shared';
import type {PaymentTransaction, Pagination} from './shared';

const TransactionsTab: React.FC = () => {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const {data, isLoading} = useQuery({
    queryKey: ['payment-transactions', page, search, statusFilter],
    queryFn: () => apiClient.get('/payment-management/transactions', {
      page,
      per_page: 15,
      search: search || undefined,
      status: statusFilter || undefined
    }),
  });

  const items: PaymentTransaction[] = data?.data?.transactions || [];
  const pagination: Pagination | undefined = data?.data?.pagination;

  return (
    <>
      <div className="flex items-center gap-2 mb-4">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
          <input value={search} onChange={e => {
            setSearch(e.target.value);
            setPage(1);
          }}
                 placeholder="搜索订单号..."
                 className="pl-9 pr-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white w-full"/>
        </div>
        <select value={statusFilter} onChange={e => {
          setStatusFilter(e.target.value);
          setPage(1);
        }}
                className="px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white">
          <option value="">全部状态</option>
          <option value="pending">待处理</option>
          <option value="completed">已完成</option>
          <option value="failed">失败</option>
          <option value="refunded">已退款</option>
          <option value="cancelled">已取消</option>
        </select>
      </div>
      {isLoading ? <div className="animate-pulse space-y-2">{[1, 2, 3].map(i => <div key={i}
                                                                                     className="h-16 bg-gray-100 dark:bg-gray-800 rounded-xl"/>)}</div> :
        items.length === 0 ? <EmptyState icon={DollarSign} title="暂无交易记录" desc="尚无支付交易数据"/> :
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
              <tr className="border-b border-gray-100 dark:border-gray-800">
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">ID</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">订单号</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">金额</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">状态</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">支付方式</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">创建时间</th>
              </tr>
              </thead>
              <tbody>{items.map(t => (
                <tr key={t.id}
                    className="border-b border-gray-50 dark:border-gray-800/50 hover:bg-gray-50 dark:hover:bg-gray-800/30">
                  <td className="py-3 px-4 font-mono text-xs text-gray-500 dark:text-gray-400">#{t.id}</td>
                  <td className="py-3 px-4 font-medium text-gray-900 dark:text-white text-xs">{t.order_id}</td>
                  <td className="py-3 px-4 font-semibold text-gray-900 dark:text-white">{t.amount} {t.currency}</td>
                  <td className="py-3 px-4"><StatusBadge status={t.status}/></td>
                  <td className="py-3 px-4 text-gray-600 dark:text-gray-400">{t.payment_method || '—'}</td>
                  <td
                    className="py-3 px-4 text-xs text-gray-500 dark:text-gray-400">{t.created_at ? new Date(t.created_at).toLocaleString('zh-CN') : '—'}</td>
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

export default TransactionsTab;
