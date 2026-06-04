'use client';

import React, {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {EmptyState, Pagination} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import {Search} from 'lucide-react';
import {SearchHistory} from './shared';

const SearchHistoryTab: React.FC = () => {
  const [page, setPage] = useState(1);

  const {data, isLoading} = useQuery({
    queryKey: ['search-history', page],
    queryFn: () => apiClient.get('/search/history', {page, per_page: 20}),
  });

  const items: SearchHistory[] = data?.data?.history || data?.data?.items || [];
  const total: number = data?.data?.total || 0;

  return (
    <>
      {isLoading ? (
        <div className="space-y-2">{[...Array(5)].map((_, i) => <div key={i}
                                                                     className="h-16 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse"/>)}</div>
      ) : items.length === 0 ? (
        <EmptyState icon={Search} title="暂无搜索历史" desc="用户搜索后将自动记录"/>
      ) : (
        <div
          className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
            <tr className="bg-gray-50 dark:bg-gray-800/50">
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">搜索词</th>
              <th className="text-right px-4 py-3 font-medium text-gray-500 dark:text-gray-400">结果数</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">IP 地址</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">时间</th>
            </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {items.map(h => (
              <tr key={h.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/30">
                <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{h.query}</td>
                <td className="px-4 py-3 text-right">
                  <span
                    className={h.results_count === 0 ? 'text-red-500' : 'text-gray-500 dark:text-gray-400'}>{h.results_count}</span>
                </td>
                <td className="px-4 py-3 text-xs font-mono text-gray-500 dark:text-gray-400">{h.ip_address || '-'}</td>
                <td className="px-4 py-3 text-xs text-gray-500 dark:text-gray-400">{h.created_at?.slice(0, 16)}</td>
              </tr>
            ))}
            </tbody>
          </table>
          {total > 20 && (
            <div className="p-3 border-t border-gray-100 dark:border-gray-800">
              <Pagination page={page} totalPages={Math.ceil(total / 20)} onPageChange={setPage}/>
            </div>
          )}
        </div>
      )}
    </>
  );
};

export default SearchHistoryTab;
