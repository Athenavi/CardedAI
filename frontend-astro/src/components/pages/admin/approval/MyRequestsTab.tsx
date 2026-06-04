'use client';

import React, {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {EmptyState, Pagination} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import {FileText} from 'lucide-react';
import {ApprovalRecord, StatusBadge} from './shared';

const MyRequestsTab: React.FC = () => {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');

  const {data, isLoading} = useQuery({
    queryKey: ['my-approval-requests', page, statusFilter],
    queryFn: () => apiClient.get('/security/content-approval/my-requests', {
      page, per_page: 15,
      status: statusFilter || undefined,
    }),
  });

  const items: ApprovalRecord[] = data?.data?.requests || data?.data?.items || [];
  const total: number = data?.data?.total || 0;

  const contentTypeLabels: Record<string, string> = {
    article: '文章', page: '页面', comment: '评论', media: '媒体', product: '商品',
  };

  return (
    <>
      <div className="flex items-center gap-2 mb-4">
        <select value={statusFilter} onChange={e => {
          setStatusFilter(e.target.value);
          setPage(1);
        }}
                className="px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm dark:text-white">
          <option value="">全部状态</option>
          <option value="pending">待审批</option>
          <option value="approved">已通过</option>
          <option value="rejected">已拒绝</option>
          <option value="cancelled">已取消</option>
        </select>
      </div>

      {isLoading ? (
        <div className="space-y-2">{[...Array(5)].map((_, i) => <div key={i}
                                                                     className="h-16 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse"/>)}</div>
      ) : items.length === 0 ? (
        <EmptyState icon={FileText} title="暂无审批请求" desc="您提交的审批请求将在此显示"/>
      ) : (
        <div
          className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
            <tr className="bg-gray-50 dark:bg-gray-800/50">
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">内容</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">类型</th>
              <th className="text-center px-4 py-3 font-medium text-gray-500 dark:text-gray-400">进度</th>
              <th className="text-center px-4 py-3 font-medium text-gray-500 dark:text-gray-400">状态</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">申请时间</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">备注</th>
            </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {items.map(r => (
              <tr key={r.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/30">
                <td
                  className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{r.content_title || `#${r.content_id}`}</td>
                <td className="px-4 py-3">
                    <span
                      className="px-2 py-0.5 text-[10px] rounded-full font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400">
                      {contentTypeLabels[r.content_type] || r.content_type}
                    </span>
                </td>
                <td
                  className="px-4 py-3 text-center text-xs text-gray-500 dark:text-gray-400">{r.current_step}/{r.total_steps}</td>
                <td className="px-4 py-3 text-center"><StatusBadge status={r.status}/></td>
                <td className="px-4 py-3 text-xs text-gray-500 dark:text-gray-400">{r.created_at?.slice(0, 16)}</td>
                <td className="px-4 py-3 text-xs text-gray-400 max-w-[150px] truncate">{r.admin_notes || '-'}</td>
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

export default MyRequestsTab;
