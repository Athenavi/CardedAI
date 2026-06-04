'use client';

import React, {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {EmptyState} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import {Link} from 'lucide-react';
import {ContentMapping} from './shared';

const ContentMappingsTab: React.FC = () => {
  const [page, setPage] = useState(1);
  const [siteFilter, setSiteFilter] = useState('');

  const {data, isLoading} = useQuery({
    queryKey: ['content-mappings', page, siteFilter],
    queryFn: () => siteFilter
      ? apiClient.get(`/system/multisite/${siteFilter}/content-mappings`, {page, per_page: 15})
      : Promise.resolve({success: true, data: {mappings: [], total: 0}}),
    enabled: !!siteFilter,
  });

  const items: ContentMapping[] = data?.data?.mappings || [];
  const _total: number = data?.data?.total || 0;

  const syncStatusColors: Record<string, string> = {
    synced: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
    pending: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400',
    failed: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400',
  };

  return (
    <>
      <div className="flex items-center gap-2 mb-4">
        <select value={siteFilter} onChange={e => {
          setSiteFilter(e.target.value);
          setPage(1);
        }}
                className="px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm dark:text-white">
          <option value="">选择站点查看映射</option>
        </select>
      </div>

      {!siteFilter ? (
        <EmptyState icon={Link} title="请选择站点" desc="选择一个站点以查看其内容映射关系"/>
      ) : isLoading ? (
        <div className="space-y-2">{[...Array(5)].map((_, i) => <div key={i}
                                                                     className="h-16 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse"/>)}</div>
      ) : items.length === 0 ? (
        <EmptyState icon={Link} title="暂无内容映射" desc="该站点暂无跨站内容同步映射"/>
      ) : (
        <div
          className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
            <tr className="bg-gray-50 dark:bg-gray-800/50">
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">来源站点</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">目标站点</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">内容类型</th>
              <th className="text-center px-4 py-3 font-medium text-gray-500 dark:text-gray-400">同步状态</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">最后同步</th>
            </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {items.map(m => (
              <tr key={m.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/30">
                <td className="px-4 py-3">{m.source_site_name || `站点#${m.source_site_id}`}</td>
                <td className="px-4 py-3">{m.target_site_name || `站点#${m.target_site_id}`}</td>
                <td className="px-4 py-3">
                    <span
                      className="px-2 py-0.5 text-[10px] rounded-full font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400">
                      {m.content_type}
                    </span>
                </td>
                <td className="px-4 py-3 text-center">
                    <span
                      className={`px-2 py-0.5 text-[10px] rounded-full font-medium ${syncStatusColors[m.sync_status] || 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'}`}>
                      {m.sync_status}
                    </span>
                </td>
                <td
                  className="px-4 py-3 text-xs text-gray-500 dark:text-gray-400">{m.last_synced_at?.slice(0, 16) || '-'}</td>
              </tr>
            ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
};

export default ContentMappingsTab;
