'use client';

import React, {useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {EmptyState, Modal, Pagination} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import {useToast} from '@/components/ui/toast-provider';
import {Download, Edit3, FileText, Search} from 'lucide-react';
import {ArticleSEO, Input, ScoreBadge} from './shared';
import type {ApiResponse} from '@/lib/api/base-types';
const ArticleSEOTab: React.FC = () => {
  const qc = useQueryClient();
  const toast = useToast();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<ArticleSEO | null>(null);
  const [form, setForm] = useState({
    meta_title: '', meta_description: '', focus_keyword: '', canonical_url: '',
    og_title: '', og_description: '', robots_directive: 'index,follow'
  });

  const {data, isLoading} = useQuery({
    queryKey: ['seo-batch-stats', page, search],
    queryFn: () => apiClient.get('/seo/batch/stats', {page, per_page: 15, search: search || undefined}),
  });

  const items: ArticleSEO[] = data?.data?.articles || data?.data?.items || [];
  const total: number = data?.data?.total || 0;

  const updateMut = useMutation({
    mutationFn: ({id, ...d}: any) => apiClient.post('/seo/batch/update', {article_ids: [id], ...d}),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['seo-batch-stats']});
        setShowForm(false);
      } else toast.error(r.error || '操作失败');
    },
  });

  const exportMut = useMutation({
    mutationFn: () => apiClient.post('/seo/batch/export', {}),
    onSuccess: (r: ApiResponse<{ download_url?: string }>) => {
      if (r.success && r.data?.download_url) window.open(r.data.download_url);
    },
  });

  const openEdit = (a: ArticleSEO) => {
    setEditing(a);
    setForm({
      meta_title: a.meta_title || '', meta_description: a.meta_description || '',
      focus_keyword: a.focus_keyword || '', canonical_url: a.canonical_url || '',
      og_title: a.og_title || '', og_description: a.og_description || '',
      robots_directive: a.robots_directive || 'index,follow',
    });
    setShowForm(true);
  };

  const submit = () => {
    if (!editing) return;
    updateMut.mutate({id: editing.article_id, ...form});
  };

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
                   placeholder="搜索文章..."
                   className="pl-9 pr-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm dark:text-white w-64"/>
          </div>
        </div>
        <button onClick={() => exportMut.mutate()} disabled={exportMut.isPending}
                className="flex items-center gap-1.5 px-4 py-2 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-sm rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700">
          <Download className="w-4 h-4"/> 导出 SEO 数据
        </button>
      </div>

      {isLoading ? (
        <div className="space-y-2">{[...Array(5)].map((_, i) => <div key={i}
                                                                     className="h-16 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse"/>)}</div>
      ) : items.length === 0 ? (
        <EmptyState icon={FileText} title="暂无 SEO 数据" desc="发布文章后将自动生成 SEO 元数据"/>
      ) : (
        <div
          className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
            <tr className="bg-gray-50 dark:bg-gray-800/50">
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">文章标题</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">焦点关键词</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Meta 标题</th>
              <th className="text-center px-4 py-3 font-medium text-gray-500 dark:text-gray-400">SEO 评分</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Robots</th>
              <th className="text-right px-4 py-3 font-medium text-gray-500 dark:text-gray-400">操作</th>
            </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {items.map(a => (
              <tr key={a.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/30">
                <td className="px-4 py-3">
                  <div
                    className="font-medium text-gray-900 dark:text-gray-100 max-w-[200px] truncate">{a.title || `文章#${a.article_id}`}</div>
                </td>
                <td className="px-4 py-3">
                  {a.focus_keyword ? (
                    <span
                      className="px-2 py-0.5 text-[10px] rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400">{a.focus_keyword}</span>
                  ) : <span className="text-xs text-gray-400">-</span>}
                </td>
                <td
                  className="px-4 py-3 text-xs text-gray-500 dark:text-gray-400 max-w-[200px] truncate">{a.meta_title || '-'}</td>
                <td className="px-4 py-3 text-center"><ScoreBadge score={a.seo_score}/></td>
                <td
                  className="px-4 py-3 text-xs font-mono text-gray-500 dark:text-gray-400">{a.robots_directive || 'index,follow'}</td>
                <td className="px-4 py-3 text-right">
                  <button onClick={() => openEdit(a)} className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800"
                          title="编辑 SEO">
                    <Edit3 className="w-3.5 h-3.5 text-gray-500 dark:text-gray-400"/>
                  </button>
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

      {/* Edit SEO Modal */}
      <Modal open={showForm} onClose={() => setShowForm(false)} title={`编辑 SEO - ${editing?.title || ''}`}>
        <div className="max-h-[70vh] overflow-y-auto pr-1">
          <Input label="Meta 标题" value={form.meta_title} onChange={v => setForm(f => ({...f, meta_title: v}))}
                 placeholder="建议 50-60 字符"/>
          <Input label="Meta 描述" value={form.meta_description}
                 onChange={v => setForm(f => ({...f, meta_description: v}))} placeholder="建议 150-160 字符" rows={3}/>
          <Input label="焦点关键词" value={form.focus_keyword} onChange={v => setForm(f => ({...f, focus_keyword: v}))}
                 placeholder="主要关键词"/>
          <Input label="规范链接" value={form.canonical_url} onChange={v => setForm(f => ({...f, canonical_url: v}))}
                 placeholder="https://..."/>
          <Input label="OG 标题" value={form.og_title} onChange={v => setForm(f => ({...f, og_title: v}))}
                 placeholder="社交分享标题"/>
          <Input label="OG 描述" value={form.og_description} onChange={v => setForm(f => ({...f, og_description: v}))}
                 placeholder="社交分享描述" rows={2}/>
          <div className="mb-3">
            <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">Robots 指令</label>
            <select value={form.robots_directive}
                    onChange={e => setForm(f => ({...f, robots_directive: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white">
              <option value="index,follow">index, follow</option>
              <option value="noindex,follow">noindex, follow</option>
              <option value="index,nofollow">index, nofollow</option>
              <option value="noindex,nofollow">noindex, nofollow</option>
            </select>
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-4 pt-3 border-t border-gray-100 dark:border-gray-800">
          <button onClick={() => setShowForm(false)}
                  className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg">取消
          </button>
          <button onClick={submit} disabled={updateMut.isPending}
                  className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
            {updateMut.isPending ? '保存中...' : '保存'}
          </button>
        </div>
      </Modal>
    </>
  );
};

export default ArticleSEOTab;
