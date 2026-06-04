'use client';

import React, {useState} from 'react';
import {useMutation, useQueryClient} from '@tanstack/react-query';
import {apiClient} from '@/lib/api/base-client';
import {useConfirm} from '@/components/ui/confirm-provider';
import {useToast} from '@/components/ui/toast-provider';
import {Shield, Plus, Edit3, Check, Trash2} from 'lucide-react';
import {VIPFeature, FeatureForm, Modal, Inp} from './shared';

const FeaturesTab: React.FC<{ features: VIPFeature[]; onChanged: () => void }> = ({features, onChanged}) => {
  const confirm = useConfirm();
  const toast = useToast();
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<VIPFeature | null>(null);
  const [f, setF] = useState<FeatureForm>({code: '', name: '', description: '', required_level: '1'});

  const openCreate = () => {
    setEditing(null);
    setF({code: '', name: '', description: '', required_level: '1'});
    setShowForm(true);
  };
  const openEdit = (fe: VIPFeature) => {
    setEditing(fe);
    setF({code: fe.code, name: fe.name, description: fe.description || '', required_level: String(fe.required_level)});
    setShowForm(true);
  };

  const createMut = useMutation({
    mutationFn: (d: FeatureForm) => apiClient.post('/dashboard/vip/features', d),
    onSuccess: (r) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['admin-vip']});
        setShowForm(false);
        onChanged();
      } else if (r.error) toast.error(r.error || '操作失败');
    },
  });
  const updateMut = useMutation({
    mutationFn: (d: { id: number; form: FeatureForm }) => apiClient.put(`/dashboard/vip/features/${d.id}`, d.form),
    onSuccess: (r) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['admin-vip']});
        setShowForm(false);
        onChanged();
      } else if (r.error) toast.error(r.error || '操作失败');
    },
  });
  const deleteMut = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/dashboard/vip/features/${id}`),
    onSuccess: (r) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['admin-vip']});
        onChanged();
      } else if (r.error) toast.error(r.error || '操作失败');
    },
  });
  const toggleMut = useMutation({
    mutationFn: (fe: VIPFeature) => apiClient.put(`/dashboard/vip/features/${fe.id}`, {
      is_active: fe.is_active ? '0' : '1',
      code: fe.code,
      name: fe.name,
      required_level: String(fe.required_level)
    }),
    onSuccess: () => {
      qc.invalidateQueries({queryKey: ['admin-vip']});
      onChanged();
    },
  });

  const submitFeature = () => {
    if (!f.code.trim() || !f.name.trim()) {
      toast.error('请填写功能代码和名称');
      return;
    }
    if (editing) updateMut.mutate({id: editing.id, form: f});
    else createMut.mutate(f);
  };

  return <>
    <div className="flex items-center justify-between mb-4">
      <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2"><Shield
        className="w-5 h-5"/>功能管理</h3>
      <button onClick={openCreate}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-xl flex items-center gap-1.5">
        <Plus className="w-4 h-4"/>新建功能
      </button>
    </div>
    <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      <table className="w-full">
        <thead className="bg-gray-50 dark:bg-gray-800 border-b">
        <tr>
          <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">代码</th>
          <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">名称</th>
          <th
            className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase hidden sm:table-cell">描述
          </th>
          <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">等级</th>
          <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">状态</th>
          <th className="px-5 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">操作
          </th>
        </tr>
        </thead>
        <tbody className="divide-y">
        {features.map(fe => (
          <tr key={fe.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
            <td className="px-5 py-3 text-sm font-mono text-gray-700 dark:text-gray-300">{fe.code}</td>
            <td className="px-5 py-3 text-sm font-medium text-gray-900 dark:text-white">{fe.name}</td>
            <td
              className="px-5 py-3 text-sm text-gray-500 dark:text-gray-400 hidden sm:table-cell">{fe.description || '-'}</td>
            <td className="px-5 py-3 text-sm"><span
              className="px-2 py-0.5 text-xs rounded-full bg-purple-100 dark:bg-purple-900/20 text-purple-700">Lv.{fe.required_level}</span>
            </td>
            <td className="px-5 py-3"><span
              className={`px-2 py-0.5 text-xs rounded-full ${fe.is_active ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' : 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'}`}>{fe.is_active ? '启用' : '禁用'}</span>
            </td>
            <td className="px-5 py-3 text-right">
              <button onClick={() => openEdit(fe)}
                      className="p-1.5 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg"
                      title="编辑"><Edit3 className="w-3.5 h-3.5"/></button>
              <button onClick={() => toggleMut.mutate(fe)}
                      className="p-1.5 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
                      title={fe.is_active ? '禁用' : '启用'}><Check className="w-3.5 h-3.5"/></button>
              <button onClick={async () => {
                if (await confirm({message: `确定删除「${fe.name}」？`, variant: 'danger'})) deleteMut.mutate(fe.id);
              }} className="p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg" title="删除"><Trash2
                className="w-3.5 h-3.5"/></button>
            </td>
          </tr>
        ))}
        </tbody>
      </table>
    </div>

    <Modal open={showForm} title={editing ? '编辑功能' : '新建功能'} onClose={() => setShowForm(false)}>
      <Inp label="功能代码 *" value={f.code} onChange={v => setF({...f, code: v})} placeholder="no_ads"/>
      <Inp label="功能名称 *" value={f.name} onChange={v => setF({...f, name: v})} placeholder="无广告"/>
      <Inp label="描述" value={f.description} onChange={v => setF({...f, description: v})}
           placeholder="浏览时无广告干扰" rows={2}/>
      <Inp label="所需 VIP 等级" value={f.required_level} onChange={v => setF({...f, required_level: v})} type="number"
           placeholder="1"/>
      <button onClick={submitFeature}
              className="w-full mt-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-xl font-medium">{editing ? '保存修改' : '创建功能'}</button>
    </Modal>
  </>;
};

export default FeaturesTab;
