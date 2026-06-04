'use client';

import React, {useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {DeleteConfirm, EmptyState, Modal} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import {ChevronLeft, ChevronRight, Edit3, FileText, Plus, Trash2} from 'lucide-react';
import {Input, Badge} from './shared';
import type {TaxConfig, Pagination} from './shared';
import {useToast} from '@/components/ui/toast-provider';
import type {ApiResponse} from '@/lib/api/base-types';
const TaxConfigsTab: React.FC = () => {
  const qc = useQueryClient();
  const toast = useToast();
  const [page, setPage] = useState(1);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<TaxConfig | null>(null);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [form, setForm] = useState({
    country: '',
    region: '',
    tax_type: 'VAT',
    rate: '',
    description: '',
    is_active: 'true'
  });

  const {data, isLoading} = useQuery({
    queryKey: ['tax-configs', page],
    queryFn: () => apiClient.get('/payment-management/tax-configs', {page, per_page: 15}),
  });

  const items: TaxConfig[] = data?.data?.tax_configs || [];
  const pagination: Pagination | undefined = data?.data?.pagination;

  const createMut = useMutation({
    mutationFn: (d: any) => apiClient.post('/payment-management/tax-configs', d),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['tax-configs']});
        setShowForm(false);
      } else toast.error(r.error || '操作失败');
    },
  });
  const updateMut = useMutation({
    mutationFn: ({id, ...d}: any) => apiClient.put(`/payment-management/tax-configs/${id}`, d),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['tax-configs']});
        setShowForm(false);
      } else toast.error(r.error || '操作失败');
    },
  });
  const deleteMut = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/payment-management/tax-configs/${id}`),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['tax-configs']});
        setDeleteId(null);
      } else toast.error(r.error || '操作失败');
    },
  });

  const openCreate = () => {
    setEditing(null);
    setForm({country: '', region: '', tax_type: 'VAT', rate: '', description: '', is_active: 'true'});
    setShowForm(true);
  };
  const openEdit = (t: TaxConfig) => {
    setEditing(t);
    setForm({
      country: t.country,
      region: t.region || '',
      tax_type: t.tax_type,
      rate: String(t.rate),
      description: t.description || '',
      is_active: String(t.is_active)
    });
    setShowForm(true);
  };
  const submit = () => {
    if (!form.country.trim() || !form.rate) {
      toast.error('请填写国家和税率');
      return;
    }
    const payload = {...form, rate: parseFloat(form.rate), is_active: form.is_active === 'true'};
    if (editing) updateMut.mutate({id: editing.id, ...payload});
    else createMut.mutate(payload);
  };

  return (
    <>
      <div className="flex items-center justify-end mb-4">
        <button onClick={openCreate}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-xl flex items-center gap-1.5">
          <Plus className="w-4 h-4"/>新建税务配置
        </button>
      </div>
      {isLoading ? <div className="animate-pulse space-y-2">{[1, 2, 3].map(i => <div key={i}
                                                                                     className="h-16 bg-gray-100 dark:bg-gray-800 rounded-xl"/>)}</div> :
        items.length === 0 ? <EmptyState icon={FileText} title="暂无税务配置" desc="创建税务配置以自动计算税费"/> :
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
              <tr className="border-b border-gray-100 dark:border-gray-800">
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">国家</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">地区</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">税种</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">税率</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">状态</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">操作</th>
              </tr>
              </thead>
              <tbody>{items.map(t => (
                <tr key={t.id}
                    className="border-b border-gray-50 dark:border-gray-800/50 hover:bg-gray-50 dark:hover:bg-gray-800/30">
                  <td className="py-3 px-4 font-medium text-gray-900 dark:text-white">{t.country}</td>
                  <td className="py-3 px-4 text-gray-600 dark:text-gray-400">{t.region || '—'}</td>
                  <td className="py-3 px-4 text-gray-600 dark:text-gray-400">{t.tax_type}</td>
                  <td className="py-3 px-4 font-semibold text-gray-900 dark:text-white">{(t.rate * 100).toFixed(1)}%
                  </td>
                  <td className="py-3 px-4"><Badge active={t.is_active}/></td>
                  <td className="py-3 px-4 text-right">
                    <button onClick={() => openEdit(t)}
                            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-400 mr-1">
                      <Edit3 className="w-3.5 h-3.5"/></button>
                    <button onClick={() => setDeleteId(t.id)}
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
      <Modal open={showForm} onClose={() => setShowForm(false)} title={editing ? '编辑税务配置' : '新建税务配置'}>
        <Input label="国家 *" value={form.country} onChange={v => setForm({...form, country: v})}
               placeholder="例如：CN"/>
        <Input label="地区" value={form.region} onChange={v => setForm({...form, region: v})} placeholder="例如：上海"/>
        <Input label="税种" value={form.tax_type} onChange={v => setForm({...form, tax_type: v})}
               placeholder="例如：VAT"/>
        <Input label="税率 (小数) *" value={form.rate} onChange={v => setForm({...form, rate: v})} type="number"
               placeholder="例如：0.13 表示 13%"/>
        <Input label="描述" value={form.description} onChange={v => setForm({...form, description: v})} rows={2}/>
        <div className="mb-3">
          <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">状态</label>
          <select value={form.is_active} onChange={e => setForm({...form, is_active: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white">
            <option value="true">启用</option>
            <option value="false">禁用</option>
          </select>
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
          <DeleteConfirm itemName={items.find(t => t.id === deleteId)?.country}
                         onConfirm={() => deleteMut.mutate(deleteId)} onCancel={() => setDeleteId(null)}
                         isPending={deleteMut.isPending}/>
        </Modal>
      )}
    </>
  );
};

export default TaxConfigsTab;
