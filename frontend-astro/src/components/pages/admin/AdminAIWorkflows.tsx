import {useState} from 'react';
import {AdminShell} from '@/components/admin/AdminShell';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {useQuery, useMutation, useQueryClient} from '@tanstack/react-query';
import {apiClient} from '@/lib/api/base-client';
import {formatDateTime as formatTime} from '@/lib/utils';
import {Bot, Clock, CheckCircle, XCircle, Loader2, RefreshCw, Eye} from 'lucide-react';

interface AIWorkflow {
    id: number;
    user_id: number;
    task_type: string;
    input_data: any;
    output_data: any;
    model_used: string;
    tokens_used: number;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    error_message?: string;
    created_at: string;
    completed_at?: string;
}

const TASK_TYPE_LABELS: Record<string, string> = {
    writing_assist: '写作辅助',
    seo_optimize: 'SEO 优化',
    tag_recommend: '标签推荐'
};

const STATUS_CONFIG = {
  pending: {color: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400', icon: Clock},
  processing: {color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400', icon: Loader2},
  completed: {color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400', icon: CheckCircle},
  failed: {color: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400', icon: XCircle}
};

function AIWorkflowsInner() {
    const qc = useQueryClient();
    const [selectedTask, setSelectedTask] = useState<AIWorkflow | null>(null);

    // 查询工作流列表
    const {data: workflows, isLoading} = useQuery({
        queryKey: ['ai-workflows'],
        queryFn: async () => {
            const res = await apiClient.get('/ai/workflows');
            return res.data || [];
        }
    });

    // 刷新任务状态
    const refreshMut = useMutation({
        mutationFn: (id: number) => apiClient.post(`/ai/workflows/${id}/refresh`),
        onSuccess: () => qc.invalidateQueries({queryKey: ['ai-workflows']})
    });

    const getStatusBadge = (status: string) => {
        const config = STATUS_CONFIG[status as keyof typeof STATUS_CONFIG];
        const Icon = config.icon;
        return (
            <span
                className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${config.color}`}>
        <Icon className="w-3 h-3"/>
                {TASK_TYPE_LABELS[status] || status}
      </span>
        );
    };

    // formatTime imported from @/lib/utils as formatDateTime

    return (
        <AdminShell title="AI 工作流管理">
            <div className="space-y-6">
                {/* 统计卡片 */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="bg-white dark:bg-gray-900 rounded-xl border p-4">
                      <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">总任务数</div>
                        <div className="text-2xl font-bold">{workflows?.length || 0}</div>
                    </div>
                    <div className="bg-white dark:bg-gray-900 rounded-xl border p-4">
                      <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">已完成</div>
                        <div className="text-2xl font-bold text-green-600">
                            {workflows?.filter((w: AIWorkflow) => w.status === 'completed').length || 0}
                        </div>
                    </div>
                    <div className="bg-white dark:bg-gray-900 rounded-xl border p-4">
                      <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">处理中</div>
                        <div className="text-2xl font-bold text-blue-600">
                            {workflows?.filter((w: AIWorkflow) => w.status === 'processing').length || 0}
                        </div>
                    </div>
                    <div className="bg-white dark:bg-gray-900 rounded-xl border p-4">
                      <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Token 消耗</div>
                        <div className="text-2xl font-bold text-purple-600">
                            {workflows?.reduce((sum: number, w: AIWorkflow) => sum + (w.tokens_used || 0), 0) || 0}
                        </div>
                    </div>
                </div>

                {/* 工作流列表 */}
                <div className="bg-white dark:bg-gray-900 rounded-xl border overflow-hidden">
                    <div className="px-6 py-4 border-b flex items-center justify-between">
                        <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                            <Bot className="w-5 h-5"/>
                            AI 任务记录
                        </h3>
                        <button
                            onClick={() => qc.invalidateQueries({queryKey: ['ai-workflows']})}
                            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition"
                        >
                            <RefreshCw className="w-4 h-4"/>
                        </button>
                    </div>

                    {isLoading ? (
                        <div className="p-12 text-center">
                            <Loader2 className="w-8 h-8 animate-spin mx-auto text-gray-400"/>
                        </div>
                    ) : !workflows?.length ? (
                        <div className="p-12 text-center text-gray-400">暂无 AI 工作流记录</div>
                    ) : (
                        <div className="divide-y">
                            {workflows.map((workflow: AIWorkflow) => (
                                <div key={workflow.id}
                                     className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition">
                                    <div className="flex items-start justify-between mb-2">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-gray-900 dark:text-white">
                          {TASK_TYPE_LABELS[workflow.task_type] || workflow.task_type}
                        </span>
                                                {getStatusBadge(workflow.status)}
                                            </div>
                                          <div className="text-xs text-gray-500 dark:text-gray-400 space-x-3">
                                                <span>ID: {workflow.id}</span>
                                                <span>模型: {workflow.model_used || 'N/A'}</span>
                                                <span>Tokens: {workflow.tokens_used}</span>
                                                <span>创建时间: {formatTime(workflow.created_at)}</span>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <button
                                                onClick={() => setSelectedTask(workflow)}
                                                className="p-2 text-gray-400 hover:text-blue-600 transition"
                                                title="查看详情"
                                            >
                                                <Eye className="w-4 h-4"/>
                                            </button>
                                            {workflow.status !== 'completed' && (
                                                <button
                                                    onClick={() => refreshMut.mutate(workflow.id)}
                                                    className="p-2 text-gray-400 hover:text-green-600 transition"
                                                    title="刷新状态"
                                                >
                                                    <RefreshCw className="w-4 h-4"/>
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                    {workflow.error_message && (
                                        <div
                                            className="mt-2 text-xs text-red-600 bg-red-50 dark:bg-red-900/20 p-2 rounded">
                                            错误: {workflow.error_message}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* 详情对话框 */}
            {selectedTask && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div
                        className="bg-white dark:bg-gray-900 rounded-2xl max-w-3xl w-full max-h-[80vh] overflow-y-auto">
                        <div
                            className="sticky top-0 bg-white dark:bg-gray-900 border-b px-6 py-4 flex items-center justify-between">
                            <h3 className="font-semibold text-lg">任务详情 #{selectedTask.id}</h3>
                            <button
                                onClick={() => setSelectedTask(null)}
                                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
                            >
                                <XCircle className="w-5 h-5"/>
                            </button>
                        </div>
                        <div className="p-6 space-y-4">
                            <div>
                              <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">任务类型</div>
                                <div>{TASK_TYPE_LABELS[selectedTask.task_type] || selectedTask.task_type}</div>
                            </div>
                            <div>
                              <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">状态</div>
                                <div>{getStatusBadge(selectedTask.status)}</div>
                            </div>
                            <div>
                              <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">输入数据</div>
                                <pre className="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg text-xs overflow-x-auto">
                  {JSON.stringify(selectedTask.input_data, null, 2)}
                </pre>
                            </div>
                            {selectedTask.output_data && (
                                <div>
                                  <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">输出结果
                                  </div>
                                    <pre className="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg text-xs overflow-x-auto">
                    {JSON.stringify(selectedTask.output_data, null, 2)}
                  </pre>
                                </div>
                            )}
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">使用模型
                                  </div>
                                    <div>{selectedTask.model_used || 'N/A'}</div>
                                </div>
                                <div>
                                  <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Token
                                    消耗
                                  </div>
                                    <div>{selectedTask.tokens_used}</div>
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">创建时间
                                  </div>
                                    <div>{formatTime(selectedTask.created_at)}</div>
                                </div>
                                {selectedTask.completed_at && (
                                    <div>
                                      <div
                                        className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">完成时间
                                      </div>
                                        <div>{formatTime(selectedTask.completed_at)}</div>
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

export default function AdminAIWorkflows() {
    return (
        <AuthGuard>
            <QueryProvider>
                <AIWorkflowsInner/>
            </QueryProvider>
        </AuthGuard>
    );
}
