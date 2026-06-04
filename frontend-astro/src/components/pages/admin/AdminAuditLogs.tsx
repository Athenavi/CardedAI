'use client';

import React, {useState, useCallback} from 'react';
import {useQuery} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {apiClient} from '@/lib/api/base-client';
import {useConfirm} from '@/components/ui/confirm-provider';
import {useToast} from '@/components/ui/toast-provider';
import {
  ScrollText, Download, Trash2, Search, Filter, X,
  AlertTriangle, AlertCircle, Info, ShieldAlert,
  ChevronLeft, ChevronRight,
} from 'lucide-react';

// ─── Level badge ──────────────────────────────────────
const levelCfg: Record<string, { bg: string; text: string; icon: React.ComponentType<{ className?: string }> }> = {
  CRITICAL: {bg:'bg-red-100 dark:bg-red-900/20', text:'text-red-700', icon:ShieldAlert},
  ERROR:    {bg:'bg-orange-100 dark:bg-orange-900/20', text:'text-orange-700', icon:AlertCircle},
  WARNING:  {bg:'bg-yellow-100 dark:bg-yellow-900/20', text:'text-yellow-700', icon:AlertTriangle},
  INFO:     {bg:'bg-blue-100 dark:bg-blue-900/20', text:'text-blue-700', icon:Info},
};
const LevelBadge: React.FC<{level:string}> = ({level}) => {
  const cfg = levelCfg[level] || levelCfg.INFO;
  const Icon = cfg.icon;
  return <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full font-medium ${cfg.bg} ${cfg.text}`}><Icon className="w-3 h-3"/>{level}</span>;
};

// ─── Action badge ─────────────────────────────────────
const actionLabels: Record<string,string> = {
  LOGIN: '登录', LOGOUT: '登出', CREATE: '创建', UPDATE: '更新',
  DELETE: '删除', VIEW: '查看', EXPORT: '导出', IMPORT: '导入',
  CONFIG_CHANGE: '配置变更', PERMISSION_CHANGE: '权限变更', SECURITY_EVENT: '安全事件',
};
const ActionBadge: React.FC<{action:string}> = ({action}) => (
  <span className="px-2 py-0.5 text-xs rounded-full bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 font-medium">
    {actionLabels[action] || action}
  </span>
);

// ─── Stat card ────────────────────────────────────────
const StatCard: React.FC<{
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: number | string;
  color?: string
}> = ({icon: Icon, label, value, color}) => (
  <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-4">
    <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-1"><Icon
      className={`w-4 h-4 ${color || ''}`}/>{label}</div>
    <p className="text-2xl font-bold text-gray-900 dark:text-white">{value ?? '—'}</p>
  </div>
);

// ─── Pagination ───────────────────────────────────────
const Pagination: React.FC<{page:number;total:number;perPage:number;onChange:(p:number)=>void}> = ({page,total,perPage,onChange}) => {
  const totalPages = Math.ceil(total / perPage);
  if (totalPages <= 1) return null;
  return (
    <div className="flex items-center justify-between px-5 py-3 border-t border-gray-100 dark:border-gray-800">
      <span className="text-xs text-gray-500 dark:text-gray-400">共 {total} 条</span>
      <div className="flex items-center gap-1">
        <button disabled={page <= 1} onClick={() => onChange(page - 1)}
                className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-30"><ChevronLeft
          className="w-4 h-4 text-gray-500 dark:text-gray-400"/></button>
        {Array.from({length:Math.min(totalPages,7)},(_,i)=>{
          let p:number;
          if (totalPages<=7) p = i+1;
          else if (page<=4) p = i+1;
          else if (page>=totalPages-3) p = totalPages-6+i;
          else p = page-3+i;
          return <button key={p} onClick={()=>onChange(p)} className={`w-8 h-8 text-xs rounded-lg ${p===page?'bg-blue-600 text-white':'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'}`}>{p}</button>;
        })}
        <button disabled={page >= totalPages} onClick={() => onChange(page + 1)}
                className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-30"><ChevronRight
          className="w-4 h-4 text-gray-500 dark:text-gray-400"/></button>
      </div>
    </div>
  );
};

// ─── Main component ───────────────────────────────────
function AuditLogsInner() {
  const confirm = useConfirm();
  const toast = useToast();
  const [page, setPage] = useState(1);
  const [searchUser, setSearchUser] = useState('');
  const [filterAction, setFilterAction] = useState('');
  const [filterLevel, setFilterLevel] = useState('');
  const [filterExpanded, setFilterExpanded] = useState(false);

  // Build query params
  const params: Record<string,any> = {page, per_page: 20};
  if (searchUser) params.user_id = searchUser;
  if (filterAction) params.action = filterAction;
  if (filterLevel) params.level = filterLevel;

  const {data, isLoading, refetch} = useQuery({
    queryKey: ['admin-audit-logs', page, searchUser, filterAction, filterLevel],
    queryFn: async () => {
      const res = await apiClient.get('/security/audit-log/logs', params);
      return res.success && res.data ? res.data : {logs: [], pagination: {total: 0}};
    },
  });

  const {data: statsData} = useQuery({
    queryKey: ['admin-audit-logs-stats'],
    queryFn: async () => {
      const res = await apiClient.get('/security/audit-log/stats', {days: 30});
      return res.success && res.data ? res.data : {total_logs: 0, active_users: 0, by_action: [], by_level: []};
    },
    staleTime: 60_000,
  });

  const logs = Array.isArray(data?.logs) ? data.logs : [];
  const pagination = data?.pagination || {total: 0};
  const stats = statsData || {};

  const handleExport = useCallback(async () => {
    const res = await apiClient.get('/security/audit-log/export', {page, per_page: 200, ...filterAction && {action: filterAction}, ...filterLevel && {level: filterLevel}});
    if (res.success && res.data) {
      const blob = new Blob([JSON.stringify(res.data, null, 2)], {type: 'application/json'});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = `audit-logs-${Date.now()}.json`; a.click();
      URL.revokeObjectURL(url);
    }
  }, [page, filterAction, filterLevel]);

  const handleCleanup = useCallback(async () => {
    if (!await confirm({message: '确定清理 90 天前的审计日志？此操作不可撤销。', variant: 'warning'})) return;
    const res = await apiClient.post('/security/audit-log/cleanup', {days: 90});
    if (res.success) {
      toast.success('清理完成');
      refetch();
    } else if (res.error) toast.error(res.error || '操作失败');
  }, [refetch]);

  const resetFilters = () => { setSearchUser(''); setFilterAction(''); setFilterLevel(''); setPage(1); };

  // Get level breakdown for stats
  const levelStats: Record<string,number> = {};
  (stats.by_level || []).forEach((s) => {
    levelStats[s.level] = s.count;
  });

  return (
    <AdminShell title="审计日志">
      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard icon={ScrollText} label="30 天日志总量" value={stats.total_logs ?? '—'} />
        <StatCard icon={Info} label="INFO" value={levelStats.INFO||0} color="text-blue-500" />
        <StatCard icon={AlertTriangle} label="WARNING" value={levelStats.WARNING||0} color="text-yellow-500" />
        <StatCard icon={AlertCircle} label="ERROR+CRITICAL" value={(levelStats.ERROR||0)+(levelStats.CRITICAL||0)} color="text-red-500" />
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 mb-4">
        <div className="flex items-center gap-2 px-5 py-3 border-b border-gray-100 dark:border-gray-800">
          <button onClick={() => setFilterExpanded(!filterExpanded)}
                  className="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300">
            <Filter className="w-4 h-4"/><span className="hidden sm:inline">筛选</span>
          </button>
          <div className="flex-1" />
          <button onClick={handleExport} className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800" title="导出 JSON"><Download className="w-4 h-4"/></button>
          <button onClick={handleCleanup} className="p-1.5 text-gray-400 hover:text-red-500 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800" title="清理旧日志"><Trash2 className="w-4 h-4"/></button>
        </div>
        {filterExpanded && (
          <div className="px-5 py-3 flex flex-wrap gap-3">
            <div className="relative flex-1 min-w-[160px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
              <input type="text" value={searchUser} onChange={e=>{setSearchUser(e.target.value);setPage(1);}} placeholder="用户 ID" className="w-full pl-9 pr-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white placeholder-gray-400"/>
            </div>
            <select value={filterAction} onChange={e=>{setFilterAction(e.target.value);setPage(1);}} className="px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white">
              <option value="">所有操作</option>
              <option value="LOGIN">登录</option><option value="LOGOUT">登出</option>
              <option value="CREATE">创建</option><option value="UPDATE">更新</option>
              <option value="DELETE">删除</option><option value="VIEW">查看</option>
              <option value="EXPORT">导出</option><option value="IMPORT">导入</option>
              <option value="CONFIG_CHANGE">配置变更</option>
              <option value="PERMISSION_CHANGE">权限变更</option>
              <option value="SECURITY_EVENT">安全事件</option>
            </select>
            <select value={filterLevel} onChange={e=>{setFilterLevel(e.target.value);setPage(1);}} className="px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white">
              <option value="">所有级别</option>
              <option value="INFO">INFO</option><option value="WARNING">WARNING</option>
              <option value="ERROR">ERROR</option><option value="CRITICAL">CRITICAL</option>
            </select>
            <button onClick={resetFilters}
                    className="px-3 py-2 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 flex items-center gap-1">
              <X className="w-3.5 h-3.5"/>重置
            </button>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center"><div className="animate-spin w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full mx-auto"/></div>
        ) : !logs.length ? (
          <div className="p-12 text-center text-gray-400"><ScrollText className="w-10 h-10 mx-auto mb-3 opacity-50"/><p>暂无审计日志</p></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full"><thead className="bg-gray-50 dark:bg-gray-800 border-b">
              <tr>
                <th
                  className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">用户
                </th>
                <th
                  className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">级别
                </th>
                <th
                  className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">操作
                </th>
                <th
                  className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase hidden sm:table-cell">详情
                </th>
                <th
                  className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase hidden lg:table-cell">资源
                </th>
                <th
                  className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase hidden md:table-cell">IP
                </th>
                <th
                  className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase whitespace-nowrap">时间
                </th>
              </tr>
            </thead><tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {logs.map((log) => (
                <tr key={log.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 text-sm">
                  <td className="px-5 py-3">
                    <div>
                      <span className="font-medium text-gray-900 dark:text-white">{log.user_name || '—'}</span>
                      {log.user_id && <span className="text-xs text-gray-400 ml-1">#{log.user_id}</span>}
                    </div>
                  </td>
                  <td className="px-5 py-3"><LevelBadge level={log.level||'INFO'} /></td>
                  <td className="px-5 py-3"><ActionBadge action={log.action} /></td>
                  <td className="px-5 py-3 text-gray-500 dark:text-gray-400 hidden sm:table-cell max-w-[200px] truncate"
                      title={log.description || ''}>{log.description || '-'}</td>
                  <td className="px-5 py-3 text-gray-500 dark:text-gray-400 hidden lg:table-cell text-xs">
                    {log.resource_type ? <><span className="text-gray-400">{log.resource_type}</span>{log.resource_id ? <span className="text-gray-300">/{log.resource_id}</span> : null}</> : '-'}
                  </td>
                  <td className="px-5 py-3 text-gray-400 font-mono text-xs hidden md:table-cell">{log.ip_address || '-'}</td>
                  <td
                    className="px-5 py-3 text-gray-500 dark:text-gray-400 whitespace-nowrap text-xs">{log.created_at ? new Date(log.created_at).toLocaleString('zh-CN') : '-'}</td>
                </tr>
              ))}
            </tbody></table>
          </div>
        )}
        <Pagination page={page} total={pagination.total||0} perPage={20} onChange={setPage} />
      </div>
    </AdminShell>
  );
}

export default function AdminAuditLogs() {
  return <AuthGuard><QueryProvider><AuditLogsInner /></QueryProvider></AuthGuard>;
}
