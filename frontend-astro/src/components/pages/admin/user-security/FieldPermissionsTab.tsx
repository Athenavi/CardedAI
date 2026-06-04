'use client';

import React, {useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {DeleteConfirm, EmptyState, Modal} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import {useToast} from '@/components/ui/toast-provider';
import {ChevronLeft, ChevronRight, Edit3, Lock as LockIcon, Plus, Trash2, Unlock} from 'lucide-react';
import {FieldPermission, Input, Pagination} from './shared';
import type {ApiResponse} from '@/lib/api/base-types';
const FieldPermissionsTab: React.FC = () => {
  const toast = useToast();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<FieldPermission | null>(null);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [form, setForm] = useState({role_id: '', model_name: '', field_name: '', can_read: 'true', can_write: 'false'});

  const {data, isLoading} = useQuery({
    queryKey: ['field-permissions', page],
    queryFn: () => apiClient.get('/users/security/field-permissions', {page, per_page: 15}),
  });
  const items: FieldPermission[] = data?.data?.field_permissions || [];
  const pagination: Pagination | undefined = data?.data?.pagination;

  const createMut = useMutation({
    mutationFn: (d: any) => apiClient.post('/users/security/field-permissions', d),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['field-permissions']});
        setShowForm(false);
      } else toast.error(r.error || '操作失败');
    },
  });
  const updateMut = useMutation({
    mutationFn: ({id, ...d}: any) => apiClient.put(`/users/security/field-permissions/${id}`, d),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['field-permissions']});
        setShowForm(false);
      } else toast.error(r.error || '操作失败');
    },
  });
  const deleteMut = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/users/security/field-permissions/${id}`),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['field-permissions']});
        setDeleteId(null);
      } else toast.error(r.error || '操作失败');
    },
  });

  const openCreate = () => {
    setEditing(null);
    setForm({role_id: '', model_name: '', field_name: '', can_read: 'true', can_write: 'false'});
    setShowForm(true);
  };
  const openEdit = (p: FieldPermission) => {
    setEditing(p);
    setForm({
      role_id: String(p.role_id),
      model_name: p.model_name,
      field_name: p.field_name,
      can_read: String(p.can_read),
      can_write: String(p.can_write)
    });
    setShowForm(true);
  };
  const submit = () => {
    if (!form.role_id || !form.model_name.trim() || !form.field_name.trim()) {
      toast.error('请填写完整信息');
      return;
    }
    const payload = {
      role_id: parseInt(form.role_id),
      model_name: form.model_name,
      field_name: form.field_name,
      can_read: form.can_read === 'true',
      can_write: form.can_write === 'true'
    };
    if (editing) updateMut.mutate({id: editing.id, ...payload});
    else createMut.mutate(payload);
  };

  return (
    <>
      <div className="flex items-center justify-end mb-4">
        <button onClick={openCreate}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-xl flex items-center gap-1.5">
          <Plus className="w-4 h-4"/>新建权限
        </button>
      </div>
      {isLoading ? <div className="animate-pulse space-y-2">{[1, 2, 3].map(i => <div key={i}
                                                                                     className="h-14 bg-gray-100 dark:bg-gray-800 rounded-xl"/>)}</div> :
        items.length === 0 ? <EmptyState icon={LockIcon} title="暂无字段权限" desc="配置角色对模型字段的读写权限"/> :
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
              <tr className="border-b border-gray-100 dark:border-gray-800">
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">角色ID</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">模型</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">字段</th>
                <th className="text-center py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">可读</th>
                <th className="text-center py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">可写</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">操作</th>
              </tr>
              </thead>
              <tbody>{items.map(p => (
                <tr key={p.id}
                    className="border-b border-gray-50 dark:border-gray-800/50 hover:bg-gray-50 dark:hover:bg-gray-800/30">
                  <td className="py-3 px-4 font-mono text-xs">#{p.role_id}</td>
                  <td className="py-3 px-4"><code
                    className="text-xs bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded">{p.model_name}</code></td>
                  <td className="py-3 px-4"><code
                    className="text-xs bg-blue-50 dark:bg-blue-900/20 px-1.5 py-0.5 rounded text-blue-700 dark:text-blue-400">{p.field_name}</code>
                  </td>
                  <td className="py-3 px-4 text-center">{p.can_read ?
                    <LockIcon className="w-4 h-4 text-green-500 mx-auto"/> :
                    <LockIcon className="w-4 h-4 text-gray-300 mx-auto"/>}</td>
                  <td className="py-3 px-4 text-center">{p.can_write ?
                    <Unlock className="w-4 h-4 text-green-500 mx-auto"/> :
                    <LockIcon className="w-4 h-4 text-gray-300 mx-auto"/>}</td>
                  <td className="py-3 px-4 text-right">
                    <button onClick={() => openEdit(p)}
                            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-400 mr-1">
                      <Edit3 className="w-3.5 h-3.5"/></button>
                    <button onClick={() => setDeleteId(p.id)}
                            className="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 text-red-500"><Trash2
                      className="w-3.5 h-3.5"/></button>
                  </td>
                </tr>
              ))}</tbody>
            </table>
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
      <Modal open={showForm} onClose={() => setShowForm(false)} title={editing ? '编辑字段权限' : '新建字段权限'}>
        <Input label="角色 ID *" value={form.role_id} onChange={v => setForm({...form, role_id: v})} type="number"
               placeholder="角色ID"/>
        <Input label="模型名称 *" value={form.model_name} onChange={v => setForm({...form, model_name: v})}
               placeholder="例如：Article"/>
        <Input label="字段名称 *" value={form.field_name} onChange={v => setForm({...form, field_name: v})}
               placeholder="例如：title"/>
        <div className="flex gap-4 mb-3">
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={form.can_read === 'true'}
                   onChange={e => setForm({...form, can_read: String(e.target.checked)})} className="rounded"/>可读
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={form.can_write === 'true'}
                   onChange={e => setForm({...form, can_write: String(e.target.checked)})} className="rounded"/>可写
          </label>
        </div>
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
          <DeleteConfirm itemName={`权限#${deleteId}`} onConfirm={() => deleteMut.mutate(deleteId)}
                         onCancel={() => setDeleteId(null)} isPending={deleteMut.isPending}/>
        </Modal>
      )}
    </>
  );
};

export default FieldPermissionsTab;
