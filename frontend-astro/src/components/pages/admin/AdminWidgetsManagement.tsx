'use client';

import React, {useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {AdminShell} from '@/components/admin/AdminShell';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {apiClient} from '@/lib/api/base-client';
import {useToast} from '@/components/ui/toast-provider';
import {useConfirm} from '@/components/ui/confirm-provider';
import {Blocks, GripVertical, Layers, Plus, RefreshCw, Settings, ToggleLeft, ToggleRight, Trash2} from 'lucide-react';

interface WidgetInstance {
  id: number;
  widget_type: string;
  area: string;
  title: string;
  config: string | Record<string, any>;
  order_index: number;
  is_active: boolean;
  conditions: string | null;
  created_at: string;
  updated_at: string;
}

interface WidgetType {
  type: string;
  name: string;
  description?: string;
  category?: string;
  icon?: string;
}

interface WidgetArea {
  id: string;
  name: string;
  description?: string;
}

function WidgetsInner() {
  const toast = useToast();
  const confirm = useConfirm();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [areaFilter, setAreaFilter] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [editingWidget, setEditingWidget] = useState<WidgetInstance | null>(null);
  const [createForm, setCreateForm] = useState({
    widget_type: '', area: '', title: '', config: '{}', is_active: true
  });
  const [editConfig, setEditConfig] = useState('');

  const {data: widgetsData, isLoading} = useQuery({
    queryKey: ['widgets', page, areaFilter],
    queryFn: () => apiClient.get('/cms/widgets/', {
      page, per_page: 20, area: areaFilter || undefined
    }),
  });

  const {data: typesData} = useQuery({
    queryKey: ['widget-types'],
    queryFn: () => apiClient.get('/cms/widgets/types'),
  });

  const {data: areasData} = useQuery({
    queryKey: ['widget-areas'],
    queryFn: () => apiClient.get('/cms/widgets/areas'),
  });

  const items: WidgetInstance[] = widgetsData?.data?.items || [];
  const total: number = widgetsData?.data?.total || 0;
  const totalPages: number = widgetsData?.data?.total_pages || 0;
  const types: WidgetType[] = typesData?.data?.types || [];
  const areas: WidgetArea[] = areasData?.data?.areas || [];

  const createMut = useMutation({
    mutationFn: (data: any) => apiClient.post('/cms/widgets/', data),
    onSuccess: (r: any) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['widgets']});
        setShowCreate(false);
        setCreateForm({widget_type: '', area: '', title: '', config: '{}', is_active: true});
        toast.success('小部件创建成功');
      } else toast.error(r.error || '创建失败');
    },
  });

  const updateMut = useMutation({
    mutationFn: ({id, data}: { id: number; data: any }) =>
      apiClient.put(`/cms/widgets/${id}`, data),
    onSuccess: (r: any) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['widgets']});
        setEditingWidget(null);
        toast.success('小部件更新成功');
      } else toast.error(r.error || '更新失败');
    },
  });

  const toggleMut = useMutation({
    mutationFn: ({id, is_active}: { id: number; is_active: boolean }) =>
      apiClient.patch(`/cms/widgets/${id}/toggle`, {is_active}),
    onSuccess: () => {
      qc.invalidateQueries({queryKey: ['widgets']});
      toast.success('状态已切换');
    },
  });

  const deleteMut = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/cms/widgets/${id}`),
    onSuccess: (r: any) => {
      if (r.success) {
        qc.invalidateQueries({queryKey: ['widgets']});
        toast.success('小部件已删除');
      } else toast.error(r.error || '删除失败');
    },
  });

  const handleCreate = () => {
    if (!createForm.widget_type || !createForm.area || !createForm.title) {
      toast.error('请填写必要字段');
      return;
    }
    let config = {};
    try {
      config = JSON.parse(createForm.config);
    } catch {
      toast.error('配置 JSON 格式错误');
      return;
    }
    createMut.mutate({...createForm, config});
  };

  const handleUpdate = () => {
    if (!editingWidget) return;
    let config = {};
    try {
      config = JSON.parse(editConfig);
    } catch {
      toast.error('配置 JSON 格式错误');
      return;
    }
    updateMut.mutate({id: editingWidget.id, data: {title: editingWidget.title, config}});
  };

  const handleDelete = async (id: number, title: string) => {
    const ok = await confirm({title: '删除小部件', message: `确定删除「${title}」？此操作不可撤销。`, variant: 'danger'});
    if (ok) deleteMut.mutate(id);
  };

  const openEdit = (w: WidgetInstance) => {
    setEditingWidget(w);
    setEditConfig(typeof w.config === 'string' ? w.config : JSON.stringify(w.config, null, 2));
  };

  const getAreaName = (areaId: string) =>
    areas.find(a => a.id === areaId)?.name || areaId;

  const getTypeName = (typeId: string) =>
    types.find(t => t.type === typeId)?.name || typeId;

  const activeCount = items.filter(w => w.is_active).length;
  const inactiveCount = items.filter(w => !w.is_active).length;

  return (
    <AdminShell title="小部件管理">
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          {[
            {label: '总小部件', value: total, icon: <Blocks className="w-5 h-5"/>, color: 'blue'},
            {label: '已启用', value: activeCount, icon: <ToggleRight className="w-5 h-5"/>, color: 'green'},
            {label: '已禁用', value: inactiveCount, icon: <ToggleLeft className="w-5 h-5"/>, color: 'gray'},
            {label: '区域数', value: areas.length, icon: <Layers className="w-5 h-5"/>, color: 'purple'},
          ].map(s => (
            <div key={s.label}
                 className="flex items-center gap-3 bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
              <div
                className={`p-2 rounded-lg bg-${s.color}-100 dark:bg-${s.color}-900/30 text-${s.color}-600 dark:text-${s.color}-400`}>
                {s.icon}
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{s.value}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">{s.label}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Toolbar */}
        <div className="flex flex-wrap items-center gap-3">
          <select value={areaFilter} onChange={e => {
            setAreaFilter(e.target.value);
            setPage(1);
          }}
                  className="px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm dark:text-white">
            <option value="">全部区域</option>
            {areas.map(a => <option key={a.id} value={a.id}>{a.name || a.id}</option>)}
          </select>
          <div className="flex-1"/>
          <button onClick={() => qc.invalidateQueries({queryKey: ['widgets']})}
                  className="flex items-center gap-1.5 px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg text-sm hover:bg-gray-50 dark:hover:bg-gray-800 dark:text-white">
            <RefreshCw className="w-4 h-4"/> 刷新
          </button>
          <button onClick={() => setShowCreate(true)}
                  className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700">
            <Plus className="w-4 h-4"/> 添加小部件
          </button>
        </div>

        {/* Widget List */}
        {isLoading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-100 dark:bg-gray-800 rounded-xl animate-pulse"/>
            ))}
          </div>
        ) : !items.length ? (
          <div className="text-center py-16 text-gray-400">
            <Blocks className="w-12 h-12 mx-auto mb-3 opacity-40"/>
            <p>暂无小部件</p>
          </div>
        ) : (
          <div
            className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-900/50">
              <tr>
                <th
                  className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">排序
                </th>
                <th
                  className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">标题
                </th>
                <th
                  className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">类型
                </th>
                <th
                  className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">区域
                </th>
                <th
                  className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">状态
                </th>
                <th
                  className="px-5 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">操作
                </th>
              </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
              {items.map(w => (
                <tr key={w.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                  <td className="px-5 py-3">
                      <span className="flex items-center gap-1 text-sm text-gray-500">
                        <GripVertical className="w-4 h-4 opacity-30"/> {w.order_index}
                      </span>
                  </td>
                  <td className="px-5 py-3">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">{w.title}</p>
                    <p className="text-xs text-gray-400">ID: {w.id}</p>
                  </td>
                  <td className="px-5 py-3">
                      <span
                        className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
                        {getTypeName(w.widget_type)}
                      </span>
                  </td>
                  <td className="px-5 py-3 text-sm text-gray-600 dark:text-gray-300">{getAreaName(w.area)}</td>
                  <td className="px-5 py-3">
                    <button onClick={() => toggleMut.mutate({id: w.id, is_active: !w.is_active})}
                            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium cursor-pointer ${
                              w.is_active
                                ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                                : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                            }`}>
                      {w.is_active ? <ToggleRight className="w-3 h-3"/> : <ToggleLeft className="w-3 h-3"/>}
                      {w.is_active ? '启用' : '禁用'}
                    </button>
                  </td>
                  <td className="px-5 py-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button onClick={() => openEdit(w)}
                              className="p-1.5 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 text-blue-600 dark:text-blue-400"
                              title="编辑">
                        <Settings className="w-4 h-4"/>
                      </button>
                      <button onClick={() => handleDelete(w.id, w.title)}
                              className="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400"
                              title="删除">
                        <Trash2 className="w-4 h-4"/>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">共 {total} 个小部件</p>
            <div className="flex gap-1">
              <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}
                      className="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-40 hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800 dark:text-white">上一页
              </button>
              <span className="px-3 py-1.5 text-sm text-gray-500">{page} / {totalPages}</span>
              <button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}
                      className="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-40 hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800 dark:text-white">下一页
              </button>
            </div>
          </div>
        )}

        {/* Create Dialog */}
        {showCreate && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
               onClick={() => setShowCreate(false)}>
            <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 w-full max-w-lg shadow-2xl"
                 onClick={e => e.stopPropagation()}>
              <h3 className="text-lg font-bold mb-4 dark:text-white">添加小部件</h3>
              <div className="space-y-3">
                <div>
                  <label
                    className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">小部件类型</label>
                  <select value={createForm.widget_type}
                          onChange={e => setCreateForm(f => ({...f, widget_type: e.target.value}))}
                          className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm dark:text-white">
                    <option value="">选择类型...</option>
                    {types.map(t => <option key={t.type} value={t.type}>{t.name} ({t.type})</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">显示区域</label>
                  <select value={createForm.area}
                          onChange={e => setCreateForm(f => ({...f, area: e.target.value}))}
                          className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm dark:text-white">
                    <option value="">选择区域...</option>
                    {areas.map(a => <option key={a.id} value={a.id}>{a.name || a.id}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">标题</label>
                  <input value={createForm.title}
                         onChange={e => setCreateForm(f => ({...f, title: e.target.value}))}
                         placeholder="小部件标题"
                         className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm dark:text-white"/>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">配置
                    (JSON)</label>
                  <textarea value={createForm.config}
                            onChange={e => setCreateForm(f => ({...f, config: e.target.value}))}
                            rows={4}
                            className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm dark:text-white font-mono resize-none"/>
                </div>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={createForm.is_active}
                         onChange={e => setCreateForm(f => ({...f, is_active: e.target.checked}))}
                         className="rounded"/>
                  <span className="text-sm dark:text-white">启用</span>
                </label>
              </div>
              <div className="flex justify-end gap-2 mt-5">
                <button onClick={() => setShowCreate(false)}
                        className="px-4 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-white">取消
                </button>
                <button onClick={handleCreate} disabled={createMut.isPending}
                        className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
                  {createMut.isPending ? '创建中...' : '创建'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Edit Dialog */}
        {editingWidget && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
               onClick={() => setEditingWidget(null)}>
            <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 w-full max-w-lg shadow-2xl"
                 onClick={e => e.stopPropagation()}>
              <h3 className="text-lg font-bold mb-4 dark:text-white">编辑小部件</h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">标题</label>
                  <input value={editingWidget.title}
                         onChange={e => setEditingWidget(w => w ? {...w, title: e.target.value} : null)}
                         className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm dark:text-white"/>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">配置
                    (JSON)</label>
                  <textarea value={editConfig}
                            onChange={e => setEditConfig(e.target.value)}
                            rows={6}
                            className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm dark:text-white font-mono resize-none"/>
                </div>
                <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
                  <span>类型: {getTypeName(editingWidget.widget_type)}</span>
                  <span>区域: {getAreaName(editingWidget.area)}</span>
                  <span>排序: {editingWidget.order_index}</span>
                </div>
              </div>
              <div className="flex justify-end gap-2 mt-5">
                <button onClick={() => setEditingWidget(null)}
                        className="px-4 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-white">取消
                </button>
                <button onClick={handleUpdate} disabled={updateMut.isPending}
                        className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
                  {updateMut.isPending ? '保存中...' : '保存'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AdminShell>
  );
}

export default function AdminWidgetsManagement() {
  return (
    <AuthGuard>
      <QueryProvider>
        <WidgetsInner/>
      </QueryProvider>
    </AuthGuard>
  );
}
