'use client';

import React, {useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {EmptyState, Modal} from '@/components/admin/shared-ui';
import {useToast} from '@/components/ui/toast-provider';
import {apiClient} from '@/lib/api/base-client';
import {Settings, Edit3} from 'lucide-react';
import {RevenueSharingConfig} from './shared';
import type {ApiResponse} from '@/lib/api/base-types';
const ConfigTab: React.FC = () => {
  const qc = useQueryClient();
  const toast = useToast();
  const [editing, setEditing] = useState<RevenueSharingConfig | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({platform_percentage: '', min_payout_amount: '', payout_cycle: '', description: ''});

  const {data, isLoading} = useQuery({
    queryKey: ['revenue-configs'],
    queryFn: () => apiClient.get('/shop/revenue/configs'),
  });

  const items: RevenueSharingConfig[] = data?.data?.configs || [];

  const updateMut = useMutation({
    mutationFn: ({revenue_type, ...d}: any) => apiClient.put(`/shop/revenue/configs/${revenue_type}`, d),
    onSuccess: (r: ApiResponse) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['revenue-configs']});
        setShowForm(false);
      } else toast.error(r.error || '操作失败');
    },
  });

  const openEdit = (c: RevenueSharingConfig) => {
    setEditing(c);
    setForm({
      platform_percentage: String(c.platform_percentage),
      min_payout_amount: String(c.min_payout_amount),
      payout_cycle: c.payout_cycle || 'monthly',
      description: c.description || '',
    });
    setShowForm(true);
  };

  const submit = () => {
    if (!editing) return;
    updateMut.mutate({
      revenue_type: editing.revenue_type,
      platform_percentage: parseFloat(form.platform_percentage) || 30,
      min_payout_amount: parseFloat(form.min_payout_amount) || 100,
      payout_cycle: form.payout_cycle,
      description: form.description,
    });
  };

  return (
    <>
      {isLoading ? (
        <div className="space-y-2">{[...Array(3)].map((_, i) => <div key={i}
                                                                     className="h-20 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse"/>)}</div>
      ) : items.length === 0 ? (
        <EmptyState icon={Settings} title="暂无分成配置" desc="系统将在首次交易时自动生成默认配置"/>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {items.map(c => (
            <div key={c.id}
                 className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100">{c.revenue_type}</h3>
                  {c.description && <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{c.description}</p>}
                </div>
                <button onClick={() => openEdit(c)} className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800">
                  <Edit3 className="w-4 h-4 text-gray-500 dark:text-gray-400"/>
                </button>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">平台分成</div>
                  <div className="text-lg font-semibold text-blue-600">{c.platform_percentage}%</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">用户分成</div>
                  <div className="text-lg font-semibold text-green-600">{(100 - c.platform_percentage).toFixed(1)}%
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">最低提现</div>
                  <div className="font-medium">¥{c.min_payout_amount.toFixed(2)}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">结算周期</div>
                  <div
                    className="font-medium">{c.payout_cycle === 'monthly' ? '每月' : c.payout_cycle === 'weekly' ? '每周' : c.payout_cycle}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal open={showForm} onClose={() => setShowForm(false)} title={`编辑分成配置 - ${editing?.revenue_type}`}>
        <div className="mb-3">
          <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">平台分成比例 (%)</label>
          <input type="number" value={form.platform_percentage}
                 onChange={e => setForm(f => ({...f, platform_percentage: e.target.value}))}
                 className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"/>
          <p
            className="text-xs text-gray-400 mt-1">用户分成将自动设为 {100 - (parseFloat(form.platform_percentage) || 30)}%</p>
        </div>
        <div className="mb-3">
          <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">最低提现金额</label>
          <input type="number" value={form.min_payout_amount}
                 onChange={e => setForm(f => ({...f, min_payout_amount: e.target.value}))}
                 className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"/>
        </div>
        <div className="mb-3">
          <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">结算周期</label>
          <select value={form.payout_cycle} onChange={e => setForm(f => ({...f, payout_cycle: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white">
            <option value="weekly">每周</option>
            <option value="biweekly">每两周</option>
            <option value="monthly">每月</option>
          </select>
        </div>
        <div className="mb-3">
          <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">说明</label>
          <textarea rows={2} value={form.description}
                    onChange={e => setForm(f => ({...f, description: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white resize-none"/>
        </div>
        <div className="flex justify-end gap-2 mt-4 pt-3 border-t border-gray-100 dark:border-gray-800">
          <button onClick={() => setShowForm(false)}
                  className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg">取消
          </button>
          <button onClick={submit} disabled={updateMut.isPending}
                  className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
            {updateMut.isPending ? '保存中...' : '保存'}
          </button>
        </div>
      </Modal>
    </>
  );
};

export default ConfigTab;
