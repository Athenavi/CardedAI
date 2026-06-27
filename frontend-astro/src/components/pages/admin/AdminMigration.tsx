'use client';

import {useQuery, useMutation, useQueryClient} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {apiClient} from '@/lib/api/base-client';
import {Database, RefreshCw, Play, History, FileText, AlertTriangle, CheckCircle, XCircle, ArrowLeft} from 'lucide-react';
import {useState} from 'react';

const statusIcon = (ok: boolean | null | undefined) => {
  if (ok === true) return <CheckCircle className="w-4 h-4 text-green-500" />;
  if (ok === false) return <XCircle className="w-4 h-4 text-red-500" />;
  return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
};

function MigrationInner() {
  const queryClient = useQueryClient();
  const [applying, setApplying] = useState(false);
  const [applyResult, setApplyResult] = useState<string | null>(null);

  const {data: statusRes, isLoading, refetch} = useQuery({
    queryKey: ['migration-status'],
    queryFn: async () => {
      const res = await apiClient.get('/system/migrations/status');
      return res;
    },
  });

  const status = statusRes?.success ? statusRes.data : null;

  const handleApply = async () => {
    setApplying(true);
    setApplyResult(null);
    try {
      const res = await apiClient.post('/system/migrations/apply', {});
      setApplyResult(res?.success ? '迁移执行成功' : `迁移失败: ${res?.error || '未知错误'}`);
      queryClient.invalidateQueries({queryKey: ['migration-status']});
    } catch (e: any) {
      setApplyResult(`迁移失败: ${e.message}`);
    } finally {
      setApplying(false);
    }
  };

  const InfoRow = ({label, value}: {label: string; value: string}) => (
    <div className="flex justify-between py-2.5 border-b border-gray-100 dark:border-gray-800 last:border-0">
      <span className="text-sm text-gray-500 dark:text-gray-400">{label}</span>
      <span className="text-sm font-medium text-gray-900 dark:text-white">{value || '—'}</span>
    </div>
  );

  return (
    <AdminShell title="数据库迁移">
      {/* Status card */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <Database className="w-5 h-5" />
          迁移状态
        </h3>
        {isLoading ? (
          <p className="text-sm text-gray-400">加载中...</p>
        ) : status ? (
          <div>
            <InfoRow label="当前版本" value={status.current_version || status.current_revision || '—'} />
            <InfoRow label="最新版本" value={status.latest_version || status.head_revision || '—'} />
            <InfoRow label="待处理迁移" value={String(status.pending_count ?? (status.is_up_to_date ? 0 : '?'))} />
            <InfoRow label="数据库状态" value={status.is_up_to_date ? '已是最新' : '需要迁移'} />
          </div>
        ) : (
          <p className="text-sm text-red-500">无法获取迁移状态</p>
        )}
      </div>

      {/* Actions card */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <Play className="w-5 h-5" />
          迁移操作
        </h3>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={handleApply}
            disabled={applying || status?.is_up_to_date}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white text-sm font-medium rounded-lg transition-colors"
          >
            {applying ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            {applying ? '执行中...' : '执行迁移'}
          </button>
          <button
            onClick={() => refetch()}
            className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm font-medium rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            刷新状态
          </button>
        </div>
        {applyResult && (
          <div className={`mt-4 p-3 rounded-xl text-sm flex items-center gap-2 ${
            applyResult.includes('成功')
              ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-400'
              : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400'
          }`}>
            {applyResult.includes('成功') ? <CheckCircle className="w-4 h-4 shrink-0" /> : <XCircle className="w-4 h-4 shrink-0" />}
            {applyResult}
          </div>
        )}
      </div>

      {/* Migration history card */}
      {status?.history && status.history.length > 0 && (
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <History className="w-5 h-5" />
            迁移历史
          </h3>
          <div className="space-y-2">
            {status.history.map((item: any, i: number) => (
              <div key={i} className="flex items-start gap-3 py-2 border-b border-gray-100 dark:border-gray-800 last:border-0">
                {statusIcon(item.success)}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {item.revision || item.version || `#${i + 1}`}
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400 shrink-0">
                      {item.applied_at ? new Date(item.applied_at).toLocaleString('zh-CN') : ''}
                    </span>
                  </div>
                  {item.message && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{item.message}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No history notice */}
      {status && (!status.history || status.history.length === 0) && (
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 text-center">
          <FileText className="w-8 h-8 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
          <p className="text-sm text-gray-500 dark:text-gray-400">暂无迁移历史</p>
        </div>
      )}
    </AdminShell>
  );
}

export default function AdminMigration() {
  return <AuthGuard><QueryProvider><MigrationInner /></QueryProvider></AuthGuard>;
}
