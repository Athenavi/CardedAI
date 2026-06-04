'use client';

import {useState, useRef} from 'react';
import {useQuery, useMutation, useQueryClient} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {apiClient} from '@/lib/api/base-client';
import {
  ChevronLeft,
  ChevronRight,
  Plus,
  Trash2,
  RefreshCw,
  AlertTriangle,
  Search,
  Pencil,
  Upload,
  X
} from 'lucide-react';
import {useConfirm} from '@/components/ui/confirm-provider';
import {useToast} from '@/components/ui/toast-provider';

const ACTION_LABELS: Record<string, string> = {block: '拦截', replace: '替换', warn: '警告'};
const ACTION_COLORS: Record<string, string> = {
  block: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  replace: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  warn: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
};
const LEVEL_NAMES = ['', '低危', '中危', '高危'];

function SensitiveWordsInner() {
  const confirm = useConfirm();
  const toast = useToast();
  const qc = useQueryClient();
  // 分页 & 筛选
  const [page, setPage] = useState(1);
  const [perPage] = useState(20);
  const [keyword, setKeyword] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [levelFilter, setLevelFilter] = useState<number | ''>('');
  const [actionFilter, setActionFilter] = useState('');

  // 新增/编辑 form
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [formWord, setFormWord] = useState('');
  const [formLevel, setFormLevel] = useState<number>(1);
  const [formAction, setFormAction] = useState('replace');
  const [formRepl, setFormRepl] = useState('');
  const [formCategory, setFormCategory] = useState('');

  // 批量导入
  const [batchOpen, setBatchOpen] = useState(false);
  const [batchText, setBatchText] = useState('');

  // 按关键词搜索时重置到第一页
  const prevKwRef = useRef('');
  if (prevKwRef.current !== keyword) {
    prevKwRef.current = keyword;
    if (page !== 1) setPage(1);
  }

  const queryKey = ['admin-sensitive-words', page, keyword, levelFilter, actionFilter];
  const {data, isLoading} = useQuery({
    queryKey,
    staleTime: 0,
    gcTime: 0,
    refetchOnMount: true,
    queryFn: async () => {
      const params: Record<string, any> = {page, per_page: perPage};
      if (keyword) params.keyword = keyword;
      if (levelFilter !== '') params.level = levelFilter;
      if (actionFilter) params.action = actionFilter;
      const res = await apiClient.get('/api/v2/security/sensitive-words/', params);
      if (res.success && res.data?.items) return res.data;
      return {items: [], total: 0, page: 1, total_pages: 1};
    },
  });

  const {data: stats} = useQuery({
    queryKey: ['admin-sensitive-stats'],
    staleTime: 0,
    gcTime: 0,
    queryFn: async () => {
      const res = await apiClient.get('/api/v2/security/sensitive-words/statistics');
      return res.success && res.data ? res.data : {};
    },
  });

  const items = data?.items || [];
  const total = data?.total || 0;
  const totalPages = data?.total_pages || 1;

  // 创建 / 更新
  const saveMut = useMutation({
    mutationFn: async () => {
      const body = {
        word: formWord,
        level: formLevel,
        action: formAction,
        replacement: formAction === 'replace' ? formRepl : null,
        category: formCategory || null,
      };
      if (editing) {
        const res = await apiClient.put(`/api/v2/security/sensitive-words/${editing.id}`, body);
        return res;
      } else {
        const res = await apiClient.post('/api/v2/security/sensitive-words/', body);
        return res;
      }
    },
    onSuccess: () => {
      qc.invalidateQueries({queryKey: ['admin-sensitive-words']});
      qc.invalidateQueries({queryKey: ['admin-sensitive-stats']});
      closeForm();
    },
  });

  const delMut = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/api/v2/security/sensitive-words/${id}`),
    onSuccess: () => qc.invalidateQueries({queryKey: ['admin-sensitive-words']}),
  });

  const refreshMut = useMutation({
    mutationFn: () => apiClient.post('/api/v2/security/sensitive-words/refresh-cache'),
    onSuccess: () => toast.success('缓存已刷新'),
  });

  const batchMut = useMutation({
    mutationFn: async () => {
      const words = batchText.split('\n').map(s => s.trim()).filter(Boolean);
      const items = words.map(w => ({
        word: w,
        level: 1,
        action: 'block',
        replacement: null,
        category: null,
      }));
      const res = await apiClient.post('/api/v2/security/sensitive-words/batch-import', {items});
      return res;
    },
    onSuccess: () => {
      qc.invalidateQueries({queryKey: ['admin-sensitive-words']});
      qc.invalidateQueries({queryKey: ['admin-sensitive-stats']});
      setBatchOpen(false);
      setBatchText('');
    },
  });

  function openNew() {
    setEditing(null);
    setFormWord('');
    setFormLevel(1);
    setFormAction('replace');
    setFormRepl('');
    setFormCategory('');
    setFormOpen(true);
  }

  function openEdit(item: any) {
    setEditing(item);
    setFormWord(item.word);
    setFormLevel(item.level || 1);
    setFormAction(item.action || 'block');
    setFormRepl(item.replacement || '');
    setFormCategory(item.category || '');
    setFormOpen(true);
  }

  function closeForm() {
    setFormOpen(false);
    setEditing(null);
  }

  const renderPagination = () => {
    if (totalPages <= 1) return null;
    const pages: (number | string)[] = [];
    const delta = 2, left = Math.max(2, page - delta), right = Math.min(totalPages - 1, page + delta);
    pages.push(1);
    if (left > 2) pages.push('…');
    for (let i = left; i <= right; i++) pages.push(i);
    if (right < totalPages - 1) pages.push('…');
    if (totalPages > 1) pages.push(totalPages);
    return (
        <div className="flex items-center justify-center gap-1.5 mt-4">
          <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}
                  className="p-2 rounded-lg border border-gray-200 dark:border-gray-700 disabled:opacity-30 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
            <ChevronLeft className="w-4 h-4"/>
          </button>
          {pages.map((p, i) =>
              p === '…' ? <span key={`e-${i}`} className="px-2 text-gray-400">…</span> :
                  <button key={p} onClick={() => setPage(p as number)}
                          className={`min-w-[36px] h-9 rounded-lg text-sm font-medium transition-colors ${
                              p === page ? 'bg-blue-600 text-white' : 'border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                          }`}>{p}</button>
          )}
          <button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}
                  className="p-2 rounded-lg border border-gray-200 dark:border-gray-700 disabled:opacity-30 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
            <ChevronRight className="w-4 h-4"/>
          </button>
        </div>
    );
  };

  return (
      <AdminShell title="敏感词管理" actions={
        <div className="flex gap-2">
          <button onClick={() => refreshMut.mutate()}
                  className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 rounded-lg text-sm hover:bg-gray-50 dark:hover:bg-gray-800 flex items-center gap-1.5 transition-colors">
            <RefreshCw className="w-4 h-4"/>刷新缓存
          </button>
        </div>
      }>
        {/* 统计 */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-5 mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-8 h-8 text-orange-500"/>
            <div>
              <p className="font-bold text-gray-900 dark:text-white text-lg">{stats?.total_count ?? total} 个敏感词</p>
              <p
                className="text-xs text-gray-500 dark:text-gray-400">最后更新: {stats?.last_updated ? new Date(stats.last_updated).toLocaleString('zh-CN') : '-'}</p>
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={openNew}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-xl transition-colors flex items-center gap-1.5">
              <Plus className="w-4 h-4"/>新增
            </button>
            <button onClick={() => setBatchOpen(true)}
                    className="px-4 py-2 border border-gray-200 dark:border-gray-700 text-sm font-medium rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors flex items-center gap-1.5">
              <Upload className="w-4 h-4"/>批量导入
            </button>
          </div>
        </div>

        {/* 搜索 & 筛选 */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-4 mb-6">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex-1 min-w-[200px] relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
              <input type="text" value={searchInput} onChange={e => setSearchInput(e.target.value)}
                     placeholder="搜索敏感词…"
                     onKeyDown={e => {if (e.key === 'Enter') setKeyword(searchInput);}}
                     className="w-full pl-9 pr-3 py-2 border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"/>
            </div>
            <select value={levelFilter} onChange={e => setLevelFilter(e.target.value === '' ? '' : Number(e.target.value))}
                    className="px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white">
              <option value="">全部级别</option>
              <option value="1">低危</option>
              <option value="2">中危</option>
              <option value="3">高危</option>
            </select>
            <select value={actionFilter} onChange={e => setActionFilter(e.target.value)}
                    className="px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white">
              <option value="">全部处理</option>
              {Object.entries(ACTION_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
            <button onClick={() => { setKeyword(searchInput); }}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-xl transition-colors flex items-center gap-1.5">
              <Search className="w-4 h-4"/>搜索
            </button>
            <button onClick={() => { setSearchInput(''); setKeyword(''); setLevelFilter(''); setActionFilter(''); }}
                    className="px-3 py-2 border border-gray-200 dark:border-gray-700 text-sm rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
              重置
            </button>
          </div>
        </div>

        {/* 新增 / 编辑弹窗 */}
        {formOpen && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30" onClick={closeForm}>
              <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 w-full max-w-lg mx-4 p-6" onClick={e => e.stopPropagation()}>
                <div className="flex items-center justify-between mb-5">
                  <h3 className="font-semibold text-gray-900 dark:text-white text-lg">{editing ? '编辑敏感词' : '新增敏感词'}</h3>
                  <button onClick={closeForm} className="p-1 text-gray-400 hover:text-gray-600"><X className="w-5 h-5"/></button>
                </div>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">敏感词</label>
                    <input type="text" value={formWord} onChange={e => setFormWord(e.target.value)}
                           className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"/>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">级别</label>
                      <select value={formLevel} onChange={e => setFormLevel(Number(e.target.value))}
                              className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white">
                        <option value={1}>低危</option>
                        <option value={2}>中危</option>
                        <option value={3}>高危</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">处理方式</label>
                      <select value={formAction} onChange={e => setFormAction(e.target.value)}
                              className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white">
                        <option value="block">拦截</option>
                        <option value="replace">替换</option>
                        <option value="warn">警告</option>
                      </select>
                    </div>
                  </div>
                  {formAction === 'replace' && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">替换为</label>
                        <input type="text" value={formRepl} onChange={e => setFormRepl(e.target.value)}
                               className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"/>
                      </div>
                  )}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">分类（可选）</label>
                    <input type="text" value={formCategory} onChange={e => setFormCategory(e.target.value)}
                           placeholder="如: 政治 / 色情 / 广告"
                           className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"/>
                  </div>
                </div>
                <button onClick={() => saveMut.mutate()} disabled={!formWord.trim() || saveMut.isPending}
                        className="mt-6 w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-xl disabled:opacity-50 transition-colors">
                  {saveMut.isPending ? '保存中…' : editing ? '保存修改' : '添加'}
                </button>
              </div>
            </div>
        )}

        {/* 批量导入弹窗 */}
        {batchOpen && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30" onClick={() => setBatchOpen(false)}>
              <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 w-full max-w-lg mx-4 p-6" onClick={e => e.stopPropagation()}>
                <div className="flex items-center justify-between mb-5">
                  <h3 className="font-semibold text-gray-900 dark:text-white text-lg">批量导入</h3>
                  <button onClick={() => setBatchOpen(false)} className="p-1 text-gray-400 hover:text-gray-600"><X className="w-5 h-5"/></button>
                </div>
                <p
                  className="text-sm text-gray-500 dark:text-gray-400 mb-3">每行一个敏感词，导入时级别默认低危、处理方式拦截。</p>
                <textarea value={batchText} onChange={e => setBatchText(e.target.value)} rows={8}
                          placeholder={"敏感词1\n敏感词2\n敏感词3"}
                          className="w-full px-4 py-3 border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white resize-none"/>
                <button onClick={() => batchMut.mutate()} disabled={!batchText.trim() || batchMut.isPending}
                        className="mt-4 w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-xl disabled:opacity-50 transition-colors">
                  {batchMut.isPending ? '导入中…' : `导入 ${batchText.split('\n').filter(s => s.trim()).length} 个敏感词`}
                </button>
              </div>
            </div>
        )}

        {/* 列表 */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          {isLoading ? (
              <div className="p-12 text-center"><div className="animate-spin w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full mx-auto"/></div>
          ) : !items.length ? (
              <div className="p-12 text-center text-gray-400"><AlertTriangle className="w-10 h-10 mx-auto mb-3 opacity-50"/><p>暂无敏感词</p></div>
          ) : (
              <table className="w-full"><thead className="bg-gray-50 dark:bg-gray-800 border-b">
              <tr>
                <th
                  className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">敏感词
                </th>
                <th
                  className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase hidden sm:table-cell">级别
                </th>
                <th
                  className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">处理
                </th>
                <th
                  className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase hidden md:table-cell">分类
                </th>
                <th
                  className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase hidden md:table-cell">创建时间
                </th>
                <th
                  className="px-5 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">操作
                </th>
              </tr>
              </thead><tbody className="divide-y">
              {items.map((w) => (
                  <tr key={w.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                    <td className="px-5 py-4">
                      <span className={`px-3 py-1 rounded-lg text-sm font-mono ${
                          w.is_active === false ? 'line-through text-gray-400 dark:text-gray-600 bg-gray-100 dark:bg-gray-800' :
                              w.level >= 3 ? 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400' :
                                  w.level === 2 ? 'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400' :
                                      'bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300'
                      }`}>{w.word}</span>
                    </td>
                    <td
                      className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400 hidden sm:table-cell">{LEVEL_NAMES[w.level] || '-'}</td>
                    <td className="px-5 py-4">
                        <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${ACTION_COLORS[w.action] || ''}`}>
                          {ACTION_LABELS[w.action] || w.action}
                        </span>
                    </td>
                    <td
                      className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400 hidden md:table-cell">{w.category || '-'}</td>
                    <td className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400 hidden md:table-cell">
                      {w.created_at ? new Date(w.created_at).toLocaleString('zh-CN') : '-'}
                    </td>
                    <td className="px-5 py-4 text-right space-x-1">
                      <button onClick={() => openEdit(w)}
                              className="p-1.5 inline-block text-gray-400 hover:text-blue-600 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20">
                        <Pencil className="w-4 h-4"/>
                      </button>
                      <button onClick={async () => {
                        if (await confirm({message: '确认删除此敏感词？', variant: 'danger'})) delMut.mutate(w.id);
                      }}
                              className="p-1.5 inline-block text-gray-400 hover:text-red-600 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20">
                        <Trash2 className="w-4 h-4"/>
                      </button>
                    </td>
                  </tr>
              ))}
              </tbody></table>
          )}
        </div>

        {/* 分页 & 总数 */}
        <div className="flex items-center justify-between mt-4">
          <span className="text-xs text-gray-400">共 {total} 个敏感词</span>
          {renderPagination()}
        </div>
      </AdminShell>
  );
}

export default function AdminSensitiveWords() {
  return <AuthGuard><QueryProvider><SensitiveWordsInner/></QueryProvider></AuthGuard>;
}
