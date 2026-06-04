'use client';

import React, {useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {DeleteConfirm, EmptyState, Modal} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import {ChevronLeft, ChevronRight, CreditCard, Edit3, Plus, Search, Trash2} from 'lucide-react';
import {Input, Badge} from './shared';
import type {PaymentGateway, Pagination} from './shared';
import {useToast} from '@/components/ui/toast-provider';
import type {ApiResponse} from '@/lib/api/base-types';
const GatewaysTab: React.FC = () => {
  const qc = useQueryClient();
  const toast = useToast();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<PaymentGateway | null>(null);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [form, setForm] = useState({
    name: '',
    provider: '',
    config_data: '{}',
    supported_currencies: '',
    is_active: 'true'
  });

  const {data, isLoading} = useQuery({
    queryKey: ['payment-gateways', page, search],
    queryFn: () => apiClient.get('/payment-management/gateways', {page, per_page: 15, search: search || undefined}),
  });

  const items: PaymentGateway[] = data?.data?.gateways || [];
  const pagination: Pagination | undefined = data?.data?.pagination;

  const createMut = useMutation({
    mutationFn: (d: any) => apiClient.post('/payment-management/gateways', d),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['payment-gateways']});
        setShowForm(false);
      } else toast.error(r.error || '操作失败');
    },
  });
  const updateMut = useMutation({
    mutationFn: ({id, ...d}: any) => apiClient.put(`/payment-management/gateways/${id}`, d),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['payment-gateways']});
        setShowForm(false);
      } else toast.error(r.error || '操作失败');
    },
  });
  const deleteMut = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/payment-management/gateways/${id}`),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['payment-gateways']});
        setDeleteId(null);
      } else toast.error(r.error || '操作失败');
    },
  });

  const openCreate = () => {
    setEditing(null);
    setForm({name: '', provider: '', config_data: '{}', supported_currencies: '', is_active: 'true'});
    setShowForm(true);
  };
  const openEdit = (g: PaymentGateway) => {
    setEditing(g);
    setForm({
      name: g.name,
      provider: g.provider,
      config_data: g.config_data || '{}',
      supported_currencies: g.supported_currencies || '',
      is_active: String(g.is_active)
    });
    setShowForm(true);
  };
  const submit = () => {
    if (!form.name.trim() || !form.provider.trim()) {
      toast.error('请填写名称和提供商');
      return;
    }
    const payload = {...form, is_active: form.is_active === 'true'};
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
                   placeholder="搜索网关..."
                   className="pl-9 pr-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white w-48"/>
          </div>
        </div>
        <button onClick={openCreate}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-xl flex items-center gap-1.5">
          <Plus className="w-4 h-4"/>新建网关
        </button>
      </div>
      {isLoading ? <div className="animate-pulse space-y-2">{[1, 2, 3].map(i => <div key={i}
                                                                                     className="h-16 bg-gray-100 dark:bg-gray-800 rounded-xl"/>)}</div> :
        items.length === 0 ?
          <EmptyState icon={CreditCard} title="暂无支付网关" desc="创建第一个支付网关以开始接受支付"/> :
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
              <tr className="border-b border-gray-100 dark:border-gray-800">
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">名称</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">提供商</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">支持货币</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">状态</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400">操作</th>
              </tr>
              </thead>
              <tbody>{items.map(g => (
                <tr key={g.id}
                    className="border-b border-gray-50 dark:border-gray-800/50 hover:bg-gray-50 dark:hover:bg-gray-800/30">
                  <td className="py-3 px-4 font-medium text-gray-900 dark:text-white">{g.name}</td>
                  <td className="py-3 px-4 text-gray-600 dark:text-gray-400">{g.provider}</td>
                  <td
                    className="py-3 px-4 text-gray-500 dark:text-gray-400 text-xs">{g.supported_currencies || '—'}</td>
                  <td className="py-3 px-4"><Badge active={g.is_active}/></td>
                  <td className="py-3 px-4 text-right">
                    <button onClick={() => openEdit(g)}
                            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-400 mr-1">
                      <Edit3 className="w-3.5 h-3.5"/></button>
                    <button onClick={() => setDeleteId(g.id)}
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
      <Modal open={showForm} onClose={() => setShowForm(false)} title={editing ? '编辑支付网关' : '新建支付网关'}>
        <Input label="名称 *" value={form.name} onChange={v => setForm({...form, name: v})} placeholder="例如：Stripe"/>
        <Input label="提供商 *" value={form.provider} onChange={v => setForm({...form, provider: v})}
               placeholder="例如：stripe"/>
        <Input label="支持货币" value={form.supported_currencies}
               onChange={v => setForm({...form, supported_currencies: v})} placeholder="例如：USD,EUR,CNY"/>
        <Input label="配置数据 (JSON)" value={form.config_data} onChange={v => setForm({...form, config_data: v})}
               rows={3}/>
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
          <DeleteConfirm itemName={items.find(g => g.id === deleteId)?.name}
                         onConfirm={() => deleteMut.mutate(deleteId)} onCancel={() => setDeleteId(null)}
                         isPending={deleteMut.isPending}/>
        </Modal>
      )}
    </>
  );
};

export default GatewaysTab;
