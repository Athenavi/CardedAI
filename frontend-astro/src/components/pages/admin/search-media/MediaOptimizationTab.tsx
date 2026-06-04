'use client';

import React, {useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {EmptyState, Modal} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import {useConfirm} from '@/components/ui/confirm-provider';
import {useToast} from '@/components/ui/toast-provider';
import {ChevronLeft, ChevronRight, Edit3, Plus, Trash2, Zap} from 'lucide-react';
import {MediaOptimization, Pagination} from './shared';
import type {ApiResponse} from '@/lib/api/base-types';
const MediaOptimizationTab: React.FC = () => {
  const confirm = useConfirm();
  const toast = useToast();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({media_id: '', webp_url: '', cdn_url: '', optimization_status: 'pending'});

  const {data, isLoading} = useQuery({
    queryKey: ['media-optimization', page, statusFilter],
    queryFn: () => apiClient.get('/search/management/media-optimization', {
      page,
      per_page: 15,
      status: statusFilter || undefined
    }),
  });
  const items: MediaOptimization[] = data?.data?.media_optimizations || [];
  const pagination: Pagination | undefined = data?.data?.pagination;

  const createMut = useMutation({
    mutationFn: (d: any) => apiClient.post('/search/management/media-optimization', d),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['media-optimization']});
        setShowForm(false);
      } else toast.error(r.error || '操作失败');
    },
  });
  const updateMut = useMutation({
    mutationFn: ({id, ...d}: any) => apiClient.put(`/search/management/media-optimization/${id}`, d),
    onSuccess: () => qc.invalidateQueries({queryKey: ['media-optimization']}),
  });
  const deleteMut = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/search/management/media-optimization/${id}`),
    onSuccess: () => qc.invalidateQueries({queryKey: ['media-optimization']}),
  });

  const submit = () => {
    if (!form.media_id) {
      toast.error('请填写媒体ID');
      return;
    }
    createMut.mutate({...form, media_id: parseInt(form.media_id)});
  };

  const statusColors: Record<string, string> = {
    completed: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
    processing: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
    pending: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400',
    failed: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400',
  };
  const statusLabels: Record<string, string> = {
    completed: '已完成', processing: '处理中', pending: '等待中', failed: '失败',
  };

  return (
    <>
      <div className="flex items-center justify-between mb-4">
        <select value={statusFilter} onChange={e => {
          setStatusFilter(e.target.value);
          setPage(1);
        }}
                className="px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white">
          <option value="">全部状态</option>
          <option value="pending">等待中</option>
          <option value="processing">处理中</option>
          <option value="completed">已完成</option>
          <option value="failed">失败</option>
        </select>
        <button onClick={() => {
          setForm({media_id: '', webp_url: '', cdn_url: '', optimization_status: 'pending'});
          setShowForm(true);
        }}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-xl flex items-center gap-1.5">
          <Plus className="w-4 h-4"/>新建优化记录
        </button>
      </div>
      {isLoading ? <div className="animate-pulse space-y-2">{[1, 2, 3].map(i => <div key={i}
                                                                                     className="h-14 bg-gray-100 dark:bg-gray-800 rounded-xl"/>)}</div> :
        items.length === 0 ? <EmptyState icon={Zap} title="暂无媒体优化记录" desc="媒体优化配置将在此显示"/> :
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
              <tr className="border-b border-gray-100 dark:border-gray-800">
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">ID</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">媒体ID</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">WebP URL</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">CDN URL</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">状态</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">多尺寸</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">操作</th>
              </tr>
              </thead>
              <tbody>{items.map(m => (
                <tr key={m.id}
                    className="border-b border-gray-50 dark:border-gray-800/50 hover:bg-gray-50 dark:hover:bg-gray-800/30">
                  <td className="py-3 px-4 font-mono text-xs">#{m.id}</td>
                  <td className="py-3 px-4 font-medium text-gray-900 dark:text-white">媒体#{m.media_id}</td>
                  <td className="py-3 px-4 text-xs">
                    {m.webp_url ? <a href={m.webp_url} target="_blank" rel="noopener"
                                     className="text-blue-500 hover:underline truncate max-w-[120px] inline-block">查看</a> : '—'}
                  </td>
                  <td className="py-3 px-4 text-xs">
                    {m.cdn_url ? <a href={m.cdn_url} target="_blank" rel="noopener"
                                    className="text-blue-500 hover:underline truncate max-w-[120px] inline-block">查看</a> : '—'}
                  </td>
                  <td className="py-3 px-4">
                 <span
                   className={`px-2 py-0.5 text-[10px] rounded-full font-medium ${statusColors[m.optimization_status] || 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'}`}>
                   {statusLabels[m.optimization_status] || m.optimization_status}
                 </span>
                  </td>
                  <td className="py-3 px-4 text-xs text-gray-500 dark:text-gray-400">{m.sizes_json ? '有' : '—'}</td>
                  <td className="py-3 px-4 text-right">
                    <button onClick={() => {
                      const url = prompt('WebP URL:', m.webp_url || '');
                      if (url !== null) updateMut.mutate({id: m.id, webp_url: url});
                    }}
                            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-400 mr-1">
                      <Edit3
                      className="w-3.5 h-3.5"/></button>
                    <button onClick={async () => {
                      if (await confirm({message: '确定删除？', variant: 'danger'})) deleteMut.mutate(m.id);
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
      <Modal open={showForm} onClose={() => setShowForm(false)} title="新建媒体优化记录">
        <div className="mb-3">
          <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">媒体 ID *</label>
          <input type="number" value={form.media_id} onChange={e => setForm({...form, media_id: e.target.value})}
                 placeholder="媒体ID"
                 className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white placeholder-gray-400"/>
        </div>
        <div className="mb-3">
          <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">WebP URL</label>
          <input value={form.webp_url} onChange={e => setForm({...form, webp_url: e.target.value})}
                 placeholder="WebP 图片URL"
                 className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white placeholder-gray-400"/>
        </div>
        <div className="mb-3">
          <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">CDN URL</label>
          <input value={form.cdn_url} onChange={e => setForm({...form, cdn_url: e.target.value})} placeholder="CDN URL"
                 className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white placeholder-gray-400"/>
        </div>
        <div className="flex justify-end gap-2 mt-4">
          <button onClick={() => setShowForm(false)}
                  className="px-4 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-300">取消
          </button>
          <button onClick={submit}
                  className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg">创建
          </button>
        </div>
      </Modal>
    </>
  );
};

export default MediaOptimizationTab;
