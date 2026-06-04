'use client';

import React, {useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {DeleteConfirm, EmptyState, Modal} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import {useToast} from '@/components/ui/toast-provider';
import {Edit3, Globe, Map, Plus, Search, Trash2, Users} from 'lucide-react';
import {Site, Input, StatusBadge} from './shared';
import SiteUsersPanel from './SiteUsersPanel';
import type {ApiResponse} from '@/lib/api/base-types';
const SitesTab: React.FC = () => {
  const toast = useToast();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Site | null>(null);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [showUsers, setShowUsers] = useState<number | null>(null);
  const [form, setForm] = useState({
    name: '', domain: '', description: '', is_active: 'true', theme: '', additional_domains: ''
  });

  const {data, isLoading} = useQuery({
    queryKey: ['sites', page, search],
    queryFn: () => apiClient.get('/system/multisite', {page, per_page: 15, search: search || undefined}),
  });

  const sites: Site[] = data?.data?.sites || data?.data?.items || [];
  const _total: number = data?.data?.total || 0;

  const createMut = useMutation({
    mutationFn: (d: any) => apiClient.post('/system/multisite', d),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['sites']});
        setShowForm(false);
      } else toast.error(r.error || '操作失败');
    },
  });
  const updateMut = useMutation({
    mutationFn: ({id, ...d}: any) => apiClient.put(`/system/multisite/${id}`, d),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['sites']});
        setShowForm(false);
      } else toast.error(r.error || '操作失败');
    },
  });
  const deleteMut = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/system/multisite/${id}`),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['sites']});
        setDeleteId(null);
      } else toast.error(r.error || '操作失败');
    },
  });

  const openCreate = () => {
    setEditing(null);
    setForm({name: '', domain: '', description: '', is_active: 'true', theme: '', additional_domains: ''});
    setShowForm(true);
  };
  const openEdit = (s: Site) => {
    setEditing(s);
    setForm({
      name: s.name, domain: s.domain, description: s.description || '',
      is_active: String(s.is_active), theme: s.theme || '',
      additional_domains: s.additional_domains?.join(', ') || '',
    });
    setShowForm(true);
  };
  const submit = () => {
    if (!form.name.trim() || !form.domain.trim()) {
      toast.error('请填写站点名称和域名');
      return;
    }
    const payload = {
      ...form,
      is_active: form.is_active === 'true',
      additional_domains: form.additional_domains ? form.additional_domains.split(',').map(d => d.trim()).filter(Boolean) : [],
    };
    if (editing) updateMut.mutate({id: editing.id, ...payload});
    else createMut.mutate(payload);
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
                   placeholder="搜索站点..."
                   className="pl-9 pr-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm dark:text-white w-64"/>
          </div>
        </div>
        <button onClick={openCreate}
                className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700">
          <Plus className="w-4 h-4"/> 新增站点
        </button>
      </div>

      {isLoading ? (
        <div className="space-y-2">{[...Array(5)].map((_, i) => <div key={i}
                                                                     className="h-16 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse"/>)}</div>
      ) : sites.length === 0 ? (
        <EmptyState icon={Globe} title="暂无站点" desc="点击「新增站点」开始配置多站点"/>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sites.map(s => (
            <div key={s.id}
                 className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                    <Globe className="w-5 h-5 text-blue-600 dark:text-blue-400"/>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100">{s.name}</h3>
                    <p className="text-xs text-gray-500 dark:text-gray-400 font-mono">{s.domain}</p>
                  </div>
                </div>
                <StatusBadge active={s.is_active}/>
              </div>
              {s.description &&
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-3 line-clamp-2">{s.description}</p>}
              <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400 mb-3">
                <span className="flex items-center gap-1"><Users className="w-3 h-3"/> {s.user_count || 0} 用户</span>
                <span className="flex items-center gap-1"><Map className="w-3 h-3"/> {s.content_count || 0} 内容</span>
              </div>
              {s.additional_domains && s.additional_domains.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-3">
                  {s.additional_domains.map((d, i) => (
                    <span key={i}
                          className="px-1.5 py-0.5 text-[10px] bg-gray-100 dark:bg-gray-800 rounded font-mono">{d}</span>
                  ))}
                </div>
              )}
              <div className="flex items-center justify-end gap-1 pt-2 border-t border-gray-100 dark:border-gray-800">
                <button onClick={() => setShowUsers(s.id)}
                        className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800" title="用户管理">
                  <Users className="w-3.5 h-3.5 text-gray-500 dark:text-gray-400"/>
                </button>
                <button onClick={() => openEdit(s)} className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800"
                        title="编辑">
                  <Edit3 className="w-3.5 h-3.5 text-gray-500 dark:text-gray-400"/>
                </button>
                <button onClick={() => setDeleteId(s.id)}
                        className="p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20" title="删除">
                  <Trash2 className="w-3.5 h-3.5 text-red-500"/>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create/Edit Modal */}
      <Modal open={showForm} onClose={() => setShowForm(false)} title={editing ? '编辑站点' : '新增站点'}>
        <div className="max-h-[70vh] overflow-y-auto pr-1">
          <Input label="站点名称 *" value={form.name} onChange={v => setForm(f => ({...f, name: v}))}
                 placeholder="我的站点"/>
          <Input label="域名 *" value={form.domain} onChange={v => setForm(f => ({...f, domain: v}))}
                 placeholder="example.com"/>
          <Input label="描述" value={form.description} onChange={v => setForm(f => ({...f, description: v}))}
                 placeholder="站点描述" rows={3}/>
          <Input label="主题" value={form.theme} onChange={v => setForm(f => ({...f, theme: v}))}
                 placeholder="default"/>
          <Input label="附加域名" value={form.additional_domains}
                 onChange={v => setForm(f => ({...f, additional_domains: v}))}
                 placeholder="www.example.com, m.example.com（逗号分隔）"/>
          <div className="mb-3">
            <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">状态</label>
            <select value={form.is_active} onChange={e => setForm(f => ({...f, is_active: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white">
              <option value="true">活跃</option>
              <option value="false">停用</option>
            </select>
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-4 pt-3 border-t border-gray-100 dark:border-gray-800">
          <button onClick={() => setShowForm(false)}
                  className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg">取消
          </button>
          <button onClick={submit} disabled={createMut.isPending || updateMut.isPending}
                  className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
            {createMut.isPending || updateMut.isPending ? '保存中...' : '保存'}
          </button>
        </div>
      </Modal>

      {/* Site Users Modal */}
      <Modal open={showUsers !== null} onClose={() => setShowUsers(null)} title="站点用户管理">
        <SiteUsersPanel siteId={showUsers}/>
      </Modal>

      {/* Delete Confirm */}
      <DeleteConfirm onConfirm={() => deleteId && deleteMut.mutate(deleteId)}
                     onCancel={() => setDeleteId(null)}
                     title="确定删除此站点？" desc="删除站点将同时移除所有关联的用户关系和内容映射。"/>
    </>
  );
};

export default SitesTab;
