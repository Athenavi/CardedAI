'use client';

import React, {useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {apiClient} from '@/lib/api/base-client';
import {useToast} from '@/components/ui/toast-provider';
import {Trash2} from 'lucide-react';
import {SiteUser} from './shared';
import type {ApiResponse} from '@/lib/api/base-types';
const SiteUsersPanel: React.FC<{ siteId: number | null }> = ({siteId}) => {
  const toast = useToast();
  const qc = useQueryClient();
  const [addUserId, setAddUserId] = useState('');
  const [addRole, setAddRole] = useState('editor');

  const {data, isLoading} = useQuery({
    queryKey: ['site-users', siteId],
    queryFn: () => siteId ? apiClient.get(`/system/multisite/${siteId}/users`) : null,
    enabled: !!siteId,
  });

  const users: SiteUser[] = data?.data?.users || [];

  const addUserMut = useMutation({
    mutationFn: (d: any) => apiClient.post('/system/multisite/users', {site_id: siteId, ...d}),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['site-users', siteId]});
        setAddUserId('');
      } else toast.error(r.error || '操作失败');
    },
  });
  const removeUserMut = useMutation({
    mutationFn: (userId: number) => apiClient.delete(`/system/multisite/users/${userId}`),
    onSuccess: (r: ApiResponse) => {
      if (r.success) qc.invalidateQueries({queryKey: ['site-users', siteId]});
      else toast.error(r.error || '操作失败');
    },
  });
  const updateRoleMut = useMutation({
    mutationFn: ({userId, role}: any) => apiClient.put(`/system/multisite/${siteId}/users/${userId}/role`, {role}),
    onSuccess: (r: ApiResponse) => {
      if (r.success) qc.invalidateQueries({queryKey: ['site-users', siteId]});
      else toast.error(r.error || '操作失败');
    },
  });

  if (!siteId) return null;

  return (
    <div>
      {isLoading ? (
        <div className="space-y-2">{[...Array(3)].map((_, i) => <div key={i}
                                                                     className="h-12 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse"/>)}</div>
      ) : (
        <>
          <div className="space-y-2 mb-4 max-h-60 overflow-y-auto">
            {users.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">暂无用户</p>
            ) : users.map(u => (
              <div key={u.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div>
                  <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{u.username}</span>
                  {u.email && <span className="text-xs text-gray-400 ml-2">{u.email}</span>}
                </div>
                <div className="flex items-center gap-2">
                  <select value={u.role} onChange={e => updateRoleMut.mutate({userId: u.user_id, role: e.target.value})}
                          className="px-2 py-1 text-xs border border-gray-200 dark:border-gray-700 rounded bg-white dark:bg-gray-800 dark:text-white">
                    <option value="admin">管理员</option>
                    <option value="editor">编辑</option>
                    <option value="author">作者</option>
                    <option value="viewer">查看者</option>
                  </select>
                  <button onClick={() => removeUserMut.mutate(u.user_id)}
                          className="p-1 rounded hover:bg-red-50 dark:hover:bg-red-900/20" title="移除">
                    <Trash2 className="w-3.5 h-3.5 text-red-500"/>
                  </button>
                </div>
              </div>
            ))}
          </div>
          <div className="border-t border-gray-100 dark:border-gray-800 pt-4">
            <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-2">添加用户</h4>
            <div className="flex gap-2">
              <input value={addUserId} onChange={e => setAddUserId(e.target.value)} placeholder="用户ID"
                     className="flex-1 px-3 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 dark:text-white"/>
              <select value={addRole} onChange={e => setAddRole(e.target.value)}
                      className="px-3 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 dark:text-white">
                <option value="admin">管理员</option>
                <option value="editor">编辑</option>
                <option value="author">作者</option>
                <option value="viewer">查看者</option>
              </select>
              <button onClick={() => addUserMut.mutate({user_id: parseInt(addUserId), role: addRole})}
                      disabled={!addUserId || addUserMut.isPending}
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

export default SiteUsersPanel;
