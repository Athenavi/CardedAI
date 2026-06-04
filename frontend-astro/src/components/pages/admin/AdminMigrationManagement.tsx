'use client';

import React, {useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {DeleteConfirm, EmptyState, Modal} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import {useToast} from '@/components/ui/toast-provider';
import {
  AlertCircle,
  ArrowRightLeft,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
  Clock,
  Edit3,
  Pause,
  Play,
  Plus,
  ScrollText,
  Search,
  Trash2,
  XCircle
} from 'lucide-react';
import type {ApiResponse} from '@/lib/api/base-types';
/* ─── Types ─────────────────────────────────────── */
interface MigrationTask {
  id: number;
  task_name: string;
  source_platform?: string;
  status: string;
  config?: string;
  progress: number;
  total_items: number;
  migrated_items: number;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_by?: number;
  created_at?: string;
  updated_at?: string;
}

interface MigrationLog {
  id: number;
  task_id: number;
  log_level: string;
  message: string;
  item_type?: string;
  item_id?: number;
  created_at?: string;
}

interface Pagination {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

/* ─── Helpers ───────────────────────────────────── */
const Input: React.FC<{
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
  rows?: number
}> = ({label, value, onChange, type, placeholder, rows}) => (
  <div className="mb-3">
    <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">{label}</label>
    {rows ? (
      <textarea rows={rows} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white placeholder-gray-400 resize-none"/>
    ) : (
      <input type={type || 'text'} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
             className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white placeholder-gray-400"/>
    )}
  </div>
);

const StatusIcon: React.FC<{ status: string }> = ({status}) => {
  switch (status) {
    case 'completed':
      return <CheckCircle className="w-4 h-4 text-green-500"/>;
    case 'running':
      return <Play className="w-4 h-4 text-blue-500"/>;
    case 'failed':
      return <XCircle className="w-4 h-4 text-red-500"/>;
    case 'paused':
      return <Pause className="w-4 h-4 text-yellow-500"/>;
    default:
      return <Clock className="w-4 h-4 text-gray-400"/>;
  }
};

const StatusBadge: React.FC<{ status: string }> = ({status}) => {
  const colors: Record<string, string> = {
    completed: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
    running: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
    pending: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400',
    failed: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400',
    paused: 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400',
  };
  const labels: Record<string, string> = {
    completed: '已完成', running: '运行中', pending: '等待中', failed: '失败', paused: '已暂停',
  };
  return <span
    className={`px-2 py-0.5 text-[10px] rounded-full font-medium ${colors[status] || 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'}`}>{labels[status] || status}</span>;
};

const LogLevelBadge: React.FC<{ level: string }> = ({level}) => {
  const colors: Record<string, string> = {
    error: 'text-red-600 dark:text-red-400',
    warning: 'text-yellow-600 dark:text-yellow-400',
    info: 'text-blue-600 dark:text-blue-400',
    debug: 'text-gray-400',
  };
  return <span
    className={`text-[10px] font-mono font-semibold uppercase ${colors[level] || 'text-gray-500 dark:text-gray-400'}`}>{level}</span>;
};

/* ─── Tasks Tab ─────────────────────────────────── */
const TasksTab: React.FC = () => {
  const qc = useQueryClient();
  const toast = useToast();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<MigrationTask | null>(null);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [viewLogsId, setViewLogsId] = useState<number | null>(null);
  const [form, setForm] = useState({task_name: '', source_platform: '', config: '{}', status: 'pending'});

  const {data, isLoading} = useQuery({
    queryKey: ['migration-tasks', page, search, statusFilter],
    queryFn: () => apiClient.get('/migration-management/tasks', {
      page,
      per_page: 15,
      search: search || undefined,
      status: statusFilter || undefined
    }),
  });

  const items: MigrationTask[] = data?.data?.tasks || [];
  const pagination: Pagination | undefined = data?.data?.pagination;

  const createMut = useMutation({
    mutationFn: (d: any) => apiClient.post('/migration-management/tasks', d),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['migration-tasks']});
        setShowForm(false);
      } else toast.error(r.error || '操作失败');
    },
  });
  const updateMut = useMutation({
    mutationFn: ({id, ...d}: any) => apiClient.put(`/migration-management/tasks/${id}`, d),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['migration-tasks']});
        setShowForm(false);
      } else toast.error(r.error || '操作失败');
    },
  });
  const deleteMut = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/migration-management/tasks/${id}`),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['migration-tasks']});
        setDeleteId(null);
      } else toast.error(r.error || '操作失败');
    },
  });

  const openCreate = () => {
    setEditing(null);
    setForm({task_name: '', source_platform: '', config: '{}', status: 'pending'});
    setShowForm(true);
  };
  const openEdit = (t: MigrationTask) => {
    setEditing(t);
    setForm({
      task_name: t.task_name,
      source_platform: t.source_platform || '',
      config: t.config || '{}',
      status: t.status
    });
    setShowForm(true);
  };
  const submit = () => {
    if (!form.task_name.trim()) {
      toast.error('请填写任务名称');
      return;
    }
    if (editing) updateMut.mutate({id: editing.id, ...form});
    else createMut.mutate(form);
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
                   placeholder="搜索任务..."
                   className="pl-9 pr-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white w-48"/>
          </div>
          <select value={statusFilter} onChange={e => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
                  className="px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white">
            <option value="">全部状态</option>
            <option value="pending">等待中</option>
            <option value="running">运行中</option>
            <option value="completed">已完成</option>
            <option value="failed">失败</option>
            <option value="paused">已暂停</option>
          </select>
        </div>
        <button onClick={openCreate}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-xl flex items-center gap-1.5">
          <Plus className="w-4 h-4"/>新建任务
        </button>
      </div>
      {isLoading ? <div className="animate-pulse space-y-2">{[1, 2, 3].map(i => <div key={i}
                                                                                     className="h-20 bg-gray-100 dark:bg-gray-800 rounded-xl"/>)}</div> :
        items.length === 0 ?
          <EmptyState icon={ArrowRightLeft} title="暂无迁移任务" desc="创建迁移任务以开始数据迁移"/> :
          <div className="space-y-3">
            {items.map(t => (
              <div key={t.id}
                   className="bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-100 dark:border-gray-700/50 p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <StatusIcon status={t.status}/>
                    <div>
                      <h4 className="text-sm font-semibold text-gray-900 dark:text-white">{t.task_name}</h4>
                      <div className="flex items-center gap-2 mt-0.5">
                        {t.source_platform && <span
                          className="text-[10px] bg-gray-200 dark:bg-gray-700 px-1.5 py-0.5 rounded text-gray-600 dark:text-gray-300">{t.source_platform}</span>}
                        <StatusBadge status={t.status}/>
                        <span
                          className="text-[10px] text-gray-400">{t.created_at ? new Date(t.created_at).toLocaleString('zh-CN') : ''}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <button onClick={() => setViewLogsId(viewLogsId === t.id ? null : t.id)}
                            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-400"
                            title="查看日志"><ScrollText className="w-3.5 h-3.5"/></button>
                    <button onClick={() => openEdit(t)}
                            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-400">
                      <Edit3
                      className="w-3.5 h-3.5"/></button>
                    <button onClick={() => setDeleteId(t.id)}
                            className="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 text-red-500"><Trash2
                      className="w-3.5 h-3.5"/></button>
                  </div>
                </div>
                {/* Progress bar */}
                {t.total_items > 0 && (
                  <div className="mt-3">
                    <div
                      className="flex items-center justify-between text-[10px] text-gray-500 dark:text-gray-400 mb-1">
                      <span>{t.migrated_items}/{t.total_items} 项</span>
                      <span>{t.progress}%</span>
                    </div>
                    <div className="h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500 rounded-full transition-all"
                           style={{width: `${t.progress}%`}}/>
                    </div>
                  </div>
                )}
                {t.error_message && (
                  <div
                    className="mt-2 p-2 bg-red-50 dark:bg-red-900/10 rounded-lg text-xs text-red-600 dark:text-red-400 flex items-start gap-2">
                    <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5"/>{t.error_message}
                  </div>
                )}
                {viewLogsId === t.id && <TaskLogs taskId={t.id}/>}
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
      <Modal open={showForm} onClose={() => setShowForm(false)} title={editing ? '编辑迁移任务' : '新建迁移任务'}>
        <Input label="任务名称 *" value={form.task_name} onChange={v => setForm({...form, task_name: v})}
               placeholder="例如：WordPress 全站迁移"/>
        <Input label="源平台" value={form.source_platform} onChange={v => setForm({...form, source_platform: v})}
               placeholder="例如：wordpress"/>
        <Input label="配置 (JSON)" value={form.config} onChange={v => setForm({...form, config: v})} rows={3}/>
        {editing && (
          <div className="mb-3">
            <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">状态</label>
            <select value={form.status} onChange={e => setForm({...form, status: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white">
              <option value="pending">等待中</option>
              <option value="running">运行中</option>
              <option value="completed">已完成</option>
              <option value="failed">失败</option>
              <option value="paused">已暂停</option>
            </select>
          </div>
        )}
        <div className="flex justify-end gap-2 mt-4">
          <button onClick={() => setShowForm(false)}
                  className="px-4 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-300">取消
          </button>
          <button onClick={submit}
                  className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg">{editing ? '更新' : '创建'}</button>
        </div>
      </Modal>
      {deleteId !== null && (
        <Modal open={true} onClose={() => setDeleteId(null)} title="确认删除">
          <DeleteConfirm itemName={items.find(t => t.id === deleteId)?.task_name}
                         onConfirm={() => deleteMut.mutate(deleteId)} onCancel={() => setDeleteId(null)}
                         isPending={deleteMut.isPending}/>
        </Modal>
      )}
    </>
  );
};

/* ─── Task Logs Inline ─────────────────────────── */
const TaskLogs: React.FC<{ taskId: number }> = ({taskId}) => {
  const {data, isLoading} = useQuery({
    queryKey: ['migration-logs', taskId],
    queryFn: () => apiClient.get('/migration-management/logs', {task_id: taskId, per_page: 50}),
  });
  const logs: MigrationLog[] = data?.data?.logs || [];
  if (isLoading) return <div className="mt-3 animate-pulse h-20 bg-gray-100 dark:bg-gray-800 rounded-lg"/>;
  if (logs.length === 0) return <div className="mt-3 text-xs text-gray-400 p-3">暂无日志</div>;
  return (
    <div className="mt-3 bg-gray-900 dark:bg-black rounded-lg p-3 max-h-48 overflow-y-auto">
      {logs.map(l => (
        <div key={l.id} className="flex items-start gap-2 py-1">
          <LogLevelBadge level={l.log_level}/>
          <span className="text-[11px] text-gray-300 font-mono">{l.message}</span>
          {l.item_type &&
            <span className="text-[10px] text-gray-500 dark:text-gray-400">[{l.item_type}#{l.item_id}]</span>}
        </div>
      ))}
    </div>
  );
};

/* ─── Logs Tab ──────────────────────────────────── */
const LogsTab: React.FC = () => {
  const [page, setPage] = useState(1);
  const [levelFilter, setLevelFilter] = useState('');
  const qc = useQueryClient();

  const {data, isLoading} = useQuery({
    queryKey: ['migration-all-logs', page, levelFilter],
    queryFn: () => apiClient.get('/migration-management/logs', {
      page,
      per_page: 20,
      log_level: levelFilter || undefined
    }),
  });

  const items: MigrationLog[] = data?.data?.logs || [];
  const pagination: Pagination | undefined = data?.data?.pagination;

  const deleteMut = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/migration-management/logs/${id}`),
    onSuccess: () => qc.invalidateQueries({queryKey: ['migration-all-logs']}),
  });

  return (
    <>
      <div className="flex items-center gap-2 mb-4">
        <select value={levelFilter} onChange={e => {
          setLevelFilter(e.target.value);
          setPage(1);
        }}
                className="px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white">
          <option value="">全部级别</option>
          <option value="info">Info</option>
          <option value="warning">Warning</option>
          <option value="error">Error</option>
          <option value="debug">Debug</option>
        </select>
      </div>
      {isLoading ? <div className="animate-pulse space-y-2">{[1, 2, 3, 4].map(i => <div key={i}
                                                                                        className="h-12 bg-gray-100 dark:bg-gray-800 rounded-xl"/>)}</div> :
        items.length === 0 ? <EmptyState icon={ScrollText} title="暂无日志" desc="迁移日志将在此显示"/> :
          <div className="bg-gray-900 dark:bg-black rounded-xl p-4 max-h-96 overflow-y-auto">
            {items.map(l => (
              <div key={l.id} className="flex items-start gap-2 py-1.5 border-b border-gray-800 last:border-0 group">
                <LogLevelBadge level={l.log_level}/>
                <span className="text-[11px] text-gray-300 font-mono flex-1">{l.message}</span>
                {l.item_type &&
                  <span className="text-[10px] text-gray-500 dark:text-gray-400">[{l.item_type}#{l.item_id}]</span>}
                <span
                  className="text-[10px] text-gray-600">{l.created_at ? new Date(l.created_at).toLocaleString('zh-CN') : ''}</span>
                <button onClick={() => deleteMut.mutate(l.id)}
                        className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-900/30 text-red-400 transition-opacity">
                  <Trash2 className="w-3 h-3"/></button>
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

/* ─── Main Component ───────────────────────────── */
type TabKey = 'tasks' | 'logs';
const TABS: { key: TabKey; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  {key: 'tasks', label: '迁移任务', icon: ArrowRightLeft},
  {key: 'logs', label: '迁移日志', icon: ScrollText},
];

function MigrationManagementInner() {
  const [tab, setTab] = useState<TabKey>('tasks');

  return (
    <AdminShell title="迁移管理" actions={<ArrowRightLeft className="w-5 h-5 text-blue-500"/>}>
      <div className="space-y-6">
        <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 rounded-xl p-1">
          {TABS.map(t => (
            <button key={t.key} onClick={() => setTab(t.key)}
                    className={`flex-1 flex items-center justify-center gap-1.5 px-4 py-2.5 text-sm rounded-lg transition-colors ${tab === t.key ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm font-medium' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'}`}>
              <t.icon className="w-4 h-4"/>
              {t.label}
            </button>
          ))}
        </div>
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-5">
          {tab === 'tasks' && <TasksTab/>}
          {tab === 'logs' && <LogsTab/>}
        </div>
      </div>
    </AdminShell>
  );
}

export default function AdminMigrationManagement() {
  return (
    <AuthGuard>
      <QueryProvider>
        <MigrationManagementInner/>
      </QueryProvider>
    </AuthGuard>
  );
}
