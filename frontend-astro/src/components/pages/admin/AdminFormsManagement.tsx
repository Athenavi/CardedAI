import {useState} from 'react';
import {AdminShell} from '@/components/admin/AdminShell';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {apiClient} from '@/lib/api/base-client';
import {formatDateTime as formatTime} from '@/lib/utils';
import {useConfirm} from '@/components/ui/confirm-provider';
import {useToast} from '@/components/ui/toast-provider';
import {Archive, CheckCircle, ChevronDown, ChevronUp, FileText, Send, Trash2} from 'lucide-react';

interface FormData {
  id: number;
  title: string;
  slug: string;
  description: string;
  status: string;
  submission_count: number;
  email_notification: boolean;
  notification_email: string | null;
  store_submissions: boolean;
  created_at: string | null;
  updated_at: string | null;
  published_at: string | null;
}

interface FormSubmissionData {
  id: number;
  data: Record<string, any>;
  ip_address: string | null;
  user_agent: string | null;
  status: string;
  created_at: string | null;
}

interface FormStats {
  form_id: number;
  total_submissions: number;
  recent_submissions: number;
  completion_rate: number;
  average_completion_time: number | null;
}

interface PaginatedForms {
  forms: FormData[];
  total: number;
  page: number;
  per_page: number;
}

const STATUS_CONFIG: Record<string, { color: string; icon: typeof FileText; label: string }> = {
  draft: {color: 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400', icon: FileText, label: '草稿'},
  published: {
    color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
    icon: CheckCircle,
    label: '已发布'
  },
  archived: {
    color: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400',
    icon: Archive,
    label: '已归档'
  },
};

const SUBMISSION_STATUS_CONFIG: Record<string, { color: string; label: string }> = {
  new: {color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400', label: '新提交'},
  read: {color: 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400', label: '已读'},
  replied: {color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400', label: '已回复'},
  spam: {color: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400', label: '垃圾'},
};

function FormsInner() {
  const confirm = useConfirm();
  const toast = useToast();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [expandedFormId, setExpandedFormId] = useState<number | null>(null);
  const [submissionsPage, setSubmissionsPage] = useState<Record<number, number>>({});

  // 查询表单列表
  const {data: formsData, isLoading} = useQuery<PaginatedForms>({
    queryKey: ['admin-forms', page, statusFilter],
    queryFn: async () => {
      const params: Record<string, any> = {page, per_page: 20};
      if (statusFilter) params.status = statusFilter;
      const res = await apiClient.get('/cms/admin/form/', params);
      return res.data || {forms: [], total: 0, page: 1, per_page: 20};
    }
  });

  // 查询展开表单的提交记录
  const {data: submissionsData} = useQuery({
    queryKey: ['form-submissions', expandedFormId, submissionsPage[expandedFormId || 0] || 1],
    queryFn: async () => {
      if (!expandedFormId) return null;
      const p = submissionsPage[expandedFormId] || 1;
      const res = await apiClient.get(`/cms/admin/form/${expandedFormId}/submissions`, {page: p, per_page: 10});
      return res.data || {submissions: [], total: 0, page: 1, per_page: 10};
    },
    enabled: !!expandedFormId
  });

  // 查询展开表单的统计
  const {data: formStats} = useQuery<FormStats>({
    queryKey: ['form-stats', expandedFormId],
    queryFn: async () => {
      if (!expandedFormId) return null;
      const res = await apiClient.get(`/cms/admin/form/${expandedFormId}/statistics`);
      return res.data || null;
    },
    enabled: !!expandedFormId
  });

  // 删除表单
  const deleteMut = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/cms/admin/form/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({queryKey: ['admin-forms']});
      toast.success('表单已删除');
      if (expandedFormId) setExpandedFormId(null);
    },
    onError: () => {
      toast.error('删除失败');
    }
  });

  const handleDelete = async (id: number, title: string) => {
    if (await confirm({message: `确定要删除表单「${title}」吗？所有提交记录也将被删除。`, variant: 'danger'})) {
      deleteMut.mutate(id);
    }
  };

  const toggleExpand = (formId: number) => {
    setExpandedFormId(prev => prev === formId ? null : formId);
    setSubmissionsPage(prev => ({...prev, [formId]: 1}));
  };

  const getStatusBadge = (status: string) => {
    const config = STATUS_CONFIG[status] || STATUS_CONFIG.draft;
    const Icon = config.icon;
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${config.color}`}>
                <Icon className="w-3 h-3"/>
        {config.label}
            </span>
    );
  };

  const getSubmissionStatusBadge = (status: string) => {
    const config = SUBMISSION_STATUS_CONFIG[status] || SUBMISSION_STATUS_CONFIG.new;
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
                {config.label}
            </span>
    );
  };

  const forms = formsData?.forms || [];
  const total = formsData?.total || 0;
  const totalPages = Math.ceil(total / 20);

  return (
    <AdminShell title="表单管理">
      <div className="space-y-6">
        {/* 统计卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-900 rounded-xl border p-4">
            <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">表单总数</div>
            <div className="text-2xl font-bold">{total}</div>
          </div>
          <div className="bg-white dark:bg-gray-900 rounded-xl border p-4">
            <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">已发布</div>
            <div className="text-2xl font-bold text-green-600">
              {forms.filter((f: FormData) => f.status === 'published').length}
            </div>
          </div>
          <div className="bg-white dark:bg-gray-900 rounded-xl border p-4">
            <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">草稿</div>
            <div className="text-2xl font-bold text-gray-600">
              {forms.filter((f: FormData) => f.status === 'draft').length}
            </div>
          </div>
          <div className="bg-white dark:bg-gray-900 rounded-xl border p-4">
            <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">总提交数</div>
            <div className="text-2xl font-bold text-blue-600">
              {forms.reduce((sum: number, f: FormData) => sum + (f.submission_count || 0), 0)}
            </div>
          </div>
        </div>

        {/* 筛选栏 */}
        <div className="bg-white dark:bg-gray-900 rounded-xl border p-4 flex items-center gap-3">
          <span className="text-sm text-gray-500">状态筛选：</span>
          {['', 'draft', 'published', 'archived'].map(s => (
            <button
              key={s}
              onClick={() => {
                setStatusFilter(s);
                setPage(1);
              }}
              className={`px-3 py-1.5 text-sm rounded-lg transition ${
                statusFilter === s
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
            >
              {s === '' ? '全部' : (STATUS_CONFIG[s]?.label || s)}
            </button>
          ))}
        </div>

        {/* 表单列表 */}
        <div className="bg-white dark:bg-gray-900 rounded-xl border overflow-hidden">
          <div className="px-6 py-4 border-b flex items-center justify-between">
            <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <FileText className="w-5 h-5"/>
              表单列表
            </h3>
          </div>

          {isLoading ? (
            <div className="p-12 text-center">
              <div className="animate-spin w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto"/>
            </div>
          ) : !forms.length ? (
            <div className="p-12 text-center text-gray-400">
              <FileText className="w-16 h-16 mx-auto mb-4 opacity-30"/>
              <p>暂无表单</p>
            </div>
          ) : (
            <div className="divide-y">
              {forms.map((form: FormData) => (
                <div key={form.id}>
                  <div className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition cursor-pointer"
                       onClick={() => toggleExpand(form.id)}>
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-gray-900 dark:text-white">{form.title}</span>
                          {getStatusBadge(form.status)}
                          {form.email_notification && (
                            <span
                              className="px-2 py-0.5 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 text-xs rounded-full">
                                                            邮件通知
                                                        </span>
                          )}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 space-x-3">
                          <span>ID: {form.id}</span>
                          {form.slug && <span>标识: {form.slug}</span>}
                          <span>提交: {form.submission_count}</span>
                          <span>创建: {formatTime(form.created_at || '')}</span>
                        </div>
                        {form.description && (
                          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{form.description}</p>
                        )}
                      </div>
                      <div className="flex items-center gap-2 ml-4">
                        <button
                          onClick={e => {
                            e.stopPropagation();
                            toggleExpand(form.id);
                          }}
                          className="p-2 text-gray-400 hover:text-blue-600 transition"
                          title="查看提交"
                        >
                          {expandedFormId === form.id ? <ChevronUp className="w-4 h-4"/> :
                            <ChevronDown className="w-4 h-4"/>}
                        </button>
                        <button
                          onClick={e => {
                            e.stopPropagation();
                            handleDelete(form.id, form.title);
                          }}
                          className="p-2 text-gray-400 hover:text-red-600 transition"
                          title="删除"
                        >
                          <Trash2 className="w-4 h-4"/>
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* 展开区域：提交记录和统计 */}
                  {expandedFormId === form.id && (
                    <div className="px-6 pb-4 bg-gray-50 dark:bg-gray-800/30 border-t">
                      {/* 统计信息 */}
                      {formStats && (
                        <div className="grid grid-cols-3 gap-4 py-4">
                          <div className="text-center">
                            <div className="text-lg font-bold text-blue-600">{formStats.total_submissions}</div>
                            <div className="text-xs text-gray-500">总提交数</div>
                          </div>
                          <div className="text-center">
                            <div className="text-lg font-bold text-green-600">{formStats.recent_submissions}</div>
                            <div className="text-xs text-gray-500">近7天提交</div>
                          </div>
                          <div className="text-center">
                            <div className="text-lg font-bold text-purple-600">{formStats.completion_rate}%</div>
                            <div className="text-xs text-gray-500">完成率</div>
                          </div>
                        </div>
                      )}

                      {/* 提交记录列表 */}
                      <div className="mt-2">
                        <h4
                          className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                          <Send className="w-4 h-4"/>
                          提交记录
                        </h4>
                        {!submissionsData?.submissions?.length ? (
                          <div className="text-center py-6 text-gray-400 text-sm">暂无提交记录</div>
                        ) : (
                          <div className="space-y-2">
                            {submissionsData.submissions.map((sub: FormSubmissionData) => (
                              <div key={sub.id}
                                   className="bg-white dark:bg-gray-900 rounded-lg border p-3">
                                <div className="flex items-center justify-between mb-2">
                                  <div className="flex items-center gap-2">
                                    <span className="text-sm font-medium">#{sub.id}</span>
                                    {getSubmissionStatusBadge(sub.status)}
                                  </div>
                                  <span className="text-xs text-gray-500">
                                                                        {formatTime(sub.created_at || '')}
                                                                    </span>
                                </div>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-1">
                                  {Object.entries(sub.data || {}).map(([key, value]) => (
                                    <div key={key} className="text-xs">
                                      <span className="text-gray-500">{key}: </span>
                                      <span className="text-gray-700 dark:text-gray-300">{String(value)}</span>
                                    </div>
                                  ))}
                                </div>
                                {sub.ip_address && (
                                  <div className="text-xs text-gray-400 mt-1">IP: {sub.ip_address}</div>
                                )}
                              </div>
                            ))}

                            {/* 分页 */}
                            {submissionsData.total > 10 && (
                              <div className="flex justify-center gap-2 pt-3">
                                <button
                                  disabled={(submissionsPage[form.id] || 1) <= 1}
                                  onClick={() => setSubmissionsPage(prev => ({
                                    ...prev,
                                    [form.id]: Math.max(1, (prev[form.id] || 1) - 1)
                                  }))}
                                  className="px-3 py-1 text-sm rounded border disabled:opacity-50 hover:bg-gray-100 dark:hover:bg-gray-800"
                                >
                                  上一页
                                </button>
                                <span className="px-3 py-1 text-sm text-gray-500">
                                                                    {submissionsPage[form.id] || 1} / {Math.ceil(submissionsData.total / 10)}
                                                                </span>
                                <button
                                  disabled={(submissionsPage[form.id] || 1) >= Math.ceil(submissionsData.total / 10)}
                                  onClick={() => setSubmissionsPage(prev => ({
                                    ...prev,
                                    [form.id]: (prev[form.id] || 1) + 1
                                  }))}
                                  className="px-3 py-1 text-sm rounded border disabled:opacity-50 hover:bg-gray-100 dark:hover:bg-gray-800"
                                >
                                  下一页
                                </button>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 列表分页 */}
        {totalPages > 1 && (
          <div className="flex justify-center gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage(p => p - 1)}
              className="px-3 py-1.5 text-sm rounded-lg border disabled:opacity-50 hover:bg-gray-100 dark:hover:bg-gray-800 transition"
            >
              上一页
            </button>
            <span className="px-3 py-1.5 text-sm text-gray-500">
                            第 {page} / {totalPages} 页
                        </span>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(p => p + 1)}
              className="px-3 py-1.5 text-sm rounded-lg border disabled:opacity-50 hover:bg-gray-100 dark:hover:bg-gray-800 transition"
            >
              下一页
            </button>
          </div>
        )}
      </div>
    </AdminShell>
  );
}

export default function AdminFormsManagement() {
  return (
    <AuthGuard>
      <QueryProvider>
        <FormsInner/>
      </QueryProvider>
    </AuthGuard>
  );
}
