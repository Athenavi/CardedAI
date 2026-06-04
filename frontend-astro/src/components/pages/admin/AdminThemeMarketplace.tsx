import {useState} from 'react';
import {useConfirm} from '@/components/ui/confirm-provider';
import {AdminShell} from '@/components/admin/AdminShell';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {useQuery, useMutation, useQueryClient} from '@tanstack/react-query';
import {apiClient} from '@/lib/api/base-client';
import {useToast} from '@/components/ui/toast-provider';
import {Palette, Download, CheckCircle, Settings, Eye, Trash2, Search, Filter, Star, Globe} from 'lucide-react';

interface Theme {
    id?: number;
    name: string;
    slug: string;
    version: string;
    description?: string;
    author?: string;
    author_url?: string;
    theme_url?: string;
    screenshot?: string;
    tags?: string;
    is_active?: boolean;
    is_installed?: boolean;
    created_at?: string;
    updated_at?: string;
    category?: string;
}

function ThemeMarketplaceInner() {
  const confirm = useConfirm();
  const toast = useToast();
    const qc = useQueryClient();
    const [activeTab, setActiveTab] = useState<'marketplace' | 'installed'>('marketplace');
    const [selectedTheme, setSelectedTheme] = useState<Theme | null>(null);
    const [showConfig, setShowConfig] = useState(false);
    const [configData, setConfigData] = useState<any>({});
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedCategory, setSelectedCategory] = useState<string>('all');

    // 查询主题市场
    const {data: marketplaceThemes, isLoading: marketplaceLoading} = useQuery({
        queryKey: ['themes-marketplace', selectedCategory],
        queryFn: async () => {
            const params = selectedCategory !== 'all' ? {category: selectedCategory} : {};
            const res = await apiClient.get('/themes/marketplace', {params});
            return res.data || [];
        },
        enabled: activeTab === 'marketplace'
    });

    // 查询已安装主题
    const {data: installedThemes, isLoading: installedLoading} = useQuery({
        queryKey: ['themes-installed'],
        queryFn: async () => {
            const res = await apiClient.get('/themes/installed');
            return res.data || [];
        },
        enabled: activeTab === 'installed'
    });

    // 查询主题分类
    const {data: categories} = useQuery({
        queryKey: ['theme-categories'],
        queryFn: async () => {
            const res = await apiClient.get('/themes/categories');
            return res.data || ['all'];
        }
    });

    // 安装主题
    const installMut = useMutation({
        mutationFn: (slug: string) => apiClient.post('/themes/install', {slug}),
        onSuccess: () => {
            qc.invalidateQueries({queryKey: ['themes-marketplace']});
            qc.invalidateQueries({queryKey: ['themes-installed']});
          toast.success('主题安装成功！');
        }
    });

    // 激活主题
    const activateMut = useMutation({
        mutationFn: (slug: string) => apiClient.post(`/themes/${slug}/activate`),
        onSuccess: () => {
            qc.invalidateQueries({queryKey: ['themes-installed']});
          toast.success('主题已激活！');
        }
    });

    // 卸载主题
    const uninstallMut = useMutation({
        mutationFn: (slug: string) => apiClient.delete(`/themes/${slug}/uninstall`),
        onSuccess: () => {
            qc.invalidateQueries({queryKey: ['themes-installed']});
          toast.success('主题已卸载！');
        }
    });

    // 获取主题配置
    const configQuery = useQuery({
        queryKey: ['theme-config', selectedTheme?.slug],
        queryFn: async () => {
            if (!selectedTheme?.slug) return {};
            const res = await apiClient.get(`/themes/${selectedTheme.slug}/config`);
            return res.data;
        },
        enabled: showConfig && !!selectedTheme?.slug
    });

    // 保存主题配置
    const saveConfigMut = useMutation({
        mutationFn: ({slug, settings}: { slug: string; settings: any }) =>
            apiClient.put(`/themes/${slug}/config`, {settings}),
        onSuccess: () => {
          toast.success('配置已保存！');
            setShowConfig(false);
        }
    });

  const handleInstall = async (slug: string) => {
    if (await confirm({message: '确定要安装此主题吗？', variant: 'warning'})) {
            installMut.mutate(slug);
        }
    };

  const handleActivate = async (slug: string) => {
    if (await confirm({message: '确定要激活此主题吗？当前活动主题将被停用。', variant: 'warning'})) {
            activateMut.mutate(slug);
        }
    };

  const handleUninstall = async (slug: string) => {
    if (await confirm({message: '确定要卸载此主题吗？', variant: 'danger'})) {
            uninstallMut.mutate(slug);
        }
    };

    const handleViewConfig = (theme: Theme) => {
        setSelectedTheme(theme);
        setShowConfig(true);
    };

    const handleSaveConfig = () => {
        if (!selectedTheme?.slug) return;
        saveConfigMut.mutate({slug: selectedTheme.slug, settings: configData});
    };

    const filteredThemes = (themes: Theme[]) => {
        return themes.filter((theme: Theme) => {
            const matchesSearch = !searchTerm ||
                theme.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                theme.description?.toLowerCase().includes(searchTerm.toLowerCase());
            return matchesSearch;
        });
    };

    const renderThemeCard = (theme: Theme, isInstalled: boolean = false) => (
        <div key={theme.slug}
             className="bg-white dark:bg-gray-900 rounded-xl border overflow-hidden hover:shadow-lg transition">
            {/* 截图 */}
            <div className="aspect-video bg-gray-100 dark:bg-gray-800 relative">
                {theme.screenshot ? (
                    <img src={theme.screenshot} alt={theme.name} className="w-full h-full object-cover"/>
                ) : (
                    <div className="w-full h-full flex items-center justify-center text-gray-400">
                        <Palette className="w-12 h-12"/>
                    </div>
                )}
                {isInstalled && theme.is_active && (
                    <div
                        className="absolute top-2 right-2 px-2 py-1 bg-green-600 text-white text-xs rounded-full flex items-center gap-1">
                        <CheckCircle className="w-3 h-3"/>
                        当前使用
                    </div>
                )}
            </div>

            {/* 信息 */}
            <div className="p-4">
                <div className="flex items-start justify-between mb-2">
                    <div>
                        <h3 className="font-semibold text-gray-900 dark:text-white">{theme.name}</h3>
                      <p className="text-xs text-gray-500 dark:text-gray-400">v{theme.version} ·
                        by {theme.author || 'Unknown'}</p>
                    </div>
                </div>

                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                    {theme.description || '暂无描述'}
                </p>

                {/* 标签 */}
                {theme.tags && (
                    <div className="flex flex-wrap gap-1 mb-3">
                        {(typeof theme.tags === 'string' ? JSON.parse(theme.tags) : theme.tags).slice(0, 3).map((tag: string, i: number) => (
                            <span key={i} className="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 text-xs rounded">
                {tag}
              </span>
                        ))}
                    </div>
                )}

                {/* 操作按钮 */}
                <div className="flex gap-2">
                    {!isInstalled ? (
                        <button
                            onClick={() => handleInstall(theme.slug)}
                            disabled={installMut.isPending}
                            className="flex-1 px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition flex items-center justify-center gap-1.5"
                        >
                            <Download className="w-4 h-4"/>
                            安装
                        </button>
                    ) : (
                        <>
                            {!theme.is_active ? (
                                <button
                                    onClick={() => handleActivate(theme.slug)}
                                    disabled={activateMut.isPending}
                                    className="flex-1 px-3 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 transition flex items-center justify-center gap-1.5"
                                >
                                    <CheckCircle className="w-4 h-4"/>
                                    激活
                                </button>
                            ) : (
                                <button
                                    disabled
                                    className="flex-1 px-3 py-2 bg-gray-300 text-gray-600 text-sm rounded-lg cursor-not-allowed flex items-center justify-center gap-1.5"
                                >
                                    <CheckCircle className="w-4 h-4"/>
                                    使用中
                                </button>
                            )}
                            <button
                                onClick={() => handleViewConfig(theme)}
                                className="px-3 py-2 border text-sm rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition"
                            >
                                <Settings className="w-4 h-4"/>
                            </button>
                            {!theme.is_active && (
                                <button
                                    onClick={() => handleUninstall(theme.slug)}
                                    disabled={uninstallMut.isPending}
                                    className="px-3 py-2 border text-red-600 text-sm rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition"
                                >
                                    <Trash2 className="w-4 h-4"/>
                                </button>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    );

    return (
        <AdminShell title="主题市场">
            <div className="space-y-6">
                {/* 标签页 */}
                <div className="flex gap-2">
                    <button
                        onClick={() => setActiveTab('marketplace')}
                        className={`px-4 py-2 rounded-lg font-medium transition ${
                            activeTab === 'marketplace'
                                ? 'bg-blue-600 text-white'
                                : 'bg-white dark:bg-gray-900 border hover:bg-gray-50 dark:hover:bg-gray-800'
                        }`}
                    >
                        <Globe className="w-4 h-4 inline mr-1.5"/>
                        主题市场
                    </button>
                    <button
                        onClick={() => setActiveTab('installed')}
                        className={`px-4 py-2 rounded-lg font-medium transition ${
                            activeTab === 'installed'
                                ? 'bg-blue-600 text-white'
                                : 'bg-white dark:bg-gray-900 border hover:bg-gray-50 dark:hover:bg-gray-800'
                        }`}
                    >
                        <Download className="w-4 h-4 inline mr-1.5"/>
                        已安装
                    </button>
                </div>

                {/* 搜索和过滤 */}
                {activeTab === 'marketplace' && (
                    <div className="flex gap-3">
                        <div className="flex-1 relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
                            <input
                                type="text"
                                placeholder="搜索主题..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full pl-10 pr-4 py-2 border rounded-lg bg-white dark:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                        <select
                            value={selectedCategory}
                            onChange={(e) => setSelectedCategory(e.target.value)}
                            className="px-4 py-2 border rounded-lg bg-white dark:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            {categories?.map((cat: string) => (
                                <option key={cat} value={cat}>
                                    {cat === 'all' ? '全部分类' : cat}
                                </option>
                            ))}
                        </select>
                    </div>
                )}

                {/* 主题网格 */}
                {activeTab === 'marketplace' ? (
                    marketplaceLoading ? (
                        <div className="text-center py-12">
                            <div
                                className="animate-spin w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto"/>
                        </div>
                    ) : !marketplaceThemes?.length ? (
                        <div className="text-center py-12 text-gray-400">
                            <Palette className="w-16 h-16 mx-auto mb-4 opacity-30"/>
                            <p>暂无可用主题</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {filteredThemes(marketplaceThemes).map((theme: Theme) => renderThemeCard(theme, false))}
                        </div>
                    )
                ) : (
                    installedLoading ? (
                        <div className="text-center py-12">
                            <div
                                className="animate-spin w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto"/>
                        </div>
                    ) : !installedThemes?.length ? (
                        <div className="text-center py-12 text-gray-400">
                            <Download className="w-16 h-16 mx-auto mb-4 opacity-30"/>
                            <p>尚未安装任何主题</p>
                            <button
                                onClick={() => setActiveTab('marketplace')}
                                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                            >
                                浏览主题市场
                            </button>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {installedThemes.map((theme: Theme) => renderThemeCard(theme, true))}
                        </div>
                    )
                )}
            </div>

            {/* 配置对话框 */}
            {showConfig && selectedTheme && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div
                        className="bg-white dark:bg-gray-900 rounded-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden flex flex-col">
                        <div className="px-6 py-4 border-b flex items-center justify-between">
                            <h3 className="font-semibold text-lg">配置主题: {selectedTheme.name}</h3>
                            <button
                                onClick={() => setShowConfig(false)}
                                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
                            >
                                ✕
                            </button>
                        </div>

                        {configQuery.isLoading ? (
                            <div className="p-12 text-center">
                                <div
                                    className="animate-spin w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto"/>
                            </div>
                        ) : (
                            <>
                                <div className="flex-1 overflow-y-auto p-6 space-y-4">
                                    {configQuery.data?.settings_schema ? (
                                        Object.entries(configQuery.data.settings_schema).map(([key, schema]: [string, any]) => (
                                            <div key={key}>
                                                <label
                                                    className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                                    {schema.label || key}
                                                </label>
                                                {schema.type === 'textarea' ? (
                                                    <textarea
                                                        value={configData[key] || configQuery.data.settings[key] || ''}
                                                        onChange={(e) => setConfigData({
                                                            ...configData,
                                                            [key]: e.target.value
                                                        })}
                                                        rows={3}
                                                        className="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                                    />
                                                ) : schema.type === 'select' ? (
                                                    <select
                                                        value={configData[key] || configQuery.data.settings[key] || ''}
                                                        onChange={(e) => setConfigData({
                                                            ...configData,
                                                            [key]: e.target.value
                                                        })}
                                                        className="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                                    >
                                                      {schema.options?.map((opt) => (
                                                            <option key={opt.value} value={opt.value}>
                                                                {opt.label}
                                                            </option>
                                                        ))}
                                                    </select>
                                                ) : (
                                                    <input
                                                        type={schema.type || 'text'}
                                                        value={configData[key] || configQuery.data.settings[key] || ''}
                                                        onChange={(e) => setConfigData({
                                                            ...configData,
                                                            [key]: e.target.value
                                                        })}
                                                        className="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                                    />
                                                )}
                                            </div>
                                        ))
                                    ) : (
                                      <p
                                        className="text-gray-500 dark:text-gray-400 text-center py-8">此主题没有可配置项</p>
                                    )}
                                </div>

                                <div className="px-6 py-4 border-t flex justify-end gap-3">
                                    <button
                                        onClick={() => setShowConfig(false)}
                                        className="px-4 py-2 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition"
                                    >
                                        取消
                                    </button>
                                    <button
                                        onClick={handleSaveConfig}
                                        disabled={saveConfigMut.isPending}
                                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                                    >
                                        保存配置
                                    </button>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            )}
        </AdminShell>
    );
}

export default function AdminThemeMarketplace() {
    return (
        <AuthGuard>
            <QueryProvider>
                <ThemeMarketplaceInner/>
            </QueryProvider>
        </AuthGuard>
    );
}
