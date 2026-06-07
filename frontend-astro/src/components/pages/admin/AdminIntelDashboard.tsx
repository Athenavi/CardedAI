'use client';

import React, {useState} from 'react';
import {useQuery, useMutation, useQueryClient} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {apiClient} from '@/lib/api/base-client';
import {useToast} from '@/components/ui/toast-provider';
import {motion, AnimatePresence} from 'framer-motion';
import {
  Activity,
  AlertTriangle,
  BookOpen,
  Clock,
  Database,
  Eye,
  FileText,
  Filter,
  Globe,
  Hash,
  Loader2,
  Newspaper,
  Plus,
  RefreshCw,
  Rss,
  Search,
  Send,
  Settings,
  TrendingUp,
  Zap,
  X,
  CheckCircle,
  XCircle,
  ExternalLink,
  BarChart3
} from 'lucide-react';

// ═══ Types ═══
interface DataSource {
  id: number;
  name: string;
  source_type: string;
  url?: string;
  config?: any;
  is_active: boolean;
  last_collected_at?: string;
  created_at: string;
}

interface CollectedItem {
  id: number;
  source_id: number;
  title: string;
  url?: string;
  content_raw?: string;
  content_cleaned?: string;
  content_hash?: string;
  metadata_json?: string;
  status: string;
  collected_at?: string;
  analyzed_at?: string;
}

interface Intelligence {
  id: number;
  title: string;
  summary: string;
  category: string;
  sentiment: string;
  importance_score: number;
  item_ids?: string;
  source_urls?: string;
  tags?: string;
  created_at: string;
}

interface Briefing {
  id: number;
  title: string;
  content: string;
  briefing_type: string;
  period_start?: string;
  period_end?: string;
  created_at: string;
}

interface AlertRule {
  id: number;
  name: string;
  rule_type: string;
  condition: any;
  actions: any;
  is_active: boolean;
  created_at: string;
}

// ═══ Tab Type ═══
type TabKey = 'sources' | 'items' | 'intelligence' | 'briefings' | 'alerts';

const TABS: { key: TabKey; label: string; icon: React.FC<any> }[] = [
  {key: 'sources', label: '数据源', icon: Database},
  {key: 'items', label: '采集条目', icon: FileText},
  {key: 'intelligence', label: '情报流', icon: Activity},
  {key: 'briefings', label: '简报', icon: Newspaper},
  {key: 'alerts', label: '预警', icon: AlertTriangle},
];

// ═══ Sentiment Badge ═══
const SENTIMENT_MAP: Record<string, { label: string; color: string }> = {
  positive: {label: '正面', color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'},
  negative: {label: '负面', color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'},
  neutral: {label: '中性', color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'},
};

const SOURCE_TYPE_MAP: Record<string, { label: string; icon: React.FC<any> }> = {
  rss: {label: 'RSS', icon: Rss},
  web: {label: '网页', icon: Globe},
  api: {label: 'API', icon: Zap},
};

// ═══ Stat Card ═══
const StatCard: React.FC<{
  label: string; value: number | string;
  icon: React.FC<any>; color: string;
}> = ({label, value, icon: Icon, color}) => {
  const colorMap: Record<string, { bg: string; text: string; icon: string }> = {
    blue: {bg: 'bg-blue-50 dark:bg-blue-900/20', text: 'text-blue-600 dark:text-blue-400', icon: 'text-blue-500'},
    green: {bg: 'bg-emerald-50 dark:bg-emerald-900/20', text: 'text-emerald-600 dark:text-emerald-400', icon: 'text-emerald-500'},
    purple: {bg: 'bg-purple-50 dark:bg-purple-900/20', text: 'text-purple-600 dark:text-purple-400', icon: 'text-purple-500'},
    orange: {bg: 'bg-orange-50 dark:bg-orange-900/20', text: 'text-orange-600 dark:text-orange-400', icon: 'text-orange-500'},
    red: {bg: 'bg-red-50 dark:bg-red-900/20', text: 'text-red-600 dark:text-red-400', icon: 'text-red-500'},
  };
  const c = colorMap[color] || colorMap.blue;
  return (
    <motion.div initial={{opacity: 0, y: 20}} animate={{opacity: 1, y: 0}}
      className="p-5 rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 card-hover">
      <div className="flex items-center gap-3 mb-3">
        <div className={`w-10 h-10 rounded-xl ${c.bg} flex items-center justify-center`}>
          <Icon className={`w-5 h-5 ${c.icon}`}/>
        </div>
        <span className="text-sm text-gray-500 dark:text-gray-400">{label}</span>
      </div>
      <p className="text-2xl font-bold text-gray-900 dark:text-white tabular-nums">{value}</p>
    </motion.div>
  );
};

// ═══ Sources Tab ═══
const SourcesPanel: React.FC = () => {
  const qc = useQueryClient();
  const toast = useToast();
  const [showCreate, setShowCreate] = useState(false);
  const [newSource, setNewSource] = useState({name: '', source_type: 'rss', url: '', config: '{}'});
  const [collectingId, setCollectingId] = useState<number | null>(null);

  const {data: sources, isLoading} = useQuery({
    queryKey: ['intel-sources'],
    queryFn: async () => {
      const res = await apiClient.get('/intel/sources');
      return res.data?.items || res.data || [];
    }
  });

  const createMutation = useMutation({
    mutationFn: async (data: typeof newSource) => {
      return apiClient.post('/intel/sources', data);
    },
    onSuccess: () => {
      qc.invalidateQueries({queryKey: ['intel-sources']});
      setShowCreate(false);
      setNewSource({name: '', source_type: 'rss', url: '', config: '{}'});
      toast.success('创建成功', '数据源已添加');
    },
    onError: (err: any) => {
      toast.error('创建失败', err?.message || '未知错误');
    }
  });

  const collectMutation = useMutation({
    mutationFn: async (id: number) => {
      setCollectingId(id);
      return apiClient.post(`/intel/sources/${id}/collect`);
    },
    onSuccess: (resp: any) => {
      setCollectingId(null);
      qc.invalidateQueries({queryKey: ['intel-sources']});
      qc.invalidateQueries({queryKey: ['intel-items']});
      qc.invalidateQueries({queryKey: ['intel-intelligence']});
      qc.invalidateQueries({queryKey: ['intel-items-count']});
      const d = resp?.data;
      if (d && typeof d === 'object' && 'total' in d) {
        const parts = [`共 ${d.total} 条`];
        if (d.new > 0) parts.push(`新增 ${d.new} 条`);
        if (d.skipped > 0) parts.push(`跳过 ${d.skipped} 条`);
        if (d.errors > 0) parts.push(`错误 ${d.errors} 条`);
        if (d.new > 0) {
          toast.success('采集完成', parts.join('，') + '。可切换到「采集条目」查看。');
        } else {
          toast.info('采集完成', parts.join('，') + '，暂无新增内容。');
        }
      } else {
        toast.success('采集成功', '数据已更新，可切换到「采集条目」查看。');
      }
    },
    onError: (err: any) => {
      setCollectingId(null);
      toast.error('采集失败', err?.message || '请检查数据源配置或网络连接');
    }
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      return apiClient.delete(`/intel/sources/${id}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({queryKey: ['intel-sources']});
      toast.success('删除成功', '数据源已移除');
    }
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">数据源管理</h3>
        <button onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors text-sm font-medium">
          <Plus className="w-4 h-4"/> 添加数据源
        </button>
      </div>

      {/* Create Form */}
      <AnimatePresence>
        {showCreate && (
          <motion.div initial={{opacity: 0, height: 0}} animate={{opacity: 1, height: 'auto'}} exit={{opacity: 0, height: 0}}
            className="overflow-hidden">
            <div className="p-5 rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">名称</label>
                  <input value={newSource.name} onChange={e => setNewSource({...newSource, name: e.target.value})}
                    className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                    placeholder="例：TechCrunch RSS"/>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">类型</label>
                  <select value={newSource.source_type} onChange={e => setNewSource({...newSource, source_type: e.target.value})}
                    className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                    <option value="rss">RSS</option>
                    <option value="web">网页</option>
                    <option value="api">API</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">URL</label>
                <input value={newSource.url} onChange={e => setNewSource({...newSource, url: e.target.value})}
                  className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="https://example.com/feed.xml"/>
              </div>
              <div className="flex gap-2 justify-end">
                <button onClick={() => setShowCreate(false)}
                  className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white">取消</button>
                <button onClick={() => createMutation.mutate(newSource)} disabled={createMutation.isPending}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 text-sm font-medium disabled:opacity-50">
                  {createMutation.isPending && <Loader2 className="w-4 h-4 animate-spin"/>}
                  创建
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Sources List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-blue-500"/></div>
      ) : sources?.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <Database className="w-12 h-12 mx-auto mb-3 opacity-50"/>
          <p>暂无数据源，点击上方按钮添加</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {sources?.map((src: DataSource) => {
            const typeInfo = SOURCE_TYPE_MAP[src.source_type] || {label: src.source_type, icon: Globe};
            const TypeIcon = typeInfo.icon;
            return (
              <motion.div key={src.id} initial={{opacity: 0}} animate={{opacity: 1}}
                className="flex items-center justify-between p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 hover:border-blue-300 dark:hover:border-blue-700 transition-colors">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center">
                    <TypeIcon className="w-5 h-5 text-blue-500"/>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900 dark:text-white">{src.name}</h4>
                    <p className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-2">
                      <span className="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-xs">{typeInfo.label}</span>
                      {src.url && <span className="truncate max-w-[200px]">{src.url}</span>}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${src.is_active ? 'bg-emerald-500' : 'bg-gray-400'}`}/>
                  {src.last_collected_at && (
                    <span className="text-xs text-gray-500">
                      {new Date(src.last_collected_at).toLocaleString('zh-CN')}
                    </span>
                  )}
                  <button onClick={() => collectMutation.mutate(src.id)} disabled={collectingId !== null}
                    className="p-2 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 text-blue-600 dark:text-blue-400 transition-colors"
                    title="立即采集">
                    <RefreshCw className={`w-4 h-4 ${collectingId === src.id ? 'animate-spin' : ''}`}/>
                  </button>
                  <button onClick={() => { if (confirm('确定删除此数据源？')) deleteMutation.mutate(src.id); }}
                    className="p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 text-red-500 transition-colors"
                    title="删除">
                    <X className="w-4 h-4"/>
                  </button>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
};

// ═══ Items Tab ═══
const ItemsPanel: React.FC = () => {
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const {data: resp, isLoading} = useQuery({
    queryKey: ['intel-items', status, page],
    queryFn: async () => {
      const params: any = {page, per_page: 20};
      if (status) params.status = status;
      const res = await apiClient.get('/intel/items', params);
      return res;
    }
  });

  const items: CollectedItem[] = Array.isArray(resp?.data) ? resp.data : [];
  const total = resp?.pagination?.total || items.length;

  const STATUS_MAP: Record<string, { label: string; color: string }> = {
    raw: {label: '待处理', color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'},
    cleaned: {label: '已清洗', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'},
    analyzed: {label: '已分析', color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'},
    error: {label: '错误', color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'},
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">采集条目</h3>
        <div className="flex items-center gap-2">
          <select value={status} onChange={e => {setStatus(e.target.value); setPage(1);}}
            className="px-3 py-1.5 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm">
            <option value="">全部状态</option>
            <option value="raw">待处理</option>
            <option value="cleaned">已清洗</option>
            <option value="analyzed">已分析</option>
            <option value="error">错误</option>
          </select>
          <span className="text-sm text-gray-500">共 {total} 条</span>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-blue-500"/></div>
      ) : items.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <FileText className="w-12 h-12 mx-auto mb-3 opacity-50"/>
          <p>暂无采集条目</p>
          <p className="text-xs mt-1">在「数据源」页面点击采集按钮获取数据</p>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => {
            const s = STATUS_MAP[item.status] || STATUS_MAP.raw;
            const isExpanded = expandedId === item.id;
            return (
              <motion.div key={item.id} initial={{opacity: 0, x: -10}} animate={{opacity: 1, x: 0}}
                className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 overflow-hidden">
                <div className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                  onClick={() => setExpandedId(isExpanded ? null : item.id)}>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-medium text-gray-900 dark:text-white truncate">{item.title || '无标题'}</h4>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${s.color}`}>{s.label}</span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
                      <span>来源 #{item.source_id}</span>
                      {item.url && <a href={item.url} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()}
                        className="text-blue-500 hover:text-blue-600 flex items-center gap-0.5 truncate max-w-[250px]">
                        <ExternalLink className="w-3 h-3"/> {item.url}
                      </a>}
                      <span>{item.collected_at ? new Date(item.collected_at).toLocaleString('zh-CN') : '-'}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 ml-4">
                    <Eye className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''} text-gray-400`}/>
                  </div>
                </div>
                <AnimatePresence>
                  {isExpanded && (
                    <motion.div initial={{height: 0, opacity: 0}} animate={{height: 'auto', opacity: 1}} exit={{height: 0, opacity: 0}}
                      className="overflow-hidden">
                      <div className="px-4 pb-4 pt-0 border-t border-gray-100 dark:border-gray-800">
                        {item.content_cleaned && (
                          <div className="mt-3">
                            <h5 className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">清洗内容</h5>
                            <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap line-clamp-8">{item.content_cleaned}</p>
                          </div>
                        )}
                        {item.content_raw && (
                          <div className="mt-3">
                            <h5 className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">原始内容</h5>
                            <pre className="text-xs text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 rounded-lg p-3 overflow-x-auto max-h-48">
                              {item.content_raw}
                            </pre>
                          </div>
                        )}
                        {!item.content_cleaned && !item.content_raw && (
                          <p className="text-sm text-gray-400 mt-3">暂无详细内容</p>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })}

          {/* Pagination */}
          {total > 20 && (
            <div className="flex items-center justify-center gap-2 pt-4">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                className="px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-sm disabled:opacity-50">
                上一页
              </button>
              <span className="text-sm text-gray-500">{page} / {Math.ceil(total / 20)}</span>
              <button onClick={() => setPage(p => p + 1)} disabled={page >= Math.ceil(total / 20)}
                className="px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-sm disabled:opacity-50">
                下一页
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ═══ Intelligence Tab ═══
const IntelligencePanel: React.FC = () => {
  const [category, setCategory] = useState('');
  const [sentiment, setSentiment] = useState('');
  const [page, setPage] = useState(1);

  const {data: resp, isLoading} = useQuery({
    queryKey: ['intel-intelligence', category, sentiment, page],
    queryFn: async () => {
      const params: any = {page, per_page: 20};
      if (category) params.category = category;
      if (sentiment) params.sentiment = sentiment;
      const res = await apiClient.get('/intel/intelligence', params);
      return res;
    }
  });

  const items: Intelligence[] = Array.isArray(resp?.data) ? resp.data : [];
  const total = resp?.pagination?.total || items.length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">情报流</h3>
        <div className="flex items-center gap-2">
          <select value={category} onChange={e => {setCategory(e.target.value); setPage(1);}}
            className="px-3 py-1.5 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm">
            <option value="">全部分类</option>
            <option value="tech">科技</option>
            <option value="finance">金融</option>
            <option value="security">安全</option>
            <option value="market">市场</option>
          </select>
          <select value={sentiment} onChange={e => {setSentiment(e.target.value); setPage(1);}}
            className="px-3 py-1.5 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm">
            <option value="">全部情感</option>
            <option value="positive">正面</option>
            <option value="neutral">中性</option>
            <option value="negative">负面</option>
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-blue-500"/></div>
      ) : items.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <Activity className="w-12 h-12 mx-auto mb-3 opacity-50"/>
          <p>暂无情报数据</p>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => {
            const s = SENTIMENT_MAP[item.sentiment] || SENTIMENT_MAP.neutral;
            return (
              <motion.div key={item.id} initial={{opacity: 0, x: -10}} animate={{opacity: 1, x: 0}}
                className="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 hover:border-blue-300 dark:hover:border-blue-700 transition-colors">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-medium text-gray-900 dark:text-white truncate">{item.title}</h4>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${s.color}`}>{s.label}</span>
                      {item.category && (
                        <span className="px-2 py-0.5 rounded-full text-xs bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                          {item.category}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">{item.summary}</p>
                    {item.tags && (
                      <div className="flex items-center gap-1.5 mt-2">
                        {item.tags.split(',').slice(0, 5).map((tag, i) => (
                          <span key={i} className="flex items-center gap-0.5 px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-xs text-gray-600 dark:text-gray-400">
                            <Hash className="w-3 h-3"/>{tag.trim()}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="flex flex-col items-end gap-2 shrink-0">
                    <div className="flex items-center gap-1">
                      {Array.from({length: 5}).map((_, i) => (
                        <div key={i} className={`w-1.5 h-4 rounded-sm ${i < (Number(item.importance_score) || 0) ? 'bg-amber-400' : 'bg-gray-200 dark:bg-gray-700'}`}/>
                      ))}
                    </div>
                    <span className="text-xs text-gray-500">{new Date(item.created_at).toLocaleString('zh-CN')}</span>
                    {item.source_urls && (() => {
                      try {
                        const urls = JSON.parse(item.source_urls);
                        const firstUrl = Array.isArray(urls) ? urls[0] : typeof urls === 'string' ? urls : null;
                        return firstUrl ? (
                          <a href={firstUrl} target="_blank" rel="noopener noreferrer"
                            className="text-blue-500 hover:text-blue-600">
                            <ExternalLink className="w-4 h-4"/>
                          </a>
                        ) : null;
                      } catch { return null; }
                    })()}
                  </div>
                </div>
              </motion.div>
            );
          })}

          {/* Pagination */}
          {total > 20 && (
            <div className="flex items-center justify-center gap-2 pt-4">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                className="px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-sm disabled:opacity-50">
                上一页
              </button>
              <span className="text-sm text-gray-500">{page} / {Math.ceil(total / 20)}</span>
              <button onClick={() => setPage(p => p + 1)} disabled={page >= Math.ceil(total / 20)}
                className="px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-sm disabled:opacity-50">
                下一页
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ═══ Briefings Tab ═══
const BriefingsPanel: React.FC = () => {
  const qc = useQueryClient();
  const [generating, setGenerating] = useState(false);
  const [genConfig, setGenConfig] = useState({briefing_type: 'daily', topic: '', days: 7});

  const {data: briefings, isLoading} = useQuery({
    queryKey: ['intel-briefings'],
    queryFn: async () => {
      const res = await apiClient.get('/intel/briefings');
      return res.data?.items || res.data || [];
    }
  });

  const generateMutation = useMutation({
    mutationFn: async () => {
      // Backend expects query params for this endpoint, build URL with params
      const qs = new URLSearchParams(
        Object.entries(genConfig).filter(([, v]) => v !== undefined && v !== null && v !== '')
          .map(([k, v]) => [k, String(v)])
      ).toString();
      return apiClient.post(`/intel/briefings/generate${qs ? '?' + qs : ''}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({queryKey: ['intel-briefings']});
    }
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">情报简报</h3>
      </div>

      {/* Generate */}
      <div className="p-5 rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
        <h4 className="font-medium text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <Send className="w-4 h-4 text-blue-500"/> 生成新简报
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">类型</label>
            <select value={genConfig.briefing_type} onChange={e => setGenConfig({...genConfig, briefing_type: e.target.value})}
              className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm">
              <option value="daily">日报</option>
              <option value="weekly">周报</option>
              <option value="monthly">月报</option>
              <option value="topic">专题</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">主题（可选）</label>
            <input value={genConfig.topic} onChange={e => setGenConfig({...genConfig, topic: e.target.value})}
              className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm"
              placeholder="例：人工智能"/>
          </div>
          <div>
            <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">天数</label>
            <input type="number" value={genConfig.days} min={1} max={30}
              onChange={e => setGenConfig({...genConfig, days: parseInt(e.target.value) || 7})}
              className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm"/>
          </div>
        </div>
        <div className="mt-4 flex justify-end">
          <button onClick={() => generateMutation.mutate()} disabled={generateMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 text-sm font-medium disabled:opacity-50">
            {generateMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin"/> : <Zap className="w-4 h-4"/>}
            生成简报
          </button>
        </div>
        {generateMutation.isError && (
          <p className="mt-2 text-sm text-red-500">生成失败：{(generateMutation.error as any)?.message || '未知错误'}</p>
        )}
      </div>

      {/* Briefings List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-blue-500"/></div>
      ) : briefings?.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <Newspaper className="w-12 h-12 mx-auto mb-3 opacity-50"/>
          <p>暂无简报</p>
        </div>
      ) : (
        <div className="space-y-3">
          {briefings?.map((b: Briefing) => (
            <motion.div key={b.id} initial={{opacity: 0}} animate={{opacity: 1}}
              className="p-5 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h4 className="font-medium text-gray-900 dark:text-white">{b.title}</h4>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="px-2 py-0.5 rounded-full text-xs bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">
                      {b.briefing_type === 'daily' ? '日报' : b.briefing_type === 'weekly' ? '周报' : b.briefing_type === 'monthly' ? '月报' : '专题'}
                    </span>
                    <span className="text-xs text-gray-500">{new Date(b.created_at).toLocaleString('zh-CN')}</span>
                  </div>
                </div>
              </div>
              <div className="prose prose-sm dark:prose-invert max-w-none text-gray-600 dark:text-gray-400 line-clamp-4 whitespace-pre-wrap">
                {b.content}
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
};

// ═══ Alerts Tab ═══
const AlertsPanel: React.FC = () => {
  const qc = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [newRule, setNewRule] = useState({
    name: '', rule_type: 'keyword', condition: '{}', actions: '{"log": true}', is_active: true
  });

  const {data: rules, isLoading} = useQuery({
    queryKey: ['intel-alert-rules'],
    queryFn: async () => {
      const res = await apiClient.get('/intel/alerts/rules');
      return res.data?.items || res.data || [];
    }
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      let condition: any, actions: any;
      try { condition = JSON.parse(newRule.condition); } catch { condition = {}; }
      try { actions = JSON.parse(newRule.actions); } catch { actions = {log: true}; }
      return apiClient.post('/intel/alerts/rules', {
        name: newRule.name, rule_type: newRule.rule_type, condition, actions, is_active: newRule.is_active
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({queryKey: ['intel-alert-rules']});
      setShowCreate(false);
    }
  });

  const RULE_TYPE_LABELS: Record<string, string> = {
    keyword: '关键词匹配',
    sentiment: '情感监控',
    threshold: '阈值预警',
    anomaly: '异常检测',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">预警规则</h3>
        <button onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 text-sm font-medium">
          <Plus className="w-4 h-4"/> 添加规则
        </button>
      </div>

      {/* Create Form */}
      <AnimatePresence>
        {showCreate && (
          <motion.div initial={{opacity: 0, height: 0}} animate={{opacity: 1, height: 'auto'}} exit={{opacity: 0, height: 0}}
            className="overflow-hidden">
            <div className="p-5 rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">规则名称</label>
                  <input value={newRule.name} onChange={e => setNewRule({...newRule, name: e.target.value})}
                    className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm"/>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">规则类型</label>
                  <select value={newRule.rule_type} onChange={e => setNewRule({...newRule, rule_type: e.target.value})}
                    className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm">
                    {Object.entries(RULE_TYPE_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">条件（JSON）</label>
                <textarea value={newRule.condition} onChange={e => setNewRule({...newRule, condition: e.target.value})} rows={3}
                  className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm font-mono"/>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">动作（JSON）</label>
                <textarea value={newRule.actions} onChange={e => setNewRule({...newRule, actions: e.target.value})} rows={3}
                  className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm font-mono"/>
              </div>
              <div className="flex gap-2 justify-end">
                <button onClick={() => setShowCreate(false)}
                  className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">取消</button>
                <button onClick={() => createMutation.mutate()} disabled={createMutation.isPending}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 text-sm font-medium disabled:opacity-50">
                  {createMutation.isPending && <Loader2 className="w-4 h-4 animate-spin"/>}
                  创建规则
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Rules List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-blue-500"/></div>
      ) : rules?.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <AlertTriangle className="w-12 h-12 mx-auto mb-3 opacity-50"/>
          <p>暂无预警规则</p>
        </div>
      ) : (
        <div className="grid gap-3">
          {rules?.map((rule: AlertRule) => (
            <motion.div key={rule.id} initial={{opacity: 0}} animate={{opacity: 1}}
              className="flex items-center justify-between p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
              <div className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full ${rule.is_active ? 'bg-emerald-500' : 'bg-gray-400'}`}/>
                <div>
                  <h4 className="font-medium text-gray-900 dark:text-white">{rule.name}</h4>
                  <p className="text-xs text-gray-500">{RULE_TYPE_LABELS[rule.rule_type] || rule.rule_type}</p>
                </div>
              </div>
              <span className="text-xs text-gray-500">{new Date(rule.created_at).toLocaleString('zh-CN')}</span>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
};

// ═══ Main Component ═══
function IntelDashboardInner() {
  const [activeTab, setActiveTab] = useState<TabKey>('sources');

  // Stats
  const {data: sourcesData} = useQuery({
    queryKey: ['intel-sources-count'],
    queryFn: async () => { const r = await apiClient.get('/intel/sources', {per_page: 1}); return r.data?.total || 0; }
  });
  const {data: intelData} = useQuery({
    queryKey: ['intel-count'],
    queryFn: async () => { const r = await apiClient.get('/intel/intelligence', {per_page: 1}); return r.data?.total || 0; }
  });
  const {data: briefingsData} = useQuery({
    queryKey: ['intel-briefings-count'],
    queryFn: async () => { const r = await apiClient.get('/intel/briefings', {per_page: 1}); return r.data?.total || 0; }
  });
  const {data: alertsData} = useQuery({
    queryKey: ['intel-alerts-count'],
    queryFn: async () => { const r = await apiClient.get('/intel/alerts/rules', {per_page: 1}); return r.data?.total || 0; }
  });

  const renderTab = () => {
    switch (activeTab) {
      case 'sources': return <SourcesPanel/>;
      case 'items': return <ItemsPanel/>;
      case 'intelligence': return <IntelligencePanel/>;
      case 'briefings': return <BriefingsPanel/>;
      case 'alerts': return <AlertsPanel/>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
          <Activity className="w-7 h-7 text-blue-500"/>
          情报中心
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">数据采集、情报分析、简报生成与预警管理</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="数据源" value={sourcesData ?? '—'} icon={Database} color="blue"/>
        <StatCard label="情报数" value={intelData ?? '—'} icon={TrendingUp} color="green"/>
        <StatCard label="简报数" value={briefingsData ?? '—'} icon={Newspaper} color="purple"/>
        <StatCard label="预警规则" value={alertsData ?? '—'} icon={AlertTriangle} color="orange"/>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 p-1 bg-gray-100 dark:bg-gray-800 rounded-xl w-fit">
        {TABS.map(({key, label, icon: Icon}) => (
          <button key={key} onClick={() => setActiveTab(key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === key
                ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}>
            <Icon className="w-4 h-4"/>
            {label}
          </button>
        ))}
      </div>

      {/* Content */}
      <AnimatePresence mode="wait">
        <motion.div key={activeTab} initial={{opacity: 0, y: 10}} animate={{opacity: 1, y: 0}} exit={{opacity: 0, y: -10}}>
          {renderTab()}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

// ═══ Export with Providers ═══
export default function AdminIntelDashboard() {
  return (
    <AuthGuard>
      <QueryProvider>
        <AdminShell title="情报中心">
          <IntelDashboardInner/>
        </AdminShell>
      </QueryProvider>
    </AuthGuard>
  );
}
