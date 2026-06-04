'use client';

import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {apiClient} from '@/lib/api/base-client';
import {useToast} from '@/components/ui/toast-provider';
import {Trash2} from 'lucide-react';
import {ChatGroupInvite, StatusBadge} from './shared';
import type {ApiResponse} from '@/lib/api/base-types';
const GroupInvitesPanel: React.FC<{ groupId: number | null }> = ({groupId}) => {
  const toast = useToast();
  const qc = useQueryClient();

  const {data, isLoading} = useQuery({
    queryKey: ['group-invites', groupId],
    queryFn: () => groupId ? apiClient.get(`/chats/groups/${groupId}/invites`) : null,
    enabled: !!groupId,
  });

  const invites: ChatGroupInvite[] = data?.data?.invites || [];

  const createMut = useMutation({
    mutationFn: () => apiClient.post(`/chats/groups/${groupId}/create-invite`, {}),
    onSuccess: (r: ApiResponse) => {
      if (r.success) qc.invalidateQueries({queryKey: ['group-invites', groupId]});
      else toast.error(r.error || '操作失败');
    },
  });
  const revokeMut = useMutation({
    mutationFn: (code: string) => apiClient.post(`/chats/groups/${groupId}/revoke-invite`, {invite_code: code}),
    onSuccess: (r: ApiResponse) => {
      if (r.success) qc.invalidateQueries({queryKey: ['group-invites', groupId]});
      else toast.error(r.error || '操作失败');
    },
  });

  if (!groupId) return null;

  return (
    <div>
      {isLoading ? (
        <div className="space-y-2">{[...Array(2)].map((_, i) => <div key={i}
                                                                     className="h-12 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse"/>)}</div>
      ) : (
        <>
          <div className="space-y-2 mb-4 max-h-60 overflow-y-auto">
            {invites.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">暂无邀请链接</p>
            ) : invites.map(inv => (
              <div key={inv.id}
                   className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div>
                  <div className="flex items-center gap-2">
                    <code
                      className="text-sm font-mono bg-gray-200 dark:bg-gray-700 px-2 py-0.5 rounded">{inv.invite_code}</code>
                    <StatusBadge active={inv.is_active}/>
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    已使用 {inv.current_uses}{inv.max_uses ? `/${inv.max_uses}` : ''} 次
                    {inv.expires_at && ` · 过期时间: ${inv.expires_at.slice(0, 16)}`}
                  </div>
                </div>
                <button onClick={() => revokeMut.mutate(inv.invite_code)}
                        className="p-1 rounded hover:bg-red-50 dark:hover:bg-red-900/20" title="撤销">
                  <Trash2 className="w-3.5 h-3.5 text-red-500"/>
                </button>
              </div>
            ))}
          </div>
          <button onClick={() => createMut.mutate()} disabled={createMut.isPending}
                  className="w-full px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
            {createMut.isPending ? '生成中...' : '生成新邀请链接'}
          </button>
        </>
      )}
    </div>
  );
};

export default GroupInvitesPanel;
