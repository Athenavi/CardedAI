'use client';

import React, {useState, useMemo, useEffect, useCallback} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {apiClient} from '@/lib/api/base-client';
import {useDebounce} from '@/lib/hooks';
import {StatCard} from '@/components/admin/shared-ui';
import {
  Bell,
  BellRing,
  Check,
  CheckCheck,
  Send,
  Trash2,
  Search,
  Mail,
  AlertTriangle,
  Shield,
  FileText,
  UserPlus,
  CreditCard,
  Settings,
  Filter,
  ChevronDown,
  Clock,
  Eye,
  EyeOff,
  Inbox,
  Archive,
  RefreshCw,
  Plus,
  X,
  ChevronLeft,
  ChevronRight,
  MessageSquare,
  Info,
  AlertCircle,
  Loader2
} from 'lucide-react';

/* ─── Notification type config ─── */
const TYPE_OPTIONS = [
  {key: 'all', label: '全部', icon: Inbox, color: 'from-gray-500 to-gray-600'},
  {key: 'system', label: '系统', icon: Settings, color: 'from-blue-500 to-blue-600'},
  {key: 'security', label: '安全', icon: Shield, color: 'from-red-500 to-rose-600'},
  {key: 'article', label: '文章', icon: FileText, color: 'from-green-500 to-emerald-600'},
  {key: 'user', label: '用户', icon: UserPlus, color: 'from-purple-500 to-violet-600'},
  {key: 'payment', label: '支付', icon: CreditCard, color: 'from-amber-500 to-orange-600'},
];

const PRIORITY_OPTIONS = [
  {key: 'normal', label: '普通', color: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'},
  {key: 'important', label: '重要', color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'},
  {key: 'urgent', label: '紧急', color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'},
];

const STATUS_TABS = [
  {key: 'all', label: '全部', icon: Inbox},
  {key: 'unread', label: '未读', icon: BellRing},
  {key: 'read', label: '已读', icon: Eye},
];


/* ─── Skeleton ─── */
const NotificationSkeleton = () => (
    <div className="divide-y divide-gray-100 dark:divide-gray-800">
      {[1, 2, 3, 4, 5, 6].map(i => (
          <div key={i} className="px-5 py-4 animate-pulse">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-xl bg-gray-200 dark:bg-gray-700 flex-shrink-0"/>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"/>
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/3"/>
              </div>
              <div className="w-16 h-6 bg-gray-200 dark:bg-gray-700 rounded"/>
            </div>
          </div>
      ))}
    </div>
);

/* ─── Notification Card ─── */
const NotificationCard: React.FC<{
  notification: any;
  onMarkRead: (id: number) => void;
  onDelete: (id: number) => void;
  readPending: boolean;
  deletePending: boolean;
  isSelected: boolean;
  onToggleSelect: (id: number) => void;
}> = ({notification: n, onMarkRead, onDelete, readPending, deletePending, isSelected, onToggleSelect}) => {
  const typeConfig = TYPE_OPTIONS.find(t => t.key === (n.type || 'system')) || TYPE_OPTIONS[1];
  const priorityConfig = PRIORITY_OPTIONS.find(p => p.key === (n.priority || 'normal')) || PRIORITY_OPTIONS[0];
  const TypeIcon = typeConfig.icon;

  return (
      <div className={`px-5 py-4 flex items-start gap-4 transition-colors group ${
          !n.is_read
              ? 'bg-blue-50/50 dark:bg-blue-900/10 hover:bg-blue-50 dark:hover:bg-blue-900/20'
              : 'hover:bg-gray-50 dark:hover:bg-gray-800/50'
      }`}>
        {/* Checkbox */}
        <button
            onClick={() => onToggleSelect(n.id)}
            className={`mt-1 w-5 h-5 rounded-md border-2 flex items-center justify-center flex-shrink-0 transition-all ${
                isSelected
                    ? 'bg-blue-600 border-blue-600'
                    : 'border-gray-300 dark:border-gray-600 hover:border-blue-400'
            }`}
        >
          {isSelected && <Check className="w-3 h-3 text-white"/>}
        </button>

        {/* Type Icon */}
        <div
            className={`w-10 h-10 rounded-xl bg-gradient-to-br ${typeConfig.color} flex items-center justify-center flex-shrink-0`}>
          <TypeIcon className="w-5 h-5 text-white"/>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
          <span className={`text-sm font-medium ${
              !n.is_read ? 'text-gray-900 dark:text-white' : 'text-gray-600 dark:text-gray-400'
          }`}>
            {n.title || n.message || n.content || '未命名通知'}
          </span>
            {!n.is_read && (
                <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse flex-shrink-0"/>
            )}
          </div>
          {n.content && n.title && (
              <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-1 mt-0.5">
                {n.content}
              </p>
          )}
          <div className="flex items-center gap-3 mt-2">
          <span className="text-xs text-gray-400 flex items-center gap-1">
            <Clock className="w-3 h-3"/>
            {n.created_at ? new Date(n.created_at).toLocaleString('zh-CN', {
              month: 'numeric',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit'
            }) : '未知'}
          </span>
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium ${typeConfig.color.replace('from-', 'bg-').split(' ')[0]}/10 ${typeConfig.color.replace('to-', 'text-').split(' ')[0] || 'text-gray-500 dark:text-gray-400'}`}>
            {typeConfig.label}
          </span>
            {n.priority && n.priority !== 'normal' && (
                <span
                    className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium ${priorityConfig.color}`}>
              {priorityConfig.label}
            </span>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
          {!n.is_read && (
              <button
                  onClick={() => onMarkRead(n.id)}
                  disabled={readPending}
                  className="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg transition-colors"
                  title="标为已读"
              >
                <CheckCheck className="w-4 h-4"/>
              </button>
          )}
          <button
              onClick={() => onDelete(n.id)}
              disabled={deletePending}
              className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
              title="删除"
          >
            <Trash2 className="w-4 h-4"/>
          </button>
        </div>
      </div>
  );
};

/* ─── Send Notification Modal ─── */
const SendModal: React.FC<{
  open: boolean;
  onClose: () => void;
  onSend: (data: { title: string; content: string; type: string; priority: string }) => void;
  isPending: boolean;
}> = ({open, onClose, onSend, isPending}) => {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [type, setType] = useState('system');
  const [priority, setPriority] = useState('normal');

  useEffect(() => {
    if (!open) {
      setTitle('');
      setContent('');
      setType('system');
      setPriority('normal');
    }
  }, [open]);

  if (!open) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;
    onSend({title: title.trim(), content: content.trim(), type, priority});
  };

  return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose}/>
        <div
            className="relative bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-800">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <div
                  className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
                <Send className="w-4 h-4 text-white"/>
              </div>
              发送通知
            </h3>
            <button onClick={onClose}
                    className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
              <X className="w-5 h-5"/>
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">标题</label>
              <input
                  type="text"
                  value={title}
                  onChange={e => setTitle(e.target.value)}
                  placeholder="输入通知标题..."
                  className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  autoFocus
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">内容</label>
              <textarea
                  value={content}
                  onChange={e => setContent(e.target.value)}
                  placeholder="输入通知内容..."
                  rows={4}
                  className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none transition-all"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">类型</label>
                <select
                    value={type}
                    onChange={e => setType(e.target.value)}
                    className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all appearance-none"
                >
                  {TYPE_OPTIONS.filter(t => t.key !== 'all').map(t => (
                      <option key={t.key} value={t.key}>{t.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">优先级</label>
                <select
                    value={priority}
                    onChange={e => setPriority(e.target.value)}
                    className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all appearance-none"
                >
                  {PRIORITY_OPTIONS.map(p => (
                      <option key={p.key} value={p.key}>{p.label}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-3 pt-2">
              <button
                  type="button"
                  onClick={onClose}
                  className="px-5 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-xl transition-colors"
              >
                取消
              </button>
              <button
                  type="submit"
                  disabled={!title.trim() || !content.trim() || isPending}
                  className="px-5 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-all shadow-lg shadow-blue-500/20"
              >
                {isPending ? <Loader2 className="w-4 h-4 animate-spin"/> : <Send className="w-4 h-4"/>}
                {isPending ? '发送中...' : '发送通知'}
              </button>
            </div>
          </form>
        </div>
      </div>
  );
};

/* ─── Delete Confirm ─── */
const DeleteConfirm: React.FC<{
  count: number;
  onConfirm: () => void;
  onCancel: () => void;
  isPending: boolean;
}> = ({count, onConfirm, onCancel, isPending}) => (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onCancel}/>
      <div
          className="relative bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-sm border border-gray-200 dark:border-gray-700 p-6 text-center">
        <div
            className="w-14 h-14 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mx-auto mb-4">
          <Trash2 className="w-7 h-7 text-red-600 dark:text-red-400"/>
        </div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">确认删除</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
          确定要删除 {count > 1 ? `这 ${count} 条` : '这条'}通知吗？此操作不可撤销。
        </p>
        <div className="flex gap-3">
          <button
              onClick={onCancel}
              className="flex-1 px-4 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-xl transition-colors"
          >
            取消
          </button>
          <button
              onClick={onConfirm}
              disabled={isPending}
              className="flex-1 px-4 py-2.5 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-xl disabled:opacity-50 flex items-center justify-center gap-2 transition-colors"
          >
            {isPending ? <Loader2 className="w-4 h-4 animate-spin"/> : <Trash2 className="w-4 h-4"/>}
            确认删除
          </button>
        </div>
      </div>
    </div>
);

/* ─── Main Component ─── */
function NotificationsInner() {
  const qc = useQueryClient();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [sendOpen, setSendOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<{ type: 'single' | 'batch'; id?: number } | null>(null);
  const debouncedSearch = useDebounce(search, 300);

  /* ─── Data fetching ─── */
  const {data: notifications = [], isLoading, refetch, isFetching} = useQuery<any[]>({
    queryKey: ['admin-notifications'],
    queryFn: async () => {
      const r = await apiClient.get('/notifications/messages');
      return r.success && r.data ? (Array.isArray(r.data) ? r.data : r.data.notifications || []) : [];
    },
  });

  /* ─── Mutations ─── */
  const sendMut = useMutation({
    mutationFn: (data: { title: string; content: string; type: string; priority: string }) =>
        apiClient.post('/notifications/email/send', data),
    onSuccess: () => {
      qc.invalidateQueries({queryKey: ['admin-notifications']});
      setSendOpen(false);
    },
  });

  const readMut = useMutation({
    mutationFn: (id: number) => apiClient.post(`/notifications/${id}/read`),
    onSuccess: () => qc.invalidateQueries({queryKey: ['admin-notifications']}),
  });

  const readAllMut = useMutation({
    mutationFn: () => apiClient.post('/notifications/read-all'),
    onSuccess: () => {
      qc.invalidateQueries({queryKey: ['admin-notifications']});
      setSelectedIds(new Set());
    },
  });

  const deleteMut = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/notifications/messages/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({queryKey: ['admin-notifications']});
      setDeleteTarget(null);
    },
  });

  const batchDeleteMut = useMutation({
    mutationFn: async () => {
      const ids = Array.from(selectedIds);
      await Promise.all(ids.map(id => apiClient.delete(`/notifications/messages/${id}`)));
    },
    onSuccess: () => {
      qc.invalidateQueries({queryKey: ['admin-notifications']});
      setSelectedIds(new Set());
      setDeleteTarget(null);
    },
  });

  const cleanAllMut = useMutation({
    mutationFn: () => apiClient.delete('/notifications/messages/clean'),
    onSuccess: () => {
      qc.invalidateQueries({queryKey: ['admin-notifications']});
      setSelectedIds(new Set());
      setDeleteTarget(null);
    },
  });

  /* ─── Stats ─── */
  const stats = useMemo(() => {
    const total = notifications.length;
    const unread = notifications.filter((n) => !n.is_read).length;
    const read = total - unread;
    const today = notifications.filter((n) => {
      if (!n.created_at) return false;
      const d = new Date(n.created_at);
      const now = new Date();
      return d.toDateString() === now.toDateString();
    }).length;
    return {total, unread, read, today};
  }, [notifications]);

  /* ─── Filtering ─── */
  const filtered = useMemo(() => {
    let result = [...notifications];

    // Status filter
    if (statusFilter === 'unread') result = result.filter((n) => !n.is_read);
    else if (statusFilter === 'read') result = result.filter((n) => n.is_read);

    // Type filter
    if (typeFilter !== 'all') result = result.filter((n) => (n.type || 'system') === typeFilter);

    // Search
    if (debouncedSearch) {
      const q = debouncedSearch.toLowerCase();
      result = result.filter((n) =>
          (n.title || '').toLowerCase().includes(q) ||
          (n.content || '').toLowerCase().includes(q) ||
          (n.message || '').toLowerCase().includes(q)
      );
    }

    // Sort by date descending
    result.sort((a: any, b: any) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime());

    return result;
  }, [notifications, statusFilter, typeFilter, debouncedSearch]);

  /* ─── Selection helpers ─── */
  const toggleSelect = useCallback((id: number) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }, []);

  const toggleSelectAll = useCallback(() => {
    if (selectedIds.size === filtered.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filtered.map((n) => n.id)));
    }
  }, [filtered, selectedIds]);

  /* ─── Render ─── */
  return (
      <AdminShell title="通知中心" actions={
        <div className="flex items-center gap-2">
          {selectedIds.size > 0 && (
              <button
                  onClick={() => setDeleteTarget({type: 'batch'})}
                  className="px-3 py-2 text-sm font-medium text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/40 rounded-xl flex items-center gap-1.5 transition-colors"
              >
                <Trash2 className="w-4 h-4"/>
                删除 ({selectedIds.size})
              </button>
          )}
          {stats.unread > 0 && (
              <button
                  onClick={() => readAllMut.mutate()}
                  disabled={readAllMut.isPending}
                  className="px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-xl flex items-center gap-1.5 transition-colors"
              >
                <CheckCheck className="w-4 h-4"/>
                全部已读
              </button>
          )}
          <button
              onClick={() => setSendOpen(true)}
              className="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 rounded-xl flex items-center gap-1.5 shadow-lg shadow-blue-500/20 transition-all"
          >
            <Plus className="w-4 h-4"/>
            发送通知
          </button>
        </div>
      }>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <StatCard icon={Bell} label="通知总数" value={stats.total} gradient="from-blue-500 to-blue-600"/>
          <StatCard icon={BellRing} label="未读通知" value={stats.unread} gradient="from-amber-500 to-orange-500"/>
          <StatCard icon={Eye} label="已读通知" value={stats.read} gradient="from-green-500 to-emerald-600"/>
          <StatCard icon={Clock} label="今日通知" value={stats.today} gradient="from-purple-500 to-violet-600"/>
        </div>

        {/* Type Filter Tabs */}
        <div className="flex items-center gap-2 mb-4 overflow-x-auto pb-1 scrollbar-hide">
          {TYPE_OPTIONS.map(opt => {
            const Icon = opt.icon;
            return (
                <button
                    key={opt.key}
                    onClick={() => setTypeFilter(opt.key)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-all ${
                        typeFilter === opt.key
                            ? 'bg-white dark:bg-gray-800 shadow-md border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white'
                            : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800/50'
                    }`}
                >
                  <Icon className="w-4 h-4"/>
                  {opt.label}
                </button>
            );
          })}
        </div>

        {/* Toolbar: Search + Status Filter + Refresh */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 mb-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
            <input
                type="text"
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="搜索通知..."
                className="w-full pl-10 pr-4 py-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
          </div>
          <div className="flex items-center gap-2">
            {STATUS_TABS.map(tab => {
              const Icon = tab.icon;
              return (
                  <button
                      key={tab.key}
                      onClick={() => setStatusFilter(tab.key)}
                      className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium transition-all ${
                          statusFilter === tab.key
                              ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
                              : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                      }`}
                  >
                    <Icon className="w-4 h-4"/>
                    {tab.label}
                  </button>
              );
            })}
            <button
                onClick={() => refetch()}
                disabled={isFetching}
                className="p-2.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-colors"
                title="刷新"
            >
              <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`}/>
            </button>
          </div>
        </div>

        {/* Select All + Count */}
        {filtered.length > 0 && (
            <div className="flex items-center justify-between mb-2 px-1">
              <button
                  onClick={toggleSelectAll}
                  className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
              >
                <div className={`w-4 h-4 rounded border-2 flex items-center justify-center transition-all ${
                    selectedIds.size === filtered.length && filtered.length > 0
                        ? 'bg-blue-600 border-blue-600'
                        : selectedIds.size > 0
                            ? 'bg-blue-600/50 border-blue-600'
                            : 'border-gray-300 dark:border-gray-600'
                }`}>
                  {selectedIds.size === filtered.length && filtered.length > 0 &&
                      <Check className="w-3 h-3 text-white"/>}
                  {selectedIds.size > 0 && selectedIds.size < filtered.length &&
                      <div className="w-2 h-2 bg-white rounded-sm"/>}
                </div>
                {selectedIds.size > 0 ? `已选 ${selectedIds.size} 项` : '全选'}
              </button>
              <span className="text-sm text-gray-400">
            共 {filtered.length} 条通知
          </span>
            </div>
        )}

        {/* Notifications List */}
        <div
            className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
        {isLoading ? (
            <NotificationSkeleton/>
        ) : filtered.length === 0 ? (
            <div className="p-16 text-center">
              <div
                  className="w-20 h-20 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mx-auto mb-4">
                <Bell className="w-10 h-10 text-gray-300 dark:text-gray-600"/>
              </div>
              <p className="text-lg font-medium text-gray-500 dark:text-gray-400 mb-1">
                {search ? '没有找到匹配的通知' : '暂无通知'}
              </p>
              <p className="text-sm text-gray-400 dark:text-gray-500 dark:text-gray-400">
                {search ? '尝试使用其他关键词搜索' : '新通知将会显示在这里'}
              </p>
            </div>
        ) : (
          <div className="divide-y divide-gray-100 dark:divide-gray-800">
            {filtered.map((n) => (
                <NotificationCard
                    key={n.id}
                    notification={n}
                    onMarkRead={(id) => readMut.mutate(id)}
                    onDelete={(id) => setDeleteTarget({type: 'single', id})}
                    readPending={readMut.isPending}
                    deletePending={deleteMut.isPending}
                    isSelected={selectedIds.has(n.id)}
                    onToggleSelect={toggleSelect}
                />
            ))}
          </div>
        )}
        </div>

        {/* Clean All Footer */}
        {notifications.length > 0 && (
            <div className="flex items-center justify-between mt-4 px-1">
          <span className="text-xs text-gray-400">
            {stats.unread > 0 ? `${stats.unread} 条未读通知` : '所有通知已读'}
          </span>
              <button
                  onClick={() => setDeleteTarget({type: 'batch'})}
                  className="text-xs text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors flex items-center gap-1"
              >
                <Trash2 className="w-3 h-3"/>
                清理全部
              </button>
            </div>
        )}

        {/* Modals */}
        <SendModal
            open={sendOpen}
            onClose={() => setSendOpen(false)}
            onSend={(data) => sendMut.mutate(data)}
            isPending={sendMut.isPending}
        />

        {deleteTarget && (
            <DeleteConfirm
                count={deleteTarget.type === 'batch' ? (selectedIds.size || notifications.length) : 1}
                onConfirm={() => {
                  if (deleteTarget.type === 'batch') {
                    if (selectedIds.size > 0) batchDeleteMut.mutate();
                    else cleanAllMut.mutate();
                  } else if (deleteTarget.id) {
                    deleteMut.mutate(deleteTarget.id);
                  }
                }}
                onCancel={() => setDeleteTarget(null)}
                isPending={deleteMut.isPending || batchDeleteMut.isPending || cleanAllMut.isPending}
            />
        )}
    </AdminShell>
  );
}

export default function AdminNotifications() {
  return (
      <AuthGuard>
        <QueryProvider>
          <NotificationsInner/>
        </QueryProvider>
      </AuthGuard>
  );
}
