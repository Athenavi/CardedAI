'use client';

import React, {useEffect, useMemo, useRef, useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {useDebounce} from '@/lib/hooks';
import {apiClient} from '@/lib/api/base-client';
import {getFullMediaUrl} from '@/lib/utils';
import {useConfirm} from '@/components/ui/confirm-provider';
import {
  Archive,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock,
  Crown,
  Edit,
  ExternalLink,
  Eye,
  EyeOff,
  FileText,
  LayoutGrid,
  List,
  MoreHorizontal,
  Plus,
  RefreshCw,
  Search,
  Trash2,
  TrendingUp,
  X
} from 'lucide-react';

const STATUS_OPTIONS = [
    {value: '', label: '全部', icon: FileText, color: 'gray'},
    {value: 'published', label: '已发布', icon: CheckCircle2, color: 'green'},
    {value: 'draft', label: '草稿', icon: Clock, color: 'amber'},
    {value: 'archived', label: '已归档', icon: Archive, color: 'gray'},
] as const;

/* ── Article Row Skeleton ── */
const ArticleSkeleton = () => (
    <tr className="animate-pulse">
        <td className="px-5 py-4">
            <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded-lg"/>
                <div className="space-y-2">
                    <div className="h-4 w-40 bg-gray-200 dark:bg-gray-700 rounded"/>
                    <div className="h-3 w-24 bg-gray-100 dark:bg-gray-800 rounded"/>
                </div>
            </div>
        </td>
        <td className="px-5 py-4 hidden sm:table-cell">
            <div className="h-5 w-14 bg-gray-200 dark:bg-gray-700 rounded-full"/>
        </td>
        <td className="px-5 py-4 hidden md:table-cell">
            <div className="h-4 w-12 bg-gray-100 dark:bg-gray-800 rounded"/>
        </td>
        <td className="px-5 py-4 hidden lg:table-cell">
            <div className="h-4 w-16 bg-gray-100 dark:bg-gray-800 rounded"/>
        </td>
        <td className="px-5 py-4">
            <div className="flex justify-end gap-1">
                <div className="w-8 h-8 bg-gray-100 dark:bg-gray-800 rounded-lg"/>
                <div className="w-8 h-8 bg-gray-100 dark:bg-gray-800 rounded-lg"/>
                <div className="w-8 h-8 bg-gray-100 dark:bg-gray-800 rounded-lg"/>
            </div>
        </td>
    </tr>
);

/* ── Status Badge ── */
const StatusBadge: React.FC<{ status: string | number }> = ({status}) => {
    const config = useMemo(() => {
        const s = String(status);
        if (s === 'published' || s === '1') return {
            label: '已发布',
            bg: 'bg-emerald-50 dark:bg-emerald-900/20',
            text: 'text-emerald-700 dark:text-emerald-400',
            dot: 'bg-emerald-500'
        };
        if (s === 'deleted') return {
            label: '已删除',
            bg: 'bg-red-50 dark:bg-red-900/20',
            text: 'text-red-700 dark:text-red-400',
            dot: 'bg-red-500'
        };
        return {
            label: '草稿',
            bg: 'bg-amber-50 dark:bg-amber-900/20',
            text: 'text-amber-700 dark:text-amber-400',
            dot: 'bg-amber-500'
        };
    }, [status]);
    return (
        <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full ${config.bg} ${config.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`}/>{config.label}
    </span>
    );
};

/* ── Article Actions Menu ── */
const ArticleActions: React.FC<{ article: any; onEdit: () => void; onDelete: () => void }> = ({
                                                                                                  article,
                                                                                                  onEdit,
                                                                                                  onDelete
                                                                                              }) => {
    const [open, setOpen] = useState(false);
    const ref = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!open) return;
        const handler = (e: MouseEvent) => {
            if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
        };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, [open]);

    return (
        <div className="relative" ref={ref}>
            <button onClick={() => setOpen(!open)}
                    className="p-2 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                <MoreHorizontal className="w-4 h-4"/>
            </button>
            {open && (
                <div
                    className="absolute right-0 top-full mt-1 z-50 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 p-1.5 min-w-[160px]">
                    <a href={`/my/posts/edit?id=${article.id}`} onClick={() => setOpen(false)}
                       className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                        <Edit className="w-4 h-4 text-gray-400"/>编辑文章
                    </a>
                    <a href={`/view?slug=${article.slug}`} target="_blank" rel="noopener noreferrer"
                       onClick={() => setOpen(false)}
                       className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                        <ExternalLink className="w-4 h-4 text-gray-400"/>查看文章
                    </a>
                    <div className="h-px bg-gray-100 dark:bg-gray-700 my-1"/>
                    <button onClick={() => {
                        setOpen(false);
                        onDelete();
                    }}
                            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors">
                        <Trash2 className="w-4 h-4"/>删除文章
                    </button>
                </div>
            )}
        </div>
    );
};

function ArticlesInner() {
  const confirm = useConfirm();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState('');
  const [status, setStatus] = useState('');
    const [viewMode, setViewMode] = useState<'table' | 'grid'>('table');
  const debouncedSearch = useDebounce(searchInput, 400);

  const prevFilters = useRef('');
  useEffect(() => {
    const f = `${status}-${debouncedSearch}`;
    if (prevFilters.current && prevFilters.current !== f) setPage(1);
    prevFilters.current = f;
  }, [status, debouncedSearch]);

    const {data, isLoading, refetch} = useQuery({
    queryKey: ['admin-articles', page, status, debouncedSearch],
    queryFn: async () => {
      const params: Record<string, any> = {page, per_page: 15};
      if (status) params.status = status;
      if (debouncedSearch) params.search = debouncedSearch;
      const res = await apiClient.get('/api/v2/dashboard/blog-management/articles', params);
      if (!res.success || !res.data) return {articles: [], total: 0};
      const articles = Array.isArray(res.data) ? res.data : [];
      const pagination = (res as any).pagination || {};
      const total = pagination.total || articles.length;
      return {articles, total};
    },
  });

  const delMut = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/api/v2/articles/${id}`),
    onSuccess: () => qc.invalidateQueries({queryKey: ['admin-articles']}),
  });

  const articles = data?.articles || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / 15);

    // Stats
    const stats = useMemo(() => {
      const published = articles.filter((a) => a.status === 'published' || a.status === 1).length;
      const drafts = articles.filter((a) => a.status !== 'published' && a.status !== 1 && a.status !== 'deleted').length;
      const totalViews = articles.reduce((sum, a) => sum + (a.views || 0), 0);
        return {published, drafts, totalViews};
    }, [articles]);

  const renderPagination = () => {
    if (totalPages <= 1) return null;
    const pages: (number | string)[] = [];
    const delta = 2, left = Math.max(2, page - delta), right = Math.min(totalPages - 1, page + delta);
    pages.push(1);
    if (left > 2) pages.push('...');
    for (let i = left; i <= right; i++) pages.push(i);
    if (right < totalPages - 1) pages.push('...');
    if (totalPages > 1) pages.push(totalPages);
    return (
        <div className="flex items-center justify-between px-5 py-4 border-t border-gray-100 dark:border-gray-800">
            <span className="text-xs text-gray-400">第 {page} / {totalPages} 页</span>
            <div className="flex items-center gap-1.5">
          <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}
                  className="p-2 rounded-lg border border-gray-200 dark:border-gray-700 disabled:opacity-30 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
            <ChevronLeft className="w-4 h-4"/>
          </button>
          {pages.map((p, i) =>
              p === '...' ? <span key={`e-${i}`} className="px-2 text-gray-400 text-sm">…</span> :
                  <button key={p} onClick={() => setPage(p as number)}
                          className={`min-w-[36px] h-9 rounded-lg text-sm font-medium transition-all ${
                              p === page
                                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                                  : 'border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                          }`}>{p}</button>
          )}
          <button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}
                  className="p-2 rounded-lg border border-gray-200 dark:border-gray-700 disabled:opacity-30 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
            <ChevronRight className="w-4 h-4"/>
          </button>
        </div>
        </div>
    );
  };

  return (
      <AdminShell title="文章管理" actions={
          <div className="flex items-center gap-2">
              <button onClick={() => refetch()}
                      className="p-2 rounded-lg border border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                      title="刷新">
                  <RefreshCw className="w-4 h-4"/>
              </button>
              <a href="/admin/editor"
                 className="flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white text-sm font-medium rounded-xl shadow-lg shadow-blue-500/20 hover:shadow-blue-500/30 transition-all">
                  <Plus className="w-4 h-4"/>新建文章
              </a>
          </div>
      }>
          {/* Stats Cards */}
          <div className="grid grid-cols-3 gap-3 mb-6">
              {[
                  {
                      label: '已发布',
                      value: stats.published,
                      icon: CheckCircle2,
                      color: 'from-emerald-500 to-teal-500',
                      bg: 'bg-emerald-50 dark:bg-emerald-900/20',
                      text: 'text-emerald-600 dark:text-emerald-400'
                  },
                  {
                      label: '草稿',
                      value: stats.drafts,
                      icon: Clock,
                      color: 'from-amber-500 to-orange-500',
                      bg: 'bg-amber-50 dark:bg-amber-900/20',
                      text: 'text-amber-600 dark:text-amber-400'
                  },
                  {
                      label: '总浏览',
                      value: stats.totalViews.toLocaleString(),
                      icon: TrendingUp,
                      color: 'from-blue-500 to-indigo-500',
                      bg: 'bg-blue-50 dark:bg-blue-900/20',
                      text: 'text-blue-600 dark:text-blue-400'
                  },
              ].map(s => (
                  <div key={s.label} className={`${s.bg} rounded-xl p-4 border border-gray-100 dark:border-gray-800`}>
                      <div className="flex items-center justify-between mb-2">
                          <span className={`text-xs font-semibold ${s.text} uppercase tracking-wider`}>{s.label}</span>
                          <div
                              className={`w-8 h-8 rounded-lg bg-gradient-to-br ${s.color} flex items-center justify-center`}>
                              <s.icon className="w-4 h-4 text-white"/>
                          </div>
                      </div>
                      <div className="text-2xl font-bold text-gray-900 dark:text-white">{s.value}</div>
                  </div>
              ))}
          </div>

          {/* Filters */}
          <div className="flex flex-wrap items-center gap-3 mb-4">
              <div className="relative flex-1 min-w-[200px]">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
                  <input type="text" value={searchInput} onChange={e => setSearchInput(e.target.value)}
                         placeholder="搜索文章标题、标签..."
                         className="w-full pl-10 pr-10 py-2.5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 dark:text-white transition-all"/>
                  {searchInput && (
                      <button onClick={() => setSearchInput('')}
                              className="absolute right-3 top-1/2 -translate-y-1/2 p-0.5 text-gray-400 hover:text-gray-600 transition-colors">
                          <X className="w-4 h-4"/>
                      </button>
                  )}
              </div>
              <div
                  className="flex gap-1 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl p-1">
                  {STATUS_OPTIONS.map(opt => (
                      <button key={opt.value} onClick={() => setStatus(opt.value)}
                              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                                  status === opt.value
                                      ? 'bg-blue-600 text-white shadow-sm'
                                      : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                              }`}>
                          <opt.icon className="w-3.5 h-3.5"/>
                          {opt.label}
                      </button>
                  ))}
              </div>
              <div
                  className="flex items-center gap-1 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl p-1">
                  <button onClick={() => setViewMode('table')}
                          className={`p-1.5 rounded-lg transition-colors ${viewMode === 'table' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600' : 'text-gray-400 hover:text-gray-600'}`}>
                      <List className="w-4 h-4"/>
                  </button>
                  <button onClick={() => setViewMode('grid')}
                          className={`p-1.5 rounded-lg transition-colors ${viewMode === 'grid' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600' : 'text-gray-400 hover:text-gray-600'}`}>
                      <LayoutGrid className="w-4 h-4"/>
                  </button>
              </div>
              <span className="text-xs text-gray-400 ml-auto">共 {total} 篇</span>
          </div>

          {/* Articles Table/Grid */}
          <div
              className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 overflow-hidden shadow-sm">
              {isLoading ? (
                  viewMode === 'table' ? (
                      <table className="w-full">
                          <thead
                              className="bg-gray-50/80 dark:bg-gray-800/50 border-b border-gray-100 dark:border-gray-800">
                          <tr>
                            <th
                              className="px-5 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">文章
                            </th>
                            <th
                              className="px-5 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden sm:table-cell">状态
                            </th>
                            <th
                              className="px-5 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden md:table-cell">浏览
                            </th>
                            <th
                              className="px-5 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden lg:table-cell">日期
                            </th>
                            <th
                              className="px-5 py-3.5 text-right text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">操作
                            </th>
                          </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-50 dark:divide-gray-800/50">
                          {[1, 2, 3, 4, 5].map(i => <ArticleSkeleton key={i}/>)}
                          </tbody>
                      </table>
                  ) : (
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
                          {[1, 2, 3, 4, 5, 6].map(i => (
                              <div key={i}
                                   className="animate-pulse rounded-xl border border-gray-100 dark:border-gray-800 p-4">
                                  <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded-lg mb-3"/>
                                  <div className="h-4 w-3/4 bg-gray-200 dark:bg-gray-700 rounded mb-2"/>
                                  <div className="h-3 w-1/2 bg-gray-100 dark:bg-gray-800 rounded"/>
                              </div>
                          ))}
                      </div>
                  )
              ) : articles.length === 0 ? (
                  <div className="p-16 text-center">
                      <div
                          className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-2xl flex items-center justify-center mx-auto mb-4">
                          <FileText className="w-8 h-8 text-gray-300 dark:text-gray-600"/>
                      </div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                          {debouncedSearch ? '未找到匹配的文章' : '暂无文章'}
                      </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
                          {debouncedSearch ? '尝试使用不同的关键词搜索' : '创建你的第一篇文章开始写作'}
                      </p>
                      {!debouncedSearch && (
                          <a href="/admin/editor"
                             className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white text-sm rounded-xl hover:bg-blue-700 transition-colors">
                              <Plus className="w-4 h-4"/>新建文章
                          </a>
                      )}
                  </div>
              ) : viewMode === 'table' ? (
                  <>
                      <table className="w-full">
                          <thead
                              className="bg-gray-50/80 dark:bg-gray-800/50 border-b border-gray-100 dark:border-gray-800">
                          <tr>
                            <th
                              className="px-5 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">文章
                            </th>
                            <th
                              className="px-5 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden sm:table-cell">状态
                            </th>
                            <th
                              className="px-5 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden md:table-cell">浏览
                            </th>
                            <th
                              className="px-5 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden lg:table-cell">日期
                            </th>
                            <th
                              className="px-5 py-3.5 text-right text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">操作
                            </th>
                          </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-50 dark:divide-gray-800/50">
                          {articles.map((a) => (
                              <tr key={a.id}
                                  className="group hover:bg-gray-50/80 dark:hover:bg-gray-800/30 transition-colors">
                    <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                            {a.cover_image ? (
                              <img src={getFullMediaUrl(a.cover_image)} alt=""
                                     className="w-10 h-10 rounded-lg object-cover border border-gray-100 dark:border-gray-800"/>
                            ) : (
                                <div
                                    className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-100 dark:border-blue-800/30 flex items-center justify-center">
                                    <FileText className="w-4 h-4 text-blue-400"/>
                                </div>
                            )}
                            <div className="min-w-0">
                                <p className="font-medium text-gray-900 dark:text-white text-sm line-clamp-1 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">{a.title}</p>
                                <div className="flex items-center gap-2 mt-0.5">
                                    {a.category_name &&
                                        <span className="text-xs text-gray-400">{a.category_name}</span>}
                                    {a.is_vip_only && <Crown className="w-3 h-3 text-amber-500"/>}
                                    {a.hidden && <EyeOff className="w-3 h-3 text-gray-400"/>}
                                </div>
                            </div>
                        </div>
                    </td>
                                  <td className="px-5 py-4 hidden sm:table-cell"><StatusBadge status={a.status}/></td>
                                  <td className="px-5 py-4 hidden md:table-cell">
                                    <div className="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400">
                                          <Eye className="w-3.5 h-3.5 text-gray-400"/>{a.views || 0}
                                      </div>
                                  </td>
                                  <td className="px-5 py-4 hidden lg:table-cell">
                                      <span
                                          className="text-xs text-gray-400">{a.created_at ? new Date(a.created_at).toLocaleDateString('zh-CN') : ''}</span>
                    </td>
                    <td className="px-5 py-4 text-right">
                        <ArticleActions
                            article={a}
                            onEdit={() => window.location.href = `/my/posts/edit?id=${a.id}`}
                            onDelete={async () => {
                              if (await confirm({
                                message: '确认删除此文章？此操作不可恢复。',
                                variant: 'danger'
                              })) delMut.mutate(a.id);
                            }}
                        />
                    </td>
                  </tr>
                          ))}
                          </tbody>
                      </table>
                      {renderPagination()}
                  </>
              ) : (
                  <div className="p-4">
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {articles.map((a) => (
                              <div key={a.id}
                                   className="group rounded-xl border border-gray-100 dark:border-gray-800 hover:border-blue-200 dark:hover:border-blue-800 hover:shadow-md transition-all overflow-hidden">
                                  {a.cover_image ? (
                                    <div className="h-36 overflow-hidden"><img src={getFullMediaUrl(a.cover_image)}
                                                                               alt=""
                                                                                 className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"/>
                                      </div>
                                  ) : (
                                      <div
                                          className="h-36 bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-blue-900/20 dark:to-indigo-900/20 flex items-center justify-center">
                                          <FileText className="w-10 h-10 text-blue-200 dark:text-blue-800"/>
                                      </div>
                                  )}
                                  <div className="p-4">
                                      <div className="flex items-start justify-between gap-2 mb-2">
                                          <h3 className="font-medium text-gray-900 dark:text-white text-sm line-clamp-2 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">{a.title}</h3>
                                          <StatusBadge status={a.status}/>
                                      </div>
                                      <p className="text-xs text-gray-400 line-clamp-2 mb-3">{a.excerpt || '暂无摘要'}</p>
                                      <div className="flex items-center justify-between">
                                          <div className="flex items-center gap-3 text-xs text-gray-400">
                                              <span className="flex items-center gap-1"><Eye
                                                  className="w-3 h-3"/>{a.views || 0}</span>
                                              <span>{a.created_at ? new Date(a.created_at).toLocaleDateString('zh-CN') : ''}</span>
                                          </div>
                                          <div className="flex items-center gap-1">
                                              <a href={`/my/posts/edit?id=${a.id}`}
                                                 className="p-1.5 rounded-lg text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors">
                                                  <Edit className="w-3.5 h-3.5"/>
                                              </a>
                                              <a href={`/view?slug=${a.slug}`} target="_blank"
                                                 className="p-1.5 rounded-lg text-gray-400 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors">
                                                  <ExternalLink className="w-3.5 h-3.5"/>
                                              </a>
                                          </div>
                                      </div>
                                  </div>
                              </div>
                          ))}
                      </div>
                      {renderPagination()}
                  </div>
              )}
          </div>
      </AdminShell>
  );
}

export default function AdminArticles() {
  return <AuthGuard><QueryProvider><ArticlesInner /></QueryProvider></AuthGuard>;
}
