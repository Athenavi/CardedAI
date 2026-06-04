'use client';

import React, {useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {apiClient} from '@/lib/api/base-client';
import {useToast} from '@/components/ui/toast-provider';
import {Trash2} from 'lucide-react';
import {ChatGroupMember} from './shared';
import type {ApiResponse} from '@/lib/api/base-types';
const GroupMembersPanel: React.FC<{ groupId: number | null }> = ({groupId}) => {
  const toast = useToast();
  const qc = useQueryClient();
  const [addUserId, setAddUserId] = useState('');

  const {data, isLoading} = useQuery({
    queryKey: ['group-members', groupId],
    queryFn: () => groupId ? apiClient.get(`/chats/groups/${groupId}/members`) : null,
    enabled: !!groupId,
  });

  const members: ChatGroupMember[] = data?.data?.members || [];

  const addMut = useMutation({
    mutationFn: (userIds: number[]) => apiClient.post(`/chats/groups/${groupId}/members`, {user_ids: userIds}),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['group-members', groupId]});
        setAddUserId('');
      } else toast.error(r.error || '操作失败');
    },
  });
  const removeMut = useMutation({
    mutationFn: (userId: number) => apiClient.delete(`/chats/groups/${groupId}/members/${userId}`),
    onSuccess: (r: ApiResponse) => {
      if (r.success) qc.invalidateQueries({queryKey: ['group-members', groupId]});
      else toast.error(r.error || '操作失败');
    },
  });

  if (!groupId) return null;

  return (
    <div>
      {isLoading ? (
        <div className="space-y-2">{[...Array(3)].map((_, i) => <div key={i}
                                                                     className="h-12 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse"/>)}</div>
      ) : (
        <>
          <div className="space-y-2 mb-4 max-h-60 overflow-y-auto">
            {members.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">暂无成员</p>
            ) : members.map(m => (
              <div key={m.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="flex items-center gap-3">
                  <div
                    className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-400 to-gray-600 flex items-center justify-center text-white text-xs font-bold">
                    {m.username.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{m.username}</span>
                    <span
                      className={`ml-2 text-[10px] px-1.5 py-0.5 rounded-full ${m.role === 'admin' ? 'bg-red-100 dark:bg-red-900/30 text-red-600' : m.role === 'moderator' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600' : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'}`}>
                      {m.role === 'admin' ? '群主' : m.role === 'moderator' ? '管理员' : '成员'}
                    </span>
                  </div>
                </div>
                {m.role !== 'admin' && (
                  <button onClick={() => removeMut.mutate(m.user_id)}
                          className="p-1 rounded hover:bg-red-50 dark:hover:bg-red-900/20" title="移除">
                    <Trash2 className="w-3.5 h-3.5 text-red-500"/>
                  </button>
                )}
              </div>
            ))}
          </div>
          <div className="border-t border-gray-100 dark:border-gray-800 pt-4">
            <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-2">添加成员</h4>
            <div className="flex gap-2">
              <input value={addUserId} onChange={e => setAddUserId(e.target.value)} placeholder="用户ID（多个用逗号分隔）"
                     className="flex-1 px-3 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 dark:text-white"/>
              <button onClick={() => {
                const ids = addUserId.split(',').map(s => parseInt(s.trim())).filter(Boolean);
                if (ids.length > 0) addMut.mutate(ids);
              }} disabled={!addUserId || addMut.isPending}
                      className="px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
                添加
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default GroupMembersPanel;
