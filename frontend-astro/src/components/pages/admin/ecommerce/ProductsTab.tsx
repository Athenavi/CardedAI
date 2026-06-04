'use client';

import React, {useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {DeleteConfirm, EmptyState, Modal, Pagination, StatusBadge} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import {useToast} from '@/components/ui/toast-provider';
import {Edit3, Package, Plus, Search, Trash2} from 'lucide-react';
import {Input, Select, MoneyDisplay} from './shared';
import type {Product} from './shared';
import type {ApiResponse} from '@/lib/api/base-types';
const ProductsTab: React.FC = () => {
  const toast = useToast();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Product | null>(null);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [form, setForm] = useState({
    name: '', slug: '', description: '', price: '', compare_price: '',
    sku: '', stock_quantity: '0', is_active: 'true', is_digital: 'false', category: ''
  });

  const {data, isLoading} = useQuery({
    queryKey: ['products', page, search],
    queryFn: () => apiClient.get('/shop/products', {page, per_page: 15, search: search || undefined}),
  });

  const items: Product[] = data?.data?.products || data?.data?.items || [];
  const total: number = data?.data?.total || 0;

  const createMut = useMutation({
    mutationFn: (d: any) => apiClient.post('/shop/products', d),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['products']});
        setShowForm(false);
      } else toast.error(r.error || '操作失败');
    },
  });
  const updateMut = useMutation({
    mutationFn: ({id, ...d}: any) => apiClient.put(`/shop/products/${id}`, d),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['products']});
        setShowForm(false);
      } else toast.error(r.error || '操作失败');
    },
  });
  const deleteMut = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/shop/products/${id}`),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['products']});
        setDeleteId(null);
      } else toast.error(r.error || '操作失败');
    },
  });

  const openCreate = () => {
    setEditing(null);
    setForm({
      name: '',
      slug: '',
      description: '',
      price: '',
      compare_price: '',
      sku: '',
      stock_quantity: '0',
      is_active: 'true',
      is_digital: 'false',
      category: ''
    });
    setShowForm(true);
  };
  const openEdit = (p: Product) => {
    setEditing(p);
    setForm({
      name: p.name, slug: p.slug, description: p.description || '', price: String(p.price),
      compare_price: p.compare_price ? String(p.compare_price) : '', sku: p.sku || '',
      stock_quantity: String(p.stock_quantity), is_active: String(p.is_active),
      is_digital: String(p.is_digital), category: p.category || ''
    });
    setShowForm(true);
  };
  const submit = () => {
    if (!form.name.trim()) {
      toast.error('请填写商品名称');
      return;
    }
    const payload = {
      ...form,
      price: parseFloat(form.price) || 0,
      compare_price: form.compare_price ? parseFloat(form.compare_price) : null,
      stock_quantity: parseInt(form.stock_quantity) || 0,
      is_active: form.is_active === 'true',
      is_digital: form.is_digital === 'true',
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
                   placeholder="搜索商品..."
                   className="pl-9 pr-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm dark:text-white w-64"/>
          </div>
        </div>
        <button onClick={openCreate}
                className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700">
          <Plus className="w-4 h-4"/> 新增商品
        </button>
      </div>

      {isLoading ? (
        <div className="space-y-2">{[...Array(5)].map((_, i) => <div key={i}
                                                                     className="h-16 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse"/>)}</div>
      ) : items.length === 0 ? (
        <EmptyState icon={Package} title="暂无商品" desc="点击「新增商品」开始创建"/>
      ) : (
        <div
          className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
            <tr className="bg-gray-50 dark:bg-gray-800/50">
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">商品名称</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">SKU</th>
              <th className="text-right px-4 py-3 font-medium text-gray-500 dark:text-gray-400">价格</th>
              <th className="text-right px-4 py-3 font-medium text-gray-500 dark:text-gray-400">库存</th>
              <th className="text-center px-4 py-3 font-medium text-gray-500 dark:text-gray-400">状态</th>
              <th className="text-center px-4 py-3 font-medium text-gray-500 dark:text-gray-400">类型</th>
              <th className="text-right px-4 py-3 font-medium text-gray-500 dark:text-gray-400">操作</th>
            </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {items.map(p => (
              <tr key={p.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/30">
                <td className="px-4 py-3">
                  <div className="font-medium text-gray-900 dark:text-gray-100">{p.name}</div>
                  {p.category && <div className="text-xs text-gray-400">{p.category}</div>}
                </td>
                <td className="px-4 py-3 text-gray-500 dark:text-gray-400 font-mono text-xs">{p.sku || '-'}</td>
                <td className="px-4 py-3 text-right">
                  <MoneyDisplay amount={p.price}/>
                  {p.compare_price && p.compare_price > p.price && (
                    <span className="ml-1 text-xs text-gray-400 line-through">¥{p.compare_price.toFixed(2)}</span>
                  )}
                </td>
                <td className="px-4 py-3 text-right">
                    <span
                      className={p.stock_quantity <= 0 ? 'text-red-500 font-medium' : p.stock_quantity <= 10 ? 'text-yellow-600' : ''}>
                      {p.stock_quantity}
                    </span>
                </td>
                <td className="px-4 py-3 text-center">
                  <StatusBadge active={p.is_active}/>
                </td>
                <td className="px-4 py-3 text-center">
                    <span
                      className={`px-2 py-0.5 text-[10px] rounded-full font-medium ${p.is_digital ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400' : 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400'}`}>
                      {p.is_digital ? '数字' : '实物'}
                    </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-1">
                    <button onClick={() => openEdit(p)}
                            className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800" title="编辑">
                      <Edit3 className="w-3.5 h-3.5 text-gray-500 dark:text-gray-400"/>
                    </button>
                    <button onClick={() => setDeleteId(p.id)}
                            className="p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20" title="删除">
                      <Trash2 className="w-3.5 h-3.5 text-red-500"/>
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            </tbody>
          </table>
          {total > 15 && (
            <div className="p-3 border-t border-gray-100 dark:border-gray-800">
              <Pagination page={page} totalPages={Math.ceil(total / 15)} onPageChange={setPage}/>
            </div>
          )}
        </div>
      )}

      {/* Create/Edit Modal */}
      <Modal open={showForm} onClose={() => setShowForm(false)} title={editing ? '编辑商品' : '新增商品'}>
        <div className="max-h-[70vh] overflow-y-auto pr-1">
          <Input label="商品名称 *" value={form.name} onChange={v => setForm(f => ({...f, name: v}))}
                 placeholder="输入商品名称"/>
          <Input label="Slug" value={form.slug} onChange={v => setForm(f => ({...f, slug: v}))}
                 placeholder="product-slug"/>
          <Input label="描述" value={form.description} onChange={v => setForm(f => ({...f, description: v}))}
                 placeholder="商品描述" rows={3}/>
          <div className="grid grid-cols-2 gap-3">
            <Input label="价格 *" value={form.price} onChange={v => setForm(f => ({...f, price: v}))} type="number"
                   placeholder="0.00"/>
            <Input label="划线价" value={form.compare_price} onChange={v => setForm(f => ({...f, compare_price: v}))}
                   type="number" placeholder="0.00"/>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Input label="SKU" value={form.sku} onChange={v => setForm(f => ({...f, sku: v}))} placeholder="SKU-001"/>
            <Input label="库存" value={form.stock_quantity} onChange={v => setForm(f => ({...f, stock_quantity: v}))}
                   type="number" placeholder="0"/>
          </div>
          <Input label="分类" value={form.category} onChange={v => setForm(f => ({...f, category: v}))}
                 placeholder="商品分类"/>
          <div className="grid grid-cols-2 gap-3">
            <Select label="状态" value={form.is_active} onChange={v => setForm(f => ({...f, is_active: v}))}
                    options={[{value: 'true', label: '启用'}, {value: 'false', label: '禁用'}]}/>
            <Select label="类型" value={form.is_digital} onChange={v => setForm(f => ({...f, is_digital: v}))}
                    options={[{value: 'false', label: '实物商品'}, {value: 'true', label: '数字商品'}]}/>
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

      {/* Delete Confirm */}
      {deleteId !== null && (
        <Modal open={true} onClose={() => setDeleteId(null)} title="确认删除">
          <DeleteConfirm itemName={`商品#${deleteId}`}
                         onConfirm={() => deleteMut.mutate(deleteId)}
                         onCancel={() => setDeleteId(null)}
                         isPending={deleteMut.isPending}/>
        </Modal>
      )}
    </>
  );
};

export default ProductsTab;
