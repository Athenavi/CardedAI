'use client';

import React, {useState} from 'react';
import {useMutation, useQueryClient} from '@tanstack/react-query';
import {apiClient} from '@/lib/api/base-client';
import {useConfirm} from '@/components/ui/confirm-provider';
import {useToast} from '@/components/ui/toast-provider';
import {Package, Plus, Crown, Edit3, Check, Trash2} from 'lucide-react';
import {VIPPlan, PlanForm, Modal, Inp} from './shared';

const PlansTab: React.FC<{ plans: VIPPlan[]; onChanged: () => void }> = ({plans, onChanged}) => {
  const confirm = useConfirm();
  const toast = useToast();
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<VIPPlan | null>(null);
  const [f, setF] = useState<PlanForm>({
    name: '',
    description: '',
    price: '',
    original_price: '',
    duration_days: '30',
    level: '1',
    features: '[]'
  });

  const openCreate = () => {
    setEditing(null);
    setF({name: '', description: '', price: '', original_price: '', duration_days: '30', level: '1', features: '[]'});
    setShowForm(true);
  };
  const openEdit = (p: VIPPlan) => {
    setEditing(p);
    setF({
      name: p.name,
      description: p.description || '',
      price: String(p.price),
      original_price: p.original_price ? String(p.original_price) : '',
      duration_days: String(p.duration_days),
      level: String(p.level),
      features: p.features || '[]'
    });
    setShowForm(true);
  };

  const createMut = useMutation({
    mutationFn: (d: PlanForm) => apiClient.post('/dashboard/vip/plans', d),
    onSuccess: (r) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['admin-vip']});
        setShowForm(false);
        onChanged();
      } else if (r.error) toast.error(r.error || '操作失败');
    },
  });
  const updateMut = useMutation({
    mutationFn: (d: { id: number; form: PlanForm }) => apiClient.put(`/dashboard/vip/plans/${d.id}`, d.form),
    onSuccess: (r) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['admin-vip']});
        setShowForm(false);
        onChanged();
      } else if (r.error) toast.error(r.error || '操作失败');
    },
  });
  const deleteMut = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/dashboard/vip/plans/${id}`),
    onSuccess: (r) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['admin-vip']});
        onChanged();
      } else if (r.error) toast.error(r.error || '操作失败');
    },
  });
  const toggleMut = useMutation({
    mutationFn: (p: VIPPlan) => apiClient.put(`/dashboard/vip/plans/${p.id}`, {
      is_active: p.is_active ? '0' : '1',
      name: p.name,
      price: String(p.price),
      duration_days: String(p.duration_days),
      level: String(p.level)
    }),
    onSuccess: () => {
      qc.invalidateQueries({queryKey: ['admin-vip']});
      onChanged();
    },
  });

  const submitPlan = () => {
    if (!f.name.trim()) {
      toast.error('请输入套餐名称');
      return;
    }
    if (editing) updateMut.mutate({id: editing.id, form: f});
    else createMut.mutate(f);
  };

  return <>
    <div className="flex items-center justify-between mb-4">
      <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2"><Package
        className="w-5 h-5"/>套餐管理</h3>
      <button onClick={openCreate}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-xl flex items-center gap-1.5">
        <Plus className="w-4 h-4"/>新建套餐
      </button>
    </div>
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {plans.map(p => (
        <div key={p.id}
             className={`rounded-2xl border p-5 relative ${p.is_active ? 'bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700' : 'bg-gray-50 dark:bg-gray-800/50 border-gray-200 dark:border-gray-700 opacity-75'}`}>
          <div className="flex items-start justify-between mb-3">
            <div>
              <h4 className="font-bold text-gray-900 dark:text-white">{p.name}</h4>
              {p.description && <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{p.description}</p>}
            </div>
            {!p.is_active && <span
              className="px-2 py-0.5 text-[10px] rounded-full bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400">已禁用</span>}
          </div>
          <div className="flex items-baseline gap-1 mb-3">
            <span className="text-2xl font-bold text-gray-900 dark:text-white">¥{p.price}</span>
            {p.original_price && p.original_price > p.price &&
              <span className="text-xs text-gray-400 line-through">¥{p.original_price}</span>}
            <span className="text-xs text-gray-400 ml-auto">/{p.duration_days}天</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 mb-3">
            <Crown className="w-3.5 h-3.5"/>Lv.{p.level}
          </div>
          <div className="flex gap-1.5 mt-3 pt-3 border-t border-gray-100 dark:border-gray-800">
            <button onClick={() => openEdit(p)}
                    className="flex-1 px-3 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-300 flex items-center justify-center gap-1">
              <Edit3 className="w-3 h-3"/>编辑
            </button>
            <button onClick={() => toggleMut.mutate(p)}
                    className={`flex-1 px-3 py-1.5 text-xs border rounded-lg flex items-center justify-center gap-1 ${p.is_active ? 'border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800' : 'border-green-200 text-green-700 hover:bg-green-50'}`}>
              <Check className="w-3 h-3"/>{p.is_active ? '禁用' : '启用'}
            </button>
            <button onClick={async () => {
              if (await confirm({message: `确定删除「${p.name}」？`, variant: 'danger'})) deleteMut.mutate(p.id);
            }}
                    className="px-3 py-1.5 text-xs border border-red-200 dark:border-red-900/30 rounded-lg text-red-500 hover:bg-red-50 dark:hover:bg-red-900/10 flex items-center justify-center gap-1">
              <Trash2 className="w-3 h-3"/></button>
          </div>
        </div>
      ))}
    </div>

    <Modal open={showForm} title={editing ? '编辑套餐' : '新建套餐'} onClose={() => setShowForm(false)}>
      <Inp label="套餐名称 *" value={f.name} onChange={v => setF({...f, name: v})} placeholder="例如：月度会员"/>
      <Inp label="描述" value={f.description} onChange={v => setF({...f, description: v})} placeholder="套餐简介"
           rows={2}/>
      <div className="flex gap-3">
        <Inp label="价格 *" value={f.price} onChange={v => setF({...f, price: v})} type="number" placeholder="29.99"
             className="flex-1"/>
        <Inp label="原价" value={f.original_price} onChange={v => setF({...f, original_price: v})} type="number"
             placeholder="49.99" className="flex-1"/>
      </div>
      <div className="flex gap-3">
        <Inp label="有效期(天) *" value={f.duration_days} onChange={v => setF({...f, duration_days: v})} type="number"
             placeholder="30" className="flex-1"/>
        <Inp label="VIP 等级" value={f.level} onChange={v => setF({...f, level: v})} type="number" placeholder="1"
             className="flex-1"/>
      </div>
      <Inp label="功能配置 (JSON)" value={f.features} onChange={v => setF({...f, features: v})} rows={2}
           placeholder='["无广告","专属标识"]'/>
      <button onClick={submitPlan}
              className="w-full mt-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-xl font-medium">{editing ? '保存修改' : '创建套餐'}</button>
    </Modal>
  </>;
};

export default PlansTab;
