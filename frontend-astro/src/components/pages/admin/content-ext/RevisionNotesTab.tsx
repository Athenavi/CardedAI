'use client';

import React, {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {EmptyState} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import {ChevronLeft, ChevronRight, MessageSquare} from 'lucide-react';
import {RevisionNote, Pagination} from './shared';

const RevisionNotesTab: React.FC = () => {
  const [page, setPage] = useState(1);
  const [revisionId, setRevisionId] = useState('');
  const {data, isLoading} = useQuery({
    queryKey: ['revision-notes', page, revisionId],
    queryFn: () => apiClient.get('/cms/management/revision-notes', {
      page,
      per_page: 15,
      revision_id: revisionId || undefined
    }),
  });
  const items: RevisionNote[] = data?.data?.revision_notes || [];
  const pagination: Pagination | undefined = data?.data?.pagination;

  return (
    <>
      <div className="flex items-center gap-2 mb-4">
        <input value={revisionId} onChange={e => {
          setRevisionId(e.target.value);
          setPage(1);
        }}
               placeholder="按修订ID筛选" type="number"
               className="px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white w-40"/>
      </div>
      {isLoading ? <div className="animate-pulse space-y-2">{[1, 2, 3].map(i => <div key={i}
                                                                                     className="h-16 bg-gray-100 dark:bg-gray-800 rounded-xl"/>)}</div> :
        items.length === 0 ? <EmptyState icon={MessageSquare} title="暂无修订注释" desc="文章修订时的注释将在此显示"/> :
          <div className="space-y-2">
            {items.map(n => (
              <div key={n.id}
                   className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-100 dark:border-gray-700/50">
                <div className="flex items-center gap-2 mb-2">
                  <span
                    className="text-[10px] bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 px-1.5 py-0.5 rounded font-mono">修订#{n.revision_id}</span>
                  <span
                    className="text-[10px] bg-gray-200 dark:bg-gray-700 px-1.5 py-0.5 rounded text-gray-600 dark:text-gray-300 font-mono">用户#{n.user_id}</span>
                  <span
                    className="text-[10px] text-gray-400 ml-auto">{n.created_at ? new Date(n.created_at).toLocaleString('zh-CN') : ''}</span>
                </div>
                <p className="text-sm text-gray-700 dark:text-gray-300">{n.note_content}</p>
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

export default RevisionNotesTab;
