'use client';

import React, {useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {EmptyState, Modal} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import {useToast} from '@/components/ui/toast-provider';
import {ChevronLeft, ChevronRight, Link2, Plus, Trash2} from 'lucide-react';
import {useConfirm} from '@/components/ui/confirm-provider';
import {Input, LocationAssignment, Pagination} from './shared';
import type {ApiResponse} from '@/lib/api/base-types';
const AssignmentsTab: React.FC = () => {
  const confirm = useConfirm();
  const toast = useToast();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({menu_id: '', location_id: ''});

  const {data, isLoading} = useQuery({
    queryKey: ['menu-assignments', page],
    queryFn: () => apiClient.get('/cms/management/menu-location-assignments', {page, per_page: 15}),
  });
  const items: LocationAssignment[] = data?.data?.assignments || [];
  const pagination: Pagination | undefined = data?.data?.pagination;

  const createMut = useMutation({
    mutationFn: (d: any) => apiClient.post('/cms/management/menu-location-assignments', d),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['menu-assignments']});
        setShowForm(false);
      } else toast.error(r.error || '操作失败');
    },
  });
  const deleteMut = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/cms/management/menu-location-assignments/${id}`),
    onSuccess: () => qc.invalidateQueries({queryKey: ['menu-assignments']}),
  });

  const submit = () => {
    if (!form.menu_id || !form.location_id) {
      toast.error('请填写菜单ID和位置ID');
      return;
    }
    createMut.mutate({menu_id: parseInt(form.menu_id), location_id: parseInt(form.location_id)});
  };

  return (
    <>
      <div className="flex items-center justify-end mb-4">
        <button onClick={() => {
          setForm({menu_id: '', location_id: ''});
          setShowForm(true);
        }}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-xl flex items-center gap-1.5">
          <Plus className="w-4 h-4"/>新建关联
        </button>
      </div>
      {isLoading ? <div className="animate-pulse space-y-2">{[1, 2, 3].map(i => <div key={i}
                                                                                     className="h-12 bg-gray-100 dark:bg-gray-800 rounded-xl"/>)}</div> :
        items.length === 0 ? <EmptyState icon={Link2} title="暂无菜单关联" desc="将菜单分配到菜单位置"/> :
          <div className="space-y-2">
            {items.map(a => (
              <div key={a.id}
                   className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-100 dark:border-gray-700/50">
                <div className="flex items-center gap-3">
                  <Link2 className="w-4 h-4 text-gray-400"/>
                  <span className="text-sm text-gray-900 dark:text-white">菜单#{a.menu_id}</span>
                  <span className="text-xs text-gray-400">→</span>
                  <span className="text-sm text-gray-600 dark:text-gray-300">位置#{a.location_id}</span>
                  <span
                    className="text-[10px] text-gray-400">{a.created_at ? new Date(a.created_at).toLocaleString('zh-CN') : ''}</span>
                </div>
                <button onClick={async () => {
                  if (await confirm({message: '确定删除此关联？', variant: 'danger'})) deleteMut.mutate(a.id);
                }}
                        className="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 text-red-500"><Trash2
                  className="w-3.5 h-3.5"/></button>
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
      <Modal open={showForm} onClose={() => setShowForm(false)} title="新建菜单-位置关联">
        <Input label="菜单 ID *" value={form.menu_id} onChange={v => setForm({...form, menu_id: v})} type="number"
               placeholder="菜单ID"/>
        <Input label="位置 ID *" value={form.location_id} onChange={v => setForm({...form, location_id: v})}
               type="number" placeholder="位置ID"/>
        <div className="flex justify-end gap-2 mt-4">
          <button onClick={() => setShowForm(false)}
                  className="px-4 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-300">取消
          </button>
          <button onClick={submit}
                  className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg">创建
          </button>
        </div>
      </Modal>
    </>
  );
};

export default AssignmentsTab;
