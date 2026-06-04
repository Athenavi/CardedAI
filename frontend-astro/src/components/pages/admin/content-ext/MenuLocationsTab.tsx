'use client';

import React, {useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {DeleteConfirm, EmptyState, Modal} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import {useToast} from '@/components/ui/toast-provider';
import {ChevronLeft, ChevronRight, Edit3, MapPin, Plus, Trash2} from 'lucide-react';
import {Input, MenuLocation, Pagination} from './shared';
import type {ApiResponse} from '@/lib/api/base-types';
const MenuLocationsTab: React.FC = () => {
  const toast = useToast();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<MenuLocation | null>(null);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [form, setForm] = useState({name: '', slug: '', description: '', theme_supports: ''});

  const {data, isLoading} = useQuery({
    queryKey: ['menu-locations', page],
    queryFn: () => apiClient.get('/cms/management/menu-locations', {page, per_page: 15}),
  });
  const items: MenuLocation[] = data?.data?.menu_locations || [];
  const pagination: Pagination | undefined = data?.data?.pagination;

  const createMut = useMutation({
    mutationFn: (d: any) => apiClient.post('/cms/management/menu-locations', d),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['menu-locations']});
        setShowForm(false);
      } else toast.error(r.error || '操作失败');
    },
  });
  const updateMut = useMutation({
    mutationFn: ({id, ...d}: any) => apiClient.put(`/cms/management/menu-locations/${id}`, d),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['menu-locations']});
        setShowForm(false);
      } else toast.error(r.error || '操作失败');
    },
  });
  const deleteMut = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/cms/management/menu-locations/${id}`),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['menu-locations']});
        setDeleteId(null);
      } else toast.error(r.error || '操作失败');
    },
  });

  const openCreate = () => {
    setEditing(null);
    setForm({name: '', slug: '', description: '', theme_supports: ''});
    setShowForm(true);
  };
  const openEdit = (l: MenuLocation) => {
    setEditing(l);
    setForm({name: l.name, slug: l.slug, description: l.description || '', theme_supports: l.theme_supports || ''});
    setShowForm(true);
  };
  const submit = () => {
    if (!form.name.trim() || !form.slug.trim()) {
      toast.error('请填写名称和标识');
      return;
    }
    if (editing) updateMut.mutate({id: editing.id, ...form});
    else createMut.mutate(form);
  };

  return (
    <>
      <div className="flex items-center justify-end mb-4">
        <button onClick={openCreate}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-xl flex items-center gap-1.5">
          <Plus className="w-4 h-4"/>新建位置
        </button>
      </div>
      {isLoading ? <div className="animate-pulse space-y-2">{[1, 2, 3].map(i => <div key={i}
                                                                                     className="h-16 bg-gray-100 dark:bg-gray-800 rounded-xl"/>)}</div> :
        items.length === 0 ? <EmptyState icon={MapPin} title="暂无菜单位置" desc="定义菜单位置（如主菜单、页脚菜单等）"/> :
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {items.map(l => (
              <div key={l.id}
                   className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-100 dark:border-gray-700/50">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h4 className="text-sm font-semibold text-gray-900 dark:text-white">{l.name}</h4>
                    <code
                      className="text-[10px] bg-gray-200 dark:bg-gray-700 px-1.5 py-0.5 rounded text-gray-600 dark:text-gray-300">{l.slug}</code>
                  </div>
                  <div className="flex gap-1">
                    <button onClick={() => openEdit(l)}
                            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-400">
                      <Edit3
                      className="w-3.5 h-3.5"/></button>
                    <button onClick={() => setDeleteId(l.id)}
                            className="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 text-red-500"><Trash2
                      className="w-3.5 h-3.5"/></button>
                  </div>
                </div>
                {l.description && <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">{l.description}</p>}
                {l.theme_supports && <p className="text-[10px] text-gray-400">主题: {l.theme_supports}</p>}
              </div>
            ))}
          </div>}
      {pagination && pagination.total_pages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <span className="text-xs text-gray-500 dark:text-gray-400">共 {pagination.total} 条</span>
          <div className="flex items-center gap-1">
            <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}
                    className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-30">
              <ChevronLeft className="w-4 h-4"/></button>
            <span className="text-xs text-gray-600 dark:text-gray-400 px-2">{page}/{pagination.total_pages}</span>
            <button disabled={page >= pagination.total_pages} onClick={() => setPage(p => p + 1)}
                    className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-30">
              <ChevronRight className="w-4 h-4"/></button>
          </div>
        </div>
      )}
      <Modal open={showForm} onClose={() => setShowForm(false)} title={editing ? '编辑菜单位置' : '新建菜单位置'}>
        <Input label="名称 *" value={form.name} onChange={v => setForm({...form, name: v})} placeholder="例如：主菜单"/>
        <Input label="标识 *" value={form.slug} onChange={v => setForm({...form, slug: v})} placeholder="例如：primary"/>
        <Input label="描述" value={form.description} onChange={v => setForm({...form, description: v})} rows={2}/>
        <Input label="主题支持" value={form.theme_supports} onChange={v => setForm({...form, theme_supports: v})}
               placeholder="例如：default,minimal"/>
        <div className="flex justify-end gap-2 mt-4">
          <button onClick={() => setShowForm(false)}
                  className="px-4 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-300">取消
          </button>
          <button onClick={submit}
                  className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg">{editing ? '更新' : '创建'}</button>
        </div>
      </Modal>
      {deleteId !== null && (
        <Modal open={true} onClose={() => setDeleteId(null)} title="确认删除">
          <DeleteConfirm itemName={items.find(l => l.id === deleteId)?.name}
                         onConfirm={() => deleteMut.mutate(deleteId)} onCancel={() => setDeleteId(null)}
                         isPending={deleteMut.isPending}/>
        </Modal>
      )}
    </>
  );
};

export default MenuLocationsTab;
