'use client';

import {useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {apiClient} from '@/lib/api/base-client';
import {Check, Eye, FileText, Loader, Medal, X} from 'lucide-react';
import {useConfirm} from '@/components/ui/confirm-provider';

function CertificationInner() {
  const confirm = useConfirm();
  const qc = useQueryClient();

  const {data: stats} = useQuery({
    queryKey: ['ext-cert-stats'],
    queryFn: async () => {
      const r = await apiClient.get('/ext/expert-certification/admin/stats');
      return r.success && r.data ? r.data : {};
    },
  });

  const {data: fields} = useQuery({
    queryKey: ['ext-cert-fields'],
    queryFn: async () => {
      const r = await apiClient.get('/ext/expert-certification/fields');
      const raw = r.success && r.data ? (r.data.fields || r.data) : [];
      return Array.isArray(raw) ? raw : [];
    },
  });

  const {data: pendingApps} = useQuery({
    queryKey: ['ext-cert-pending'],
    queryFn: async () => {
      const r = await apiClient.get('/ext/expert-certification/admin/pending-applications');
      const raw = r.success && r.data ? (r.data.applications || r.data) : [];
      return Array.isArray(raw) ? raw : [];
    },
  });

  const {data: experts} = useQuery({
    queryKey: ['ext-cert-experts'],
    queryFn: async () => {
      const r = await apiClient.get('/ext/expert-certification/experts', {limit: 50});
      const raw = r.success && r.data ? (r.data.experts || r.data) : [];
      return Array.isArray(raw) ? raw : [];
    },
  });

  // Review mutation
  const reviewMut = useMutation({
    mutationFn: (data: any) => apiClient.post('/ext/expert-certification/admin/review', data),
    onSuccess: () => qc.invalidateQueries({queryKey: ['ext-cert-pending', 'ext-cert-stats', 'ext-cert-experts']}),
  });
  const revokeMut = useMutation({
    mutationFn: (data: any) => apiClient.post('/ext/expert-certification/admin/revoke', data),
    onSuccess: () => qc.invalidateQueries({queryKey: ['ext-cert-experts']}),
  });

  const [revokeUserId, setRevokeUserId] = useState('');
  const [revokeReason, setRevokeReason] = useState('');

  return (
    <AdminShell title="专家认证">
      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-white dark:bg-gray-900 rounded-2xl border p-5">
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-1"><Medal
            className="w-4 h-4"/>总认证专家
          </div>
          <p className="text-2xl font-bold">{stats?.total_experts ?? '—'}</p>
        </div>
        <div className="bg-white dark:bg-gray-900 rounded-2xl border p-5">
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-1"><FileText
            className="w-4 h-4"/>认证领域
          </div>
          <p className="text-2xl font-bold">{stats?.total_fields ?? (Array.isArray(fields) ? fields.length : '—')}</p>
        </div>
        <div className="bg-white dark:bg-gray-900 rounded-2xl border p-5">
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-1"><Eye
            className="w-4 h-4"/>待审核
          </div>
          <p className="text-2xl font-bold">{stats?.pending_applications ?? (Array.isArray(pendingApps) ? pendingApps.length : '—')}</p>
        </div>
        <div className="bg-white dark:bg-gray-900 rounded-2xl border p-5">
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-1"><X
            className="w-4 h-4"/>已拒绝
          </div>
          <p className="text-2xl font-bold">{stats?.rejected_count ?? '—'}</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6 mb-6">
        {/* Available fields */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border p-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">可认证领域</h3>
          <div className="flex flex-wrap gap-2">
            {Array.isArray(fields) && fields.map((f: any, i: number) => (
              <span key={f.id || i} className="px-3 py-1.5 bg-blue-50 dark:bg-blue-900/20 text-blue-700 rounded-lg text-sm">{f.name || f.field || f.id}</span>
            ))}
            {!Array.isArray(fields) || !fields.length ? <p className="text-sm text-gray-400">暂无领域</p> : null}
          </div>
        </div>

        {/* Experts list */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold text-gray-900 dark:text-white">已认证专家</h3>
          </div>
          {Array.isArray(experts) && experts.length > 0 ? (
            <div className="divide-y divide-gray-100 dark:divide-gray-800 max-h-80 overflow-y-auto">
              {experts.map((exp: any, i: number) => (
                <div key={exp.user_id || i} className="px-6 py-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-700 dark:text-gray-300">{exp.username || `用户 #${exp.user_id}`}</p>
                    <p className="text-xs text-gray-400">{exp.field_name || exp.field || ''}</p>
                  </div>
                  <span
                    className="px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-[10px] rounded font-medium">已认证</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-6 text-center text-sm text-gray-400">暂无认证专家</div>
          )}
        </div>
      </div>

      {/* Pending applications */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border overflow-hidden mb-6">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="font-semibold text-gray-900 dark:text-white">待审核申请</h3>
        </div>
        {Array.isArray(pendingApps) && pendingApps.length > 0 ? (
          <div className="divide-y divide-gray-100 dark:divide-gray-800">
            {pendingApps.map((app: any, i: number) => (
              <div key={app.application_id || app.id || i} className="px-6 py-4 flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {app.username || `用户 #${app.user_id}`} — {app.field_name || app.field || app.field_id}
                  </p>
                  <p className="text-xs text-gray-400 truncate">{app.bio || ''}</p>
                </div>
                <div className="flex items-center gap-2 shrink-0 ml-4">
                  <button onClick={() => reviewMut.mutate({application_id: app.application_id || app.id, approved: true})}
                    disabled={reviewMut.isPending}
                    className="px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white text-xs rounded-lg inline-flex items-center gap-1 disabled:opacity-50">
                    <Check className="w-3 h-3"/>通过
                  </button>
                  <button onClick={() => {
                    const reason = prompt('拒绝原因:');
                    if (reason) reviewMut.mutate({application_id: app.application_id || app.id, approved: false, rejection_reason: reason});
                  }}
                    disabled={reviewMut.isPending}
                    className="px-3 py-1.5 border border-red-200 text-red-600 text-xs rounded-lg hover:bg-red-50 inline-flex items-center gap-1 disabled:opacity-50">
                    <X className="w-3 h-3"/>拒绝
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-6 text-center text-sm text-gray-400">暂无待审核申请</div>
        )}
      </div>

      {/* Revoke */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border p-6">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-4">撤销认证</h3>
        <div className="flex gap-3 items-end">
          <div className="flex-1">
            <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">用户 ID</label>
            <input type="number" value={revokeUserId} onChange={e => setRevokeUserId(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg text-sm dark:bg-gray-800 dark:text-white dark:border-gray-700"/>
          </div>
          <div className="flex-1">
            <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">原因</label>
            <input value={revokeReason} onChange={e => setRevokeReason(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg text-sm dark:bg-gray-800 dark:text-white dark:border-gray-700"/>
          </div>
          <button onClick={async () => {
            if (await confirm({
              message: '确认撤销该用户的认证？',
              variant: 'warning'
            })) revokeMut.mutate({user_id: parseInt(revokeUserId), reason: revokeReason});
            setRevokeUserId('');
            setRevokeReason('');
          }}
            disabled={revokeMut.isPending || !revokeUserId}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded-lg disabled:opacity-50">
            {revokeMut.isPending ? <Loader className="w-4 h-4 animate-spin"/> : '撤销认证'}
          </button>
        </div>
      </div>
    </AdminShell>
  );
}

export default function ExtCertification() { return <AuthGuard><QueryProvider><CertificationInner/></QueryProvider></AuthGuard>; }
