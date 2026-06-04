'use client';

import React, {useState, useMemo, useEffect} from 'react';
import {useQuery, useQueryClient} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {apiClient} from '@/lib/api/base-client';
import {useDebounce} from '@/lib/hooks';
import {StatCard} from '@/components/admin/shared-ui';
import {
  Shield,
  AlertTriangle,
  Activity,
  Users,
  Lock,
  Eye,
  Filter,
  Download,
  RefreshCw,
  Search,
  Clock,
  Globe,
  Zap,
  ChevronDown,
  X,
  ChevronLeft,
  ChevronRight,
  Loader2,
  CheckCircle,
  XCircle,
  Info,
  Ban,
  UserX,
  FileText,
  Database,
  Settings,
  ArrowUpRight,
  TrendingUp,
  ShieldAlert,
  Fingerprint,
  Network,
  Server
} from 'lucide-react';

/* ─── Interfaces ─── */
interface AuditLog {
  id: number;
  user_id?: number;
  username?: string;
  action: string;
  resource_type?: string;
  resource_id?: number;
  ip_address?: string;
  user_agent?: string;
  request_data?: any;
  status: 'success' | 'failure';
  error_message?: string;
  created_at: string;
  risk_level?: 'low' | 'medium' | 'high' | 'critical';
}


const ACTION_OPTIONS = [
  {key: 'all', label: '全部动作', icon: Activity},
  {key: 'login', label: '登录', icon: Lock},
  {key: 'create', label: '创建', icon: FileText},
  {key: 'update', label: '更新', icon: Settings},
  {key: 'delete', label: '删除', icon: AlertTriangle},
  {key: 'export', label: '导出', icon: Download},
];

const STATUS_OPTIONS = [
  {key: 'all', label: '全部状态'},
  {key: 'success', label: '成功'},
  {key: 'failure', label: '失败'},
];

const RISK_CONFIG: Record<string, {
  label: string;
  color: string;
  bg: string;
  icon: React.ComponentType<{ className?: string }>
}> = {
  low: {
    label: '低风险',
    color: 'text-green-600 dark:text-green-400',
    bg: 'bg-green-100 dark:bg-green-900/30',
    icon: CheckCircle
  },
  medium: {
    label: '中风险',
    color: 'text-amber-600 dark:text-amber-400',
    bg: 'bg-amber-100 dark:bg-amber-900/30',
    icon: AlertTriangle
  },
  high: {
    label: '高风险',
    color: 'text-red-600 dark:text-red-400',
    bg: 'bg-red-100 dark:bg-red-900/30',
    icon: ShieldAlert
  },
  critical: {label: '严重', color: 'text-red-700 dark:text-red-300', bg: 'bg-red-200 dark:bg-red-900/50', icon: Ban},
};


/* ─── Skeleton ─── */
const LogSkeleton = () => (
    <div className="divide-y divide-gray-100 dark:divide-gray-800">
      {[1, 2, 3, 4, 5, 6, 7, 8].map(i => (
          <div key={i} className="px-5 py-4 animate-pulse">
            <div className="flex items-center gap-4">
              <div className="w-8 h-8 rounded-lg bg-gray-200 dark:bg-gray-700"/>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4"/>
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/3"/>
              </div>
              <div className="w-16 h-6 bg-gray-200 dark:bg-gray-700 rounded-full"/>
              <div className="w-24 h-4 bg-gray-200 dark:bg-gray-700 rounded hidden sm:block"/>
            </div>
          </div>
      ))}
    </div>
);

/* ─── Action Icon ─── */
const ActionBadge: React.FC<{ action: string }> = ({action}) => {
  const getActionConfig = (a: string) => {
    if (a.includes('login')) return {icon: Lock, color: 'from-blue-500 to-blue-600', label: '登录'};
    if (a.includes('logout')) return {icon: UserX, color: 'from-gray-500 to-gray-600', label: '登出'};
    if (a.includes('create')) return {icon: FileText, color: 'from-green-500 to-emerald-600', label: '创建'};
    if (a.includes('update')) return {icon: Settings, color: 'from-amber-500 to-orange-600', label: '更新'};
    if (a.includes('delete')) return {icon: AlertTriangle, color: 'from-red-500 to-rose-600', label: '删除'};
    if (a.includes('export')) return {icon: Download, color: 'from-purple-500 to-violet-600', label: '导出'};
    if (a.includes('access')) return {icon: Eye, color: 'from-cyan-500 to-teal-600', label: '访问'};
    return {icon: Activity, color: 'from-gray-500 to-gray-600', label: a};
  };
  const config = getActionConfig(action);
  const Icon = config.icon;
  return (
      <div className="flex items-center gap-2.5">
        <div
            className={`w-8 h-8 rounded-lg bg-gradient-to-br ${config.color} flex items-center justify-center flex-shrink-0`}>
          <Icon className="w-4 h-4 text-white"/>
        </div>
        <div>
          <span className="text-sm font-medium text-gray-900 dark:text-white">{config.label}</span>
          <span className="block text-[10px] text-gray-400 font-mono">{action}</span>
        </div>
      </div>
  );
};

/* ─── Log Detail Modal ─── */
const LogDetailModal: React.FC<{ log: AuditLog; onClose: () => void }> = ({log, onClose}) => {
  const riskConfig = RISK_CONFIG[log.risk_level || 'low'];
  const RiskIcon = riskConfig.icon;

  return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose}/>
        <div
            className="relative bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-2xl border border-gray-200 dark:border-gray-700 overflow-hidden max-h-[85vh] flex flex-col">
          {/* Header */}
          <div
              className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex-shrink-0">
            <div className="flex items-center gap-3">
              <div
                  className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
                <Shield className="w-5 h-5 text-white"/>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">审计日志详情</h3>
                <p className="text-xs text-gray-400">ID: #{log.id}</p>
              </div>
            </div>
            <button onClick={onClose}
                    className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
              <X className="w-5 h-5"/>
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-5">
            {/* Risk & Status */}
            <div className="flex items-center gap-3">
            <span
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium ${riskConfig.bg} ${riskConfig.color}`}>
              <RiskIcon className="w-3.5 h-3.5"/>
              {riskConfig.label}
            </span>
              <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium ${
                  log.status === 'success'
                      ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                      : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
              }`}>
              {log.status === 'success' ? <CheckCircle className="w-3.5 h-3.5"/> : <XCircle className="w-3.5 h-3.5"/>}
                {log.status === 'success' ? '成功' : '失败'}
            </span>
            </div>

            {/* Info Grid */}
            <div className="grid grid-cols-2 gap-4">
              {[
                {label: '动作', value: log.action, icon: Activity},
                {label: '用户 ID', value: log.user_id || 'N/A', icon: Users},
                {label: 'IP 地址', value: log.ip_address || 'N/A', icon: Globe, mono: true},
                {label: '时间', value: new Date(log.created_at).toLocaleString('zh-CN'), icon: Clock},
              ].map(item => (
                  <div key={item.label} className="bg-gray-50 dark:bg-gray-800/50 rounded-xl p-3">
                    <div className="flex items-center gap-1.5 mb-1">
                      <item.icon className="w-3.5 h-3.5 text-gray-400"/>
                      <span className="text-xs text-gray-500 dark:text-gray-400">{item.label}</span>
                    </div>
                    <p className={`text-sm font-medium text-gray-900 dark:text-white ${item.mono ? 'font-mono' : ''}`}>
                      {item.value}
                    </p>
                  </div>
              ))}
            </div>

            {log.resource_type && (
                <div className="bg-gray-50 dark:bg-gray-800/50 rounded-xl p-3">
                  <div className="flex items-center gap-1.5 mb-1">
                    <Database className="w-3.5 h-3.5 text-gray-400"/>
                    <span className="text-xs text-gray-500 dark:text-gray-400">资源</span>
                  </div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {log.resource_type} #{log.resource_id}
                  </p>
                </div>
            )}

            {log.user_agent && (
                <div className="bg-gray-50 dark:bg-gray-800/50 rounded-xl p-3">
                  <div className="flex items-center gap-1.5 mb-1">
                    <Fingerprint className="w-3.5 h-3.5 text-gray-400"/>
                    <span className="text-xs text-gray-500 dark:text-gray-400">User Agent</span>
                  </div>
                  <p className="text-xs font-mono text-gray-700 dark:text-gray-300 break-all">{log.user_agent}</p>
                </div>
            )}

            {log.request_data && (
                <div className="bg-gray-50 dark:bg-gray-800/50 rounded-xl p-3">
                  <div className="flex items-center gap-1.5 mb-2">
                    <Network className="w-3.5 h-3.5 text-gray-400"/>
                    <span className="text-xs text-gray-500 dark:text-gray-400">请求数据</span>
                  </div>
                  <pre
                      className="bg-gray-100 dark:bg-gray-800 p-3 rounded-lg text-xs font-mono overflow-x-auto text-gray-700 dark:text-gray-300">
                {JSON.stringify(log.request_data, null, 2)}
              </pre>
                </div>
            )}

            {log.error_message && (
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4">
                  <div className="flex items-center gap-1.5 mb-2">
                    <AlertTriangle className="w-4 h-4 text-red-500"/>
                    <span className="text-xs font-medium text-red-700 dark:text-red-300">错误信息</span>
                  </div>
                  <p className="text-sm text-red-600 dark:text-red-400">{log.error_message}</p>
                </div>
            )}
          </div>
        </div>
      </div>
  );
};

/* ─── Main Component ─── */
function SecurityDashboardInner() {
  const __qc = useQueryClient();
  const [filterAction, setFilterAction] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [search, setSearch] = useState('');
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const debouncedSearch = useDebounce(search, 300);

  /* ─── Data fetching ─── */
  const {data: summary, refetch: refetchSummary} = useQuery({
    queryKey: ['security-summary'],
    queryFn: async () => {
      const res = await apiClient.get('/security/dashboard/summary');
      return (res as any).data || (res as any) || {};
    },
  });

  const {data: auditLogsRaw, isLoading: logsLoading, refetch: refetchLogs} = useQuery({
    queryKey: ['audit-logs', filterAction, filterStatus],
    queryFn: async () => {
      const params: any = {};
      if (filterAction !== 'all') params.action = filterAction;
      if (filterStatus !== 'all') params.status = filterStatus;
      const res = await apiClient.get('/security/audit/logs', {params});
      return (res as any).data || (res as any) || [];
    },
  });

  /* ─── Auto refresh ─── */
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      refetchSummary();
      refetchLogs();
    }, 30000);
    return () => clearInterval(interval);
  }, [autoRefresh, refetchSummary, refetchLogs]);

  /* ─── Filtered logs ─── */
  const auditLogs = useMemo(() => {
    const logs = Array.isArray(auditLogsRaw) ? auditLogsRaw : [];
    if (!debouncedSearch) return logs;
    const q = debouncedSearch.toLowerCase();
    return logs.filter((log: AuditLog) =>
        (log.action || '').toLowerCase().includes(q) ||
        (log.ip_address || '').toLowerCase().includes(q) ||
        (log.username || '').toLowerCase().includes(q) ||
        (log.resource_type || '').toLowerCase().includes(q)
    );
  }, [auditLogsRaw, debouncedSearch]);

  /* ─── Stats ─── */
  const stats = useMemo(() => ({
    total: summary?.total_actions_24h || 0,
    failedLogins: summary?.failed_logins_24h || 0,
    suspiciousIPs: summary?.suspicious_ips?.length || 0,
    criticalEvents: summary?.recent_critical_events?.length || 0,
    threatScore: summary?.threat_score || 0,
    activeSessions: summary?.active_sessions || 0,
    blockedAttempts: summary?.blocked_attempts || 0,
  }), [summary]);

  /* ─── Export CSV ─── */
  const exportLogs = () => {
    if (!auditLogs?.length) return;
    const csv = [
      ['ID', '用户ID', '用户名', '动作', '资源类型', '资源ID', 'IP地址', '状态', '风险等级', '时间'].join(','),
      ...auditLogs.map((log: AuditLog) => [
        log.id,
        log.user_id || '',
        log.username || '',
        log.action,
        log.resource_type || '',
        log.resource_id || '',
        log.ip_address || '',
        log.status,
        log.risk_level || 'low',
        log.created_at
      ].join(','))
    ].join('\n');

    const BOM = '\uFEFF';
    const blob = new Blob([BOM + csv], {type: 'text/csv;charset=utf-8'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `security-audit-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
      <AdminShell title="安全监控中心" actions={
        <div className="flex items-center gap-2">
          <button
              onClick={() => {
                refetchSummary();
                refetchLogs();
              }}
              className="p-2.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-colors"
              title="刷新"
          >
            <RefreshCw className="w-4 h-4"/>
          </button>
          <button
              onClick={exportLogs}
              disabled={!auditLogs?.length}
              className="px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-xl flex items-center gap-1.5 transition-colors disabled:opacity-50"
          >
            <Download className="w-4 h-4"/>
            导出日志
          </button>
          <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-3 py-2 text-sm font-medium rounded-xl flex items-center gap-1.5 transition-colors ${
                  autoRefresh
                      ? 'text-green-700 dark:text-green-300 bg-green-100 dark:bg-green-900/30'
                      : 'text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
          >
            <Zap className={`w-4 h-4 ${autoRefresh ? 'text-green-600' : ''}`}/>
            {autoRefresh ? '自动刷新中' : '自动刷新'}
          </button>
        </div>
      }>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <StatCard icon={Activity} label="24h 操作总数" value={stats.total} gradient="from-blue-500 to-blue-600"
                    subtitle="所有审计事件"/>
          <StatCard icon={Lock} label="失败登录" value={stats.failedLogins} gradient="from-red-500 to-rose-600"
                    subtitle="近24小时" trend={stats.failedLogins > 10 ? 15 : undefined}/>
          <StatCard icon={Globe} label="可疑 IP" value={stats.suspiciousIPs} gradient="from-amber-500 to-orange-500"
                    subtitle="需要关注"/>
          <StatCard icon={Shield} label="严重事件" value={stats.criticalEvents} gradient="from-purple-500 to-violet-600"
                    subtitle="高风险操作"/>
        </div>

        {/* Threat Score Bar */}
        {stats.threatScore > 0 && (
            <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-5 mb-6">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <ShieldAlert className="w-5 h-5 text-amber-500"/>
                  <span className="text-sm font-semibold text-gray-900 dark:text-white">威胁指数</span>
                </div>
                <span className={`text-2xl font-bold ${
                    stats.threatScore > 70 ? 'text-red-600' : stats.threatScore > 40 ? 'text-amber-600' : 'text-green-600'
                }`}>
              {stats.threatScore}%
            </span>
              </div>
              <div className="w-full h-3 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                <div
                    className={`h-full rounded-full transition-all duration-1000 ${
                        stats.threatScore > 70 ? 'bg-gradient-to-r from-red-500 to-red-600' :
                            stats.threatScore > 40 ? 'bg-gradient-to-r from-amber-500 to-orange-500' :
                                'bg-gradient-to-r from-green-500 to-emerald-500'
                    }`}
                    style={{width: `${Math.min(stats.threatScore, 100)}%`}}
                />
              </div>
              <div className="flex justify-between mt-2 text-[10px] text-gray-400">
                <span>安全</span>
                <span>警告</span>
                <span>危险</span>
              </div>
            </div>
        )}

        {/* Suspicious IPs Alert */}
        {summary?.suspicious_ips && summary.suspicious_ips.length > 0 && (
            <div
                className="bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 border border-amber-200 dark:border-amber-800 rounded-2xl p-5 mb-6">
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle className="w-5 h-5 text-amber-600"/>
                <h3 className="text-sm font-semibold text-amber-800 dark:text-amber-200">可疑 IP 地址</h3>
                <span
                    className="px-2 py-0.5 bg-amber-200 dark:bg-amber-800 text-amber-800 dark:text-amber-200 rounded-full text-xs font-medium">
              {summary.suspicious_ips.length}
            </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {summary.suspicious_ips.map((ip: string, i: number) => (
                    <span key={i}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white dark:bg-gray-800 border border-amber-200 dark:border-amber-700 rounded-xl text-sm font-mono text-amber-800 dark:text-amber-200">
                <Globe className="w-3.5 h-3.5"/>
                      {ip}
              </span>
                ))}
              </div>
            </div>
        )}

        {/* Toolbar */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 mb-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
            <input
                type="text"
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="搜索日志（动作、IP、用户...）"
                className="w-full pl-10 pr-4 py-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
          </div>
          <div className="flex items-center gap-2">
            <select
                value={filterAction}
                onChange={e => setFilterAction(e.target.value)}
                className="px-3 py-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all appearance-none"
            >
              {ACTION_OPTIONS.map(opt => (
                  <option key={opt.key} value={opt.key}>{opt.label}</option>
              ))}
            </select>
            <select
                value={filterStatus}
                onChange={e => setFilterStatus(e.target.value)}
                className="px-3 py-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all appearance-none"
            >
              {STATUS_OPTIONS.map(opt => (
                  <option key={opt.key} value={opt.key}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Count */}
        <div className="flex items-center justify-between mb-2 px-1">
        <span className="text-sm text-gray-500 dark:text-gray-400">
          共 {auditLogs?.length || 0} 条审计记录
        </span>
          {(filterAction !== 'all' || filterStatus !== 'all' || debouncedSearch) && (
              <button
                  onClick={() => {
                    setFilterAction('all');
                    setFilterStatus('all');
                    setSearch('');
                  }}
                  className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
              >
                清除筛选
              </button>
          )}
        </div>

        {/* Audit Logs Table */}
        <div
            className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
          {logsLoading ? (
              <LogSkeleton/>
          ) : !auditLogs?.length ? (
              <div className="p-16 text-center">
                <div
                    className="w-20 h-20 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mx-auto mb-4">
                  <Shield className="w-10 h-10 text-gray-300 dark:text-gray-600"/>
                </div>
                <p className="text-lg font-medium text-gray-500 dark:text-gray-400 mb-1">暂无审计日志</p>
                <p className="text-sm text-gray-400 dark:text-gray-500 dark:text-gray-400">安全事件将会记录在这里</p>
              </div>
          ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50/80 dark:bg-gray-800/50 border-b border-gray-100 dark:border-gray-800">
                  <tr>
                    <th className="px-5 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">动作</th>
                    <th className="px-5 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden md:table-cell">资源</th>
                    <th className="px-5 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden lg:table-cell">IP
                      地址
                    </th>
                    <th className="px-5 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">状态</th>
                    <th className="px-5 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden sm:table-cell">时间</th>
                    <th className="px-5 py-3.5 text-right text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">详情</th>
                  </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50 dark:divide-gray-800/50">
                  {auditLogs.map((log: AuditLog) => (
                      <tr key={log.id}
                          className="group hover:bg-gray-50/80 dark:hover:bg-gray-800/30 transition-colors">
                        <td className="px-5 py-4">
                          <ActionBadge action={log.action}/>
                        </td>
                        <td className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400 hidden md:table-cell">
                          {log.resource_type ? (
                              <span
                                  className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded-lg text-xs">
                          <Database className="w-3 h-3"/>
                                {log.resource_type} #{log.resource_id}
                        </span>
                          ) : (
                              <span className="text-gray-300 dark:text-gray-600">-</span>
                          )}
                        </td>
                        <td className="px-5 py-4 text-sm font-mono text-gray-500 dark:text-gray-400 hidden lg:table-cell">
                          {log.ip_address || <span className="text-gray-300 dark:text-gray-600">-</span>}
                        </td>
                        <td className="px-5 py-4">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${
                          log.status === 'success'
                              ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                              : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                      }`}>
                        {log.status === 'success' ? <CheckCircle className="w-3 h-3"/> : <XCircle className="w-3 h-3"/>}
                        {log.status === 'success' ? '成功' : '失败'}
                      </span>
                        </td>
                        <td className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400 hidden sm:table-cell">
                          <div className="flex items-center gap-1.5">
                            <Clock className="w-3.5 h-3.5 text-gray-400"/>
                            {new Date(log.created_at).toLocaleString('zh-CN', {
                              month: 'numeric',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </div>
                        </td>
                        <td className="px-5 py-4 text-right">
                          <button
                              onClick={() => setSelectedLog(log)}
                              className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                          >
                            <Eye className="w-4 h-4"/>
                          </button>
                        </td>
                      </tr>
                  ))}
                  </tbody>
                </table>
              </div>
          )}
        </div>

        {/* Log Detail Modal */}
        {selectedLog && (
            <LogDetailModal log={selectedLog} onClose={() => setSelectedLog(null)}/>
        )}
      </AdminShell>
  );
}

export default function AdminSecurityDashboard() {
  return (
      <AuthGuard>
        <QueryProvider>
          <SecurityDashboardInner/>
        </QueryProvider>
      </AuthGuard>
  );
}
