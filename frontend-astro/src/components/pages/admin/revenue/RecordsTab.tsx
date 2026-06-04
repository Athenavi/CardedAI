'use client';

import React, {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {EmptyState, Pagination} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import {Search, DollarSign} from 'lucide-react';
import {RevenueRecord, MoneyDisplay, StatusBadge} from './shared';

const RecordsTab: React.FC = () => {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');

  const {data, isLoading} = useQuery({
    queryKey: ['revenue-records', page, search, typeFilter],
    queryFn: () => apiClient.get('/shop/revenue/records', {
      page, per_page: 15,
      search: search || undefined,
      revenue_type: typeFilter || undefined,
    }),
  });

  const items: RevenueRecord[] = data?.data?.records || data?.data?.items || [];
  const total: number = data?.data?.total || 0;

  const revenueTypes = ['article_purchase', 'ad_revenue', 'tipping', 'subscription', 'digital_download'];

  return (
    <>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
            <input value={search} onChange={e => {
              setSearch(e.target.value);
              setPage(1);
            }}
                   placeholder="搜索用户..."
                   className="pl-9 pr-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm dark:text-white w-64"/>
          </div>
          <select value={typeFilter} onChange={e => {
            setTypeFilter(e.target.value);
            setPage(1);
          }}
                  className="px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm dark:text-white">
            <option value="">全部类型</option>
            {revenueTypes.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-2">{[...Array(5)].map((_, i) => <div key={i}
                                                                     className="h-16 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse"/>)}</div>
      ) : items.length === 0 ? (
        <EmptyState icon={DollarSign} title="暂无收益记录" desc="收益记录将在产生交易后自动生成"/>
      ) : (
        <div
          className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
            <tr className="bg-gray-50 dark:bg-gray-800/50">
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">用户</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">类型</th>
              <th className="text-right px-4 py-3 font-medium text-gray-500 dark:text-gray-400">总额</th>
              <th className="text-right px-4 py-3 font-medium text-gray-500 dark:text-gray-400">平台费用</th>
              <th className="text-right px-4 py-3 font-medium text-gray-500 dark:text-gray-400">用户收益</th>
              <th className="text-center px-4 py-3 font-medium text-gray-500 dark:text-gray-400">状态</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">时间</th>
            </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {items.map(r => (
              <tr key={r.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/30">
                <td className="px-4 py-3 text-gray-900 dark:text-gray-100">{r.username || `用户#${r.user_id}`}</td>
                <td className="px-4 py-3">
                    <span
                      className="px-2 py-0.5 text-[10px] rounded-full font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400">
                      {r.revenue_type}
                    </span>
                </td>
                <td className="px-4 py-3 text-right"><MoneyDisplay amount={r.amount}/></td>
                <td className="px-4 py-3 text-right text-gray-500 dark:text-gray-400">¥{r.platform_fee.toFixed(2)}</td>
                <td className="px-4 py-3 text-right text-green-600 font-medium">¥{r.user_earnings.toFixed(2)}</td>
                <td className="px-4 py-3 text-center"><StatusBadge status={r.status}/></td>
                <td className="px-4 py-3 text-xs text-gray-500 dark:text-gray-400">{r.created_at?.slice(0, 16)}</td>
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

export default RecordsTab;
