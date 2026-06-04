'use client';

import React, {useEffect, useMemo, useRef, useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {apiClient} from '@/lib/api/base-client';
import {
  AlertTriangle,
  Archive,
  BarChart3,
  ChevronLeft,
  ChevronRight,
  Clock,
  Database,
  Download,
  FileDown,
  HardDrive,
  Loader,
  Package,
  RefreshCw,
  Search,
  Trash2
} from 'lucide-react';
import {timeAgo} from '@/lib/utils';
import {StatCard} from '@/components/admin/shared-ui';

/* ─── Helpers ─── */
function formatSize(bytes: number | string | undefined | null): string {
  if (bytes == null) return '—';
  const n = typeof bytes === 'string' ? parseFloat(bytes) : bytes;
  if (isNaN(n) || n <= 0) return '—';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let i = 0;
  let size = n;
  while (size >= 1024 && i < units.length - 1) { size /= 1024; i++; }
  return `${size.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

/* ─── Constants ─── */
const TYPE_OPTIONS = [
  {value: '', label: '全部', icon: Package, gradient: 'from-gray-500 to-gray-600'},
  {value: 'database', label: '数据库', icon: Database, gradient: 'from-blue-500 to-cyan-500'},
  {value: 'files', label: '文件', icon: HardDrive, gradient: 'from-emerald-500 to-teal-500'},
  {value: 'full', label: '完整', icon: Archive, gradient: 'from-purple-500 to-pink-500'},
] as const;

const BACKUP_TYPE_CONFIG: Record<string, {
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  gradient: string;
  color: string;
  bg: string
}> = {
  database: {
    label: '数据库',
    icon: Database,
    gradient: 'from-blue-500 to-cyan-500',
    color: 'text-blue-600 dark:text-blue-400',
    bg: 'bg-blue-50 dark:bg-blue-900/20'
  },
  files: {
    label: '文件',
    icon: HardDrive,
    gradient: 'from-emerald-500 to-teal-500',
    color: 'text-emerald-600 dark:text-emerald-400',
    bg: 'bg-emerald-50 dark:bg-emerald-900/20'
  },
  full: {
    label: '完整',
    icon: Archive,
    gradient: 'from-purple-500 to-pink-500',
    color: 'text-purple-600 dark:text-purple-400',
    bg: 'bg-purple-50 dark:bg-purple-900/20'
  },
};

const GRADIENT_COLORS = [
  'from-blue-500 to-cyan-500',
  'from-emerald-500 to-teal-500',
  'from-purple-500 to-pink-500',
  'from-amber-500 to-orange-500',
] as const;

/* ─── Shared Components ─── */

const SectionTitle: React.FC<{
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  subtitle?: string;
  action?: React.ReactNode
}> = ({
                                                                                                             icon: Icon,
                                                                                                             title,
                                                                                                             subtitle,
                                                                                                             action
                                                                                                           }) => (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div
            className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
          <Icon className="w-4 h-4 text-white"/>
        </div>
        <div>
          <h3 className="font-semibold text-gray-900 dark:text-white">{title}</h3>
          {subtitle && <p className="text-xs text-gray-500 dark:text-gray-400">{subtitle}</p>}
        </div>
      </div>
      {action}
    </div>
);

const BackupSkeleton = () => (
    <div className="animate-pulse space-y-3">
      {[1, 2, 3, 4, 5, 6].map(i => (
          <div key={i} className="flex items-center gap-4 px-5 py-4">
            <div className="w-16 h-5 bg-gray-200 dark:bg-gray-700 rounded-full"/>
            <div className="flex-1 h-4 bg-gray-200 dark:bg-gray-700 rounded max-w-[200px]"/>
            <div className="w-28 h-4 bg-gray-200 dark:bg-gray-700 rounded hidden md:block"/>
            <div className="w-16 h-4 bg-gray-200 dark:bg-gray-700 rounded"/>
            <div className="w-20 h-4 bg-gray-200 dark:bg-gray-700 rounded"/>
          </div>
      ))}
    </div>
);

const EmptyState: React.FC<{
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  desc: string;
  action?: React.ReactNode
}> = ({
                                                                                                      icon: Icon,
                                                                                                      title,
                                                                                                      desc,
                                                                                                      action
                                                                                                    }) => (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <div className="w-16 h-16 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-4">
        <Icon className="w-8 h-8 text-gray-300 dark:text-gray-600"/>
      </div>
      <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-1">{title}</h3>
      <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">{desc}</p>
      {action}
    </div>
);

const Modal: React.FC<{
  open: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  maxWidth?: string
}> = ({open, onClose, title, subtitle, children, maxWidth = 'max-w-lg'}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);
  useEffect(() => {
    if (open) {
      setIsVisible(true);
      requestAnimationFrame(() => setIsAnimating(true));
    } else {
      setIsAnimating(false);
      const timer = setTimeout(() => setIsVisible(false), 200);
      return () => clearTimeout(timer);
    }
  }, [open]);
  if (!isVisible) return null;
  return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose}>
        <div
            className={`absolute inset-0 bg-black/50 backdrop-blur-sm transition-opacity duration-200 ${isAnimating ? 'opacity-100' : 'opacity-0'}`}/>
        <div
            className={`relative ${maxWidth} w-full bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 max-h-[85vh] flex flex-col transition-all duration-200 ${isAnimating ? 'scale-100 opacity-100 translate-y-0' : 'scale-95 opacity-0 translate-y-4'}`}
            onClick={e => e.stopPropagation()}>
          <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800 flex-shrink-0">
            <h2 className="text-lg font-bold text-gray-900 dark:text-white">{title}</h2>
            {subtitle && <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{subtitle}</p>}
          </div>
          <div className="px-6 py-4 overflow-y-auto flex-1">{children}</div>
        </div>
      </div>
  );
};

const DeleteConfirm: React.FC<{
  filename: string;
  onConfirm: () => void;
  onCancel: () => void;
  isPending?: boolean
}> = ({filename, onConfirm, onCancel, isPending}) => (
    <div className="space-y-4">
      <div
          className="flex items-start gap-3 p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-800/30">
        <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5"/>
        <div>
          <p className="text-sm font-medium text-red-800 dark:text-red-300">确认删除此备份？</p>
          <p className="text-xs text-red-600 dark:text-red-400 mt-1">备份文件 <span
              className="font-mono font-medium">{filename}</span> 将被永久删除，此操作无法撤销。</p>
        </div>
      </div>
      <div className="flex justify-end gap-2">
        <button onClick={onCancel}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 rounded-xl hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">取消
        </button>
        <button onClick={onConfirm} disabled={isPending}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-xl hover:bg-red-700 transition-colors disabled:opacity-50 flex items-center gap-2">
          {isPending && <Loader className="w-3.5 h-3.5 animate-spin"/>}
          {isPending ? '删除中…' : '确认删除'}
        </button>
      </div>
    </div>
);

const TypeBadge: React.FC<{ type: string }> = ({type}) => {
  const config = BACKUP_TYPE_CONFIG[type] || BACKUP_TYPE_CONFIG.database;
  const Icon = config.icon;
  return (
      <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full ${config.bg} ${config.color}`}>
      <Icon className="w-3 h-3"/>
        {config.label}
    </span>
  );
};

/* ─── Main Component ─── */
function BackupInner() {
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [typeFilter, setTypeFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [backingUp, setBackingUp] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [confirmAction, setConfirmAction] = useState<string | null>(null);
  const [confirmCleanup, setConfirmCleanup] = useState(false);
  const prevFilterRef = useRef('');
  const filterKey = `${typeFilter}`;
  if (prevFilterRef.current !== filterKey) {
    prevFilterRef.current = filterKey;
    if (page !== 1) setPage(1);
  }

  const {data, isLoading} = useQuery({
    queryKey: ['admin-backups', page, typeFilter],
    queryFn: async () => {
      const params: Record<string, any> = {page, per_page: 15};
      if (typeFilter) params.backup_type = typeFilter;
      const res = await apiClient.get('/api/v2/system/backup/list', params);
      if (res.success && res.data) return res.data;
      return {backups: [], total: 0, page: 1, per_page: 15, total_pages: 1};
    },
  });

  const {data: stats, refetch: refetchStats} = useQuery({
    queryKey: ['admin-backup-stats'],
    queryFn: async () => {
      const res = await apiClient.get('/api/v2/system/backup/stats');
      return res.success && res.data ? res.data : {};
    },
  });

  const backups = data?.backups || [];
  const total = data?.total || 0;
  const totalPages = data?.total_pages || 1;

  const filteredBackups = useMemo(() => {
    if (!searchQuery.trim()) return backups;
    const q = searchQuery.toLowerCase();
    return backups.filter((b) => {
      const filename = b.filename || b.path?.split('/').pop() || b.backup_dir?.split('/').pop() || '';
      return filename.toLowerCase().includes(q) || (b.type || '').toLowerCase().includes(q);
    });
  }, [backups, searchQuery]);

  const statCards = useMemo(() => [
    {
      label: '数据库备份',
      value: stats?.by_type?.database?.count ?? 0,
      icon: Database,
      gradient: GRADIENT_COLORS[0],
      subtitle: formatSize(stats?.by_type?.database?.total_size)
    },
    {
      label: '文件备份',
      value: stats?.by_type?.files?.count ?? 0,
      icon: HardDrive,
      gradient: GRADIENT_COLORS[1],
      subtitle: formatSize(stats?.by_type?.files?.total_size)
    },
    {
      label: '完整备份',
      value: stats?.by_type?.full?.count ?? 0,
      icon: Archive,
      gradient: GRADIENT_COLORS[2],
      subtitle: formatSize(stats?.by_type?.full?.total_size)
    },
    {
      label: '总存储大小',
      value: formatSize(stats?.total_size),
      icon: BarChart3,
      gradient: GRADIENT_COLORS[3],
      subtitle: `共 ${total} 个备份`
    },
  ], [stats, total]);

  const createMut = useMutation({
    mutationFn: async (type: string) => {
      setBackingUp(type);
      const res = await apiClient.post(`/api/v2/system/backup/${type}`);
      return {type, res};
    },
    onSuccess: ({type}) => {
      setBackingUp(null);
      qc.invalidateQueries({queryKey: ['admin-backups']});
      refetchStats();
    },
    onError: () => setBackingUp(null),
  });

  const delOneMut = useMutation({
    mutationFn: (filename: string) => apiClient.delete(`/api/v2/system/backup/${encodeURIComponent(filename)}`),
    onSuccess: () => {
      setDeleteTarget(null);
      qc.invalidateQueries({queryKey: ['admin-backups']});
      refetchStats();
    },
  });

  const delMut = useMutation({
    mutationFn: () => apiClient.post('/api/v2/system/backup/cleanup'),
    onSuccess: () => {
      qc.invalidateQueries({queryKey: ['admin-backups']});
      refetchStats();
    },
  });

  const isBusy = backingUp !== null;

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
        <div className="flex items-center justify-center gap-1.5 mt-4">
          <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}
                  className="p-2 rounded-lg border border-gray-200 dark:border-gray-700 disabled:opacity-30 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
            <ChevronLeft className="w-4 h-4"/>
          </button>
          {pages.map((p, i) =>
              p === '...' ? <span key={`e-${i}`} className="px-2 text-gray-400">…</span> :
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
      <AdminShell title="备份管理" actions={
        <div className="flex items-center gap-2">
          <button onClick={() => {
            qc.invalidateQueries({queryKey: ['admin-backups']});
            refetchStats();
          }}
                  className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                  title="刷新">
            <RefreshCw className="w-4 h-4"/>
          </button>
        </div>
      }>
        {/* Stats Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {statCards.map((card, i) => (
              <StatCard key={i} {...card}/>
          ))}
        </div>

        {/* Create Backup + Filter Bar */}
        <div
            className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/80 dark:border-gray-700/80 overflow-hidden mb-6">
          <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
            <SectionTitle icon={Download} title="创建备份" subtitle="选择备份类型立即创建系统备份"
                          action={
                            <button onClick={() => setConfirmCleanup(true)}
                                    className="px-3 py-1.5 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 text-xs font-medium rounded-xl hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-1.5 transition-colors">
                              <Trash2 className="w-3.5 h-3.5"/>清理旧备份
                            </button>
                          }
            />
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {(['database', 'files', 'full'] as const).map(t => {
                const config = BACKUP_TYPE_CONFIG[t];
                const Icon = config.icon;
                return (
                    <button key={t} onClick={() => {
                      if (!isBusy) setConfirmAction(t);
                    }} disabled={isBusy}
                            className={`relative group flex flex-col items-center gap-3 p-5 rounded-xl border-2 transition-all duration-300 ${
                                backingUp === t
                                    ? 'border-blue-300 dark:border-blue-700 bg-blue-50 dark:bg-blue-900/20'
                                    : isBusy
                                        ? 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 opacity-50 cursor-not-allowed'
                                        : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-blue-300 dark:hover:border-blue-700 hover:shadow-lg hover:-translate-y-0.5'
                            }`}>
                      <div
                          className={`w-12 h-12 rounded-xl bg-gradient-to-br ${config.gradient} flex items-center justify-center shadow-lg ${
                              backingUp === t ? 'animate-pulse' : ''
                          }`}>
                        {backingUp === t ? <Loader className="w-6 h-6 text-white animate-spin"/> :
                            <Icon className="w-6 h-6 text-white"/>}
                      </div>
                      <div className="text-center">
                        <p className="text-sm font-semibold text-gray-900 dark:text-white">
                          {backingUp === t ? '备份中…' : config.label + '备份'}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                          {t === 'database' ? '备份数据库数据' : t === 'files' ? '备份上传文件' : '完整系统备份'}
                        </p>
                      </div>
                      {backingUp === t && (
                          <div
                              className="absolute bottom-0 left-0 right-0 h-1 bg-gray-200 dark:bg-gray-700 rounded-b-xl overflow-hidden">
                            <div className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 animate-pulse"
                                 style={{width: '60%'}}/>
                          </div>
                      )}
                    </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Backup List */}
        <div
            className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/80 dark:border-gray-700/80 overflow-hidden">
          <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
            <SectionTitle icon={Archive} title="备份列表" subtitle={`共 ${total} 个备份文件`}/>
          </div>
          <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex flex-wrap items-center gap-3">
            {/* Type Filter */}
            <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 rounded-xl p-1">
              {TYPE_OPTIONS.map(opt => (
                  <button key={opt.value} onClick={() => setTypeFilter(opt.value)}
                          className={`relative px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 ${
                              typeFilter === opt.value
                                  ? 'bg-white dark:bg-gray-700 shadow-sm text-gray-900 dark:text-white'
                                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                          }`}>
                <span className="flex items-center gap-1.5">
                  <opt.icon className="w-3 h-3"/>
                  {opt.label}
                </span>
              </button>
              ))}
            </div>
            {/* Search */}
            <div className="flex-1 min-w-[200px] max-w-md relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
              <input type="text" placeholder="搜索备份文件名…" value={searchQuery}
                     onChange={e => setSearchQuery(e.target.value)}
                     className="w-full pl-9 pr-4 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-all"/>
          </div>
        </div>

          <div className="overflow-x-auto">
          {isLoading ? (
              <BackupSkeleton/>
          ) : !backups.length ? (
              <EmptyState icon={Archive} title="暂无备份" desc="点击上方按钮创建您的第一个系统备份"
                          action={<button onClick={() => setConfirmAction('full')}
                                          className="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-cyan-600 rounded-xl hover:shadow-lg transition-all">立即创建完整备份</button>}
              />
          ) : filteredBackups.length === 0 ? (
              <EmptyState icon={Search} title="未找到匹配的备份" desc="请尝试其他搜索关键词"/>
          ) : (
              <table className="w-full">
                <thead className="bg-gray-50/80 dark:bg-gray-800/50 border-b border-gray-100 dark:border-gray-800">
                <tr>
                  <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">类型</th>
                  <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden sm:table-cell">文件名</th>
                  <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden md:table-cell">创建时间</th>
                  <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">大小</th>
                  <th className="px-6 py-3.5 text-right text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">操作</th>
                </tr>
                </thead>
                <tbody className="divide-y divide-gray-50 dark:divide-gray-800/50">
                {filteredBackups.map((b: any, i: number) => {
                  const filename = b.filename || b.path?.split('/').pop() || b.backup_dir?.split('/').pop() || '';
                  const isFull = b.type === 'full';
                  const downloadUrl = `/api/v2/system/backup/download/${encodeURIComponent(filename)}`;
                  return (
                      <tr key={b.filename || i}
                          className="group hover:bg-gray-50/80 dark:hover:bg-gray-800/30 transition-colors">
                        <td className="px-6 py-4">
                          <TypeBadge type={b.type || 'database'}/>
                      </td>
                        <td className="px-6 py-4 hidden sm:table-cell">
                          <div className="flex items-center gap-2">
                            <FileDown className="w-4 h-4 text-gray-400 flex-shrink-0"/>
                            <span className="text-sm text-gray-700 dark:text-gray-300 font-mono max-w-[200px] truncate"
                                  title={filename}>{filename}</span>
                          </div>
                      </td>
                        <td className="px-6 py-4 hidden md:table-cell">
                          <div className="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400">
                            <Clock className="w-3.5 h-3.5"/>
                            <span>{b.created_at ? new Date(b.created_at).toLocaleString('zh-CN') : '—'}</span>
                          </div>
                          {b.created_at && <span
                            className="text-xs text-gray-400 dark:text-gray-500 dark:text-gray-400 ml-5">{timeAgo(b.created_at)}</span>}
                        </td>
                        <td className="px-6 py-4">
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          {isFull ? (b.database_backup?.size_human || b.files_backup?.size_human || '—') : formatSize(b.size)}
                        </span>
                      </td>
                        <td className="px-6 py-4 text-right">
                          <div
                              className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <a href={downloadUrl}
                               className="p-2 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                               title="下载备份">
                              <Download className="w-4 h-4"/>
                            </a>
                            <button onClick={() => setDeleteTarget(filename)}
                                    className="p-2 text-gray-400 hover:text-red-600 dark:hover:text-red-400 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                                    title="删除备份">
                              <Trash2 className="w-4 h-4"/>
                            </button>
                          </div>
                          {/* Mobile: always visible */}
                          <div className="flex items-center justify-end gap-1 sm:hidden">
                            <a href={downloadUrl}
                               className="p-2 text-gray-400 hover:text-blue-600 rounded-lg hover:bg-blue-50 transition-colors">
                              <Download className="w-4 h-4"/>
                            </a>
                            <button onClick={() => setDeleteTarget(filename)}
                                    className="p-2 text-gray-400 hover:text-red-600 rounded-lg hover:bg-red-50 transition-colors">
                              <Trash2 className="w-4 h-4"/>
                            </button>
                          </div>
                      </td>
                    </tr>
                  );
                })}
                </tbody>
              </table>
          )}
        </div>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between mt-4">
          <span className="text-xs text-gray-400">共 {total} 个备份</span>
          {renderPagination()}
        </div>

        {/* Delete Confirmation Modal */}
        <Modal open={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="确认删除">
          {deleteTarget && (
              <DeleteConfirm
                  filename={deleteTarget}
                  onConfirm={() => delOneMut.mutate(deleteTarget)}
                  onCancel={() => setDeleteTarget(null)}
                  isPending={delOneMut.isPending}
              />
          )}
        </Modal>

        {/* Create Backup Confirmation Modal */}
        <Modal open={!!confirmAction} onClose={() => setConfirmAction(null)} title="确认创建备份">
          {confirmAction && (() => {
            const config = BACKUP_TYPE_CONFIG[confirmAction];
            const Icon = config?.icon || Database;
            const labelMap: Record<string, string> = {database: '数据库', files: '文件', full: '完整系统'};
            const descMap: Record<string, string> = {
              database: '备份数据库数据',
              files: '备份上传文件',
              full: '完整系统备份'
            };
            return (
              <div className="space-y-4">
                <div
                  className="flex items-start gap-3 p-4 rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800/30">
                  <Icon className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5"/>
                  <div>
                    <p
                      className="text-sm font-medium text-blue-800 dark:text-blue-300">确认创建{labelMap[confirmAction]}备份？</p>
                    <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                      即将执行「{descMap[confirmAction]}」操作，备份过程可能需要一些时间。
                    </p>
                  </div>
                </div>
                <div className="flex justify-end gap-2">
                  <button onClick={() => setConfirmAction(null)}
                          className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 rounded-xl hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">取消
                  </button>
                  <button onClick={() => {
                    createMut.mutate(confirmAction);
                    setConfirmAction(null);
                  }}
                          disabled={backingUp !== null}
                          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-xl hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center gap-2">
                    {backingUp !== null && <Loader className="w-3.5 h-3.5 animate-spin"/>}
                    确认备份
                  </button>
                </div>
              </div>
            );
          })()}
        </Modal>

        {/* Cleanup Confirmation Modal */}
        <Modal open={confirmCleanup} onClose={() => setConfirmCleanup(false)} title="确认清理旧备份">
          <div className="space-y-4">
            <div
              className="flex items-start gap-3 p-4 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-100 dark:border-amber-800/30">
              <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5"/>
              <div>
                <p className="text-sm font-medium text-amber-800 dark:text-amber-300">确认清理旧备份？</p>
                <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                  此操作将清理过期的旧备份文件，以释放存储空间。清理后的文件无法恢复。
                </p>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <button onClick={() => setConfirmCleanup(false)}
                      className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 rounded-xl hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">取消
              </button>
              <button onClick={() => {
                delMut.mutate();
                setConfirmCleanup(false);
              }}
                      disabled={delMut.isPending}
                      className="px-4 py-2 text-sm font-medium text-white bg-amber-600 rounded-xl hover:bg-amber-700 transition-colors disabled:opacity-50 flex items-center gap-2">
                {delMut.isPending && <Loader className="w-3.5 h-3.5 animate-spin"/>}
                {delMut.isPending ? '清理中…' : '确认清理'}
              </button>
            </div>
          </div>
        </Modal>
      </AdminShell>
  );
}

export default function AdminBackup() {
  return <AuthGuard><QueryProvider><BackupInner/></QueryProvider></AuthGuard>;
}
