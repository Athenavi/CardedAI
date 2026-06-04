'use client';


import {useQuery} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {apiClient} from '@/lib/api/base-client';
import {Server, Activity, Database, HardDrive, Shield, Zap, CheckCircle, XCircle, AlertTriangle} from 'lucide-react';

const statusIcon = (status: string) => {
  if (status === 'pass' || status === 'good') return <CheckCircle className="w-4 h-4 text-green-500" />;
  if (status === 'fail' || status === 'critical') return <XCircle className="w-4 h-4 text-red-500" />;
  return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
};
const statusBadge = (status: string, label?: string) => {
  const cls = status === 'pass' || status === 'good' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
    : status === 'fail' || status === 'critical' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
      : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400';
  return <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${cls}`}>{label || status}</span>;
};

function SystemInner() {
  const {data: infoRes} = useQuery({
    queryKey: ['admin-system-info'],
    queryFn: async () => {
      const res = await apiClient.get('/system/info');
      return res.success && res.data ? res.data : {};
    },
  });
  const {data: healthRes} = useQuery({
    queryKey: ['admin-system-health'],
    queryFn: async () => {
      const res = await apiClient.get('/system/health');
      return res.success && res.data ? res.data : {};
    },
  });

  const info = infoRes || {};
  const health = healthRes || {};
  const checks: Record<string, unknown[]> = health.checks || {};

  const InfoRow = ({label, value}: {label: string; value: string}) => (
    <div className="flex justify-between py-2.5 border-b border-gray-100 dark:border-gray-800 last:border-0">
      <span className="text-sm text-gray-500 dark:text-gray-400">{label}</span>
      <span className="text-sm font-medium text-gray-900 dark:text-white">{value || '—'}</span>
    </div>
  );

  return (
    <AdminShell title="系统信息">
      {/* Total score */}
      {health.overall_score !== undefined && (
        <div className="mb-6 bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">健康评分</p>
          <p className={`text-4xl font-bold ${health.overall_score >= 80 ? 'text-green-600' : health.overall_score >= 60 ? 'text-yellow-600' : 'text-red-600'}`}>
            {health.overall_score}/100
          </p>
          {statusBadge(health.status, health.status?.toUpperCase())}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* System info */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2"><Server className="w-5 h-5"/>系统信息</h3>
          <InfoRow label="Python 版本" value={info.python_version} />
          <InfoRow label="操作系统" value={info.platform} />
          <InfoRow label="运行环境" value={info.environment} />
          <InfoRow label="调试模式" value={info.debug_mode ? '开启' : '关闭'} />
        </div>

        {/* Health checks grouped by category */}
        {Object.entries(checks).map(([category, items]) => (
          <div key={category} className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2 capitalize">
              {category === 'database' ? <Database className="w-5 h-5"/> :
               category === 'storage' ? <HardDrive className="w-5 h-5"/> :
               category === 'security' ? <Shield className="w-5 h-5"/> :
               category === 'performance' ? <Zap className="w-5 h-5"/> :
               <Activity className="w-5 h-5"/>}
              {category === 'system' ? '系统' : category === 'database' ? '数据库' : category === 'storage' ? '存储' : category === 'security' ? '安全' : category === 'performance' ? '性能' : category}
            </h3>
            {items.map((item: any, i: number) => (
              <div key={i} className="flex items-start gap-3 py-2.5 border-b border-gray-100 dark:border-gray-800 last:border-0">
                {statusIcon(item.status)}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-medium text-gray-900 dark:text-white">{item.name}</span>
                    <span className="text-xs text-gray-500 dark:text-gray-400 shrink-0">{item.value}</span>
                  </div>
                  {item.recommendation && (
                    <p className="text-xs text-yellow-600 dark:text-yellow-400 mt-0.5">{item.recommendation}</p>
                  )}
                  {item.error && (
                    <p className="text-xs text-red-500 mt-0.5">{item.error}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>
    </AdminShell>
  );
}

export default function AdminSystem() {
  return <AuthGuard><QueryProvider><SystemInner /></QueryProvider></AuthGuard>;
}
