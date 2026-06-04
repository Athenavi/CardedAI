'use client';

import React, {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {EmptyState, Pagination} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import {Share2} from 'lucide-react';
import {ShareStat} from './shared';

const ShareStatsTab: React.FC = () => {
  const [page, setPage] = useState(1);

  const {data, isLoading} = useQuery({
    queryKey: ['share-stats', page],
    queryFn: () => apiClient.get('/social/shares', {page, per_page: 20}),
  });

  const items: ShareStat[] = data?.data?.stats || data?.data?.items || [];
  const total: number = data?.data?.total || 0;

  const platformColors: Record<string, string> = {
    weibo: 'bg-red-100 dark:bg-red-900/30 text-red-600',
    wechat: 'bg-green-100 dark:bg-green-900/30 text-green-600',
    twitter: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600',
    facebook: 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600',
    linkedin: 'bg-sky-100 dark:bg-sky-900/30 text-sky-600',
    qq: 'bg-cyan-100 dark:bg-cyan-900/30 text-cyan-600',
  };

  return (
    <>
      {isLoading ? (
        <div className="space-y-2">{[...Array(5)].map((_, i) => <div key={i}
                                                                     className="h-16 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse"/>)}</div>
      ) : items.length === 0 ? (
        <EmptyState icon={Share2} title="暂无分享数据" desc="文章被分享后将自动记录统计数据"/>
      ) : (
        <div
          className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
            <tr className="bg-gray-50 dark:bg-gray-800/50">
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">文章</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">平台</th>
              <th className="text-right px-4 py-3 font-medium text-gray-500 dark:text-gray-400">分享次数</th>
              <th className="text-right px-4 py-3 font-medium text-gray-500 dark:text-gray-400">点击次数</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">最后分享</th>
            </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {items.map(s => (
              <tr key={s.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/30">
                <td
                  className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100 max-w-[200px] truncate">{s.article_title || `文章#${s.article_id}`}</td>
                <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 text-[10px] rounded-full font-medium ${platformColors[s.platform] || 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'}`}>
                      {s.platform}
                    </span>
                </td>
                <td className="px-4 py-3 text-right font-medium">{s.share_count}</td>
                <td className="px-4 py-3 text-right text-gray-500 dark:text-gray-400">{s.click_count}</td>
                <td
                  className="px-4 py-3 text-xs text-gray-500 dark:text-gray-400">{s.last_shared_at?.slice(0, 16) || '-'}</td>
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

export default ShareStatsTab;
