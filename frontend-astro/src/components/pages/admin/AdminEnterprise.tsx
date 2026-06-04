'use client';

import React, {useCallback, useMemo, useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock,
  Eye,
  Play,
  RefreshCw,
  Search,
  Send,
  Shield,
  Terminal,
  Ticket,
  Trash2,
  XCircle
} from 'lucide-react';
import {AnimatePresence, motion} from 'framer-motion';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {useConfirm} from '@/components/ui/confirm-provider';
import {
  type DeploymentLog,
  type DeploymentScript,
  type EnterpriseLicense,
  type EnterpriseOverview,
  enterpriseService,
  type MonitoringAlert,
  type PaginatedResponse,
  type SupportTicket,
  type SupportTicketReply
} from '@/lib/api/enterprise-service';

// ==================== 子组件 ====================

interface TabDef {
  key: string;
  label: string;
  icon: React.FC<{ className?: string }>;
}

const TABS: TabDef[] = [
  {key: 'overview', label: '概览', icon: BarChart3},
  {key: 'licenses', label: '许可证', icon: Shield},
  {key: 'tickets', label: '工单', icon: Ticket},
  {key: 'scripts', label: '部署脚本', icon: Terminal},
  {key: 'logs', label: '部署日志', icon: Clock},
  {key: 'alerts', label: '监控告警', icon: AlertTriangle},
];

const StatusBadge: React.FC<{ status: string }> = ({status}) => {
  const config: Record<string, { bg: string; text: string; label: string }> = {
    open: {bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-700 dark:text-blue-300', label: '待处理'},
    in_progress: {
      bg: 'bg-yellow-100 dark:bg-yellow-900/30',
      text: 'text-yellow-700 dark:text-yellow-300',
      label: '处理中'
    },
    resolved: {bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-300', label: '已解决'},
    closed: {bg: 'bg-gray-100 dark:bg-gray-800', text: 'text-gray-600 dark:text-gray-400', label: '已关闭'},
    running: {bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-700 dark:text-blue-300', label: '运行中'},
    success: {bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-300', label: '成功'},
    failed: {bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-300', label: '失败'},
    pending: {bg: 'bg-gray-100 dark:bg-gray-800', text: 'text-gray-600 dark:text-gray-400', label: '待执行'},
  };
  const c = config[status] || config.pending;
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${c.bg} ${c.text}`}>
            {c.label}
        </span>
  );
};

const SeverityBadge: React.FC<{ severity: string }> = ({severity}) => {
  const config: Record<string, { bg: string; text: string }> = {
    critical: {bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-300'},
    warning: {bg: 'bg-yellow-100 dark:bg-yellow-900/30', text: 'text-yellow-700 dark:text-yellow-300'},
    info: {bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-700 dark:text-blue-300'},
  };
  const c = config[severity] || config.info;
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${c.bg} ${c.text}`}>
            {severity.toUpperCase()}
        </span>
  );
};

const PriorityBadge: React.FC<{ priority: string }> = ({priority}) => {
  const config: Record<string, { bg: string; text: string }> = {
    high: {bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-300'},
    medium: {bg: 'bg-yellow-100 dark:bg-yellow-900/30', text: 'text-yellow-700 dark:text-yellow-300'},
    low: {bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-300'},
  };
  const c = config[priority] || config.medium;
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${c.bg} ${c.text}`}>
            {priority}
        </span>
  );
};

const StatCard: React.FC<{
  icon: React.FC<{ className?: string }>;
  label: string;
  value: number;
  color: string;
  suffix?: string;
}> = ({icon: Icon, label, value, color, suffix}) => (
  <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5">
    <div className="flex items-center gap-3">
      <div className={`w-10 h-10 rounded-lg ${color} flex items-center justify-center`}>
        <Icon className="w-5 h-5 text-white"/>
      </div>
      <div>
        <p className="text-sm text-gray-500 dark:text-gray-400">{label}</p>
        <p className="text-2xl font-bold text-gray-900 dark:text-white">
          {value}{suffix && <span className="text-sm font-normal ml-1">{suffix}</span>}
        </p>
      </div>
    </div>
  </div>
);

const Pagination: React.FC<{
  page: number;
  pages: number;
  onPageChange: (p: number) => void;
}> = ({page, pages, onPageChange}) => {
  if (pages <= 1) return null;
  return (
    <div className="flex items-center justify-center gap-2 mt-6">
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        className="p-2 rounded-lg border border-gray-200 dark:border-gray-700 disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-gray-800"
      >
        <ChevronLeft className="w-4 h-4"/>
      </button>
      <span className="text-sm text-gray-600 dark:text-gray-400 px-3">
                {page} / {pages}
            </span>
      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page >= pages}
        className="p-2 rounded-lg border border-gray-200 dark:border-gray-700 disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-gray-800"
      >
        <ChevronRight className="w-4 h-4"/>
      </button>
    </div>
  );
};

const EmptyState: React.FC<{ icon: React.FC<{ className?: string }>; title: string; desc: string }> = ({
                                                                                                         icon: Icon,
                                                                                                         title,
                                                                                                         desc
                                                                                                       }) => (
  <div className="text-center py-16">
    <Icon className="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600 mb-4"/>
    <p className="text-gray-500 dark:text-gray-400 font-medium">{title}</p>
    <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">{desc}</p>
  </div>
);

const Skeleton: React.FC<{ rows?: number }> = ({rows = 4}) => (
  <div className="space-y-3">
    {Array.from({length: rows}).map((_, i) => (
      <div key={i} className="h-16 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse"/>
    ))}
  </div>
);

// ==================== 主组件 ====================

function EnterpriseInner() {
  const [activeTab, setActiveTab] = useState('overview');
  const [page, setPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [ticketDetail, setTicketDetail] = useState<SupportTicket | null>(null);
  const [replyContent, setReplyContent] = useState('');
  const [scriptDetail, setScriptDetail] = useState<DeploymentScript | null>(null);
  const queryClient = useQueryClient();
  const confirm = useConfirm();

  // ---- 概览查询 ----
  const {data: overview, isLoading: overviewLoading} = useQuery({
    queryKey: ['enterprise-overview'],
    queryFn: () => enterpriseService.getOverview().then(r => r.data as EnterpriseOverview),
  });

  // ---- 许可证查询 ----
  const {data: licensesData, isLoading: licensesLoading} = useQuery({
    queryKey: ['enterprise-licenses', page],
    queryFn: () => enterpriseService.getLicenses({
      page,
      page_size: 20
    }).then(r => r.data as PaginatedResponse<EnterpriseLicense>),
    enabled: activeTab === 'licenses',
  });

  // ---- 工单查询 ----
  const {data: ticketsData, isLoading: ticketsLoading} = useQuery({
    queryKey: ['enterprise-tickets', page],
    queryFn: () => enterpriseService.getTickets({
      page,
      page_size: 20
    }).then(r => r.data as PaginatedResponse<SupportTicket>),
    enabled: activeTab === 'tickets',
  });

  // ---- 脚本查询 ----
  const {data: scriptsData, isLoading: scriptsLoading} = useQuery({
    queryKey: ['enterprise-scripts', page],
    queryFn: () => enterpriseService.getScripts({
      page,
      page_size: 20
    }).then(r => r.data as PaginatedResponse<DeploymentScript>),
    enabled: activeTab === 'scripts',
  });

  // ---- 日志查询 ----
  const {data: logsData, isLoading: logsLoading} = useQuery({
    queryKey: ['enterprise-logs', page],
    queryFn: () => enterpriseService.getLogs({
      page,
      page_size: 20
    }).then(r => r.data as PaginatedResponse<DeploymentLog>),
    enabled: activeTab === 'logs',
  });

  // ---- 告警查询 ----
  const {data: alertsData, isLoading: alertsLoading} = useQuery({
    queryKey: ['enterprise-alerts', page],
    queryFn: () => enterpriseService.getAlerts({
      page,
      page_size: 20
    }).then(r => r.data as PaginatedResponse<MonitoringAlert>),
    enabled: activeTab === 'alerts',
  });

  // ---- 工单详情查询 ----
  const {data: ticketDetailData} = useQuery({
    queryKey: ['enterprise-ticket-detail', ticketDetail?.id],
    queryFn: () => enterpriseService.getTicketDetail(ticketDetail!.id).then(r => r.data as SupportTicket),
    enabled: !!ticketDetail,
  });

  // ---- Mutations ----
  const resolveAlertMut = useMutation({
    mutationFn: (id: number) => enterpriseService.resolveAlert(id),
    onSuccess: () => queryClient.invalidateQueries({queryKey: ['enterprise-alerts']}),
  });

  const deleteAlertMut = useMutation({
    mutationFn: (id: number) => enterpriseService.deleteAlert(id),
    onSuccess: () => queryClient.invalidateQueries({queryKey: ['enterprise-alerts']}),
  });

  const updateTicketMut = useMutation({
    mutationFn: ({id, data}: {
      id: number;
      data: { status?: string; priority?: string }
    }) => enterpriseService.updateTicket(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({queryKey: ['enterprise-tickets']});
      queryClient.invalidateQueries({queryKey: ['enterprise-ticket-detail']});
    },
  });

  const replyTicketMut = useMutation({
    mutationFn: ({ticketId, content}: {
      ticketId: number;
      content: string
    }) => enterpriseService.replyToTicket(ticketId, content),
    onSuccess: () => {
      queryClient.invalidateQueries({queryKey: ['enterprise-ticket-detail']});
      setReplyContent('');
    },
  });

  const executeScriptMut = useMutation({
    mutationFn: (id: number) => enterpriseService.executeScript(id),
    onSuccess: () => queryClient.invalidateQueries({queryKey: ['enterprise-logs']}),
  });

  const deactivateLicenseMut = useMutation({
    mutationFn: (id: number) => enterpriseService.deactivateLicense(id),
    onSuccess: () => queryClient.invalidateQueries({queryKey: ['enterprise-licenses']}),
  });

  // ---- Tab 切换重置分页 ----
  const handleTabChange = useCallback((key: string) => {
    setActiveTab(key);
    setPage(1);
  }, []);

  // ---- 搜索过滤 ----
  const filteredTickets = useMemo(() => {
    if (!ticketsData?.items || !searchQuery) return ticketsData?.items || [];
    const q = searchQuery.toLowerCase();
    return ticketsData.items.filter(t =>
      t.subject?.toLowerCase().includes(q) ||
      t.ticket_number?.toLowerCase().includes(q) ||
      t.description?.toLowerCase().includes(q)
    );
  }, [ticketsData, searchQuery]);

  const filteredAlerts = useMemo(() => {
    if (!alertsData?.items || !searchQuery) return alertsData?.items || [];
    const q = searchQuery.toLowerCase();
    return alertsData.items.filter(a =>
      a.title?.toLowerCase().includes(q) ||
      a.message?.toLowerCase().includes(q) ||
      a.alert_type?.toLowerCase().includes(q)
    );
  }, [alertsData, searchQuery]);

  // ---- 渲染 Tab 内容 ----
  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return renderOverview();
      case 'licenses':
        return renderLicenses();
      case 'tickets':
        return renderTickets();
      case 'scripts':
        return renderScripts();
      case 'logs':
        return renderLogs();
      case 'alerts':
        return renderAlerts();
      default:
        return null;
    }
  };

  const renderOverview = () => {
    if (overviewLoading) return <Skeleton rows={4}/>;
    if (!overview) return <EmptyState icon={BarChart3} title="暂无数据" desc="企业管理概览数据为空"/>;

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard icon={Shield} label="许可证总数" value={overview.licenses.total} color="bg-blue-500"/>
          <StatCard icon={CheckCircle2} label="活跃许可证" value={overview.licenses.active} color="bg-green-500"/>
          <StatCard icon={Ticket} label="待处理工单" value={overview.tickets.open} color="bg-yellow-500"/>
          <StatCard icon={AlertTriangle} label="未解决告警" value={overview.alerts.unresolved} color="bg-red-500"/>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard icon={Ticket} label="处理中工单" value={overview.tickets.in_progress} color="bg-orange-500"/>
          <StatCard icon={Terminal} label="部署脚本" value={overview.scripts.total} color="bg-purple-500"/>
          <StatCard icon={Play} label="部署次数" value={overview.scripts.deployments} color="bg-indigo-500"/>
          <StatCard icon={XCircle} label="失败部署" value={overview.scripts.failed} color="bg-red-500"/>
        </div>
      </div>
    );
  };

  const renderLicenses = () => {
    if (licensesLoading) return <Skeleton rows={6}/>;
    const items = licensesData?.items || [];
    if (items.length === 0) return <EmptyState icon={Shield} title="暂无许可证" desc="还没有创建企业许可证"/>;

    return (
      <>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">公司
              </th>
              <th
                className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase hidden md:table-cell">类型
              </th>
              <th
                className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase hidden lg:table-cell">许可证密钥
              </th>
              <th
                className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">支持级别
              </th>
              <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">状态
              </th>
              <th
                className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase hidden lg:table-cell">有效期至
              </th>
              <th className="text-right py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">操作
              </th>
            </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {items.map(lic => (
              <tr key={lic.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                <td className="py-3 px-4">
                  <div className="font-medium text-gray-900 dark:text-white">{lic.company_name || '-'}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">{lic.contact_email}</div>
                </td>
                <td
                  className="py-3 px-4 hidden md:table-cell text-sm text-gray-600 dark:text-gray-300">{lic.license_type}</td>
                <td className="py-3 px-4 hidden lg:table-cell">
                  <code className="text-xs bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">{lic.license_key}</code>
                </td>
                <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-300">{lic.support_level}</td>
                <td className="py-3 px-4">
                  {lic.is_active
                    ? <span className="text-green-600 dark:text-green-400 text-xs font-medium">激活</span>
                    : <span className="text-red-600 dark:text-red-400 text-xs font-medium">停用</span>
                  }
                </td>
                <td className="py-3 px-4 hidden lg:table-cell text-sm text-gray-600 dark:text-gray-300">
                  {lic.valid_until ? new Date(lic.valid_until).toLocaleDateString() : '永久'}
                </td>
                <td className="py-3 px-4 text-right">
                  {lic.is_active && (
                    <button
                      onClick={async () => {
                        if (await confirm({
                          title: '停用许可证',
                          message: `确定要停用 ${lic.company_name || lic.license_key} 的许可证吗？`,
                          confirmText: '停用',
                          variant: 'danger'
                        })) {
                          deactivateLicenseMut.mutate(lic.id);
                        }
                      }}
                      className="text-xs text-red-600 dark:text-red-400 hover:underline"
                    >
                      停用
                    </button>
                  )}
                </td>
              </tr>
            ))}
            </tbody>
          </table>
        </div>
        <Pagination page={licensesData?.page || 1} pages={licensesData?.pages || 1} onPageChange={setPage}/>
      </>
    );
  };

  const renderTickets = () => {
    if (ticketsLoading) return <Skeleton rows={6}/>;
    const items = filteredTickets;
    if (items.length === 0) return <EmptyState icon={Ticket} title="暂无工单" desc="还没有技术支持工单"/>;

    return (
      <>
        <div className="mb-4">
          <div className="relative max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
            <input
              type="text"
              placeholder="搜索工单..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
            />
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              <th
                className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">工单编号
              </th>
              <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">主题
              </th>
              <th
                className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase hidden md:table-cell">优先级
              </th>
              <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">状态
              </th>
              <th
                className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase hidden lg:table-cell">分类
              </th>
              <th
                className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase hidden lg:table-cell">创建时间
              </th>
              <th className="text-right py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">操作
              </th>
            </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {items.map(ticket => (
              <tr key={ticket.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                <td className="py-3 px-4">
                  <code className="text-xs bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">{ticket.ticket_number}</code>
                </td>
                <td
                  className="py-3 px-4 max-w-[200px] truncate text-sm text-gray-900 dark:text-white">{ticket.subject}</td>
                <td className="py-3 px-4 hidden md:table-cell"><PriorityBadge priority={ticket.priority}/></td>
                <td className="py-3 px-4"><StatusBadge status={ticket.status}/></td>
                <td
                  className="py-3 px-4 hidden lg:table-cell text-sm text-gray-600 dark:text-gray-300">{ticket.category || '-'}</td>
                <td className="py-3 px-4 hidden lg:table-cell text-sm text-gray-600 dark:text-gray-300">
                  {ticket.created_at ? new Date(ticket.created_at).toLocaleDateString() : '-'}
                </td>
                <td className="py-3 px-4 text-right space-x-2">
                  <button onClick={() => setTicketDetail(ticket)}
                          className="text-xs text-blue-600 dark:text-blue-400 hover:underline">
                    <Eye className="w-3.5 h-3.5 inline"/>
                  </button>
                  {ticket.status === 'open' && (
                    <button
                      onClick={() => updateTicketMut.mutate({id: ticket.id, data: {status: 'in_progress'}})}
                      className="text-xs text-yellow-600 dark:text-yellow-400 hover:underline"
                    >
                      处理
                    </button>
                  )}
                  {(ticket.status === 'open' || ticket.status === 'in_progress') && (
                    <button
                      onClick={() => updateTicketMut.mutate({id: ticket.id, data: {status: 'resolved'}})}
                      className="text-xs text-green-600 dark:text-green-400 hover:underline"
                    >
                      解决
                    </button>
                  )}
                </td>
              </tr>
            ))}
            </tbody>
          </table>
        </div>
        <Pagination page={ticketsData?.page || 1} pages={ticketsData?.pages || 1} onPageChange={setPage}/>
      </>
    );
  };

  const renderScripts = () => {
    if (scriptsLoading) return <Skeleton rows={6}/>;
    const items = scriptsData?.items || [];
    if (items.length === 0) return <EmptyState icon={Terminal} title="暂无部署脚本" desc="还没有创建部署脚本"/>;

    return (
      <>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              <th
                className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">脚本名称
              </th>
              <th
                className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase hidden md:table-cell">类型
              </th>
              <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">版本
              </th>
              <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">状态
              </th>
              <th
                className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase hidden lg:table-cell">创建时间
              </th>
              <th className="text-right py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">操作
              </th>
            </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {items.map(script => (
              <tr key={script.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                <td className="py-3 px-4 font-medium text-gray-900 dark:text-white">{script.name}</td>
                <td
                  className="py-3 px-4 hidden md:table-cell text-sm text-gray-600 dark:text-gray-300">{script.script_type}</td>
                <td className="py-3 px-4">
                  <code className="text-xs bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">v{script.version}</code>
                </td>
                <td className="py-3 px-4">
                  {script.is_active
                    ? <span className="text-green-600 dark:text-green-400 text-xs font-medium">激活</span>
                    : <span className="text-gray-400 text-xs font-medium">停用</span>
                  }
                </td>
                <td className="py-3 px-4 hidden lg:table-cell text-sm text-gray-600 dark:text-gray-300">
                  {script.created_at ? new Date(script.created_at).toLocaleDateString() : '-'}
                </td>
                <td className="py-3 px-4 text-right space-x-2">
                  <button onClick={() => setScriptDetail(script)}
                          className="text-xs text-blue-600 dark:text-blue-400 hover:underline" title="查看详情">
                    <Eye className="w-3.5 h-3.5 inline"/>
                  </button>
                  <button
                    onClick={async () => {
                      if (await confirm({
                        title: '执行脚本',
                        message: `确定要执行 "${script.name}" 吗？`,
                        confirmText: '执行'
                      })) {
                        executeScriptMut.mutate(script.id);
                      }
                    }}
                    className="text-xs text-green-600 dark:text-green-400 hover:underline"
                    title="执行"
                  >
                    <Play className="w-3.5 h-3.5 inline"/>
                  </button>
                </td>
              </tr>
            ))}
            </tbody>
          </table>
        </div>
        <Pagination page={scriptsData?.page || 1} pages={scriptsData?.pages || 1} onPageChange={setPage}/>
      </>
    );
  };

  const renderLogs = () => {
    if (logsLoading) return <Skeleton rows={6}/>;
    const items = logsData?.items || [];
    if (items.length === 0) return <EmptyState icon={Clock} title="暂无部署日志" desc="还没有部署记录"/>;

    return (
      <>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              <th
                className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">日志ID
              </th>
              <th
                className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">脚本ID
              </th>
              <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">状态
              </th>
              <th
                className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase hidden md:table-cell">开始时间
              </th>
              <th
                className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase hidden lg:table-cell">完成时间
              </th>
              <th
                className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase hidden lg:table-cell">错误信息
              </th>
            </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {items.map(log => (
              <tr key={log.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                <td className="py-3 px-4 text-sm font-mono text-gray-900 dark:text-white">#{log.id}</td>
                <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-300">#{log.script_id}</td>
                <td className="py-3 px-4"><StatusBadge status={log.status}/></td>
                <td className="py-3 px-4 hidden md:table-cell text-sm text-gray-600 dark:text-gray-300">
                  {log.started_at ? new Date(log.started_at).toLocaleString() : '-'}
                </td>
                <td className="py-3 px-4 hidden lg:table-cell text-sm text-gray-600 dark:text-gray-300">
                  {log.completed_at ? new Date(log.completed_at).toLocaleString() : '-'}
                </td>
                <td
                  className="py-3 px-4 hidden lg:table-cell text-sm text-red-600 dark:text-red-400 max-w-[200px] truncate">
                  {log.error_message || '-'}
                </td>
              </tr>
            ))}
            </tbody>
          </table>
        </div>
        <Pagination page={logsData?.page || 1} pages={logsData?.pages || 1} onPageChange={setPage}/>
      </>
    );
  };

  const renderAlerts = () => {
    if (alertsLoading) return <Skeleton rows={6}/>;
    const items = filteredAlerts;
    if (items.length === 0) return <EmptyState icon={AlertTriangle} title="暂无告警" desc="监控告警列表为空"/>;

    return (
      <>
        <div className="mb-4">
          <div className="relative max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
            <input
              type="text"
              placeholder="搜索告警..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
            />
          </div>
        </div>
        <div className="space-y-3">
          {items.map(alert => (
            <div key={alert.id}
                 className={`p-4 rounded-xl border ${alert.is_resolved ? 'border-gray-200 dark:border-gray-800 opacity-60' : 'border-red-200 dark:border-red-900/30'} bg-white dark:bg-gray-900`}>
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <SeverityBadge severity={alert.severity}/>
                    <span className="text-xs text-gray-500 dark:text-gray-400">{alert.alert_type}</span>
                    {alert.is_resolved && <StatusBadge status="resolved"/>}
                  </div>
                  <h4 className="font-medium text-gray-900 dark:text-white">{alert.title}</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{alert.message}</p>
                  {alert.metric_name && (
                    <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                      指标: {alert.metric_name} = {alert.metric_value} (阈值: {alert.threshold})
                    </p>
                  )}
                  <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
                    {alert.created_at ? new Date(alert.created_at).toLocaleString() : '-'}
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {!alert.is_resolved && (
                    <button
                      onClick={() => resolveAlertMut.mutate(alert.id)}
                      className="flex items-center gap-1 px-3 py-1.5 text-xs rounded-lg bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-900/40"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5"/> 解决
                    </button>
                  )}
                  <button
                    onClick={async () => {
                      if (await confirm({
                        title: '删除告警',
                        message: '确定要删除这条告警吗？',
                        confirmText: '删除',
                        variant: 'danger'
                      })) {
                        deleteAlertMut.mutate(alert.id);
                      }
                    }}
                    className="flex items-center gap-1 px-3 py-1.5 text-xs rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/40"
                  >
                    <Trash2 className="w-3.5 h-3.5"/> 删除
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
        <Pagination page={alertsData?.page || 1} pages={alertsData?.pages || 1} onPageChange={setPage}/>
      </>
    );
  };

  // ---- 操作按钮 ----
  const actions = (
    <button
      onClick={() => queryClient.invalidateQueries({queryKey: ['enterprise']})}
      className="flex items-center gap-2 px-4 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
    >
      <RefreshCw className="w-4 h-4"/> 刷新
    </button>
  );

  return (
    <AdminShell title="企业管理" actions={actions}>
      {/* Tab 导航 */}
      <div className="border-b border-gray-200 dark:border-gray-800 mb-6">
        <nav className="flex gap-1 overflow-x-auto pb-px">
          {TABS.map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => handleTabChange(tab.key)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                  isActive
                    ? 'border-blue-600 text-blue-600 dark:text-blue-400 dark:border-blue-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
              >
                <Icon className="w-4 h-4"/>
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab 内容 */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{opacity: 0, y: 8}}
          animate={{opacity: 1, y: 0}}
          exit={{opacity: 0, y: -8}}
          transition={{duration: 0.2}}
        >
          {renderTabContent()}
        </motion.div>
      </AnimatePresence>

      {/* 工单详情弹窗 */}
      <AnimatePresence>
        {ticketDetail && (
          <motion.div
            initial={{opacity: 0}}
            animate={{opacity: 1}}
            exit={{opacity: 0}}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
            onClick={() => setTicketDetail(null)}
          >
            <motion.div
              initial={{scale: 0.95, opacity: 0}}
              animate={{scale: 1, opacity: 1}}
              exit={{scale: 0.95, opacity: 0}}
              className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto"
              onClick={e => e.stopPropagation()}
            >
              <div className="p-6 border-b border-gray-200 dark:border-gray-800">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {ticketDetail.subject}
                  </h3>
                  <button onClick={() => setTicketDetail(null)}
                          className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                    <XCircle className="w-5 h-5"/>
                  </button>
                </div>
                <div className="flex items-center gap-2 mt-2">
                  <code
                    className="text-xs bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">{ticketDetail.ticket_number}</code>
                  <PriorityBadge priority={ticketDetail.priority}/>
                  <StatusBadge status={ticketDetail.status}/>
                </div>
              </div>
              <div className="p-6">
                <p className="text-gray-700 dark:text-gray-300 mb-4">{ticketDetail.description}</p>
                <h4 className="font-medium text-gray-900 dark:text-white mb-3">
                  回复 ({ticketDetailData?.replies?.length || 0})
                </h4>
                <div className="space-y-3 mb-4">
                  {(ticketDetailData?.replies || []).map((reply: SupportTicketReply) => (
                    <div key={reply.id}
                         className={`p-3 rounded-lg ${reply.is_staff ? 'bg-blue-50 dark:bg-blue-900/20 ml-4' : 'bg-gray-50 dark:bg-gray-800'}`}>
                      <div className="flex items-center gap-2 mb-1">
                                                <span className="text-xs font-medium text-gray-600 dark:text-gray-300">
                                                    {reply.is_staff ? '🧑‍💼 工作人员' : '👤 用户'} #{reply.user_id}
                                                </span>
                        <span className="text-xs text-gray-400">
                                                    {reply.created_at ? new Date(reply.created_at).toLocaleString() : ''}
                                                </span>
                      </div>
                      <p className="text-sm text-gray-700 dark:text-gray-300">{reply.content}</p>
                    </div>
                  ))}
                </div>
                {/* 回复输入框 */}
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="输入回复..."
                    value={replyContent}
                    onChange={e => setReplyContent(e.target.value)}
                    className="flex-1 px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
                  />
                  <button
                    onClick={() => {
                      if (replyContent.trim()) {
                        replyTicketMut.mutate({ticketId: ticketDetail.id, content: replyContent});
                      }
                    }}
                    disabled={!replyContent.trim()}
                    className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700 disabled:opacity-40"
                  >
                    <Send className="w-4 h-4"/>
                  </button>
                </div>
                {/* 状态操作 */}
                <div className="flex gap-2 mt-4 pt-4 border-t border-gray-200 dark:border-gray-800">
                  {ticketDetail.status !== 'resolved' && ticketDetail.status !== 'closed' && (
                    <>
                      <button
                        onClick={() => updateTicketMut.mutate({id: ticketDetail.id, data: {status: 'in_progress'}})}
                        className="px-4 py-2 text-sm rounded-lg bg-yellow-50 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-400 hover:bg-yellow-100"
                      >
                        标记处理中
                      </button>
                      <button
                        onClick={() => {
                          updateTicketMut.mutate({id: ticketDetail.id, data: {status: 'resolved'}});
                          setTicketDetail(null);
                        }}
                        className="px-4 py-2 text-sm rounded-lg bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 hover:bg-green-100"
                      >
                        标记已解决
                      </button>
                      <button
                        onClick={() => {
                          updateTicketMut.mutate({id: ticketDetail.id, data: {status: 'closed'}});
                          setTicketDetail(null);
                        }}
                        className="px-4 py-2 text-sm rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-100"
                      >
                        关闭工单
                      </button>
                    </>
                  )}
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 脚本详情弹窗 */}
      <AnimatePresence>
        {scriptDetail && (
          <motion.div
            initial={{opacity: 0}}
            animate={{opacity: 1}}
            exit={{opacity: 0}}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
            onClick={() => setScriptDetail(null)}
          >
            <motion.div
              initial={{scale: 0.95, opacity: 0}}
              animate={{scale: 1, opacity: 1}}
              exit={{scale: 0.95, opacity: 0}}
              className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto"
              onClick={e => e.stopPropagation()}
            >
              <div className="p-6 border-b border-gray-200 dark:border-gray-800">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{scriptDetail.name}</h3>
                  <button onClick={() => setScriptDetail(null)} className="text-gray-400 hover:text-gray-600">
                    <XCircle className="w-5 h-5"/>
                  </button>
                </div>
                <div className="flex items-center gap-2 mt-2">
                  <code
                    className="text-xs bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">{scriptDetail.script_type}</code>
                  <code
                    className="text-xs bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">v{scriptDetail.version}</code>
                </div>
              </div>
              <div className="p-6">
                {scriptDetail.description && (
                  <p className="text-gray-600 dark:text-gray-400 mb-4">{scriptDetail.description}</p>
                )}
                <h4 className="font-medium text-gray-900 dark:text-white mb-2">脚本内容</h4>
                <pre
                  className="bg-gray-950 text-green-400 p-4 rounded-lg text-sm overflow-x-auto max-h-[400px] overflow-y-auto">
                                    {scriptDetail.content}
                                </pre>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </AdminShell>
  );
}

// ==================== 导出 ====================

const AdminEnterprise: React.FC = () => (
  <AuthGuard>
    <QueryProvider>
      <EnterpriseInner/>
    </QueryProvider>
  </AuthGuard>
);

export default AdminEnterprise;
