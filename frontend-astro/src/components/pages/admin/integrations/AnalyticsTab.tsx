'use client';

import {useState} from 'react';
import {useQuery, useMutation, useQueryClient} from '@tanstack/react-query';
import {EmptyState, Modal, SectionTitle, StatCard, StatusBadge} from '@/components/admin/shared-ui';
import {Activity, BarChart3, Edit3, Eye, Loader, Plus, Save, Trash2, X} from 'lucide-react';
import {apiClient} from '@/lib/api/base-client';
import {useConfirm} from '@/components/ui/confirm-provider';
import {GAConfig, BaiduConfig, Toggle, InputField, ActionButton} from './shared';


export default function AnalyticsTab({showToast}: {
  showToast: (msg: string, type?: 'success' | 'error' | 'info') => void
}) {
  const confirm = useConfirm();
  const qc = useQueryClient();
  const [showGAModal, setShowGAModal] = useState(false);
  const [showBaiduModal, setShowBaiduModal] = useState(false);
  const [editingBaidu, setEditingBaidu] = useState<BaiduConfig | null>(null);
  const [gaForm, setGAForm] = useState({
    tracking_id: '',
    measurement_id: '',
    api_secret: '',
    enable_page_view_tracking: true,
    enable_event_tracking: true,
    anonymize_ip: true,
    sample_rate: 100
  });
  const [baiduForm, setBaiduForm] = useState({
    site_token: '',
    api_key: '',
    enable_tracking: true,
    enable_data_sync: false
  });

  // GA Config
  const {data: gaConfig, isLoading: gaLoading} = useQuery({
    queryKey: ['integ-ga-config'],
    queryFn: async () => {
      const r = await apiClient.get('/integrations/analytics/google/config');
      return r.success && r.data ? r.data as GAConfig : null;
    },
  });

  // Baidu Configs
  const {data: baiduConfigs, isLoading: baiduLoading} = useQuery({
    queryKey: ['integ-baidu-configs'],
    queryFn: async () => {
      const r = await apiClient.get('/integrations/analytics/baidu/configs');
      const raw = r.success && r.data ? (r.data.configs || r.data) : [];
      return (Array.isArray(raw) ? raw : []) as BaiduConfig[];
    },
  });

  // GA Mutations
  const createGAMut = useMutation({
    mutationFn: (data: any) => apiClient.post('/integrations/analytics/google/config', data),
    onSuccess: (r) => {
      qc.invalidateQueries({queryKey: ['integ-ga-config']});
      setShowGAModal(false);
      showToast(r.message || 'Google Analytics 配置已创建');
    },
    onError: () => showToast('创建失败', 'error'),
  });

  const deleteGAMut = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/integrations/analytics/google/config/${id}`),
    onSuccess: (r) => {
      qc.invalidateQueries({queryKey: ['integ-ga-config']});
      showToast(r.message || '已停用');
    },
    onError: () => showToast('操作失败', 'error'),
  });

  // Baidu Mutations
  const createBaiduMut = useMutation({
    mutationFn: (data: any) => apiClient.post('/integrations/analytics/baidu/config', data),
    onSuccess: (r) => {
      qc.invalidateQueries({queryKey: ['integ-baidu-configs']});
      setShowBaiduModal(false);
      showToast(r.message || '百度统计配置已创建');
    },
    onError: () => showToast('创建失败', 'error'),
  });

  const updateBaiduMut = useMutation({
    mutationFn: ({id, data}: {
      id: number;
      data: any
    }) => apiClient.put(`/integrations/analytics/baidu/config/${id}`, data),
    onSuccess: (r) => {
      qc.invalidateQueries({queryKey: ['integ-baidu-configs']});
      setEditingBaidu(null);
      showToast(r.message || '已更新');
    },
    onError: () => showToast('更新失败', 'error'),
  });

  const deleteBaiduMut = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/integrations/analytics/baidu/config/${id}`),
    onSuccess: (r) => {
      qc.invalidateQueries({queryKey: ['integ-baidu-configs']});
      showToast(r.message || '已停用');
    },
    onError: () => showToast('操作失败', 'error'),
  });

  const handleCreateGA = () => {
    if (!gaForm.tracking_id) {
      showToast('请填写 Tracking ID', 'error');
      return;
    }
    createGAMut.mutate(gaForm);
  };

  const handleCreateBaidu = () => {
    if (!baiduForm.site_token) {
      showToast('请填写 Site Token', 'error');
      return;
    }
    createBaiduMut.mutate(baiduForm);
  };

  const baiduList = Array.isArray(baiduConfigs) ? baiduConfigs : [];

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={BarChart3} label="Google Analytics" value={gaConfig ? '已配置' : '未配置'}
                  color="from-orange-500 to-amber-500"/>
        <StatCard icon={BarChart3} label="百度统计" value={`${baiduList.length} 个配置`}
                  color="from-blue-500 to-indigo-500"/>
        <StatCard icon={Eye} label="页面追踪" value={gaConfig?.enable_page_view_tracking ? '启用' : '禁用'}
                  color="from-green-500 to-emerald-500"/>
        <StatCard icon={Activity} label="事件追踪" value={gaConfig?.enable_event_tracking ? '启用' : '禁用'}
                  color="from-purple-500 to-violet-500"/>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Google Analytics */}
        <div
          className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="p-5 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
            <SectionTitle icon={BarChart3} title="Google Analytics" subtitle="GA4 数据追踪"/>
            {!gaConfig && <ActionButton onClick={() => setShowGAModal(true)} icon={Plus} label="添加配置"/>}
          </div>
          {gaLoading ? (
            <div className="p-8 text-center"><Loader className="w-6 h-6 animate-spin mx-auto text-gray-400"/></div>
          ) : gaConfig ? (
            <div className="p-5 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                {[
                  ['Tracking ID', gaConfig.tracking_id || '—'],
                  ['Measurement ID', gaConfig.measurement_id || '—'],
                  ['采样率', gaConfig.sample_rate ? `${gaConfig.sample_rate}%` : '100%'],
                  ['状态', gaConfig.is_active ? '活跃' : '未激活'],
                ].map(([label, val], i) => (
                  <div key={i} className="p-3 bg-gray-50 dark:bg-gray-800 rounded-xl">
                    <p className="text-[11px] text-gray-400 uppercase tracking-wider">{label}</p>
                    <p className="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{val}</p>
                  </div>
                ))}
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Toggle checked={gaConfig.enable_page_view_tracking || false} onChange={() => {
                  }} disabled/>
                  <span className="text-xs text-gray-500 dark:text-gray-400">页面追踪</span>
                </div>
                <div className="flex items-center gap-2">
                  <Toggle checked={gaConfig.enable_event_tracking || false} onChange={() => {
                  }} disabled/>
                  <span className="text-xs text-gray-500 dark:text-gray-400">事件追踪</span>
                </div>
                <div className="flex items-center gap-2">
                  <Toggle checked={gaConfig.anonymize_ip || false} onChange={() => {
                  }} disabled/>
                  <span className="text-xs text-gray-500 dark:text-gray-400">IP 匿名化</span>
                </div>
              </div>
              {gaConfig.id && (
                <div className="flex gap-2">
                  <ActionButton onClick={async () => {
                    if (await confirm({
                      message: '确定停用 Google Analytics?',
                      variant: 'warning'
                    })) deleteGAMut.mutate(gaConfig.id!);
                  }} icon={Trash2} label="停用" variant="danger" size="sm"/>
                </div>
              )}
            </div>
          ) : (
            <EmptyState icon={BarChart3} title="尚未配置" desc="添加 GA4 配置以开始追踪访客数据"
                        action={<ActionButton onClick={() => setShowGAModal(true)} icon={Plus}
                                              label="添加 Google Analytics"/>}/>
          )}
        </div>

        {/* Baidu Analytics */}
        <div
          className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="p-5 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
            <SectionTitle icon={BarChart3} title="百度统计" subtitle="百度数据追踪"/>
            <ActionButton onClick={() => {
              setBaiduForm({site_token: '', api_key: '', enable_tracking: true, enable_data_sync: false});
              setEditingBaidu(null);
              setShowBaiduModal(true);
            }} icon={Plus} label="添加配置"/>
          </div>
          {baiduLoading ? (
            <div className="p-8 text-center"><Loader className="w-6 h-6 animate-spin mx-auto text-gray-400"/></div>
          ) : baiduList.length > 0 ? (
            <div className="divide-y divide-gray-100 dark:divide-gray-800">
              {baiduList.map((cfg: BaiduConfig, i: number) => (
                <div key={cfg.id || i} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <p
                        className="text-sm font-medium text-gray-900 dark:text-white">{cfg.site_name || `配置 #${cfg.id || i + 1}`}</p>
                      <p className="text-xs text-gray-400 font-mono">{cfg.site_token || cfg.tracking_id || '—'}</p>
                    </div>
                    <StatusBadge active={cfg.is_active || false}/>
                  </div>
                  <div className="flex items-center gap-3 mt-2">
                    <div className="flex items-center gap-2">
                      <Toggle checked={cfg.enable_tracking || false} onChange={() => {
                      }} disabled/>
                      <span className="text-xs text-gray-500 dark:text-gray-400">追踪</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Toggle checked={cfg.enable_data_sync || false} onChange={() => {
                      }} disabled/>
                      <span className="text-xs text-gray-500 dark:text-gray-400">数据同步</span>
                    </div>
                    <div className="flex-1"/>
                    <ActionButton onClick={() => {
                      setBaiduForm({
                        site_token: cfg.site_token || '',
                        api_key: cfg.api_key || '',
                        enable_tracking: cfg.enable_tracking || false,
                        enable_data_sync: cfg.enable_data_sync || false
                      });
                      setEditingBaidu(cfg);
                      setShowBaiduModal(true);
                    }} icon={Edit3} label="编辑" variant="ghost" size="sm"/>
                    <ActionButton onClick={async () => {
                      if (await confirm({
                        message: '确定停用此百度统计配置?',
                        variant: 'warning'
                      })) deleteBaiduMut.mutate(cfg.id!);
                    }} icon={Trash2} label="停用" variant="danger" size="sm"/>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState icon={BarChart3} title="尚未配置" desc="添加百度统计配置以追踪国内用户数据"
                        action={<ActionButton onClick={() => setShowBaiduModal(true)} icon={Plus}
                                              label="添加百度统计"/>}/>
          )}
        </div>
      </div>

      {/* GA Config Modal */}
      <Modal open={showGAModal} onClose={() => setShowGAModal(false)} title="添加 Google Analytics"
             subtitle="配置 GA4 追踪">
        <div className="space-y-4">
          <InputField label="Tracking ID *" value={gaForm.tracking_id}
                      onChange={v => setGAForm(f => ({...f, tracking_id: v}))} placeholder="G-XXXXXXXXXX"
                      hint="Google Analytics 4 的 Measurement ID"/>
          <InputField label="Measurement ID" value={gaForm.measurement_id}
                      onChange={v => setGAForm(f => ({...f, measurement_id: v}))} placeholder="G-XXXXXXXXXX"/>
          <InputField label="API Secret" value={gaForm.api_secret}
                      onChange={v => setGAForm(f => ({...f, api_secret: v}))} type="password"
                      hint="用于 Measurement Protocol 的密钥（可选）"/>
          <InputField label="采样率 (%)" value={String(gaForm.sample_rate)}
                      onChange={v => setGAForm(f => ({...f, sample_rate: Number(v) || 100}))} type="number"
                      placeholder="100"/>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700 dark:text-gray-300">页面浏览追踪</span>
              <Toggle checked={gaForm.enable_page_view_tracking}
                      onChange={v => setGAForm(f => ({...f, enable_page_view_tracking: v}))}/>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700 dark:text-gray-300">事件追踪</span>
              <Toggle checked={gaForm.enable_event_tracking}
                      onChange={v => setGAForm(f => ({...f, enable_event_tracking: v}))}/>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700 dark:text-gray-300">IP 匿名化</span>
              <Toggle checked={gaForm.anonymize_ip} onChange={v => setGAForm(f => ({...f, anonymize_ip: v}))}/>
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <ActionButton onClick={() => setShowGAModal(false)} icon={X} label="取消" variant="ghost"/>
            <ActionButton onClick={handleCreateGA} icon={Save} label="保存配置" loading={createGAMut.isPending}/>
          </div>
        </div>
      </Modal>

      {/* Baidu Config Modal */}
      <Modal open={showBaiduModal} onClose={() => {
        setShowBaiduModal(false);
        setEditingBaidu(null);
      }}
             title={editingBaidu ? '编辑百度统计' : '添加百度统计'} subtitle="配置百度数据追踪">
        <div className="space-y-4">
          <InputField label="Site Token *" value={baiduForm.site_token}
                      onChange={v => setBaiduForm(f => ({...f, site_token: v}))} placeholder="UM-XXXXXXXX-X"
                      hint="百度统计站点 Token"/>
          <InputField label="API Key" value={baiduForm.api_key} onChange={v => setBaiduForm(f => ({...f, api_key: v}))}
                      type="password" hint="用于数据同步的 API Key（可选）"/>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700 dark:text-gray-300">启用追踪</span>
              <Toggle checked={baiduForm.enable_tracking}
                      onChange={v => setBaiduForm(f => ({...f, enable_tracking: v}))}/>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700 dark:text-gray-300">数据同步</span>
              <Toggle checked={baiduForm.enable_data_sync}
                      onChange={v => setBaiduForm(f => ({...f, enable_data_sync: v}))}/>
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <ActionButton onClick={() => {
              setShowBaiduModal(false);
              setEditingBaidu(null);
            }} icon={X} label="取消" variant="ghost"/>
            {editingBaidu ? (
              <ActionButton onClick={() => updateBaiduMut.mutate({id: editingBaidu.id!, data: baiduForm})} icon={Save}
                            label="更新配置" loading={updateBaiduMut.isPending}/>
            ) : (
              <ActionButton onClick={handleCreateBaidu} icon={Save} label="保存配置"
                            loading={createBaiduMut.isPending}/>
            )}
          </div>
        </div>
      </Modal>
    </div>
  );
}
