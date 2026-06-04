'use client';

import React, {useState, useMemo} from 'react';
import {useQuery, useMutation, useQueryClient} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {StatCard} from '@/components/admin/shared-ui';
import {apiClient} from '@/lib/api/base-client';
import {
  Puzzle,
  Download,
  Upload,
  Settings,
  Trash2,
  RefreshCw,
  Search,
  Star,
  ExternalLink,
  Info,
  Shield,
  Zap,
  ChevronRight,
  X,
  AlertTriangle,
  Package,
  ToggleLeft,
  ToggleRight,
  Clock,
  User,
  Globe,
  Tag
} from 'lucide-react';

/* ── 类型 ── */
interface Plugin {
  slug: string;
  name: string;
  version: string;
  description?: string;
  author?: string;
  author_url?: string;
  is_active: boolean;
  is_installed: boolean;
  capabilities?: string[];
  created_at?: string;
  updated_at?: string;
  downloads?: number;
  rating?: number;
}

/* ── 骨架屏 ── */
const PluginSkeleton = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      {[1, 2, 3, 4, 5, 6].map(i => (
          <div key={i}
               className="animate-pulse bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 overflow-hidden">
            <div className="h-2 bg-gray-200 dark:bg-gray-700"/>
            <div className="p-5 space-y-4">
              <div className="flex items-start gap-3">
                <div className="w-12 h-12 bg-gray-200 dark:bg-gray-700 rounded-xl"/>
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-32"/>
                  <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-20"/>
                </div>
              </div>
              <div className="space-y-2">
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-full"/>
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-3/4"/>
              </div>
              <div className="flex gap-1.5">
                <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded-full w-16"/>
                <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded-full w-20"/>
              </div>
              <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded-xl"/>
            </div>
          </div>
      ))}
    </div>
);

/* ── 插件卡片 ── */
const PluginCard: React.FC<{
  plugin: Plugin;
  isInstalled: boolean;
  onInstall: (slug: string) => void;
  onToggle: (slug: string, activate: boolean) => void;
  onUninstall: (slug: string) => void;
  onConfig: (plugin: Plugin) => void;
  installPending: boolean;
  togglePending: boolean;
  uninstallPending: boolean;
}> = ({
        plugin,
        isInstalled,
        onInstall,
        onToggle,
        onUninstall,
        onConfig,
        installPending,
        togglePending,
        uninstallPending
      }) => {
  const colorIdx = plugin.slug.charCodeAt(0) % 6;
  const gradients = [
    'from-blue-500 to-cyan-500',
    'from-purple-500 to-pink-500',
    'from-emerald-500 to-teal-500',
    'from-amber-500 to-orange-500',
    'from-rose-500 to-red-500',
    'from-indigo-500 to-blue-500',
  ];

  return (
      <div
          className="group relative bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 hover:border-gray-200 dark:hover:border-gray-700 hover:shadow-xl transition-all duration-300 overflow-hidden">
        {/* 顶部渐变条 */}
        <div className={`h-1.5 bg-gradient-to-r ${gradients[colorIdx]}`}/>

        <div className="p-5">
          {/* 头部 */}
          <div className="flex items-start gap-3 mb-4">
            <div
                className={`w-12 h-12 rounded-xl bg-gradient-to-br ${gradients[colorIdx]} flex items-center justify-center flex-shrink-0 shadow-lg`}>
              <Puzzle className="w-6 h-6 text-white"/>
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-gray-900 dark:text-white truncate">{plugin.name}</h3>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-xs text-gray-400">v{plugin.version}</span>
                {plugin.author && (
                    <>
                      <span className="text-gray-300 dark:text-gray-600">·</span>
                      <span className="text-xs text-gray-400 flex items-center gap-1">
                    <User className="w-3 h-3"/>
                        {plugin.author}
                  </span>
                    </>
                )}
              </div>
            </div>
            {/* 状态标签 */}
            {isInstalled && (
                <span className={`flex items-center gap-1 px-2 py-1 rounded-full text-[10px] font-semibold ${
                    plugin.is_active
                        ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400'
                        : 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'
                }`}>
              <span
                  className={`w-1.5 h-1.5 rounded-full ${plugin.is_active ? 'bg-emerald-500 animate-pulse' : 'bg-gray-400'}`}/>
                  {plugin.is_active ? '运行中' : '已停止'}
            </span>
            )}
          </div>

          {/* 描述 */}
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 line-clamp-2 leading-relaxed">
            {plugin.description || '暂无描述'}
          </p>

          {/* 标签 */}
          <div className="flex flex-wrap gap-1.5 mb-4">
            {plugin.capabilities?.slice(0, 3).map((cap: string, i: number) => (
                <span key={i}
                      className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 text-[10px] font-medium rounded-full">
              <Tag className="w-2.5 h-2.5"/>
                  {cap}
            </span>
            ))}
            {(plugin.capabilities?.length || 0) > 3 && (
              <span
                className="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 text-[10px] rounded-full">
              +{plugin.capabilities!.length - 3}
            </span>
            )}
          </div>

          {/* 元信息 */}
          {isInstalled && (
              <div className="flex items-center gap-3 mb-4 text-xs text-gray-400">
                {plugin.updated_at && (
                    <span className="flex items-center gap-1">
                <Clock className="w-3 h-3"/>
                      {new Date(plugin.updated_at).toLocaleDateString('zh-CN')}
              </span>
                )}
                {plugin.rating && (
                    <span className="flex items-center gap-1">
                <Star className="w-3 h-3 text-amber-400 fill-amber-400"/>
                      {plugin.rating.toFixed(1)}
              </span>
                )}
              </div>
          )}

          {/* 操作按钮 */}
          <div className="flex gap-2">
            {!isInstalled ? (
                <button onClick={() => onInstall(plugin.slug)} disabled={installPending}
                        className="flex-1 flex items-center justify-center gap-1.5 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-xl transition-colors disabled:opacity-50 shadow-sm">
                  {installPending ? (
                      <><span
                          className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/>安装中...</>
                  ) : (
                      <><Download className="w-4 h-4"/>安装</>
                  )}
                </button>
            ) : (
                <>
                  <button onClick={() => onToggle(plugin.slug, !plugin.is_active)} disabled={togglePending}
                          className={`flex-1 flex items-center justify-center gap-1.5 px-4 py-2.5 text-sm font-medium rounded-xl transition-colors disabled:opacity-50 ${
                              plugin.is_active
                                  ? 'bg-amber-100 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 hover:bg-amber-200 dark:hover:bg-amber-900/30'
                                  : 'bg-emerald-100 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-200 dark:hover:bg-emerald-900/30'
                          }`}>
                    {togglePending ? (
                        <span
                            className="w-4 h-4 border-2 border-current/30 border-t-current rounded-full animate-spin"/>
                    ) : (
                        plugin.is_active ? <><ToggleLeft className="w-4 h-4"/>停用</> : <><ToggleRight
                            className="w-4 h-4"/>启用</>
                    )}
                  </button>
                  <button onClick={() => onConfig(plugin)}
                          className="p-2.5 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-xl transition-colors">
                    <Settings className="w-4 h-4"/>
                  </button>
                  {!plugin.is_active && (
                      <button onClick={() => onUninstall(plugin.slug)} disabled={uninstallPending}
                              className="p-2.5 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-xl transition-colors disabled:opacity-50">
                        <Trash2 className="w-4 h-4"/>
                      </button>
                  )}
                </>
            )}
          </div>
        </div>
      </div>
  );
};

/* ── 配置弹窗 ── */
const ConfigModal: React.FC<{
  plugin: Plugin;
  onClose: () => void;
}> = ({plugin, onClose}) => (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <div
          className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 w-full max-w-lg max-h-[85vh] flex flex-col"
          onClick={e => e.stopPropagation()}>
        {/* 头部 */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
              <Settings className="w-5 h-5 text-blue-600 dark:text-blue-400"/>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white">插件配置</h3>
              <p className="text-xs text-gray-400">{plugin.name}</p>
            </div>
          </div>
          <button onClick={onClose}
                  className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800">
            <X className="w-5 h-5"/>
          </button>
        </div>

        {/* 内容 */}
        <div className="p-6 overflow-y-auto space-y-5">
          {/* 插件信息 */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">插件信息</h4>
            <div className="bg-gray-50 dark:bg-gray-800/50 rounded-xl p-4 space-y-3">
              {[
                {label: '名称', value: plugin.name},
                {label: '版本', value: `v${plugin.version}`},
                {label: '作者', value: plugin.author || 'N/A'},
                {label: '标识', value: plugin.slug},
                {label: '状态', value: plugin.is_active ? '已启用' : '已禁用'},
                {
                  label: '更新时间',
                  value: plugin.updated_at ? new Date(plugin.updated_at).toLocaleString('zh-CN') : 'N/A'
                },
              ].map(item => (
                  <div key={item.label} className="flex items-center justify-between">
                    <span className="text-sm text-gray-500 dark:text-gray-400">{item.label}</span>
                    <span className="text-sm text-gray-900 dark:text-white font-medium">{item.value}</span>
                  </div>
              ))}
            </div>
          </div>

          {/* 权限能力 */}
          {plugin.capabilities && plugin.capabilities.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">权限能力</h4>
                <div className="flex flex-wrap gap-2">
                  {plugin.capabilities.map((cap: string, i: number) => (
                      <span key={i}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 text-xs font-medium rounded-lg">
                  <Shield className="w-3 h-3"/>
                        {cap}
                </span>
                  ))}
                </div>
              </div>
          )}

          {/* 提示 */}
          <div
              className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl p-4">
            <div className="flex items-start gap-2.5">
              <Info className="w-4.5 h-4.5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0"/>
              <div>
                <p className="text-sm font-medium text-amber-800 dark:text-amber-200">配置选项开发中</p>
                <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                  此插件的详细配置选项将在后续版本中提供。当前版本仅支持启用/禁用操作。
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* 底部 */}
        <div className="flex justify-end px-6 py-4 border-t border-gray-100 dark:border-gray-800">
          <button onClick={onClose}
                  className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-xl transition-colors">
            关闭
          </button>
        </div>
      </div>
    </div>
);

/* ── 主页面 ── */
function PluginsInner() {
  const qc = useQueryClient();
  const [activeTab, setActiveTab] = useState<'installed' | 'marketplace'>('installed');
  const [searchTerm, setSearchTerm] = useState('');
  const [configPlugin, setConfigPlugin] = useState<Plugin | null>(null);
  const [uninstallTarget, setUninstallTarget] = useState<string | null>(null);

  // 查询已安装插件
  const {data: installedPlugins, isLoading: installedLoading} = useQuery({
    queryKey: ['plugins-installed'],
    queryFn: async () => {
      const res = await apiClient.get('/plugins/active');
      return res.data || [];
    },
    enabled: activeTab === 'installed'
  });

  // 查询插件市场
  const {data: marketplacePlugins, isLoading: marketplaceLoading} = useQuery({
    queryKey: ['plugins-marketplace'],
    queryFn: async () => {
      const res = await apiClient.get('/plugins/marketplace');
      return res.data || [];
    },
    enabled: activeTab === 'marketplace'
  });

  // 安装插件
  const installMut = useMutation({
    mutationFn: (slug: string) => apiClient.post('/plugins/install', {slug, capabilities: []}),
    onSuccess: () => {
      qc.invalidateQueries({queryKey: ['plugins-installed']});
      qc.invalidateQueries({queryKey: ['plugins-marketplace']});
    }
  });

  // 激活/停用插件
  const toggleMut = useMutation({
    mutationFn: ({slug, activate}: { slug: string; activate: boolean }) =>
        activate ? apiClient.post(`/plugins/${slug}/activate`) : apiClient.post(`/plugins/${slug}/deactivate`),
    onSuccess: () => qc.invalidateQueries({queryKey: ['plugins-installed']})
  });

  // 卸载插件
  const uninstallMut = useMutation({
    mutationFn: (slug: string) => apiClient.delete(`/plugins/${slug}/uninstall`),
    onSuccess: () => {
      qc.invalidateQueries({queryKey: ['plugins-installed']});
      qc.invalidateQueries({queryKey: ['plugins-marketplace']});
      setUninstallTarget(null);
    }
  });

  // 过滤
  const filteredInstalled = useMemo(() => {
    if (!installedPlugins) return [];
    if (!searchTerm.trim()) return installedPlugins;
    const q = searchTerm.toLowerCase();
    return installedPlugins.filter((p: Plugin) =>
        p.name?.toLowerCase().includes(q) || p.description?.toLowerCase().includes(q) || p.slug?.toLowerCase().includes(q)
    );
  }, [installedPlugins, searchTerm]);

  const filteredMarketplace = useMemo(() => {
    if (!marketplacePlugins) return [];
    if (!searchTerm.trim()) return marketplacePlugins;
    const q = searchTerm.toLowerCase();
    return marketplacePlugins.filter((p: Plugin) =>
        p.name?.toLowerCase().includes(q) || p.description?.toLowerCase().includes(q) || p.slug?.toLowerCase().includes(q)
    );
  }, [marketplacePlugins, searchTerm]);

  // 统计
  const stats = useMemo(() => {
    const installed = installedPlugins?.length || 0;
    const active = installedPlugins?.filter((p: Plugin) => p.is_active).length || 0;
    const available = marketplacePlugins?.length || 0;
    return {installed, active, available};
  }, [installedPlugins, marketplacePlugins]);

  const currentPlugins = activeTab === 'installed' ? filteredInstalled : filteredMarketplace;
  const isLoading = activeTab === 'installed' ? installedLoading : marketplaceLoading;

  return (
      <AdminShell title="插件市场">
        {/* 统计卡片 */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <StatCard icon={Package} label="已安装" value={stats.installed}
                    gradient="from-blue-500 to-blue-600"/>
          <StatCard icon={Zap} label="运行中" value={stats.active}
                    gradient="from-emerald-500 to-emerald-600"/>
          <StatCard icon={Globe} label="可用插件" value={stats.available}
                    gradient="from-purple-500 to-purple-600"/>
          <StatCard icon={Shield} label="安全评分" value="A+"
                    gradient="from-amber-500 to-amber-600"/>
        </div>

        {/* 标签页 + 搜索 */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 mb-6">
          {/* 标签页 */}
          <div
              className="flex items-center gap-1 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl p-1">
            <button onClick={() => setActiveTab('installed')}
                    className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                        activeTab === 'installed'
                            ? 'bg-blue-600 text-white shadow-sm'
                          : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                    }`}>
              <Puzzle className="w-4 h-4"/>
              已安装
              {stats.installed > 0 && (
                  <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-semibold ${
                      activeTab === 'installed' ? 'bg-white/20' : 'bg-gray-200 dark:bg-gray-700'
                  }`}>{stats.installed}</span>
              )}
            </button>
            <button onClick={() => setActiveTab('marketplace')}
                    className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                        activeTab === 'marketplace'
                            ? 'bg-blue-600 text-white shadow-sm'
                          : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                    }`}>
              <Download className="w-4 h-4"/>
              插件市场
            </button>
          </div>

          {/* 搜索 */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
            <input type="text" value={searchTerm} onChange={e => setSearchTerm(e.target.value)}
                   placeholder="搜索插件名称、描述..."
                   className="w-full pl-10 pr-8 py-2.5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white transition-all"/>
            {searchTerm && (
                <button onClick={() => setSearchTerm('')}
                        className="absolute right-2.5 top-1/2 -translate-y-1/2 p-0.5 text-gray-400 hover:text-gray-600">
                  <X className="w-4 h-4"/>
                </button>
            )}
          </div>
        </div>

        {/* 插件网格 */}
        {isLoading ? (
            <PluginSkeleton/>
        ) : currentPlugins.length === 0 ? (
            <div
                className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 p-16 text-center">
              <div
                  className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                {activeTab === 'installed' ? <Puzzle className="w-8 h-8 text-gray-300 dark:text-gray-600"/> :
                    <Download className="w-8 h-8 text-gray-300 dark:text-gray-600"/>}
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                {searchTerm ? '未找到匹配的插件' : activeTab === 'installed' ? '尚未安装任何插件' : '暂无可用插件'}
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
                {searchTerm ? '尝试使用不同的搜索词' : activeTab === 'installed' ? '浏览插件市场发现更多功能' : '请稍后再来查看'}
              </p>
              {activeTab === 'installed' && !searchTerm && (
                  <button onClick={() => setActiveTab('marketplace')}
                          className="inline-flex items-center gap-1.5 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-xl transition-colors">
                    <Download className="w-4 h-4"/>浏览插件市场
                  </button>
              )}
            </div>
        ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {currentPlugins.map((plugin: Plugin) => (
                  <PluginCard
                      key={plugin.slug}
                      plugin={plugin}
                      isInstalled={activeTab === 'installed' || plugin.is_installed}
                      onInstall={(slug) => installMut.mutate(slug)}
                      onToggle={(slug, activate) => toggleMut.mutate({slug, activate})}
                      onUninstall={(slug) => setUninstallTarget(slug)}
                      onConfig={setConfigPlugin}
                      installPending={installMut.isPending}
                      togglePending={toggleMut.isPending}
                      uninstallPending={uninstallMut.isPending}
                  />
              ))}
            </div>
        )}

        {/* 配置弹窗 */}
        {configPlugin && <ConfigModal plugin={configPlugin} onClose={() => setConfigPlugin(null)}/>}

        {/* 卸载确认弹窗 */}
        {uninstallTarget && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
                 onClick={() => setUninstallTarget(null)}>
              <div
                  className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 w-full max-w-md p-6"
                  onClick={e => e.stopPropagation()}>
                <div className="flex items-center gap-3 mb-4">
                  <div
                      className="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                    <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400"/>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">确认卸载插件</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">此操作不可恢复</p>
                  </div>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                  确定要卸载此插件吗？所有相关数据将被清除。
                </p>
                <div className="flex justify-end gap-3">
                  <button onClick={() => setUninstallTarget(null)}
                          className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-colors">
                    取消
                  </button>
                  <button onClick={() => uninstallMut.mutate(uninstallTarget)} disabled={uninstallMut.isPending}
                          className="px-4 py-2 text-sm font-medium bg-red-600 hover:bg-red-700 text-white rounded-xl transition-colors flex items-center gap-1.5 disabled:opacity-50">
                    {uninstallMut.isPending ? (
                        <><span
                            className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/>卸载中...</>
                    ) : (
                        <><Trash2 className="w-4 h-4"/>卸载</>
                    )}
                  </button>
                </div>
          </div>
            </div>
        )}
    </AdminShell>
  );
}

export default function AdminPlugins() {
  return <AuthGuard><QueryProvider><PluginsInner/></QueryProvider></AuthGuard>;
}
