'use client';

import React, {useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {EmptyState} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import {useConfirm} from '@/components/ui/confirm-provider';
import {useToast} from '@/components/ui/toast-provider';
import {CheckCircle, ChevronLeft, ChevronRight, Plus, RefreshCw, Search, Trash2, XCircle} from 'lucide-react';
import {SearchIndex, Pagination} from './shared';
import type {ApiResponse} from '@/lib/api/base-types';
const SearchIndexTab: React.FC = () => {
  const confirm = useConfirm();
  const toast = useToast();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [indexedFilter, setIndexedFilter] = useState('');
  const [reindexArticleId, setReindexArticleId] = useState('');

  const {data, isLoading} = useQuery({
    queryKey: ['search-index', page, indexedFilter],
    queryFn: () => apiClient.get('/search/management/search-index', {
      page, per_page: 15,
      indexed: indexedFilter !== '' ? indexedFilter === 'true' : undefined,
    }),
  });
  const items: SearchIndex[] = data?.data?.search_indexes || [];
  const pagination: Pagination | undefined = data?.data?.pagination;

  const createMut = useMutation({
    mutationFn: (d: any) => apiClient.post('/search/management/search-index', d),
    onSuccess: (r: ApiResponse) => {
      if (r.success) qc.invalidateQueries({queryKey: ['search-index']}); else toast.error(r.error || '操作失败');
    },
  });
  const updateMut = useMutation({
    mutationFn: ({id, ...d}: any) => apiClient.put(`/search/management/search-index/${id}`, d),
    onSuccess: () => qc.invalidateQueries({queryKey: ['search-index']}),
  });
  const deleteMut = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/search/management/search-index/${id}`),
    onSuccess: () => qc.invalidateQueries({queryKey: ['search-index']}),
  });
  const batchReindexMut = useMutation({
    mutationFn: (articleIds?: number[]) => apiClient.post('/search/management/search-index/batch-reindex', {article_ids: articleIds}),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['search-index']});
        toast.success(r.message || '重新索引已触发');
      } else toast.error(r.error || '操作失败');
    },
  });

  return (
    <>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <select value={indexedFilter} onChange={e => {
            setIndexedFilter(e.target.value);
            setPage(1);
          }}
                  className="px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white">
            <option value="">全部状态</option>
            <option value="true">已索引</option>
            <option value="false">未索引</option>
          </select>
          <div className="flex items-center gap-1">
            <input value={reindexArticleId} onChange={e => setReindexArticleId(e.target.value)}
                   placeholder="文章ID" type="number"
                   className="px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white w-28"/>
            <button onClick={() => {
              const ids = reindexArticleId ? [parseInt(reindexArticleId)] : undefined;
              batchReindexMut.mutate(ids);
            }} disabled={batchReindexMut.isPending}
                    className="px-3 py-2 bg-yellow-500 hover:bg-yellow-600 text-white text-sm rounded-lg flex items-center gap-1 disabled:opacity-50">
              <RefreshCw className={`w-4 h-4 ${batchReindexMut.isPending ? 'animate-spin' : ''}`}/>重建索引
            </button>
          </div>
        </div>
        <button onClick={() => {
          const id = prompt('输入文章ID:');
          if (id) createMut.mutate({article_id: parseInt(id)});
        }} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-xl flex items-center gap-1.5">
          <Plus className="w-4 h-4"/>添加索引
        </button>
      </div>
      {isLoading ? <div className="animate-pulse space-y-2">{[1, 2, 3].map(i => <div key={i}
                                                                                     className="h-14 bg-gray-100 dark:bg-gray-800 rounded-xl"/>)}</div> :
        items.length === 0 ? <EmptyState icon={Search} title="暂无搜索索引" desc="文章索引状态将在此显示"/> :
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
              <tr className="border-b border-gray-100 dark:border-gray-800">
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">ID</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">文章ID</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">索引状态</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">索引哈希</th>
                <th
                  className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">最后索引时间
                </th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">操作</th>
              </tr>
              </thead>
              <tbody>{items.map(s => (
                <tr key={s.id}
                    className="border-b border-gray-50 dark:border-gray-800/50 hover:bg-gray-50 dark:hover:bg-gray-800/30">
                  <td className="py-3 px-4 font-mono text-xs">#{s.id}</td>
                  <td className="py-3 px-4 font-medium text-gray-900 dark:text-white">文章#{s.article_id}</td>
                  <td className="py-3 px-4">
                 <span
                   className={`flex items-center gap-1 text-xs ${s.indexed ? 'text-green-600 dark:text-green-400' : 'text-gray-400'}`}>
                   {s.indexed ? <CheckCircle className="w-3.5 h-3.5"/> : <XCircle className="w-3.5 h-3.5"/>}
                   {s.indexed ? '已索引' : '未索引'}
                 </span>
                  </td>
                  <td
                    className="py-3 px-4 text-xs font-mono text-gray-500 dark:text-gray-400">{s.index_hash ? s.index_hash.substring(0, 12) + '...' : '—'}</td>
                  <td
                    className="py-3 px-4 text-xs text-gray-500 dark:text-gray-400">{s.last_indexed_at ? new Date(s.last_indexed_at).toLocaleString('zh-CN') : '—'}</td>
                  <td className="py-3 px-4 text-right">
                    <button onClick={() => updateMut.mutate({id: s.id, indexed: !s.indexed})}
                            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-400 mr-1"
                            title="切换索引状态">
                      <RefreshCw className="w-3.5 h-3.5"/>
                    </button>
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

export default SearchIndexTab;
