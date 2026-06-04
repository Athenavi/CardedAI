import {useState} from 'react';
import {AdminShell} from '@/components/admin/AdminShell';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {useQuery, useMutation, useQueryClient} from '@tanstack/react-query';
import {apiClient} from '@/lib/api/base-client';
import {useToast} from '@/components/ui/toast-provider';
import {formatDateTime as formatTime} from '@/lib/utils';
import {
    Share2, Send, CheckCircle, XCircle, Clock,
    ExternalLink, Settings, RefreshCw, FileText
} from 'lucide-react';

interface Article {
    id: number;
    title: string;
    slug: string;
    status: string;
    created_at: string;
}

interface PublishRecord {
    id: number;
    article_id: number;
    article_title: string;
    platform: string;
    status: 'pending' | 'success' | 'failed';
    external_url?: string;
    error_message?: string;
    published_at: string;
}

const PLATFORMS = [
  {id: 'zhihu', name: '知乎', icon: '📝', color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400'},
  {
    id: 'juejin',
    name: '掘金',
    icon: '⛏️',
    color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
  },
    {id: 'medium', name: 'Medium', icon: '📰', color: 'bg-gray-100 text-gray-700'},
    {id: 'twitter', name: 'Twitter', icon: '🐦', color: 'bg-sky-100 text-sky-700'}
];

const STATUS_CONFIG = {
  pending: {
    color: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400',
    icon: Clock,
    label: '待发布'
  },
  success: {
    color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
    icon: CheckCircle,
    label: '成功'
  },
  failed: {color: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400', icon: XCircle, label: '失败'}
};

function ThirdPartyPublishInner() {
  const toast = useToast();
    const qc = useQueryClient();
    const [selectedArticle, setSelectedArticle] = useState<number | null>(null);
    const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);
    const [showPublishDialog, setShowPublishDialog] = useState(false);

    // 查询文章列表
    const {data: articles} = useQuery({
        queryKey: ['articles-published'],
        queryFn: async () => {
            const res = await apiClient.get('/articles', {params: {status: 'published', limit: 50}});
            return res.data?.items || [];
        }
    });

    // 查询发布记录
    const {data: publishRecords, isLoading: recordsLoading} = useQuery({
        queryKey: ['publish-records'],
        queryFn: async () => {
            const res = await apiClient.get('/publish/records');
            return res.data || [];
        }
    });

    // 发布到平台
    const publishMut = useMutation({
        mutationFn: ({article_id, platforms}: { article_id: number; platforms: string[] }) =>
            apiClient.post('/publish/sync', {article_id, platforms}),
        onSuccess: () => {
            qc.invalidateQueries({queryKey: ['publish-records']});
            setShowPublishDialog(false);
            setSelectedPlatforms([]);
          toast.success('发布任务已提交！');
        }
    });

    const handlePublish = () => {
        if (!selectedArticle || selectedPlatforms.length === 0) {
          toast.error('请选择文章和至少一个平台');
            return;
        }
        publishMut.mutate({article_id: selectedArticle, platforms: selectedPlatforms});
    };

    const togglePlatform = (platformId: string) => {
        setSelectedPlatforms(prev =>
            prev.includes(platformId)
                ? prev.filter(p => p !== platformId)
                : [...prev, platformId]
        );
    };

    const getPlatformInfo = (platformId: string) => {
        return PLATFORMS.find(p => p.id === platformId) || PLATFORMS[0];
    };

    const getStatusBadge = (status: string) => {
        const config = STATUS_CONFIG[status as keyof typeof STATUS_CONFIG];
        const Icon = config.icon;
        return (
            <span
                className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${config.color}`}>
        <Icon className="w-3 h-3"/>
                {config.label}
      </span>
        );
    };

    // formatTime imported from @/lib/utils as formatDateTime

    return (
        <AdminShell title="第三方平台发布">
            <div className="space-y-6">
                {/* 快速发布卡片 */}
                <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl p-6 text-white">
                    <div className="flex items-start justify-between">
                        <div>
                            <h3 className="text-xl font-bold mb-2 flex items-center gap-2">
                                <Share2 className="w-6 h-6"/>
                                一键发布到多平台
                            </h3>
                            <p className="text-blue-100 mb-4">
                                将文章同步发布到知乎、掘金、Medium、Twitter 等平台，扩大内容影响力
                            </p>
                            <button
                                onClick={() => setShowPublishDialog(true)}
                                className="px-6 py-2 bg-white dark:bg-gray-800 text-blue-600 dark:text-blue-400 rounded-lg font-semibold hover:bg-blue-50 transition flex items-center gap-2"
                            >
                                <Send className="w-4 h-4"/>
                                开始发布
                            </button>
                        </div>
                        <div className="hidden md:flex gap-3">
                            {PLATFORMS.map(platform => (
                                <div key={platform.id}
                                     className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center text-2xl">
                                    {platform.icon}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* 发布统计 */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="bg-white dark:bg-gray-900 rounded-xl border p-4">
                      <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">总发布次数</div>
                        <div className="text-2xl font-bold">{publishRecords?.length || 0}</div>
                    </div>
                    <div className="bg-white dark:bg-gray-900 rounded-xl border p-4">
                      <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">成功发布</div>
                        <div className="text-2xl font-bold text-green-600">
                            {publishRecords?.filter((r: PublishRecord) => r.status === 'success').length || 0}
                        </div>
                    </div>
                    <div className="bg-white dark:bg-gray-900 rounded-xl border p-4">
                      <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">待发布</div>
                        <div className="text-2xl font-bold text-yellow-600">
                            {publishRecords?.filter((r: PublishRecord) => r.status === 'pending').length || 0}
                        </div>
                    </div>
                    <div className="bg-white dark:bg-gray-900 rounded-xl border p-4">
                      <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">发布失败</div>
                        <div className="text-2xl font-bold text-red-600">
                            {publishRecords?.filter((r: PublishRecord) => r.status === 'failed').length || 0}
                        </div>
                    </div>
                </div>

                {/* 发布历史 */}
                <div className="bg-white dark:bg-gray-900 rounded-xl border overflow-hidden">
                    <div className="px-6 py-4 border-b flex items-center justify-between">
                        <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                            <FileText className="w-5 h-5"/>
                            发布历史
                        </h3>
                        <button
                            onClick={() => qc.invalidateQueries({queryKey: ['publish-records']})}
                            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition"
                        >
                            <RefreshCw className="w-4 h-4"/>
                        </button>
                    </div>

                    {recordsLoading ? (
                        <div className="p-12 text-center">
                            <div
                                className="animate-spin w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto"/>
                        </div>
                    ) : !publishRecords?.length ? (
                        <div className="p-12 text-center text-gray-400">
                            <Share2 className="w-16 h-16 mx-auto mb-4 opacity-30"/>
                            <p>暂无发布记录</p>
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead className="bg-gray-50 dark:bg-gray-800">
                                <tr>
                                  <th
                                    className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">文章
                                  </th>
                                  <th
                                    className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">平台
                                  </th>
                                  <th
                                    className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">状态
                                  </th>
                                  <th
                                    className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase hidden lg:table-cell">外部链接
                                  </th>
                                  <th
                                    className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase hidden md:table-cell">发布时间
                                  </th>
                                </tr>
                                </thead>
                                <tbody className="divide-y">
                                {publishRecords.map((record: PublishRecord) => {
                                    const platform = getPlatformInfo(record.platform);
                                    return (
                                        <tr key={record.id}
                                            className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition">
                                            <td className="px-5 py-4">
                                                <div className="text-sm font-medium text-gray-900 dark:text-white">
                                                    {record.article_title}
                                                </div>
                                            </td>
                                            <td className="px-5 py-4">
                          <span
                              className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-lg text-xs font-medium ${platform.color}`}>
                            <span>{platform.icon}</span>
                              {platform.name}
                          </span>
                                            </td>
                                            <td className="px-5 py-4">{getStatusBadge(record.status)}</td>
                                            <td className="px-5 py-4 hidden lg:table-cell">
                                                {record.external_url ? (
                                                    <a
                                                        href={record.external_url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="text-blue-600 hover:underline flex items-center gap-1 text-sm"
                                                    >
                                                        查看
                                                        <ExternalLink className="w-3 h-3"/>
                                                    </a>
                                                ) : (
                                                    <span className="text-gray-400 text-sm">-</span>
                                                )}
                                            </td>
                                          <td
                                            className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400 hidden md:table-cell">
                                                {formatTime(record.published_at)}
                                            </td>
                                        </tr>
                                    );
                                })}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>

                {/* 平台配置提示 */}
                <div
                    className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
                    <div className="flex items-start gap-3">
                        <Settings className="w-5 h-5 text-blue-600 mt-0.5"/>
                        <div>
                            <h4 className="font-medium text-blue-900 dark:text-blue-200 mb-1">平台账号配置</h4>
                            <p className="text-sm text-blue-700 dark:text-blue-300">
                                使用前需要在系统设置中配置各平台的 API 密钥和账号信息。
                                <a href="/admin/settings/integrations" className="underline ml-1">前往配置 →</a>
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* 发布对话框 */}
            {showPublishDialog && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-2xl w-full">
                        <div className="px-6 py-4 border-b">
                            <h3 className="font-semibold text-lg flex items-center gap-2">
                                <Send className="w-5 h-5"/>
                                发布到第三方平台
                            </h3>
                        </div>
                        <div className="p-6 space-y-6">
                            {/* 选择文章 */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                    选择文章 *
                                </label>
                                <select
                                    value={selectedArticle || ''}
                                    onChange={(e) => setSelectedArticle(Number(e.target.value))}
                                    className="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="">请选择文章</option>
                                    {articles?.map((article: Article) => (
                                        <option key={article.id} value={article.id}>
                                            {article.title}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            {/* 选择平台 */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                    选择平台 *
                                </label>
                                <div className="grid grid-cols-2 gap-3">
                                    {PLATFORMS.map(platform => (
                                        <label
                                            key={platform.id}
                                            className={`flex items-center gap-3 p-3 border rounded-lg cursor-pointer transition ${
                                                selectedPlatforms.includes(platform.id)
                                                    ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20'
                                                    : 'hover:bg-gray-50 dark:hover:bg-gray-800'
                                            }`}
                                        >
                                            <input
                                                type="checkbox"
                                                checked={selectedPlatforms.includes(platform.id)}
                                                onChange={() => togglePlatform(platform.id)}
                                                className="w-4 h-4 text-blue-600 rounded"
                                            />
                                            <span className="text-2xl">{platform.icon}</span>
                                            <span className="text-sm font-medium">{platform.name}</span>
                                        </label>
                                    ))}
                                </div>
                            </div>

                            {/* 提示信息 */}
                            <div
                                className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3">
                                <p className="text-sm text-yellow-800 dark:text-yellow-200">
                                    ⚠️ 发布后将在后台异步处理，可在发布历史中查看状态。
                                </p>
                            </div>
                        </div>
                        <div className="px-6 py-4 border-t flex justify-end gap-3">
                            <button
                                onClick={() => setShowPublishDialog(false)}
                                className="px-4 py-2 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition"
                            >
                                取消
                            </button>
                            <button
                                onClick={handlePublish}
                                disabled={!selectedArticle || selectedPlatforms.length === 0 || publishMut.isPending}
                                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <Send className="w-4 h-4"/>
                                确认发布
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </AdminShell>
    );
}

export default function AdminThirdPartyPublish() {
    return (
        <AuthGuard>
            <QueryProvider>
                <ThirdPartyPublishInner/>
            </QueryProvider>
        </AuthGuard>
    );
}
