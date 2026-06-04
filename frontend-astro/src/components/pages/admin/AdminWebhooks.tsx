import {useState} from 'react';
import {AdminShell} from '@/components/admin/AdminShell';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {useQuery, useMutation, useQueryClient} from '@tanstack/react-query';
import {apiClient} from '@/lib/api/base-client';
import {formatDateTime as formatTime} from '@/lib/utils';
import {useConfirm} from '@/components/ui/confirm-provider';
import {useToast} from '@/components/ui/toast-provider';
import {Webhook, Plus, Trash2, Edit3, CheckCircle, XCircle, Clock, Eye, Activity, AlertTriangle} from 'lucide-react';

interface WebhookData {
    id: number;
    url: string;
    events: string[];
    is_active: boolean;
    created_at?: string;
    updated_at?: string;
}

interface WebhookDelivery {
    id: number;
    webhook_id: number;
    event: string;
    payload: any;
    status: 'pending' | 'success' | 'failed';
    status_code?: number;
    response_body?: string;
    error_message?: string;
    created_at: string;
    completed_at?: string;
}

const EVENT_OPTIONS = [
    'article.created',
    'article.updated',
    'article.published',
    'article.deleted',
    'comment.created',
    'user.registered',
    'media.uploaded'
];

const STATUS_CONFIG = {
  pending: {color: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400', icon: Clock},
  success: {color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400', icon: CheckCircle},
  failed: {color: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400', icon: XCircle}
};

function WebhooksInner() {
  const confirm = useConfirm();
  const toast = useToast();
    const qc = useQueryClient();
    const [showCreateDialog, setShowCreateDialog] = useState(false);
    const [editingWebhook, setEditingWebhook] = useState<WebhookData | null>(null);
    const [selectedDelivery, setSelectedDelivery] = useState<WebhookDelivery | null>(null);
    const [formData, setFormData] = useState({url: '', events: [] as string[], is_active: true});

    // 查询 Webhook 列表
    const {data: webhooks, isLoading: webhooksLoading} = useQuery({
        queryKey: ['webhooks'],
        queryFn: async () => {
            const res = await apiClient.get('/webhooks');
            return res.data || [];
        }
    });

    // 查询投递记录
    const {data: deliveries} = useQuery({
        queryKey: ['webhook-deliveries'],
        queryFn: async () => {
            const res = await apiClient.get('/webhooks/deliveries');
            return res.data || [];
        }
    });

    // 创建 Webhook
    const createMut = useMutation({
        mutationFn: (data: any) => apiClient.post('/webhooks', data),
        onSuccess: () => {
            qc.invalidateQueries({queryKey: ['webhooks']});
            setShowCreateDialog(false);
            setFormData({url: '', events: [], is_active: true});
          toast.success('Webhook 创建成功！');
        }
    });

    // 更新 Webhook
    const updateMut = useMutation({
        mutationFn: ({id, data}: { id: number; data: any }) =>
            apiClient.put(`/webhooks/${id}`, data),
        onSuccess: () => {
            qc.invalidateQueries({queryKey: ['webhooks']});
            setEditingWebhook(null);
          toast.success('Webhook 更新成功！');
        }
    });

    // 删除 Webhook
    const deleteMut = useMutation({
        mutationFn: (id: number) => apiClient.delete(`/webhooks/${id}`),
        onSuccess: () => {
            qc.invalidateQueries({queryKey: ['webhooks']});
          toast.success('Webhook 已删除！');
        }
    });

    // 测试 Webhook
    const testMut = useMutation({
        mutationFn: (id: number) => apiClient.post(`/webhooks/${id}/test`),
        onSuccess: () => {
            qc.invalidateQueries({queryKey: ['webhook-deliveries']});
          toast.success('测试事件已发送！');
        }
    });

    const handleCreate = () => {
        if (!formData.url || formData.events.length === 0) {
          toast.error('请填写 URL 并至少选择一个事件');
            return;
        }
        createMut.mutate(formData);
    };

    const handleUpdate = () => {
        if (!editingWebhook) return;
        updateMut.mutate({id: editingWebhook.id, data: formData});
    };

  const handleDelete = async (id: number) => {
    if (await confirm({message: '确定要删除此 Webhook 吗？', variant: 'danger'})) {
            deleteMut.mutate(id);
        }
    };

    const handleEdit = (webhook: WebhookData) => {
        setEditingWebhook(webhook);
        setFormData({
            url: webhook.url,
            events: webhook.events,
            is_active: webhook.is_active
        });
    };

    const toggleEvent = (event: string) => {
        setFormData(prev => ({
            ...prev,
            events: prev.events.includes(event)
                ? prev.events.filter(e => e !== event)
                : [...prev.events, event]
        }));
    };

    const getStatusBadge = (status: string) => {
        const config = STATUS_CONFIG[status as keyof typeof STATUS_CONFIG];
        const Icon = config.icon;
        return (
            <span
                className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${config.color}`}>
        <Icon className="w-3 h-3"/>
                {status}
      </span>
        );
    };

    // formatTime imported from @/lib/utils as formatDateTime

    return (
        <AdminShell title="Webhook 管理">
            <div className="space-y-6">
                {/* 统计卡片 */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="bg-white dark:bg-gray-900 rounded-xl border p-4">
                      <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">活跃 Webhook</div>
                        <div className="text-2xl font-bold text-green-600">
                            {webhooks?.filter((w: WebhookData) => w.is_active).length || 0}
                        </div>
                    </div>
                    <div className="bg-white dark:bg-gray-900 rounded-xl border p-4">
                      <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">总 Webhook</div>
                        <div className="text-2xl font-bold">{webhooks?.length || 0}</div>
                    </div>
                    <div className="bg-white dark:bg-gray-900 rounded-xl border p-4">
                      <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">今日投递</div>
                        <div className="text-2xl font-bold text-blue-600">
                            {deliveries?.filter((d: WebhookDelivery) => {
                                const today = new Date().toDateString();
                                return new Date(d.created_at).toDateString() === today;
                            }).length || 0}
                        </div>
                    </div>
                    <div className="bg-white dark:bg-gray-900 rounded-xl border p-4">
                      <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">失败次数</div>
                        <div className="text-2xl font-bold text-red-600">
                            {deliveries?.filter((d: WebhookDelivery) => d.status === 'failed').length || 0}
                        </div>
                    </div>
                </div>

                {/* Webhook 列表 */}
                <div className="bg-white dark:bg-gray-900 rounded-xl border overflow-hidden">
                    <div className="px-6 py-4 border-b flex items-center justify-between">
                        <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                            <Webhook className="w-5 h-5"/>
                            Webhook 列表
                        </h3>
                        <button
                            onClick={() => {
                                setEditingWebhook(null);
                                setFormData({url: '', events: [], is_active: true});
                                setShowCreateDialog(true);
                            }}
                            className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition flex items-center gap-1.5"
                        >
                            <Plus className="w-4 h-4"/>
                            新建 Webhook
                        </button>
                    </div>

                    {webhooksLoading ? (
                        <div className="p-12 text-center">
                            <div
                                className="animate-spin w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto"/>
                        </div>
                    ) : !webhooks?.length ? (
                        <div className="p-12 text-center text-gray-400">
                            <Webhook className="w-16 h-16 mx-auto mb-4 opacity-30"/>
                            <p>暂无 Webhook</p>
                        </div>
                    ) : (
                        <div className="divide-y">
                            {webhooks.map((webhook: WebhookData) => (
                                <div key={webhook.id}
                                     className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition">
                                    <div className="flex items-start justify-between mb-2">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2 mb-1">
                                                <span
                                                    className="font-medium text-gray-900 dark:text-white">{webhook.url}</span>
                                                {webhook.is_active ? (
                                                    <span
                                                      className="px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs rounded-full">活跃</span>
                                                ) : (
                                                    <span
                                                      className="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 text-xs rounded-full">停用</span>
                                                )}
                                            </div>
                                          <div className="text-xs text-gray-500 dark:text-gray-400 space-x-3">
                                                <span>ID: {webhook.id}</span>
                                                <span>事件: {webhook.events.join(', ')}</span>
                                                <span>创建时间: {formatTime(webhook.created_at || '')}</span>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <button
                                                onClick={() => testMut.mutate(webhook.id)}
                                                className="p-2 text-gray-400 hover:text-blue-600 transition"
                                                title="测试"
                                            >
                                                <Activity className="w-4 h-4"/>
                                            </button>
                                            <button
                                                onClick={() => handleEdit(webhook)}
                                                className="p-2 text-gray-400 hover:text-blue-600 transition"
                                                title="编辑"
                                            >
                                                <Edit3 className="w-4 h-4"/>
                                            </button>
                                            <button
                                                onClick={() => handleDelete(webhook.id)}
                                                className="p-2 text-gray-400 hover:text-red-600 transition"
                                                title="删除"
                                            >
                                                <Trash2 className="w-4 h-4"/>
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* 投递记录 */}
                {deliveries && deliveries.length > 0 && (
                    <div className="bg-white dark:bg-gray-900 rounded-xl border overflow-hidden">
                        <div className="px-6 py-4 border-b">
                            <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                                <Clock className="w-5 h-5"/>
                                最近投递记录
                            </h3>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead className="bg-gray-50 dark:bg-gray-800">
                                <tr>
                                  <th
                                    className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">事件
                                  </th>
                                  <th
                                    className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">状态
                                  </th>
                                  <th
                                    className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase hidden md:table-cell">状态码
                                  </th>
                                  <th
                                    className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase hidden lg:table-cell">时间
                                  </th>
                                  <th
                                    className="px-5 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">操作
                                  </th>
                                </tr>
                                </thead>
                                <tbody className="divide-y">
                                {deliveries.slice(0, 10).map((delivery: WebhookDelivery) => (
                                    <tr key={delivery.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                                        <td className="px-5 py-4 text-sm text-gray-900 dark:text-white">{delivery.event}</td>
                                        <td className="px-5 py-4">{getStatusBadge(delivery.status)}</td>
                                      <td
                                        className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400 hidden md:table-cell">
                                            {delivery.status_code || '-'}
                                        </td>
                                      <td
                                        className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400 hidden lg:table-cell">
                                            {formatTime(delivery.created_at)}
                                        </td>
                                        <td className="px-5 py-4 text-right">
                                            <button
                                                onClick={() => setSelectedDelivery(delivery)}
                                                className="p-1.5 inline-block text-gray-400 hover:text-blue-600"
                                            >
                                                <Eye className="w-4 h-4"/>
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>

            {/* 创建/编辑对话框 */}
            {(showCreateDialog || editingWebhook) && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-2xl w-full">
                        <div className="px-6 py-4 border-b">
                            <h3 className="font-semibold text-lg">
                                {editingWebhook ? '编辑 Webhook' : '新建 Webhook'}
                            </h3>
                        </div>
                        <div className="p-6 space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    URL *
                                </label>
                                <input
                                    type="url"
                                    value={formData.url}
                                    onChange={(e) => setFormData({...formData, url: e.target.value})}
                                    placeholder="https://example.com/webhook"
                                    className="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                    订阅事件 *
                                </label>
                                <div className="grid grid-cols-2 gap-2">
                                    {EVENT_OPTIONS.map(event => (
                                        <label key={event}
                                               className="flex items-center gap-2 p-2 border rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
                                            <input
                                                type="checkbox"
                                                checked={formData.events.includes(event)}
                                                onChange={() => toggleEvent(event)}
                                                className="w-4 h-4 text-blue-600 rounded"
                                            />
                                            <span className="text-sm">{event}</span>
                                        </label>
                                    ))}
                                </div>
                            </div>

                            <div>
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={formData.is_active}
                                        onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                                        className="w-4 h-4 text-blue-600 rounded"
                                    />
                                    <span className="text-sm">立即激活</span>
                                </label>
                            </div>
                        </div>
                        <div className="px-6 py-4 border-t flex justify-end gap-3">
                            <button
                                onClick={() => {
                                    setShowCreateDialog(false);
                                    setEditingWebhook(null);
                                }}
                                className="px-4 py-2 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition"
                            >
                                取消
                            </button>
                            <button
                                onClick={editingWebhook ? handleUpdate : handleCreate}
                                disabled={createMut.isPending || updateMut.isPending}
                                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                            >
                                {editingWebhook ? '保存' : '创建'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* 投递详情对话框 */}
            {selectedDelivery && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div
                        className="bg-white dark:bg-gray-900 rounded-2xl max-w-3xl w-full max-h-[80vh] overflow-hidden flex flex-col">
                        <div className="px-6 py-4 border-b flex items-center justify-between">
                            <h3 className="font-semibold text-lg">投递详情 #{selectedDelivery.id}</h3>
                            <button
                                onClick={() => setSelectedDelivery(null)}
                                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
                            >
                                ✕
                            </button>
                        </div>
                        <div className="flex-1 overflow-y-auto p-6 space-y-4">
                            <div>
                              <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">事件</div>
                                <div>{selectedDelivery.event}</div>
                            </div>
                            <div>
                              <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">状态</div>
                                <div>{getStatusBadge(selectedDelivery.status)}</div>
                            </div>
                            {selectedDelivery.status_code && (
                                <div>
                                  <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">HTTP
                                    状态码
                                  </div>
                                    <div>{selectedDelivery.status_code}</div>
                                </div>
                            )}
                            <div>
                              <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">请求载荷</div>
                                <pre className="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg text-xs overflow-x-auto">
                  {JSON.stringify(selectedDelivery.payload, null, 2)}
                </pre>
                            </div>
                            {selectedDelivery.response_body && (
                                <div>
                                  <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">响应内容
                                  </div>
                                    <pre className="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg text-xs overflow-x-auto">
                    {selectedDelivery.response_body.slice(0, 1000)}
                  </pre>
                                </div>
                            )}
                            {selectedDelivery.error_message && (
                                <div>
                                  <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">错误信息
                                  </div>
                                    <div className="text-red-600 bg-red-50 dark:bg-red-900/20 p-3 rounded-lg text-sm">
                                        {selectedDelivery.error_message}
                                    </div>
                                </div>
                            )}
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">发送时间
                                  </div>
                                    <div>{formatTime(selectedDelivery.created_at)}</div>
                                </div>
                                {selectedDelivery.completed_at && (
                                    <div>
                                      <div
                                        className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">完成时间
                                      </div>
                                        <div>{formatTime(selectedDelivery.completed_at)}</div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </AdminShell>
    );
}

export default function AdminWebhooks() {
    return (
        <AuthGuard>
            <QueryProvider>
                <WebhooksInner/>
            </QueryProvider>
        </AuthGuard>
    );
}
