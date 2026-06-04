'use client';

import React, {useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {EmptyState, Modal, Pagination} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import {useToast} from '@/components/ui/toast-provider';
import {Link2, MessageSquare, Plus, Search, Users} from 'lucide-react';
import {ChatGroup, Input, StatusBadge} from './shared';
import GroupMembersPanel from './GroupMembersPanel';
import GroupInvitesPanel from './GroupInvitesPanel';
import type {ApiResponse} from '@/lib/api/base-types';
const GroupsTab: React.FC = () => {
  const toast = useToast();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [_editing, setEditing] = useState<ChatGroup | null>(null);
  const [_deleteId, _setDeleteId] = useState<number | null>(null);
  const [showMembers, setShowMembers] = useState<number | null>(null);
  const [showInvites, setShowInvites] = useState<number | null>(null);
  const [form, setForm] = useState({
    name: '', description: '', max_members: '500', is_public: 'true'
  });

  const {data, isLoading} = useQuery({
    queryKey: ['chat-groups', page, search],
    queryFn: () => apiClient.get('/chats/groups', {page, per_page: 15, search: search || undefined}),
  });

  const items: ChatGroup[] = data?.data?.groups || data?.data?.items || [];
  const total: number = data?.data?.total || 0;

  const createMut = useMutation({
    mutationFn: (d: any) => apiClient.post('/chats/groups', d),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['chat-groups']});
        setShowForm(false);
      } else toast.error(r.error || '操作失败');
    },
  });

  const openCreate = () => {
    setEditing(null);
    setForm({name: '', description: '', max_members: '500', is_public: 'true'});
    setShowForm(true);
  };
  const submit = () => {
    if (!form.name.trim()) {
      toast.error('请填写群聊名称');
      return;
    }
    const payload = {
      ...form,
      max_members: parseInt(form.max_members) || 500,
      is_public: form.is_public === 'true',
    };
    createMut.mutate(payload);
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
                   placeholder="搜索群聊..."
                   className="pl-9 pr-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm dark:text-white w-64"/>
          </div>
        </div>
        <button onClick={openCreate}
                className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700">
          <Plus className="w-4 h-4"/> 创建群聊
        </button>
      </div>

      {isLoading ? (
        <div className="space-y-2">{[...Array(5)].map((_, i) => <div key={i}
                                                                     className="h-16 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse"/>)}</div>
      ) : items.length === 0 ? (
        <EmptyState icon={MessageSquare} title="暂无群聊" desc="点击「创建群聊」开始"/>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map(g => (
            <div key={g.id}
                 className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div
                    className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg">
                    {g.name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100">{g.name}</h3>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{g.owner_name || `创建者#${g.owner_id}`}</p>
                  </div>
                </div>
                <StatusBadge active={g.is_active}/>
              </div>
              {g.description &&
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-3 line-clamp-2">{g.description}</p>}
              <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400 mb-3">
                <span className="flex items-center gap-1"><Users
                  className="w-3 h-3"/> {g.member_count}/{g.max_members || '∞'}</span>
                <span
                  className={`px-1.5 py-0.5 rounded-full text-[10px] ${g.is_public ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600' : 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'}`}>
                  {g.is_public ? '公开' : '私密'}
                </span>
              </div>
              <div className="flex items-center justify-end gap-1 pt-2 border-t border-gray-100 dark:border-gray-800">
                <button onClick={() => setShowMembers(g.id)}
                        className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800" title="成员管理">
                  <Users className="w-3.5 h-3.5 text-gray-500 dark:text-gray-400"/>
                </button>
                <button onClick={() => setShowInvites(g.id)}
                        className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800" title="邀请链接">
                  <Link2 className="w-3.5 h-3.5 text-gray-500 dark:text-gray-400"/>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {total > 15 &&
        <div className="mt-4"><Pagination page={page} totalPages={Math.ceil(total / 15)} onPageChange={setPage}/></div>}

      {/* Create Group Modal */}
      <Modal open={showForm} onClose={() => setShowForm(false)} title="创建群聊">
        <Input label="群聊名称 *" value={form.name} onChange={v => setForm(f => ({...f, name: v}))}
               placeholder="输入群聊名称"/>
        <Input label="描述" value={form.description} onChange={v => setForm(f => ({...f, description: v}))}
               placeholder="群聊描述" rows={3}/>
        <Input label="最大成员数" value={form.max_members} onChange={v => setForm(f => ({...f, max_members: v}))}
               type="number" placeholder="500"/>
        <div className="mb-3">
          <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">群聊类型</label>
          <select value={form.is_public} onChange={e => setForm(f => ({...f, is_public: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white">
            <option value="true">公开群聊</option>
            <option value="false">私密群聊</option>
          </select>
        </div>
        <div className="flex justify-end gap-2 mt-4 pt-3 border-t border-gray-100 dark:border-gray-800">
          <button onClick={() => setShowForm(false)}
                  className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg">取消
          </button>
          <button onClick={submit} disabled={createMut.isPending}
                  className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
            {createMut.isPending ? '创建中...' : '创建'}
          </button>
        </div>
      </Modal>

      {/* Members Modal */}
      <Modal open={showMembers !== null} onClose={() => setShowMembers(null)} title="群聊成员管理">
        <GroupMembersPanel groupId={showMembers}/>
      </Modal>

      {/* Invites Modal */}
      <Modal open={showInvites !== null} onClose={() => setShowInvites(null)} title="邀请链接管理">
        <GroupInvitesPanel groupId={showInvites}/>
      </Modal>
    </>
  );
};

export default GroupsTab;
