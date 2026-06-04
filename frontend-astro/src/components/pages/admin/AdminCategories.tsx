'use client';

import React, {useState, useMemo, useEffect, useCallback} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {StatCard} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import {
  FolderTree,
  Plus,
  Edit3,
  Trash2,
  Search,
  X,
  ChevronDown,
  ChevronRight,
  Hash,
  FileText,
  GripVertical,
  MoreVertical,
  Eye,
  EyeOff,
  Check,
  AlertTriangle,
  LayoutGrid,
  List,
  ArrowUp,
  ArrowDown
} from 'lucide-react';

/* ── 颜色方案 ── */
const CATEGORY_COLORS = [
  {
    bg: 'bg-blue-50 dark:bg-blue-900/20',
    border: 'border-blue-200 dark:border-blue-800',
    text: 'text-blue-600 dark:text-blue-400',
    dot: 'bg-blue-500'
  },
  {
    bg: 'bg-purple-50 dark:bg-purple-900/20',
    border: 'border-purple-200 dark:border-purple-800',
    text: 'text-purple-600 dark:text-purple-400',
    dot: 'bg-purple-500'
  },
  {
    bg: 'bg-emerald-50 dark:bg-emerald-900/20',
    border: 'border-emerald-200 dark:border-emerald-800',
    text: 'text-emerald-600 dark:text-emerald-400',
    dot: 'bg-emerald-500'
  },
  {
    bg: 'bg-amber-50 dark:bg-amber-900/20',
    border: 'border-amber-200 dark:border-amber-800',
    text: 'text-amber-600 dark:text-amber-400',
    dot: 'bg-amber-500'
  },
  {
    bg: 'bg-rose-50 dark:bg-rose-900/20',
    border: 'border-rose-200 dark:border-rose-800',
    text: 'text-rose-600 dark:text-rose-400',
    dot: 'bg-rose-500'
  },
  {
    bg: 'bg-cyan-50 dark:bg-cyan-900/20',
    border: 'border-cyan-200 dark:border-cyan-800',
    text: 'text-cyan-600 dark:text-cyan-400',
    dot: 'bg-cyan-500'
  },
  {
    bg: 'bg-indigo-50 dark:bg-indigo-900/20',
    border: 'border-indigo-200 dark:border-indigo-800',
    text: 'text-indigo-600 dark:text-indigo-400',
    dot: 'bg-indigo-500'
  },
  {
    bg: 'bg-orange-50 dark:bg-orange-900/20',
    border: 'border-orange-200 dark:border-orange-800',
    text: 'text-orange-600 dark:text-orange-400',
    dot: 'bg-orange-500'
  },
];

function getColor(idx: number) {
  return CATEGORY_COLORS[idx % CATEGORY_COLORS.length];
}

/* ── 分类骨架屏 ── */
const CategorySkeleton = () => (
    <div className="space-y-3">
      {[1, 2, 3, 4, 5].map(i => (
          <div key={i}
               className="animate-pulse flex items-center gap-4 p-4 bg-white dark:bg-gray-900 rounded-xl border border-gray-100 dark:border-gray-800">
            <div className="w-5 h-5 bg-gray-200 dark:bg-gray-700 rounded"/>
            <div className="w-9 h-9 bg-gray-200 dark:bg-gray-700 rounded-xl"/>
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-32"/>
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-48"/>
            </div>
            <div className="w-16 h-6 bg-gray-200 dark:bg-gray-700 rounded-full"/>
            <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-lg"/>
          </div>
      ))}
    </div>
);

/* ── 分类行 ── */
const CategoryRow: React.FC<{
  cat: any;
  index: number;
  viewMode: 'list' | 'grid';
  onEdit: (c: any) => void;
  onDelete: (c: any) => void;
  isExpanded?: boolean;
  onToggle?: () => void;
  hasChildren?: boolean;
  depth?: number;
}> = ({cat, index, viewMode, onEdit, onDelete, isExpanded, onToggle, hasChildren, depth = 0}) => {
  const [showMenu, setShowMenu] = useState(false);
  const color = getColor(index);
  const count = cat.articles_count || cat.article_count || 0;

  if (viewMode === 'grid') {
    return (
        <div
            className="group relative bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 hover:border-gray-200 dark:hover:border-gray-700 hover:shadow-lg transition-all duration-200 overflow-hidden">
          {/* 顶部色条 */}
          <div className={`h-1.5 ${color.dot}`}/>
          <div className="p-5">
            <div className="flex items-start justify-between mb-3">
              <div className={`w-10 h-10 rounded-xl ${color.bg} flex items-center justify-center`}>
                <FolderTree className={`w-5 h-5 ${color.text}`}/>
              </div>
              <div className="relative">
                <button onClick={() => setShowMenu(!showMenu)}
                        className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 opacity-0 group-hover:opacity-100 transition-opacity">
                  <MoreVertical className="w-4 h-4"/>
                </button>
                {showMenu && (
                    <>
                      <div className="fixed inset-0 z-10" onClick={() => setShowMenu(false)}/>
                      <div
                          className="absolute right-0 top-full mt-1 z-20 w-36 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 py-1">
                        <button onClick={() => {
                          onEdit(cat);
                          setShowMenu(false);
                        }}
                                className="flex items-center gap-2 w-full px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700">
                          <Edit3 className="w-4 h-4"/>编辑
                        </button>
                        <button onClick={() => {
                          onDelete(cat);
                          setShowMenu(false);
                        }}
                                className="flex items-center gap-2 w-full px-3 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20">
                          <Trash2 className="w-4 h-4"/>删除
                        </button>
                      </div>
                    </>
                )}
              </div>
            </div>
            <h3 className="font-semibold text-gray-900 dark:text-white mb-1 truncate">{cat.name}</h3>
            {cat.slug && (
                <p className="text-xs text-gray-400 font-mono mb-3 truncate">/{cat.slug}</p>
            )}
            <div className="flex items-center justify-between pt-3 border-t border-gray-100 dark:border-gray-800">
            <span className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
              <FileText className="w-3.5 h-3.5"/>
              {count} 篇文章
            </span>
              <button onClick={() => onEdit(cat)}
                      className="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-700 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                编辑
              </button>
            </div>
          </div>
        </div>
    );
  }

  return (
      <div
          className="group flex items-center gap-3 px-5 py-3.5 hover:bg-gray-50/80 dark:hover:bg-gray-800/30 transition-colors"
          style={{paddingLeft: `${20 + depth * 24}px`}}>
        {/* 展开/折叠 */}
        {hasChildren ? (
            <button onClick={onToggle} className="p-0.5 text-gray-400 hover:text-gray-600">
              {isExpanded ? <ChevronDown className="w-4 h-4"/> : <ChevronRight className="w-4 h-4"/>}
            </button>
        ) : (
            <div className="w-5"/>
        )}

        {/* 拖拽手柄 */}
        <GripVertical
            className="w-4 h-4 text-gray-300 dark:text-gray-600 cursor-grab opacity-0 group-hover:opacity-100 transition-opacity"/>

        {/* 图标 */}
        <div className={`w-9 h-9 rounded-xl ${color.bg} flex items-center justify-center flex-shrink-0`}>
          <FolderTree className={`w-4 h-4 ${color.text}`}/>
        </div>

        {/* 名称和slug */}
        <div className="flex-1 min-w-0">
          <p className="font-medium text-gray-900 dark:text-white text-sm truncate">{cat.name}</p>
          {cat.slug && <p className="text-xs text-gray-400 font-mono truncate">/{cat.slug}</p>}
        </div>

        {/* 文章数 */}
        <span
            className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${color.bg} ${color.text}`}>
        <FileText className="w-3 h-3"/>
          {count}
      </span>

        {/* 操作 */}
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button onClick={() => onEdit(cat)}
                  className="p-1.5 rounded-lg text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors">
            <Edit3 className="w-4 h-4"/>
          </button>
          <button onClick={() => onDelete(cat)}
                  className="p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors">
            <Trash2 className="w-4 h-4"/>
          </button>
        </div>
      </div>
  );
};

/* ── 创建/编辑表单 ── */
const CategoryForm: React.FC<{
  editing: any | null;
  onCancel: () => void;
  onSuccess: () => void;
}> = ({editing, onCancel, onSuccess}) => {
  const qc = useQueryClient();
  const [name, setName] = useState(editing?.name || '');
  const [slug, setSlug] = useState(editing?.slug || '');
  const [description, setDescription] = useState(editing?.description || '');

  useEffect(() => {
    setName(editing?.name || '');
    setSlug(editing?.slug || '');
    setDescription(editing?.description || '');
  }, [editing]);

  const saveMut = useMutation({
    mutationFn: async () => {
      const body: any = {name, slug: slug || undefined, description: description || undefined};
      if (editing) return apiClient.put(`/api/v2/categories/${editing.id}`, body);
      return apiClient.post('/api/v2/categories', body);
    },
    onSuccess: () => {
      qc.invalidateQueries({queryKey: ['admin-categories']});
      onSuccess();
    },
  });

  // 自动生成 slug
  const autoSlug = useCallback(() => {
    if (!slug && name) {
      const auto = name.toLowerCase().replace(/[^a-z0-9\u4e00-\u9fff]+/g, '-').replace(/^-|-$/g, '');
      setSlug(auto || `cat-${Date.now()}`);
    }
  }, [name, slug]);

  return (
      <div
          className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 overflow-hidden">
        {/* 表头 */}
        <div
            className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/20">
          <div className="flex items-center gap-3">
            <div
                className={`w-9 h-9 rounded-xl flex items-center justify-center ${editing ? 'bg-amber-100 dark:bg-amber-900/30' : 'bg-blue-100 dark:bg-blue-900/30'}`}>
              {editing ? <Edit3 className="w-4.5 h-4.5 text-amber-600 dark:text-amber-400"/> :
                  <Plus className="w-4.5 h-4.5 text-blue-600 dark:text-blue-400"/>}
            </div>
            <h3 className="font-semibold text-gray-900 dark:text-white">{editing ? '编辑分类' : '新建分类'}</h3>
          </div>
          {editing && (
              <button onClick={onCancel}
                      className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800">
                <X className="w-5 h-5"/>
              </button>
          )}
        </div>

        {/* 表单 */}
        <div className="p-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                分类名称 <span className="text-red-500">*</span>
              </label>
              <input type="text" value={name} onChange={e => setName(e.target.value)} onBlur={autoSlug}
                     placeholder="例如：前端开发"
                     className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:text-white transition-all"/>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                URL 别名
              </label>
              <input type="text" value={slug} onChange={e => setSlug(e.target.value)}
                     placeholder="自动生成或自定义"
                     className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:text-white font-mono transition-all"/>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              描述 <span className="text-gray-400 font-normal">(可选)</span>
            </label>
            <textarea value={description} onChange={e => setDescription(e.target.value)} rows={2}
                      placeholder="简要描述这个分类..."
                      className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:text-white resize-none transition-all"/>
          </div>
        </div>

        {/* 操作栏 */}
        <div
            className="flex items-center justify-between px-6 py-4 border-t border-gray-100 dark:border-gray-800 bg-gray-50/30 dark:bg-gray-800/10">
          <p className="text-xs text-gray-400">
            {editing ? '修改后将立即生效' : '创建后可在列表中编辑'}
          </p>
          <div className="flex items-center gap-2">
            {editing && (
                <button onClick={onCancel}
                        className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-colors">
                  取消
                </button>
            )}
            <button onClick={() => saveMut.mutate()} disabled={!name.trim() || saveMut.isPending}
                    className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-1.5">
              {saveMut.isPending ? (
                  <><span
                      className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/>保存中...</>
              ) : (
                  <><Check className="w-4 h-4"/>{editing ? '更新' : '创建'}</>
              )}
            </button>
          </div>
        </div>
      </div>
  );
};

/* ── 删除确认弹窗 ── */
const DeleteConfirm: React.FC<{
  category: any;
  onConfirm: () => void;
  onCancel: () => void;
  isPending: boolean;
}> = ({category, onConfirm, onCancel, isPending}) => (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
         onClick={onCancel}>
      <div
          className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 w-full max-w-md p-6"
          onClick={e => e.stopPropagation()}>
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
            <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400"/>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white">确认删除分类</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">此操作不可撤销</p>
          </div>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
          确定要删除分类 <strong className="text-gray-900 dark:text-white">{category.name}</strong> 吗？
        </p>
        <p className="text-xs text-gray-400 mb-6">该分类下的文章将变为未分类状态。</p>
        <div className="flex justify-end gap-3">
          <button onClick={onCancel}
                  className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-colors">
            取消
          </button>
          <button onClick={onConfirm} disabled={isPending}
                  className="px-4 py-2 text-sm font-medium bg-red-600 hover:bg-red-700 text-white rounded-xl transition-colors flex items-center gap-1.5 disabled:opacity-50">
            {isPending ? (
                <><span
                    className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/>删除中...</>
            ) : (
                <><Trash2 className="w-4 h-4"/>删除</>
            )}
          </button>
        </div>
      </div>
    </div>
);

/* ── 主页面 ── */
function CategoriesInner() {
  const qc = useQueryClient();
  const [editing, setEditing] = useState<any | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<any | null>(null);
  const [searchInput, setSearchInput] = useState('');
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');
  const [sortBy, setSortBy] = useState<'name' | 'count'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [_expandedIds, _setExpandedIds] = useState<Set<number>>(new Set());

  const {data: cats, isLoading} = useQuery({
    queryKey: ['admin-categories'],
    queryFn: async () => {
      const res = await apiClient.get('/api/v2/categories');
      if (!res.success || !res.data) return [];
      const categoriesData = (res.data as any).categories || [];
      return categoriesData.map((item) => ({
        ...item.category,
        article_count: item.article_count || 0
      }));
    },
  });

  const delMut = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/api/v2/categories/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({queryKey: ['admin-categories']});
      setDeleteTarget(null);
    },
  });

  // 统计
  const stats = useMemo(() => {
    if (!cats) return {total: 0, totalArticles: 0, maxArticles: 0, topCategory: ''};
    const total = cats.length;
    const totalArticles = cats.reduce((sum, c) => sum + (c.articles_count || c.article_count || 0), 0);
    const sorted = [...cats].sort((a: any, b: any) =>
        ((b.articles_count || b.article_count || 0) - (a.articles_count || a.article_count || 0))
    );
    return {
      total,
      totalArticles,
      maxArticles: sorted[0]?.articles_count || sorted[0]?.article_count || 0,
      topCategory: sorted[0]?.name || '-',
    };
  }, [cats]);

  // 过滤和排序
  const filteredCats = useMemo(() => {
    if (!cats) return [];
    let result = cats;
    if (searchInput.trim()) {
      const q = searchInput.toLowerCase();
      result = result.filter((c) =>
          c.name?.toLowerCase().includes(q) || c.slug?.toLowerCase().includes(q)
      );
    }
    result = [...result].sort((a: any, b: any) => {
      if (sortBy === 'name') {
        return sortOrder === 'asc' ? a.name.localeCompare(b.name) : b.name.localeCompare(a.name);
      }
      const ca = a.articles_count || a.article_count || 0;
      const cb = b.articles_count || b.article_count || 0;
      return sortOrder === 'asc' ? ca - cb : cb - ca;
    });
    return result;
  }, [cats, searchInput, sortBy, sortOrder]);

  const toggleSort = (by: 'name' | 'count') => {
    if (sortBy === by) {
      setSortOrder(o => o === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(by);
      setSortOrder('asc');
    }
  };

  const handleEdit = (cat: any) => {
    setEditing(cat);
    setShowForm(true);
  };

  const handleCancelForm = () => {
    setEditing(null);
    setShowForm(false);
  };

  const handleFormSuccess = () => {
    setEditing(null);
    setShowForm(false);
  };

  return (
      <AdminShell title="分类管理" actions={
        <button onClick={() => {
          setEditing(null);
          setShowForm(true);
        }}
                className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors shadow-sm">
          <Plus className="w-4 h-4"/>新建分类
        </button>
      }>
        {/* 统计卡片 */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <StatCard icon={FolderTree} label="分类总数" value={stats.total}
                    gradient="from-blue-500 to-blue-600"/>
          <StatCard icon={FileText} label="文章总数" value={stats.totalArticles}
                    gradient="from-emerald-500 to-emerald-600"/>
          <StatCard icon={Hash} label="平均文章数"
                    value={stats.total > 0 ? Math.round(stats.totalArticles / stats.total) : 0}
                    gradient="from-purple-500 to-purple-600"/>
          <StatCard icon={Eye} label="热门分类" value={stats.topCategory}
                    gradient="from-amber-500 to-amber-600"/>
        </div>

        {/* 工具栏 */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 mb-4">
          {/* 搜索 */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
            <input type="text" value={searchInput} onChange={e => setSearchInput(e.target.value)}
                   placeholder="搜索分类名称或 Slug..."
                   className="w-full pl-10 pr-8 py-2.5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white transition-all"/>
            {searchInput && (
                <button onClick={() => setSearchInput('')}
                        className="absolute right-2.5 top-1/2 -translate-y-1/2 p-0.5 text-gray-400 hover:text-gray-600">
                  <X className="w-4 h-4"/>
                </button>
            )}
          </div>

          {/* 排序 */}
          <div
              className="flex items-center gap-1 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl p-1">
            <button onClick={() => toggleSort('name')}
                    className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                      sortBy === 'name' ? 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                    }`}>
              名称 {sortBy === 'name' && (sortOrder === 'asc' ? <ArrowUp className="w-3 h-3"/> :
                <ArrowDown className="w-3 h-3"/>)}
            </button>
            <button onClick={() => toggleSort('count')}
                    className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                      sortBy === 'count' ? 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                    }`}>
              文章数 {sortBy === 'count' && (sortOrder === 'asc' ? <ArrowUp className="w-3 h-3"/> :
                <ArrowDown className="w-3 h-3"/>)}
            </button>
          </div>

          {/* 视图切换 */}
          <div
              className="flex items-center gap-1 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl p-1">
            <button onClick={() => setViewMode('list')}
                    className={`p-2 rounded-lg transition-colors ${viewMode === 'list' ? 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white' : 'text-gray-400 hover:text-gray-600'}`}>
              <List className="w-4 h-4"/>
            </button>
            <button onClick={() => setViewMode('grid')}
                    className={`p-2 rounded-lg transition-colors ${viewMode === 'grid' ? 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white' : 'text-gray-400 hover:text-gray-600'}`}>
              <LayoutGrid className="w-4 h-4"/>
            </button>
          </div>
        </div>

        {/* 创建/编辑表单 */}
        {showForm && (
            <div className="mb-6">
              <CategoryForm editing={editing} onCancel={handleCancelForm} onSuccess={handleFormSuccess}/>
            </div>
        )}

        {/* 分类列表 */}
        {isLoading ? (
            <CategorySkeleton/>
        ) : filteredCats.length === 0 ? (
            <div
                className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 p-16 text-center">
              <div
                  className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                <FolderTree className="w-8 h-8 text-gray-300 dark:text-gray-600"/>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                {searchInput ? '未找到匹配的分类' : '暂无分类'}
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
                {searchInput ? '尝试使用不同的搜索词' : '创建第一个分类来组织你的文章'}
              </p>
              {!searchInput && (
                  <button onClick={() => {
                    setEditing(null);
                    setShowForm(true);
                  }}
                          className="inline-flex items-center gap-1.5 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-xl transition-colors">
                    <Plus className="w-4 h-4"/>创建分类
                  </button>
              )}
            </div>
        ) : viewMode === 'grid' ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {filteredCats.map((cat: any, i: number) => (
                  <CategoryRow key={cat.id} cat={cat} index={i} viewMode={viewMode}
                               onEdit={handleEdit} onDelete={setDeleteTarget}/>
              ))}
            </div>
        ) : (
            <div
                className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 overflow-hidden">
              {/* 表头 */}
              <div
                className="flex items-center gap-3 px-5 py-3 border-b border-gray-100 dark:border-gray-800 bg-gray-50/80 dark:bg-gray-800/30 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                <div className="w-5"/>
                <div className="w-5"/>
                <div className="w-9"/>
                <div className="flex-1">分类名称</div>
                <div className="w-20 text-center">文章数</div>
                <div className="w-20"/>
              </div>
              {/* 行 */}
              <div className="divide-y divide-gray-50 dark:divide-gray-800/50">
                {filteredCats.map((cat: any, i: number) => (
                    <CategoryRow key={cat.id} cat={cat} index={i} viewMode={viewMode}
                                 onEdit={handleEdit} onDelete={setDeleteTarget}/>
                ))}
              </div>
              {/* 底部 */}
              <div
                  className="px-5 py-3 border-t border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/10">
                <p className="text-xs text-gray-400">
                  共 {filteredCats.length} 个分类{searchInput ? ` (搜索: "${searchInput}")` : ''}
                </p>
              </div>
            </div>
        )}

        {/* 删除确认弹窗 */}
        {deleteTarget && (
            <DeleteConfirm
                category={deleteTarget}
                onConfirm={() => delMut.mutate(deleteTarget.id)}
                onCancel={() => setDeleteTarget(null)}
                isPending={delMut.isPending}
            />
        )}
    </AdminShell>
  );
}

export default function AdminCategories() {
  return <AuthGuard><QueryProvider><CategoriesInner /></QueryProvider></AuthGuard>;
}
